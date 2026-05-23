import json
import os
from llm.adapter import LLMAdapter
from llm.kimi_client import KimiClient
from llm.deepseek_client import DeepSeekClient

CORRECT_PROMPT = """请对以下语音转录文本进行错别字纠正。

这是一段由语音识别（ASR）生成的转录文本，可能存在以下类型的错误：
1. 同音字/近音字替换（如"上证"被识别为"上涨"、"蓝筹"被识别为"蓝球"）
2. 专业术语误识别（如"PE估值"被识别为"PE骨直"、"MACD"被识别为"麦克迪"）
3. 语气词、口头禅的误识别
4. 人名、地名、机构名的误识别

纠正规则：
- 只修改明确的错误，不要改变原文的语义和表达
- 不要润色、不要改写、不要添加内容
- 不要修改口语化的表达（如"就是说"、"然后"等口头禅保留原样）
- 不要添加标点或改变标点风格
- 如果不确定是否为错误，保留原文
- 输出完整的纠正后文本，不要省略任何部分

转录文本：
{text}

纠正后的文本："""

CORRECT_BATCH_PROMPT = """请对以下语音转录文本片段进行错别字纠正。

这是由语音识别（ASR）生成的文本，可能存在同音字替换、专业术语误识别等错误。

纠正规则：
- 只修改明确的错误，不改变语义和表达
- 不润色、不改写、不添加内容
- 口语化表达保留原样
- 不确定则保留原文
- 输出完整纠正后文本，不省略

转录文本片段：
{chunk}

纠正后的文本："""


def estimate_tokens(text):
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    total_words = len(text.split())
    english_words = max(0, total_words - chinese_chars)
    return max(1, int(chinese_chars / 1.5 + english_words / 0.25))


