from llm.adapter import LLMAdapter
from llm.kimi_client import KimiClient

def outline_summary(chunks, llm_provider, detail_level, bullet_count):
    """Generate outline summary with chunked processing and context management"""
    
    # 使用KimiClient来保持上下文连续性
    if llm_provider == "kimi":
        client = KimiClient()
        # 重置上下文，开始新的会话
        client.generate("你是一名专业的视频总结专家，擅长分析各类视频内容并生成结构化的大纲摘要。我将为你提供转录文本的分段，你需要生成一个全面、深入、有条理的大纲摘要。请直接改正转录文本中的错别字，不要标注，确保输出的内容语言清晰、准确、专业。", reset_context=True)
    else:
        adapter = LLMAdapter(llm_provider)
    
    # 分块处理逻辑
    if len(chunks) > 1:
        print(f"Processing {len(chunks)} chunks for outline summary...")
        
        # 先对每个块生成局部摘要
        partial_summaries = []
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}...")
            chunk_prompt = f"""请仔细分析以下转录文本片段，然后生成一个简洁但全面的总结。

分析要点：
1. 识别主要话题和核心观点
2. 提取关键信息和重要细节
3. 注意逻辑结构和论证思路
4. 关注说话者的意图和重点
5. 直接改正文本中的错别字，不要标注

转录文本片段：
{chunk}

请提供一个结构清晰、信息准确的总结，直接改正错别字："""
            
            if llm_provider == "kimi":
                partial_summary = client.generate(chunk_prompt)
            else:
                partial_summary = adapter.generate(chunk_prompt)
            
            partial_summaries.append(partial_summary)
        
        # 然后将局部摘要组合成最终大纲
        combined_summaries = "\n".join(partial_summaries)
        final_prompt = f"""基于你已经处理过的所有局部摘要，创建一个结构化的大纲摘要。

大纲要求：
1. 遵循严格的层次结构，使用编号系统（如：I. 主章节, A. 子章节, 1. 小节）
2. 每个章节和子章节都要有明确的主题
3. 内容要全面覆盖视频的主要内容
4. 分析要深入，不仅要列出信息，还要解释其重要性和意义
5. 逻辑要清晰，各部分之间要有合理的关联
6. 语言要专业、准确、简洁

不要添加外部知识，不要进行推测，所有内容都必须基于转录文本。

请生成一个高质量的大纲摘要，直接改正错别字："""
        
        if llm_provider == "kimi":
            summary = client.generate(final_prompt)
        else:
            summary = adapter.generate(final_prompt)
    else:
        # 如果只有一个块，直接处理
        combined_text = "\n".join(chunks)
        prompt = f"""请为以下转录文本创建一个结构化的大纲摘要。

大纲要求：
1. 遵循严格的层次结构，使用编号系统（如：I. 主章节, A. 子章节, 1. 小节）
2. 每个章节和子章节都要有明确的主题
3. 内容要全面覆盖视频的主要内容
4. 分析要深入，不仅要列出信息，还要解释其重要性和意义
5. 逻辑要清晰，各部分之间要有合理的关联
6. 语言要专业、准确、简洁

分析要点：
1. 识别视频的主要话题和核心观点
2. 提取关键信息和重要细节
3. 分析逻辑结构和论证思路
4. 理解说话者的意图和重点
5. 识别视频中的重要转折点和结论
6. 直接改正文本中的错别字，不要标注

不要添加外部知识，不要进行推测，所有内容都必须基于转录文本。

转录文本：
{combined_text}

请生成一个高质量的大纲摘要，直接改正错别字："""
        
        if llm_provider == "kimi":
            summary = client.generate(prompt, reset_context=True)
        else:
            summary = adapter.generate(prompt)
    
    return summary
