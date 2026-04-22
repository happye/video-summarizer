from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.transcript_loader import load_transcript
from config import CHUNK_SIZE, CHUNK_OVERLAP
import json
import os

def chunk_transcript(transcript_path):
    """Split transcript into chunks for processing with dynamic chunk size"""
    print("Chunking transcript...")
    
    # Load transcript
    full_transcript = load_transcript(transcript_path)
    
    # Calculate transcript length
    transcript_length = len(full_transcript)
    print(f"Transcript length: {transcript_length} characters")
    
    # Dynamic chunk size adjustment based on transcript length
    # 目标：控制chunk数量在15个以内，避免会话稳定性问题
    target_chunks = 15
    
    if transcript_length > 50000:
        # 超长视频：根据长度动态计算chunk大小
        estimated_chunk_size = transcript_length // target_chunks
        # 限制在合理范围内（4000-6000）
        dynamic_chunk_size = max(4000, min(6000, estimated_chunk_size))
        dynamic_chunk_overlap = int(dynamic_chunk_size * 0.15)  # 15%重叠
        print(f"Very long transcript detected ({transcript_length} chars)")
        print(f"Using optimized chunks: {dynamic_chunk_size} with overlap {dynamic_chunk_overlap}")
        print(f"Target chunk count: ~{transcript_length // dynamic_chunk_size}")
    elif transcript_length > 30000:
        # 长视频：使用较大的chunk
        dynamic_chunk_size = 4000
        dynamic_chunk_overlap = 500
        print(f"Long transcript detected, using larger chunks: {dynamic_chunk_size} with overlap {dynamic_chunk_overlap}")
    else:
        # 普通视频：使用标准chunk
        dynamic_chunk_size = CHUNK_SIZE
        dynamic_chunk_overlap = CHUNK_OVERLAP
        print(f"Normal transcript, using standard chunks: {dynamic_chunk_size} with overlap {dynamic_chunk_overlap}")
    
    # Create text splitter with dynamic settings
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=dynamic_chunk_size,
        chunk_overlap=dynamic_chunk_overlap,
        length_function=len
    )
    
    # Split into chunks
    chunks = splitter.split_text(full_transcript)
    
    # Import CHUNKS_PATH after setting paths
    from config import CHUNKS_PATH
    print(f"CHUNKS_PATH: {CHUNKS_PATH}")
    
    # Ensure the directory exists
    chunks_dir = os.path.dirname(CHUNKS_PATH)
    if not os.path.exists(chunks_dir):
        os.makedirs(chunks_dir, exist_ok=True)
        print(f"Created directory: {chunks_dir}")
    
    # Save chunks to JSON
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    
    print(f"Transcript split into {len(chunks)} chunks")
    
    # 性能警告：如果chunk数量过多，给出警告
    if len(chunks) > 20:
        print(f"[WARNING] Large number of chunks ({len(chunks)}) may cause session stability issues!")
        print(f"[WARNING] Consider using a larger chunk size or splitting the video into parts.")
    
    return chunks