def correct_transcript(transcript_path, llm_provider="deepseek"):
    """对转录文本进行AI纠错，返回纠错后的文本文件路径"""
    corrected_path = transcript_path.replace(".json", "_corrected.json")
    diff_path = transcript_path.replace(".json", "_correction_diff.json")

    if os.path.exists(corrected_path):
        print(f"[CORRECT] Corrected transcript already exists: {corrected_path}")
        return corrected_path

    with open(transcript_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    segments = data.get("segments", [])
    if not segments:
        print("[CORRECT] No segments found in transcript, skipping correction")
        return transcript_path

    original_text = " ".join([seg.get("text", "") for seg in segments])
    if not original_text.strip():
        print("[CORRECT] Empty transcript, skipping correction")
        return transcript_path

    total_tokens = estimate_tokens(original_text)
    print(f"[CORRECT] Original transcript: {len(original_text)} chars, ~{total_tokens} tokens")

    if llm_provider == "kimi":
        client = KimiClient()
        adapter = None
        max_context_tokens = 194000
    elif llm_provider == "deepseek":
        client = DeepSeekClient()
        adapter = None
        max_context_tokens = 378000
    else:
        client = None
        adapter = LLMAdapter(llm_provider)
        max_context_tokens = 122000

    corrected_text = _correct_text(original_text, total_tokens, max_context_tokens, client, adapter, llm_provider)

    if not corrected_text or not corrected_text.strip():
        print("[CORRECT] Correction returned empty, falling back to original")
        return transcript_path

    _save_diff(original_text, corrected_text, diff_path)

    corrected_segments = _apply_corrections(segments, original_text, corrected_text)

    corrected_data = dict(data)
    corrected_data["segments"] = corrected_segments
    corrected_data["correction_applied"] = True

    with open(corrected_path, "w", encoding="utf-8") as f:
        json.dump(corrected_data, f, ensure_ascii=False, indent=2)

    print(f"[CORRECT] Corrected transcript saved to: {corrected_path}")
    print(f"[CORRECT] Correction diff saved to: {diff_path}")

    return corrected_path


def _correct_text(text, total_tokens, max_context_tokens, client, adapter, llm_provider):
    """根据文本长度选择单次或分批纠错"""
    if total_tokens <= max_context_tokens * 0.7:
        print(f"[CORRECT] Single request correction ({total_tokens} tokens)")
        return _correct_single(text, client, adapter)

    print(f"[CORRECT] Batch correction ({total_tokens} tokens > {int(max_context_tokens * 0.7)})")
    return _correct_batch(text, max_context_tokens, client, adapter)


def _correct_single(text, client, adapter):
    prompt = CORRECT_PROMPT.format(text=text)
    try:
        if client:
            return client.generate(prompt, reset_context=True)
        else:
            return adapter.generate(prompt)
    except Exception as e:
        print(f"[CORRECT] Single correction failed: {e}")
        return None


def _correct_batch(text, max_context_tokens, client, adapter):
    batch_limit = int(max_context_tokens * 0.6)
    chunk_size = batch_limit

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            last_period = text.rfind("。", start, end)
            last_comma = text.rfind("，", start, end)
            last_space = text.rfind(" ", start, end)
            break_point = max(last_period, last_comma, last_space)
            if break_point > start + chunk_size // 2:
                end = break_point + 1
        chunks.append(text[start:end])
        start = end

    print(f"[CORRECT] Split into {len(chunks)} batches")

    corrected_parts = []
    for i, chunk in enumerate(chunks):
        print(f"[CORRECT] Processing batch {i+1}/{len(chunks)}...")
        prompt = CORRECT_BATCH_PROMPT.format(chunk=chunk)
        try:
            if client:
                result = client.generate(prompt, reset_context=(i == 0))
            else:
                result = adapter.generate(prompt)
            corrected_parts.append(result)
        except Exception as e:
            print(f"[CORRECT] Batch {i+1} failed: {e}, using original")
            corrected_parts.append(chunk)

    return "\n".join(corrected_parts)


def _save_diff(original, corrected, diff_path):
    """保存纠错差异记录"""
    orig_words = list(original)
    corr_words = list(corrected)

    diffs = []
    min_len = min(len(orig_words), len(corr_words))
    for i in range(min_len):
        if orig_words[i] != corr_words[i]:
            context_start = max(0, i - 5)
            context_end = min(len(orig_words), i + 6)
            diffs.append({
                "original": orig_words[i],
                "corrected": corr_words[i],
                "position": i,
                "context_orig": "".join(orig_words[context_start:context_end]),
                "context_corr": "".join(corr_words[context_start:context_end])
            })

    diff_data = {
        "total_chars_original": len(original),
        "total_chars_corrected": len(corrected),
        "total_changes": len(diffs),
        "changes": diffs[:200]
    }

    diff_dir = os.path.dirname(diff_path)
    if diff_dir and not os.path.exists(diff_dir):
        os.makedirs(diff_dir, exist_ok=True)

    with open(diff_path, "w", encoding="utf-8") as f:
        json.dump(diff_data, f, ensure_ascii=False, indent=2)

    print(f"[CORRECT] Total changes: {len(diffs)}")


def _apply_corrections(segments, original_text, corrected_text):
    """将纠错后的文本重新分配到segments中"""
    orig_parts = original_text.split()
    corr_parts = corrected_text.split()

    if len(orig_parts) == len(corr_parts):
        word_map = dict(zip(orig_parts, corr_parts))
        corrected_segments = []
        for seg in segments:
            new_seg = dict(seg)
            orig_seg_text = seg.get("text", "")
            words = orig_seg_text.split()
            corrected_words = [word_map.get(w, w) for w in words]
            new_seg["text"] = " ".join(corrected_words)
            corrected_segments.append(new_seg)
        return corrected_segments

    corrected_segments = []
    for seg in segments:
        new_seg = dict(seg)
        new_seg["text"] = seg.get("text", "")
        corrected_segments.append(new_seg)

    print(f"[CORRECT] Word count mismatch (orig={len(orig_parts)}, corr={len(corr_parts)}), segments not updated")
    return corrected_segments
