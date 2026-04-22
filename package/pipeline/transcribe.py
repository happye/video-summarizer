import os
import whisper
import json
import torch

# Disable symlinks for Hugging Face Hub on Windows
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['HF_HUB_DISABLE_SYMLINKS'] = '1'

def transcribe_video(video_path):
    """Transcribe video using Whisper"""
    print(f"Transcribing video {video_path}...")
    
    # Load Whisper model
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU device name: {torch.cuda.get_device_name(0)}")
        print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Use medium model for faster inference on CPU
    model = whisper.load_model("medium", device=device)
    
    # Transcribe
    result = model.transcribe(video_path)
    
    # Import TRANSCRIPT_PATH after setting paths
    from config import TRANSCRIPT_PATH
    print(f"TRANSCRIPT_PATH: {TRANSCRIPT_PATH}")
    
    # Ensure the directory exists
    transcript_dir = os.path.dirname(TRANSCRIPT_PATH)
    if not os.path.exists(transcript_dir):
        os.makedirs(transcript_dir, exist_ok=True)
        print(f"Created directory: {transcript_dir}")
    
    # Save transcript to JSON
    with open(TRANSCRIPT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("Transcription completed successfully!")
    return TRANSCRIPT_PATH
