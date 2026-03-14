from llm.adapter import LLMAdapter

def timeline_summary(chunks, llm_provider, detail_level, bullet_count):
    """Generate timeline summary"""
    adapter = LLMAdapter(llm_provider)
    
    # Combine chunks for timeline generation
    combined_text = "\n".join(chunks)
    
    prompt = f"""You must create a timeline summary of the following transcript.

The timeline should include key events with approximate timestamps in the format:
00:00 Event description

Do not add external knowledge.
Do not speculate.
Keep the timeline concise but informative.

Transcript:
{combined_text}

Timeline summary:"""
    
    summary = adapter.generate(prompt)
    return summary
