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
    corrected_path = transcript_path.replace(".json", "_corrected.json")
    diff_path = transcript_path.replace(".json", "_correction_diff.json")

    print(f"[CORRECT] {'='*60}")
    print(f"[CORRECT] 纠错流程开始")
    print(f"[CORRECT] {'='*60}")
    print(f"[CORRECT] 输入文件: {transcript_path}")
    print(f"[CORRECT] 输出文件: {corrected_path}")
    print(f"[CORRECT] LLM: {llm_provider}")

    if os.path.exists(corrected_path):
        print(f"[CORRECT] [跳过] 纠错文件已存在: {corrected_path}")
        print(f"[CORRECT] {'='*60}")
        return corrected_path

    with open(transcript_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    segments = data.get("segments", [])
    if not segments:
        print(f"[CORRECT] [跳过] 转录文件无segments, 跳过纠错")
        print(f"[CORRECT] {'='*60}")
        return transcript_path

    original_text = " ".join([seg.get("text", "") for seg in segments])
    if not original_text.strip():
        print(f"[CORRECT] [跳过] 转录文本为空, 跳过纠错")
        print(f"[CORRECT] {'='*60}")
        return transcript_path

    total_tokens = estimate_tokens(original_text)

    print(f"[CORRECT] [步骤1/5] 读取转录文本")
    print(f"[CORRECT]   段落数: {len(segments)}, 字符数: {len(original_text)}, 估算Tokens: ~{total_tokens}")

    print(f"[CORRECT] [步骤2/5] 选择纠错策略")
    if llm_provider == "kimi":
        client = KimiClient()
        adapter = None
        max_context_tokens = 256000
        max_output_tokens = 262144
        model_name = "kimi-k2.6"
    elif llm_provider == "deepseek":
        client = DeepSeekClient()
        client.thinking_enabled = False
        adapter = None
        max_context_tokens = 1000000
        max_output_tokens = 384000
        model_name = "deepseek-v4-pro (思考模式: 已关闭)"
    else:
        client = None
        adapter = LLMAdapter(llm_provider)
        max_context_tokens = 122000
        max_output_tokens = 122000
        model_name = llm_provider

    effective_limit = min(max_context_tokens * 0.7, max_output_tokens * 0.9)
    strategy = "single" if total_tokens <= effective_limit else "batch"

    print(f"[CORRECT]   模型: {model_name}")
    print(f"[CORRECT]   上下文窗口: {max_context_tokens}, 输出上限: {max_output_tokens}")
    print(f"[CORRECT]   有效限制: {int(effective_limit)} tokens (取上下文70%和输出90%的较小值)")
    print(f"[CORRECT]   决策: {total_tokens} {'≤' if strategy == 'single' else '>'} {int(effective_limit)} → {'单次纠错' if strategy == 'single' else '分批纠错'}")

    print(f"[CORRECT] [步骤3/5] 调用LLM ({'单次纠错' if strategy == 'single' else '分批纠错'})")
    corrected_text = _correct_text(original_text, total_tokens, max_context_tokens, max_output_tokens, client, adapter, llm_provider)

    if client and hasattr(client, 'last_finish_reason') and client.last_finish_reason:
        finish_reason = client.last_finish_reason
        print(f"[CORRECT]   API finish_reason: {finish_reason}")
        if finish_reason == "length":
            print(f"[CORRECT]   ⚠ 输出被截断! 输出tokens达到max_tokens上限, 纠错结果不完整")
            print(f"[CORRECT]   ⚠ 建议: 检查max_tokens设置或使用分批纠错")
        elif finish_reason == "content_filter":
            print(f"[CORRECT]   ⚠ 内容被API过滤! 部分内容被安全审查拦截")

    print(f"[CORRECT] [步骤4/5] 验证纠错结果")
    if not corrected_text or not corrected_text.strip():
        print(f"[CORRECT]   ✗ 纠错返回为空!")
        if client and hasattr(client, 'last_usage') and client.last_usage:
            usage = client.last_usage
            print(f"[CORRECT]   诊断: prompt_tokens={usage.get('prompt_tokens', '?')}, completion_tokens={usage.get('completion_tokens', '?')}")
            if usage.get('completion_tokens', 0) > 0 and not corrected_text:
                print(f"[CORRECT]   诊断: API返回了{usage.get('completion_tokens')}个tokens但content为空")
                print(f"[CORRECT]   诊断: 可能原因 → 思考模式消耗了所有输出tokens, 实际内容为空")
                print(f"[CORRECT]   诊断: 解决方案 → 确认thinking模式已关闭")
        print(f"[CORRECT]   回退使用原始转录")
        print(f"[CORRECT] {'='*60}")
        return transcript_path

    char_diff = len(corrected_text) - len(original_text)
    print(f"[CORRECT]   原始: {len(original_text)}字符 → 纠错: {len(corrected_text)}字符 (差异: {char_diff:+d})")

    print(f"[CORRECT] [步骤5/5] 保存结果")
    _save_diff(original_text, corrected_text, diff_path)

    corrected_segments = _apply_corrections(segments, original_text, corrected_text)

    corrected_data = dict(data)
    corrected_data["segments"] = corrected_segments
    corrected_data["correction_applied"] = True
    corrected_data["text"] = corrected_text

    with open(corrected_path, "w", encoding="utf-8") as f:
        json.dump(corrected_data, f, ensure_ascii=False, indent=2)

    print(f"[CORRECT]   ✓ 纠错文件: {corrected_path}")
    print(f"[CORRECT]   ✓ 差异文件: {diff_path}")
    print(f"[CORRECT] {'='*60}")
    print(f"[CORRECT] 纠错完成")
    print(f"[CORRECT] {'='*60}")

    return corrected_path


def _correct_text(text, total_tokens, max_context_tokens, max_output_tokens, client, adapter, llm_provider):
    effective_limit = min(max_context_tokens * 0.7, max_output_tokens * 0.9)
    if total_tokens <= effective_limit:
        return _correct_single(text, client, adapter)
    return _correct_batch(text, max_output_tokens, client, adapter)


def _correct_single(text, client, adapter):
    prompt = CORRECT_PROMPT.format(text=text)
    prompt_tokens = estimate_tokens(prompt)
    print(f"[CORRECT]   Prompt长度: ~{prompt_tokens} tokens")
    print(f"[CORRECT]   等待API响应...")
    try:
        if client:
            result = client.generate(prompt, reset_context=True)
        else:
            result = adapter.generate(prompt)
        if result:
            print(f"[CORRECT]   收到响应: {len(result)} 字符")
        else:
            print(f"[CORRECT]   ✗ 响应content为空 (API返回了tokens但无实际内容)")
        return result
    except Exception as e:
        print(f"[CORRECT]   ✗ 请求失败: {e}")
        return None


def _correct_batch(text, max_output_tokens, client, adapter):
    batch_limit = int(max_output_tokens * 0.8)
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

    print(f"[CORRECT]   分成 {len(chunks)} 批, 每批上限 ~{batch_limit} tokens")

    corrected_parts = []
    for i, chunk in enumerate(chunks):
        chunk_tokens = estimate_tokens(chunk)
        print(f"[CORRECT]   批次 {i+1}/{len(chunks)}: {len(chunk)}字符, ~{chunk_tokens} tokens")
        prompt = CORRECT_BATCH_PROMPT.format(chunk=chunk)
        try:
            if client:
                result = client.generate(prompt, reset_context=True)
            else:
                result = adapter.generate(prompt)
            if result and result.strip():
                finish = getattr(client, 'last_finish_reason', '?') if client else '?'
                print(f"[CORRECT]     响应: {len(result)} 字符, finish_reason={finish}")
                if finish == "length":
                    print(f"[CORRECT]     ⚠ 此批次输出被截断, 结果可能不完整")
                corrected_parts.append(result)
            else:
                print(f"[CORRECT]     ✗ 响应为空, 使用原文")
                corrected_parts.append(chunk)
        except Exception as e:
            print(f"[CORRECT]     ✗ 批次 {i+1} 失败: {e}, 使用原文")
            corrected_parts.append(chunk)

    return "\n".join(corrected_parts)


def _save_diff(original, corrected, diff_path):
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

    print(f"[CORRECT]   修改处: {len(diffs)}")


def _apply_corrections(segments, original_text, corrected_text):
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
        print(f"[CORRECT]   Segments映射: 成功 (词数匹配: {len(orig_parts)})")
        return corrected_segments

    corrected_segments = []
    for seg in segments:
        new_seg = dict(seg)
        new_seg["text"] = seg.get("text", "")
        corrected_segments.append(new_seg)

    print(f"[CORRECT]   ⚠ Segments映射失败: 词数不匹配 (原始={len(orig_parts)}, 纠错={len(corr_parts)})")
    print(f"[CORRECT]   ⚠ 原因: LLM纠错时增删了词, 无法逐词映射回segments")
    print(f"[CORRECT]   ⚠ 结果: segments文本未更新, 但完整纠错文本已保存在corrected文件中")
    return corrected_segments
