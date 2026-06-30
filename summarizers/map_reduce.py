from llm.adapter import LLMAdapter
from llm.kimi_client import KimiClient
from llm.deepseek_client import DeepSeekClient
import time


def _estimate_tokens(text):
    """估算中文文本的 token 数"""
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    total_words = len(text.split())
    english_words = max(0, total_words - chinese_chars)
    return max(1, int(chinese_chars / 1.5 + english_words / 0.25))


SYSTEM_PROMPT = """你是一位资深的内容分析专家，擅长从视频转录文本中提炼核心观点、梳理逻辑脉络，并以清晰、专业的方式呈现分析结果。

你的核心写作原则：
- 原话引用：对关键观点必须引用视频原话（用「」标注），让读者感受到说话者的真实表达
- 深入浅出：对专业术语、复杂概念必须用通俗易懂的语言解释，确保不同知识水平的读者都能理解
- 详实不省略：每个重要论点都要展开说明，不能一笔带过或简单概括
- 逻辑连贯：不仅罗列信息，更要说明信息之间的因果、递进、对比关系
- 纠错无声：直接改正转录文本中的错别字和语病，不标注、不解释修改"""

MAP_PROMPT = """请对以下视频转录文本片段进行详尽的摘要分析。

【摘要要求】
1. 提炼本片段的核心主题和关键论点，用「」引用关键原话
2. 保留重要数据、事实和具体细节，不要笼统化
3. 梳理论证逻辑和推理链条，说明观点之间的因果关系
4. 对专业术语和复杂概念，用通俗易懂的语言解释其含义
5. 识别关键结论和转折点，说明其重要性
6. 直接改正错别字，不标注

【撰写规范】
- 关键观点必须引用原话（用「」标注），然后进行解释
- 专业概念必须用通俗语言解释，让外行也能理解
- 保留具体数字、名称等细节，不要笼统化
- 不要简单概括，要展开说明每个重要论点
- 宁可详尽不可省略

转录文本片段 {chunk_num}/{total_chunks}：
{chunk}

摘要："""

REDUCE_PROMPT = """请将以下各片段摘要整合为一份详尽、连贯的综合摘要。

【整合要求】
1. 将各片段的核心观点有机整合，消除重复和矛盾
2. 按逻辑顺序组织内容，确保行文连贯
3. 保留所有重要数据、事实和关键细节，不要笼统化
4. 突出整体论证脉络和核心结论
5. 对关键观点用「」引用原话，对专业概念进行通俗解释
6. 说明不同观点之间的因果、递进、转折关系

【撰写规范】
- 关键观点必须引用原话（用「」标注），然后进行解释
- 专业概念必须用通俗语言解释，让外行也能理解
- 保留具体数字、名称等细节
- 宁可详尽不可省略，宁可啰嗦不可遗漏关键信息

各片段摘要：
{combined_summaries}

综合摘要："""

def map_reduce_summary(chunks, llm_provider, detail_level, bullet_count):
    start = time.time()

    # 判断是否能单次全量处理（利用 DeepSeek/Kimi 超长上下文）
    all_text = "\n".join(chunks)
    total_tokens = _estimate_tokens(all_text)

    if llm_provider == "deepseek":
        max_ctx = 378000
    elif llm_provider == "kimi":
        max_ctx = 194000
    else:
        max_ctx = 122000

    if total_tokens <= max_ctx * 0.8:
        print(f"[PERF] Transcript fits in context ({total_tokens} <= {int(max_ctx*0.8)} tokens), single-pass mode")
        # 单次全量：直接用 REDUCE 逻辑生成完整摘要
        single_prompt = f"""请对以下视频转录文本进行详尽的摘要分析。

【摘要要求】
1. 提炼核心主题和关键论点，用「」引用关键原话
2. 保留重要数据、事实和具体细节，不要笼统化
3. 梳理论证逻辑和推理链条，说明观点之间的因果关系
4. 对专业术语和复杂概念，用通俗易懂的语言解释其含义
5. 识别关键结论和转折点，说明其重要性
6. 直接改正错别字，不标注

【撰写规范】
- 关键观点必须引用原话（用「」标注），然后进行解释
- 专业概念必须用通俗语言解释，让外行也能理解
- 保留具体数字、名称等细节，不要笼统化
- 不要简单概括，要展开说明每个重要论点
- 宁可详尽不可省略

转录文本：
{all_text}

详尽摘要："""
        adapter = LLMAdapter(llm_provider)
        summary = adapter.generate(single_prompt)
        print(f"[PERF] Single-pass completed in {time.time()-start:.1f}s")
        return summary

    print(f"[PERF] Transcript too long ({total_tokens} > {int(max_ctx*0.8)} tokens), using map-reduce")

    adapter = LLMAdapter(llm_provider)

    partial_summaries = []
    for i, chunk in enumerate(chunks):
        prompt = MAP_PROMPT.format(chunk_num=i+1, total_chunks=len(chunks), chunk=chunk)
        summary = adapter.generate(prompt)
        partial_summaries.append(summary)
        print(f"[PERF] Map chunk {i+1}/{len(chunks)} done")

    combined_summaries = "\n".join(partial_summaries)
    final_prompt = REDUCE_PROMPT.format(combined_summaries=combined_summaries)

    final_summary = adapter.generate(final_prompt)
    print(f"[PERF] Map-reduce completed in {time.time()-start:.1f}s")
    return final_summary