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
    # Note: Do NOT specify encoding here. Let Python use the system default
    # encoding (gbk/cp936 on Chinese Windows) to correctly decode Chinese titles.
    title_process = subprocess.Popen(
        [yt_dlp_path, "--no-playlist", "--get-title", url],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    video_title = title_process.stdout.read().strip()
    title_process.wait()
    
    # Check if title is empty or contains errors
    if not video_title or "ERROR" in video_title or "Error" in video_title:
        print(f"Warning: Failed to get video title, using URL-based title")
        # Extract video ID from URL as fallback
        import re
        video_id_match = re.search(r'BV([a-zA-Z0-9]+)', url)
        if video_id_match:
            video_title = f"video_{video_id_match.group(1)}"
        else:
            video_title = "video_download"
    
    # Clean up video title to remove invalid characters for filename
    import re
    video_title_clean = re.sub(r'[<>:"/\\|?*]', '_', video_title)
    video_title_clean = video_title_clean.strip('_')
    video_title_clean = video_title_clean[:100]  # Limit length
    
    # Check if video already exists in output directory
    output_dir = os.path.join(BASE_DIR, video_title_clean)
    if os.path.exists(output_dir):
        # Look for video files in the output directory
        import glob
        video_files = glob.glob(os.path.join(output_dir, "*.mp4")) + glob.glob(os.path.join(output_dir, "*.mkv")) + glob.glob(os.path.join(output_dir, "*.webm"))
        if video_files:
            print(f"Video already exists in output directory: {video_files[0]}")
            print("Skipping download, using existing file...")
            return video_files[0], video_title_clean
    
    # Build command arguments
    args = [yt_dlp_path]
    
    # Add deno runtime if available
    if os.path.exists(deno_path):
        args.extend(["--js-runtimes", f"deno:{deno_path}", "--remote-components", "ejs:github"])
    
    # Add cookies if available
    if os.path.exists(cookies_path):
        args.extend(["--cookies", cookies_path])
    
    # Add output format and URL
    # Use --no-restrict-filenames to preserve Unicode characters (Chinese, etc.)
    temp_output = f"temp/%(title)s.%(ext)s"
    args.extend(["-o", temp_output, "--no-playlist", "--no-restrict-filenames", url])
    
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
    
    # Return video path and cleaned title (for consistent path naming)
    print(f"Download completed successfully! Video saved as: {temp_video_path}")
    return temp_video_path, video_title_clean
