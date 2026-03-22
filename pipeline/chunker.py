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
    # For long transcripts (> 50,000 characters), use larger chunks
    if transcript_length > 50000:
        dynamic_chunk_size = 3000
        dynamic_chunk_overlap = 400
        print(f"Long transcript detected, using larger chunks: {dynamic_chunk_size} with overlap {dynamic_chunk_overlap}")
    else:
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
    return chunks
