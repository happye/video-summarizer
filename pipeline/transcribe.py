import os
import json
import math
import torch
import subprocess
import tempfile

# 模型配置
MODEL_ID = "Qwen/Qwen3-ASR-1.7B"
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# modelscope 在 Windows 下载时 . 会被替换为 ___
_MODEL_CANDIDATES = [
    os.path.join(_PROJECT_ROOT, "models", "Qwen", "Qwen3-ASR-1.7B"),
    os.path.join(_PROJECT_ROOT, "models", "models", "Qwen", "Qwen3-ASR-1.7B"),
    os.path.join(_PROJECT_ROOT, "models", "models", "Qwen", "Qwen3-ASR-1___7B"),
    os.path.join(_PROJECT_ROOT, "models", "Qwen3-ASR-1.7B"),
]
# 中文转录语言标识（qwen-asr 要求全称，非 ISO code）
_ASR_LANGUAGE = "Chinese"
# 单 chunk 转录最大生成 token 数
_ASR_MAX_NEW_TOKENS = 4096
# 手动分 chunk 的音频长度（秒）。
# qwen-asr 默认 1200s/chunk 对 16GB 显存太大（cross-attention KV Cache 爆显存），
# 300s/chunk 在 16GB 显存上峰值约 8-10GB，留足够余量。
_CHUNK_SECONDS = 300

# 全局模型实例（懒加载，避免交互模式启动慢）
_model = None


def _find_model_path():
    """查找本地模型路径，找不到则返回 ModelScope ID 在线加载"""
    for path in _MODEL_CANDIDATES:
        if os.path.isdir(path) and any(f.endswith(".safetensors") for f in os.listdir(path)):
            return path
    return MODEL_ID


def _get_model():
    """懒加载 Qwen3-ASR 模型"""
    global _model
    if _model is None:
        from qwen_asr import Qwen3ASRModel

        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if device == "cuda" else torch.float32

        model_path = _find_model_path()
        print(f"[ASR] Loading Qwen3-ASR from: {model_path}")

        # 注意：Qwen3ASRModel.from_pretrained 不会自动把模型放到 GPU，
        # 必须加载后手动迁移，否则会在 CPU 上推理，慢 100 倍以上。
        _model = Qwen3ASRModel.from_pretrained(
            model_path,
            dtype=dtype,
        )
        # 设置 max_new_tokens（from_pretrained 不一定透传此参数）
        _model.max_new_tokens = _ASR_MAX_NEW_TOKENS
        if device == "cuda":
            _model.model = _model.model.to("cuda")
        print(f"[ASR] Model loaded on {device} ({dtype}), max_new_tokens={_ASR_MAX_NEW_TOKENS}")
    return _model


def _extract_audio(video_path, output_wav):
    """用 ffmpeg 从视频提取 16kHz 单声道 PCM 音频"""
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-ar", "16000", "-ac", "1",
        "-acodec", "pcm_s16le", "-f", "wav",
        output_wav,
    ]
    # 注意：capture_output=True 会导致 ffmpeg 的 stderr 进度输出填满管道缓冲区，
    # 在 Windows 上引发死锁。这里丢弃 stdout，仅在失败时读取 stderr。
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if result.returncode != 0:
        err = result.stderr.decode("utf-8", errors="ignore")[:500]
        raise RuntimeError(f"ffmpeg failed: {err}")


def _transcribe_chunk(model, audio_chunk, sr):
    """转录单个音频 chunk，返回文本"""
    results = model.transcribe(
        (audio_chunk, sr),
        language=_ASR_LANGUAGE,
        return_time_stamps=False,
    )
    transcription = results[0] if results else None
    if transcription:
        if hasattr(transcription, "text"):
            return transcription.text or ""
        elif isinstance(transcription, dict):
            return transcription.get("text", "")
    return ""


def transcribe_video(video_path):
    """使用 Qwen3-ASR 转录视频，输出兼容 {text, segments} 格式"""
    print(f"Transcribing video {video_path}...")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU device name: {torch.cuda.get_device_name(0)}")
        print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    print(f"Using device: {device}")

    model = _get_model()

    # 提取音频到临时 wav 文件
    temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_wav.close()
    try:
        print("Extracting audio with ffmpeg...")
        _extract_audio(video_path, temp_wav.name)

        # 用 soundfile 直接读取（比 librosa.load 快 100 倍以上）。
        # ffmpeg 输出已是 16kHz mono，无需重采样。
        import soundfile as sf
        import numpy as np
        audio_array, sr = sf.read(temp_wav.name, dtype="float32", always_2d=False)
        if audio_array.ndim > 1:
            audio_array = audio_array.mean(axis=-1).astype(np.float32)
        total_seconds = len(audio_array) / sr
        print(f"Audio loaded: {total_seconds:.1f}s, {sr}Hz")

        # 手动按 _CHUNK_SECONDS 分 chunk 转录，避免长音频 cross-attention KV Cache 爆显存
        chunk_samples = _CHUNK_SECONDS * sr
        num_chunks = math.ceil(len(audio_array) / chunk_samples)
        all_text_parts = []

        if num_chunks <= 1:
            # 短音频直接转录
            print("Transcribing with Qwen3-ASR (single chunk)...")
            text = _transcribe_chunk(model, audio_array, sr)
            all_text_parts.append(text)
        else:
            # 长音频分 chunk 转录
            print(f"Transcribing with Qwen3-ASR ({num_chunks} chunks × {_CHUNK_SECONDS}s)...")
            for i in range(num_chunks):
                start = i * chunk_samples
                end = min(start + chunk_samples, len(audio_array))
                chunk_audio = audio_array[start:end]
                chunk_dur = len(chunk_audio) / sr

                print(f"  Chunk {i+1}/{num_chunks} ({chunk_dur:.1f}s)...")
                text = _transcribe_chunk(model, chunk_audio, sr)
                all_text_parts.append(text)

                # 释放上一轮 KV Cache 显存
                if device == "cuda":
                    torch.cuda.empty_cache()

        full_text = "".join(all_text_parts)

        # Qwen3-ASR 在 return_time_stamps=False 时不返回时间戳，
        # 用整段文本作为单个 segment 保持输出格式兼容
        segments = [{"start": 0, "end": 0, "text": full_text}] if full_text else []
        result = {"text": full_text, "segments": segments}

        # 保存
        from config import TRANSCRIPT_PATH
        print(f"TRANSCRIPT_PATH: {TRANSCRIPT_PATH}")
        transcript_dir = os.path.dirname(TRANSCRIPT_PATH)
        if not os.path.exists(transcript_dir):
            os.makedirs(transcript_dir, exist_ok=True)

        with open(TRANSCRIPT_PATH, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"Transcription completed! {len(segments)} segments, {len(full_text)} chars")
        return TRANSCRIPT_PATH

    finally:
        if os.path.exists(temp_wav.name):
            os.unlink(temp_wav.name)
