from llm.adapter import LLMAdapter
from llm.kimi_client import KimiClient
from llm.deepseek_client import DeepSeekClient
import time
from datetime import datetime
import os
import json

def outline_summary(chunks, llm_provider, detail_level, bullet_count):
    """Generate outline summary with chunked processing and context management"""

    overall_start = time.time()
    print(f"[PERF] Starting outline summary generation at {datetime.now().isoformat()}")
    print(f"[PERF] Total chunks to process: {len(chunks)}")

    # 根据提供者创建对应的客户端（都支持上下文管理）
    if llm_provider == "kimi":
        client = KimiClient()
    elif llm_provider == "deepseek":
        client = DeepSeekClient()
    else:
        client = None
        adapter = LLMAdapter(llm_provider)

    # 如果有状态化客户端，设置系统提示
    if client:
        client.generate("你是一名资深的金融/经济/投资专家，拥有丰富的市场分析经验和专业知识。你擅长将复杂的投资概念解释清楚，并且能够提供深入、有洞察力的分析。我将为你提供投资相关视频的转录文本分段，希望你能以朋友般的专业顾问身份，为我生成一个全面、深入、有条理的分析报告。请直接改正转录文本中的错别字，不要标注，确保输出的内容专业、准确、有深度，同时语言自然、流畅、拟人化。", reset_context=True)

    # 分块处理逻辑
    if len(chunks) > 1:
        print(f"Processing {len(chunks)} chunks for outline summary...")

        # 先对每个块生成局部摘要
        partial_summaries = []
        chunk_times = []

        for i, chunk in enumerate(chunks):
            chunk_start = time.time()
            print(f"[PERF] Processing chunk {i+1}/{len(chunks)}...")
            chunk_prompt = f"""作为我的投资顾问，请仔细分析以下投资视频的转录文本片段，然后以自然、专业的语气为我生成一个简洁但全面的分析总结。

分析要点：
1. 识别投资主题和核心投资观点
2. 提取关键市场信息、数据和投资建议
3. 分析投资逻辑、策略和风险管理思路
4. 关注说话者的投资理念和决策依据
5. 识别潜在的投资机会和风险点
6. 直接改正文本中的错别字，不要标注

转录文本片段：
{chunk}

请以朋友般的专业顾问身份，为我提供一个结构清晰、信息准确的分析总结，语言自然流畅，同时体现你作为投资专家的专业视角："""

            if client:
                partial_summary = client.generate(chunk_prompt)
            else:
                partial_summary = adapter.generate(chunk_prompt)

            partial_summaries.append(partial_summary)

            chunk_duration = time.time() - chunk_start
            chunk_times.append(chunk_duration)
            print(f"[PERF] Chunk {i+1} completed in {chunk_duration:.2f}s")

            # 智能等待策略：根据前面的处理时间动态调整
            if i < len(chunks) - 1:
                # 计算平均处理时间
                avg_time = sum(chunk_times) / len(chunk_times)
                # 动态调整等待时间：如果处理快，等待短；处理慢，等待长
                wait_time = min(max(avg_time * 0.1, 1), 5)  # 最小1秒，最大5秒
                print(f"[PERF] Average chunk time: {avg_time:.2f}s, waiting {wait_time:.2f}s before next chunk...")
                time.sleep(wait_time)

        # 然后将局部摘要组合成最终大纲
        combined_summaries = "\n".join(partial_summaries)

        # 保存中间结果，防止最终生成失败导致全部丢失
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
            # 返回已生成的局部摘要组合，避免全部丢失
            summary = f"# 投资分析大纲（部分生成）\n\n> 注意：最终整合阶段出错，以下为各片段分析的汇总\n\n{combined_summaries}"
    else:
        # 如果只有一个块，直接处理
        combined_text = "\n".join(chunks)
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
{combined_text}

请以朋友般的专业顾问身份，为我生成一个高质量的投资分析大纲，语言自然流畅，直接改正错别字："""

        if client:
            summary = client.generate(prompt, reset_context=True)
        else:
            summary = adapter.generate(prompt)

    # 输出性能总结
    overall_duration = time.time() - overall_start
    print(f"\n[PERF] ========== Performance Summary ==========")
    print(f"[PERF] Total processing time: {overall_duration:.2f}s")
    print(f"[PERF] Number of chunks: {len(chunks)}")

    if len(chunks) > 1 and chunk_times:
        avg_chunk_time = sum(chunk_times) / len(chunk_times)
        print(f"[PERF] Average chunk processing time: {avg_chunk_time:.2f}s")
        print(f"[PERF] Fastest chunk: {min(chunk_times):.2f}s")
        print(f"[PERF] Slowest chunk: {max(chunk_times):.2f}s")

    if client:
        print(client.get_performance_summary())

    print(f"[PERF] ===========================================\n")

    return summary
