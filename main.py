import argparse
import os
import shutil
from pipeline.download import download_video
from pipeline.transcribe import transcribe_video
from pipeline.chunker import chunk_transcript
from pipeline.summarize import generate_summary
from pipeline.output import write_output
from config import MODEL_PROVIDER, SUMMARY_STYLE, set_paths

def main():
    parser = argparse.ArgumentParser(description="Video Summarizer")
    parser.add_argument("--url", type=str, help="Video URL (supports YouTube, Bilibili, etc.)")
    parser.add_argument("--file", type=str, help="Local video file path")
    parser.add_argument("--llm", type=str, choices=["ollama", "kimi", "deepseek"], default=MODEL_PROVIDER, help="LLM provider")
    parser.add_argument("--mode", type=str, choices=["outline", "timeline", "mapreduce"], default=SUMMARY_STYLE, help="Summarization mode")
    parser.add_argument("--detail-level", type=int, default=2, help="Summary detail level (1-5)")
    parser.add_argument("--bullet-count", type=int, default=10, help="Number of bullet points")
    
    args = parser.parse_args()
    
    if not args.url and not args.file:
        parser.error("Either --url or --file must be specified")
    
    # Step 1: Download video if URL is provided
    video_path = args.file
    video_name = ""
    if args.url:
        temp_video_path, video_name = download_video(args.url)
    else:
        # Extract video name from local file path
        video_name = os.path.basename(video_path).split('.')[0]
    
    # Step 1.5: Set paths based on video name
    print(f"Setting paths for video: {video_name}")
    video_dir = set_paths(video_name)
    print(f"Video directory: {video_dir}")
    
    # Import VIDEO_PATH after setting paths
    from config import VIDEO_PATH, OUTPUT_PATH
    print(f"VIDEO_PATH: {VIDEO_PATH}")
    
    # Check if the video has already been fully processed (video + summary exist)
    if os.path.exists(VIDEO_PATH) and os.path.exists(OUTPUT_PATH):
        print(f"Video already processed: {VIDEO_PATH}")
        print(f"Summary already exists: {OUTPUT_PATH}")
        print("Skipping download and processing. Use --force to reprocess.")
        return
    
    # Step 1.6: Move video to the video-specific directory
    if args.url:
        # Move downloaded video to the video-specific directory
        print(f"Moving temp video from {temp_video_path} to {VIDEO_PATH}")
        os.makedirs(video_dir, exist_ok=True)
        shutil.move(temp_video_path, VIDEO_PATH)
        video_path = VIDEO_PATH
        print(f"Video moved to: {VIDEO_PATH}")
    else:
        # For local files, create a copy in the video-specific directory
        print(f"Copying local video from {video_path} to {VIDEO_PATH}")
        print(f"Source file exists: {os.path.exists(video_path)}")
        print(f"Destination directory exists: {os.path.exists(video_dir)}")
        
        # Ensure the directory exists
        os.makedirs(video_dir, exist_ok=True)
        print(f"Destination directory: {video_dir}")
        
        try:
            shutil.copy2(video_path, VIDEO_PATH)
            print(f"Video copied to: {VIDEO_PATH}")
        except Exception as e:
            print(f"Error copying video: {e}")
            # Try with absolute paths
            abs_src = os.path.abspath(video_path)
            abs_dst = os.path.abspath(VIDEO_PATH)
            print(f"Trying with absolute paths:")
            print(f"  Source: {abs_src}")
            print(f"  Destination: {abs_dst}")
            print(f"  Source exists: {os.path.exists(abs_src)}")
            shutil.copy2(abs_src, abs_dst)
            print(f"Video copied to: {abs_dst}")
    
    # Step 2: Transcribe video
    transcript_path = transcribe_video(video_path)
    
    # Step 3: Chunk transcript (pass llm_provider to optimize chunk size)
    chunks = chunk_transcript(transcript_path, llm_provider=args.llm)
    
    # Step 4: Generate summary
    summary = generate_summary(chunks, args.llm, args.mode, args.detail_level, args.bullet_count)
    
    # Step 5: Write output
    write_output(summary, args.mode)
    
    # Step 6: Clean up temp directory
    if os.path.exists("temp"):
        import glob
        temp_files = glob.glob("temp/*")
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass
        try:
            os.rmdir("temp")
        except:
            pass
        print("Temp directory cleaned up")

if __name__ == "__main__":
    main()
