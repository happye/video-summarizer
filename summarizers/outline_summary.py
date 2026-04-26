from llm.adapter import LLMAdapter
from llm.kimi_client import KimiClient
from llm.deepseek_client import DeepSeekClient
import time
from datetime import datetime
import os
import json

def estimate_tokens(text):
    """快速估算 token 数"""
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    total_words = len(text.split())
    english_words = max(0, total_words - chinese_chars)
    return max(1, int(chinese_chars / 1.5 + english_words / 0.25))

def outline_summary(chunks, llm_provider, detail_level, bullet_count):
    """Generate outline summary with chunked processing and context management"""

    overall_start = time.time()
    print(f"[PERF] Starting outline summary generation at {datetime.now().isoformat()}")
    print(f"[PERF] Total chunks to process: {len(chunks)}")

    # 根据提供者创建对应的客户端（都支持上下文管理）
    if llm_provider == "kimi":
        client = KimiClient()
        max_context_tokens = 194000  # 200K - 6K reserve
    elif llm_provider == "deepseek":
        client = DeepSeekClient()
        max_context_tokens = 378000  # 384K - 6K reserve
    else:
        client = None
        adapter = LLMAdapter(llm_provider)
        max_context_tokens = 122000  # Ollama 128K - 6K reserve

    # 计算所有 chunks 的总 token 数
    all_text = "\n".join(chunks)
    total_tokens = estimate_tokens(all_text)
    print(f"[PERF] Total transcript tokens: {total_tokens}")
    print(f"[PERF] Model max context: {max_context_tokens} tokens")

    # 如果所有文本可以直接放入上下文，直接一次性处理！
    if total_tokens <= max_context_tokens * 0.8:  # 留 20% 余量给 prompt 和 response
        print(f"[PERF] Transcript fits in context window, processing in ONE request!")

        prompt = f"""作为我的投资顾问，请为以下投资视频的转录文本创建一个结构化的投资分析大纲。

大纲要求：
1. 遵循严格的层次结构，使用编号系统（如：I. 主章节, A. 子章节, 1. 小节）
2. 每个章节和子章节都要有明确的投资主题
3. 内容要全面覆盖视频的主要投资内容
4. 分析要由浅入深，从基础概念到深入分析
5. 不仅要列出信息，还要解释其投资意义和市场影响
6. 逻辑要清晰，各部分之间要有合理的关联
7. 语言要专业、准确、自然，体现你作为投资顾问的专业视角和朋友般的语气

分析要点：
1. 识别视频的投资主题和核心投资观点
2. 提取关键市场信息、数据和投资建议
3. 分析投资逻辑、策略和风险管理思路
4. 理解说话者的投资理念和决策依据
5. 识别视频中的重要投资转折点和结论
6. 分析潜在的投资机会和风险点
7. 直接改正文本中的错别字，不要标注

分析层次：
- 基础层：投资主题、市场背景、基本概念
- 分析层：投资逻辑、策略分析、风险评估
- 深度层：投资机会、市场趋势、长期展望

不要添加外部知识，不要进行推测，所有内容都必须基于转录文本。

转录文本：
{all_text}

请以朋友般的专业顾问身份，为我生成一个高质量的投资分析大纲，语言自然流畅，直接改正错别字："""

        if client:
            summary = client.generate(prompt, reset_context=True)
        else:
            summary = adapter.generate(prompt)

        overall_duration = time.time() - overall_start
        print(f"\n[PERF] ========== Performance Summary ==========")
        print(f"[PERF] Total processing time: {overall_duration:.2f}s")
        print(f"[PERF] Number of chunks: {len(chunks)} (processed in 1 request)")
        if client:
            print(client.get_performance_summary())
        print(f"[PERF] ===========================================\n")

        return summary

    # 如果文本太长，需要分块处理，但尽量合并多个 chunk 一起发送
    print(f"[PERF] Transcript too long for single request, using batch processing...")

    # 如果有状态化客户端，设置系统提示
    if client:
        client.generate("你是一名资深的金融/经济/投资专家，拥有丰富的市场分析经验和专业知识。你擅长将复杂的投资概念解释清楚，并且能够提供深入、有洞察力的分析。我将为你提供投资相关视频的转录文本分段，希望你能以朋友般的专业顾问身份，为我生成一个全面、深入、有条理的分析报告。请直接改正转录文本中的错别字，不要标注，确保输出的内容专业、准确、有深度，同时语言自然、流畅、拟人化。", reset_context=True)

    # 合并 chunks 成批次，每批不超过模型限制的 70%
    batch_limit = int(max_context_tokens * 0.7)
    batches = []
    current_batch = []
    current_batch_tokens = 0

    for chunk in chunks:
        chunk_tokens = estimate_tokens(chunk)
        if current_batch_tokens + chunk_tokens > batch_limit and current_batch:
            # 当前批次已满，保存并开始新批次
            batches.append("\n".join(current_batch))
            current_batch = [chunk]
            current_batch_tokens = chunk_tokens
        else:
            current_batch.append(chunk)
            current_batch_tokens += chunk_tokens

    if current_batch:
        batches.append("\n".join(current_batch))

    print(f"[PERF] Merged {len(chunks)} chunks into {len(batches)} batches")

    # 对每个批次生成局部摘要
    partial_summaries = []
    batch_times = []

    for i, batch in enumerate(batches):
        batch_start = time.time()
        print(f"[PERF] Processing batch {i+1}/{len(batches)}...")

        batch_prompt = f"""作为我的投资顾问，请仔细分析以下投资视频的转录文本片段，然后以自然、专业的语气为我生成一个简洁但全面的分析总结。

分析要点：
1. 识别投资主题和核心投资观点
2. 提取关键市场信息、数据和投资建议
3. 分析投资逻辑、策略和风险管理思路
4. 关注说话者的投资理念和决策依据
5. 识别潜在的投资机会和风险点
6. 直接改正文本中的错别字，不要标注

转录文本片段：
{batch}

请以朋友般的专业顾问身份，为我提供一个结构清晰、信息准确的分析总结，语言自然流畅，同时体现你作为投资专家的专业视角："""

        if client:
            partial_summary = client.generate(batch_prompt)
        else:
            partial_summary = adapter.generate(batch_prompt)

        partial_summaries.append(partial_summary)

        batch_duration = time.time() - batch_start
        batch_times.append(batch_duration)
        print(f"[PERF] Batch {i+1} completed in {batch_duration:.2f}s")

        # 智能等待
        if i < len(batches) - 1:
            avg_time = sum(batch_times) / len(batch_times)
            wait_time = min(max(avg_time * 0.1, 1), 5)
            print(f"[PERF] Average batch time: {avg_time:.2f}s, waiting {wait_time:.2f}s before next batch...")
            time.sleep(wait_time)

    # 组合所有局部摘要生成最终大纲
    combined_summaries = "\n".join(partial_summaries)

    # 保存中间结果
    try:
        from config import PARTIAL_SUMMARY_PATH
        partial_summary_dir = os.path.dirname(PARTIAL_SUMMARY_PATH)
        if not os.path.exists(partial_summary_dir):
            os.makedirs(partial_summary_dir, exist_ok=True)
        with open(PARTIAL_SUMMARY_PATH, "w", encoding="utf-8") as f:
            json.dump({"partial_summaries": partial_summaries, "combined": combined_summaries}, f, ensure_ascii=False, indent=2)
        print(f"[PERF] Partial summaries saved to {PARTIAL_SUMMARY_PATH}")
    except Exception as e:
        print(f"[PERF] Warning: Failed to save partial summaries: {e}")

    final_prompt = f"""作为我的投资顾问，基于你已经处理过的所有局部摘要，为我创建一个结构化的投资分析大纲。

大纲要求：
1. 遵循严格的层次结构，使用编号系统（如：I. 主章节, A. 子章节, 1. 小节）
2. 每个章节和子章节都要有明确的投资主题
3. 内容要全面覆盖视频的主要投资内容
4. 分析要由浅入深，从基础概念到深入分析
5. 不仅要列出信息，还要解释其投资意义和市场影响
6. 逻辑要清晰，各部分之间要有合理的关联
7. 语言要专业、准确、自然，体现你作为投资顾问的专业视角和朋友般的语气

分析层次：
- 基础层：投资主题、市场背景、基本概念
- 分析层：投资逻辑、策略分析、风险评估
- 深度层：投资机会、市场趋势、长期展望

不要添加外部知识，不要进行推测，所有内容都必须基于转录文本。

请以朋友般的专业顾问身份，为我生成一个高质量的投资分析大纲，语言自然流畅，直接改正错别字："""

    try:
        if client:
            summary = client.generate(final_prompt)
        else:
            summary = adapter.generate(final_prompt)
    except Exception as e:
        print(f"\n[PERF] ERROR: Final summary generation failed: {e}")
        print("[PERF] Returning combined partial summaries as fallback...")
        summary = f"# 投资分析大纲（部分生成）\n\n> 注意：最终整合阶段出错，以下为各片段分析的汇总\n\n{combined_summaries}"

    # 输出性能总结
    overall_duration = time.time() - overall_start
    print(f"\n[PERF] ========== Performance Summary ==========")
    print(f"[PERF] Total processing time: {overall_duration:.2f}s")
    print(f"[PERF] Original chunks: {len(chunks)}, Batches: {len(batches)}")

    if batch_times:
        avg_batch_time = sum(batch_times) / len(batch_times)
        print(f"[PERF] Average batch processing time: {avg_batch_time:.2f}s")
        print(f"[PERF] Fastest batch: {min(batch_times):.2f}s")
        print(f"[PERF] Slowest batch: {max(batch_times):.2f}s")

    if client:
        print(client.get_performance_summary())

    print(f"[PERF] ===========================================\n")

    return summary
