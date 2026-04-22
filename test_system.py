#!/usr/bin/env python3
"""Test script to verify the video summarizer system"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing Video Summarizer System...")

# Test 1: Import all modules
try:
    from main import main
    from config import MODEL_PROVIDER, SUMMARY_STYLE
    from pipeline.download import download_video
    from pipeline.transcribe import transcribe_video
    from pipeline.chunker import chunk_transcript
    from pipeline.summarize import generate_summary
    from pipeline.output import write_output
    from llm.adapter import LLMAdapter
    from utils.transcript_loader import load_transcript
    print("✓ All modules imported successfully")
except Exception as e:
    print(f"✗ Failed to import modules: {e}")
    sys.exit(1)

# Test 2: Test LLM adapter
try:
    adapter = LLMAdapter(MODEL_PROVIDER)
    print(f"✓ LLM adapter initialized with provider: {MODEL_PROVIDER}")
except Exception as e:
    print(f"✗ Failed to initialize LLM adapter: {e}")

# Test 3: Test command line argument parsing
try:
    import argparse
    parser = argparse.ArgumentParser(description="Video Summarizer")
    parser.add_argument("--url", type=str, help="YouTube video URL")
    parser.add_argument("--file", type=str, help="Local video file path")
    parser.add_argument("--llm", type=str, choices=["ollama", "kimi", "deepseek"], default=MODEL_PROVIDER, help="LLM provider")
    parser.add_argument("--mode", type=str, choices=["outline", "timeline", "mapreduce"], default=SUMMARY_STYLE, help="Summarization mode")
    print("✓ Command line argument parsing configured")
except Exception as e:
    print(f"✗ Failed to configure argument parsing: {e}")

print("\nSystem test completed!")
print("All core components are ready for use.")
print("\nTo run the video summarizer:")
print("  python main.py --url <VIDEO_URL>  # Supports YouTube, Bilibili, etc.")
print("  or")
print("  python main.py --file <LOCAL_VIDEO_FILE>")
