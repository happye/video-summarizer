from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.transcript_loader import load_transcript
from config import CHUNK_SIZE, CHUNK_OVERLAP
import json
import os

def chunk_transcript(transcript_path):
    """Split transcript into chunks for processing"""
    print("Chunking transcript...")
    
    # Load transcript
    full_transcript = load_transcript(transcript_path)
    
    # Create text splitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
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
