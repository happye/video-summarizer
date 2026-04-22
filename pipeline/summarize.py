from summarizers.map_reduce import map_reduce_summary
from summarizers.timeline_summary import timeline_summary
from summarizers.outline_summary import outline_summary
import json
import os

def generate_summary(chunks, llm_provider, mode, detail_level, bullet_count):
    """Generate summary based on selected mode"""
    print(f"Generating summary using {mode} mode...")
    
    if mode == "mapreduce":
        summary = map_reduce_summary(chunks, llm_provider, detail_level, bullet_count)
    elif mode == "timeline":
        summary = timeline_summary(chunks, llm_provider, detail_level, bullet_count)
    elif mode == "outline":
        summary = outline_summary(chunks, llm_provider, detail_level, bullet_count)
    else:
        raise ValueError(f"Unsupported summarization mode: {mode}")
    
    # Import PARTIAL_SUMMARY_PATH after setting paths
    from config import PARTIAL_SUMMARY_PATH
    print(f"PARTIAL_SUMMARY_PATH: {PARTIAL_SUMMARY_PATH}")
    
    # Ensure the directory exists
    partial_summary_dir = os.path.dirname(PARTIAL_SUMMARY_PATH)
    if not os.path.exists(partial_summary_dir):
        os.makedirs(partial_summary_dir, exist_ok=True)
        print(f"Created directory: {partial_summary_dir}")
    
    # Save partial summary (for debugging/restart)
    with open(PARTIAL_SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "mode": mode}, f, ensure_ascii=False, indent=2)
    
    print("Summary generation completed successfully!")
    return summary
