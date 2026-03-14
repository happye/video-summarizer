from llm.adapter import LLMAdapter

def map_reduce_summary(chunks, llm_provider, detail_level, bullet_count):
    """Generate summary using map-reduce strategy"""
    adapter = LLMAdapter(llm_provider)
    
    # Map phase: summarize each chunk
    partial_summaries = []
    for i, chunk in enumerate(chunks):
        prompt = f"""You must summarize ONLY the provided transcript chunk.

Do not add external knowledge.
Do not speculate.
Use clear bullet points.

Transcript chunk {i+1}/{len(chunks)}:
{chunk}

Summary:"""
        summary = adapter.generate(prompt)
        partial_summaries.append(summary)
    
    # Reduce phase: combine partial summaries
    combined_summaries = "\n".join(partial_summaries)
    final_prompt = f"""You must create a comprehensive summary of the following partial summaries.

Do not add external knowledge.
Do not speculate.
Use clear bullet points.

Partial summaries:
{combined_summaries}

Comprehensive summary:"""
    
    final_summary = adapter.generate(final_prompt)
    return final_summary
