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
# Qwen3-ASR 默认 512，官方推荐长音频设 200000。
# 4096 对密集语速的 300s chunk 可能截断（截尾不截头，但仍丢数据）。
# 65536 对 300s chunk 绰绰有余，KV Cache 随实际生成量增长，不会预分配。
_ASR_MAX_NEW_TOKENS = 65536
# 手动分 chunk 的音频长度（秒）。
# qwen-asr 默认 1200s/chunk 对 16GB 显存太大（cross-attention KV Cache 爆显存），
# 300s/chunk 在 16GB 显存上峰值约 8-10GB，留足够余量。
_CHUNK_SECONDS = 300
# chunk 间重叠时长（秒）。重叠确保句子不被截断，转录后通过文本去重消除重复。
_OVERLAP_SECONDS = 30

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


# 递归细分的最小粒度(秒)。低于此长度不再切分,避免片段过短影响 ASR 质量。
_ASR_MIN_SUBSEC = 15


def _transcribe_with_fallback(model, audio, sr, depth=0):
    """递归细分转录:返回空则对半切分重试,直到找到有文本的片段或达到最小粒度。

    Qwen3-ASR 遇到以音乐/片头开头的音频,可能对整段返回空文本(language None)。
    对半切分后,纯音乐片段返回空(继续细分),说话片段返回文本(停止细分),
    最终拼接所有有文本的片段,确保无论音乐持续多久都不丢失说话内容。

    示例(300s chunk,开头 90s 音乐):
      300s 空 → 150s+150s
      150s(0-150s,含音乐)空 → 75s+75s
      75s(0-75s,纯音乐)空 → 37.5s+37.5s(都≤15s阈值附近,停止)
      75s(75-150s,音乐尾+说话)有文本 → 保留
      150s(150-300s,纯说话)有文本 → 保留
    """
    dur = len(audio) / sr
    text = _transcribe_chunk(model, audio, sr)

    if text:
        return text
    if dur <= _ASR_MIN_SUBSEC:
        return ""  # 达到最小粒度仍为空,判定为纯非语音,丢弃

    # 返回空且片段够大,对半切分递归
    indent = "  " * (depth + 1)
    print(f"{indent}├─ Empty ({dur:.0f}s), split → {dur/2:.0f}s + {dur/2:.0f}s")
    mid = len(audio) // 2
    left = _transcribe_with_fallback(model, audio[:mid], sr, depth + 1)
    right = _transcribe_with_fallback(model, audio[mid:], sr, depth + 1)
    return left + right


def _deduplicate_overlap(prev_text, curr_text, min_overlap_chars=6):
    """去除重叠区域的重复文本。

    前一个 chunk 的尾部与当前 chunk 的头部包含相同音频的转录，
    通过在 prev 尾部搜索 curr 头部的子串找到重叠点，只保留新增部分。
    """
    if not prev_text or not curr_text:
        return curr_text

    # 搜索范围：prev 最后 200 字 vs curr 前 200 字
    search_range = min(200, len(prev_text), len(curr_text))
    prev_tail = prev_text[-search_range:]

    # 从长到短搜索 prev_tail 中的子串是否出现在 curr 头部
    best_cut = 0
    for length in range(min(search_range, 150), min_overlap_chars - 1, -1):
        # 在 prev_tail 中取长度为 length 的子串
        for start in range(len(prev_tail) - length + 1):
            candidate = prev_tail[start:start + length]
            pos = curr_text.find(candidate)
            if pos != -1 and pos <= 100:  # 重叠必须在 curr 头部附近
                best_cut = pos + length
                break
        if best_cut > 0:
            break

    if best_cut > 0:
        return curr_text[best_cut:]
    return curr_text


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
        # chunk 间有 _OVERLAP_SECONDS 重叠，转录后通过文本去重消除重复
        chunk_samples = _CHUNK_SECONDS * sr
        overlap_samples = _OVERLAP_SECONDS * sr
        step_samples = chunk_samples - overlap_samples  # 实际步进
        num_chunks = max(1, math.ceil((len(audio_array) - overlap_samples) / step_samples))
        all_text_parts = []

        if num_chunks <= 1 or len(audio_array) <= chunk_samples:
            # 短音频直接转录（无需重叠）
            print("Transcribing with Qwen3-ASR (single chunk)...")
            text = _transcribe_with_fallback(model, audio_array, sr)
            all_text_parts.append(text)
        else:
            # 长音频分 chunk 转录（带重叠 + 去重）
            print(f"Transcribing with Qwen3-ASR ({num_chunks} chunks × {_CHUNK_SECONDS}s, overlap {_OVERLAP_SECONDS}s)...")
            prev_text = ""
            for i in range(num_chunks):
                start = i * step_samples
                end = min(start + chunk_samples, len(audio_array))
                chunk_audio = audio_array[start:end]
                chunk_dur = len(chunk_audio) / sr

                print(f"  Chunk {i+1}/{num_chunks} ({chunk_dur:.1f}s)...")

                # 所有 chunk 统一用递归细分转录:
                # 正常 chunk(说话开头)一次返回文本,零额外开销;
                # 音乐开头/中间音乐间奏导致空返回时,自动对半切分递归,
                # 保留音乐后的说话内容,无论音乐出现在哪个位置。
                raw_text = _transcribe_with_fallback(model, chunk_audio, sr)
                print(f"    raw: {len(raw_text)} chars")

                if not raw_text:
                    print(f"    ⚠ Chunk {i+1} returned empty text!")

                # 去除与上一个 chunk 重叠部分的重复文本
                if prev_text:
                    text = _deduplicate_overlap(prev_text, raw_text)
                else:
                    text = raw_text

                all_text_parts.append(text)
                prev_text = raw_text  # 用原始文本（非去重后）作为下一轮重叠比对基准

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
