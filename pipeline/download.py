import subprocess
import os
from config import BASE_DIR

def download_video(url):
    """Download video from URL (supports YouTube, Bilibili, etc.) using yt-dlp"""
    print(f"Downloading video from {url}...")
    
    # Use the local yt-dlp executable directly
    yt_dlp_path = os.path.join(os.getcwd(), "yt-dlp", "dist", "yt-dlp.exe")
    deno_path = os.path.join(os.getcwd(), "yt-dlp", "dist", "deno.exe")
    cookies_path = os.path.join(os.getcwd(), "yt-dlp", "cookies.txt")
    
    if not os.path.exists(yt_dlp_path):
        raise FileNotFoundError(f"yt-dlp executable not found at {yt_dlp_path}")
    
    # Get video title without downloading
    title_process = subprocess.Popen(
        [yt_dlp_path, "--no-playlist", "--get-title", url],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    video_title = title_process.stdout.read().strip()
    title_process.wait()
    
    # Build command arguments
    args = [yt_dlp_path]
    
    # Add deno runtime if available
    if os.path.exists(deno_path):
        args.extend(["--js-runtimes", f"deno:{deno_path}", "--remote-components", "ejs:github"])
    
    # Add cookies if available
    if os.path.exists(cookies_path):
        args.extend(["--cookies", cookies_path])
    
    # Add output format and URL
    temp_output = f"temp/%(title)s.%(ext)s"
    args.extend(["-o", temp_output, "--no-playlist", url])
    
    # Run yt-dlp with live output
    print(f"Running: {' '.join(args)}")
    print("----------------------------------------")
    
    # First try to update yt-dlp
    update_process = subprocess.Popen(
        [yt_dlp_path, "-U"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    for line in iter(update_process.stdout.readline, ''):
        print(line.strip())
    update_process.wait()
    
    print("----------------------------------------")
    
    # Now run the actual download
    process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Read and display output in real-time
    for line in iter(process.stdout.readline, ''):
        print(line.strip())
    
    # Wait for process to complete
    process.wait()
    
    if process.returncode != 0:
        # If download fails, show available formats for debugging
        print("\nShowing available formats for debugging:")
        formats_process = subprocess.Popen(
            [yt_dlp_path, "--no-playlist", "--list-formats", url],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        for line in iter(formats_process.stdout.readline, ''):
            print(line.strip())
        formats_process.wait()
        
        raise Exception(f"Failed to download video. Return code: {process.returncode}")
    
    print("----------------------------------------")
    
    # Find the downloaded video file
    import glob
    video_files = glob.glob("temp/*.mp4") + glob.glob("temp/*.mkv") + glob.glob("temp/*.webm")
    if not video_files:
        raise Exception("No video file found after download")
    
    # Use the most recently modified video file
    video_files.sort(key=os.path.getmtime, reverse=True)
    temp_video_path = video_files[0]
    
    # Return video path and title
    print(f"Download completed successfully! Video saved as: {temp_video_path}")
    return temp_video_path, video_title
