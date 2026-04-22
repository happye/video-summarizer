import json

def load_transcript(transcript_path):
    """Load WhisperX transcript JSON and return full transcript text"""
    with open(transcript_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Extract text from segments
    segments = data.get("segments", [])
    full_transcript = " ".join([segment.get("text", "") for segment in segments])
    
    return full_transcript
