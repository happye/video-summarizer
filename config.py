# Model configuration
MODEL_PROVIDER = "kimi"
OLLAMA_MODEL = "qwen2.5"
KIMI_API_KEY = "your_kimi_api_key_here"
DEEPSEEK_API_KEY = "your_deepseek_api_key_here"

# Chunking configuration
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200

# Summarization configuration
SUMMARY_STYLE = "outline"
SUMMARY_DETAIL_LEVEL = 2
SUMMARY_BULLET_COUNT = 10

# Paths
BASE_DIR = "output"

# Ensure base directory exists
import os
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

# File paths (will be dynamically set based on video name)
VIDEO_PATH = ""
TRANSCRIPT_PATH = ""
CHUNKS_PATH = ""
PARTIAL_SUMMARY_PATH = ""
OUTPUT_PATH = ""

# Function to set paths based on video name
def set_paths(video_name):
    global VIDEO_PATH, TRANSCRIPT_PATH, CHUNKS_PATH, PARTIAL_SUMMARY_PATH, OUTPUT_PATH
    
    # Create video-specific directory
    video_dir = os.path.join(BASE_DIR, video_name)
    if not os.path.exists(video_dir):
        os.makedirs(video_dir, exist_ok=True)
    
    # Set paths
    VIDEO_PATH = os.path.join(video_dir, f"{video_name}.mp4")
    TRANSCRIPT_PATH = os.path.join(video_dir, "transcript.json")
    CHUNKS_PATH = os.path.join(video_dir, "chunks.json")
    PARTIAL_SUMMARY_PATH = os.path.join(video_dir, "partial_summary.json")
    OUTPUT_PATH = os.path.join(video_dir, "summary.md")
    
    print(f"Set paths:")
    print(f"  VIDEO_PATH: {VIDEO_PATH}")
    print(f"  TRANSCRIPT_PATH: {TRANSCRIPT_PATH}")
    print(f"  CHUNKS_PATH: {CHUNKS_PATH}")
    print(f"  PARTIAL_SUMMARY_PATH: {PARTIAL_SUMMARY_PATH}")
    print(f"  OUTPUT_PATH: {OUTPUT_PATH}")
    
    return video_dir
