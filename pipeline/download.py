import subprocess
import os
from config import BASE_DIR

def download_video(url):
    """Download video from URL (supports YouTube, Bilibili, etc.) using yt-dlp"""
    # 清理 URL：去除首尾反引号、引号、空格
    url = url.strip().strip('`').strip('"').strip("'").strip()
    
    print(f"Downloading video from {url}...")
    
    # Use the local yt-dlp executable directly
    yt_dlp_path = os.path.join(os.getcwd(), "yt-dlp", "dist", "yt-dlp.exe")
    deno_path = os.path.join(os.getcwd(), "yt-dlp", "dist", "deno.exe")
    cookies_path = os.path.join(os.getcwd(), "yt-dlp", "cookies.txt")
    
    if not os.path.exists(yt_dlp_path):
        raise FileNotFoundError(f"yt-dlp executable not found at {yt_dlp_path}")
    
    # Get video title without downloading
    # Must use cookies for Bilibili to avoid 412 error
    title_args = [yt_dlp_path, "--no-playlist", "--get-title"]
    if os.path.exists(cookies_path):
        title_args.extend(["--cookies", cookies_path])
    title_args.append(url)

    title_process = subprocess.Popen(
        title_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = title_process.communicate()
    title_lines = [line.strip() for line in stdout.strip().splitlines() if line.strip()]
    video_title = ""
    for line in reversed(title_lines):
        if not line.upper().startswith("WARNING") and not line.upper().startswith("ERROR") and not line.startswith("["):
            video_title = line
            break
    if not video_title and title_lines:
        video_title = title_lines[-1]
    
    if not video_title or video_title.upper().startswith("WARNING") or video_title.upper().startswith("ERROR") or "HTTPSConnectionPool" in video_title:
        print(f"Warning: Failed to get video title, using URL-based title")
        import re
        video_id_match = re.search(r'BV([a-zA-Z0-9]+)', url)
        if video_id_match:
            video_title = f"video_{video_id_match.group(1)}"
        else:
            video_id_match = re.search(r'(?:v=|youtu\.be/|/shorts/)([a-zA-Z0-9_-]{11})', url)
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
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout_lines = []
    stderr_lines = []
    for line in iter(process.stdout.readline, ''):
        stdout_lines.append(line.strip())
        print(line.strip())
    for line in iter(process.stderr.readline, ''):
        stderr_lines.append(line.strip())
        print(line.strip())
    
    process.wait()
    
    if process.returncode != 0:
        has_video = False
        import glob as _glob
        for ext in ('*.mp4', '*.mkv', '*.webm'):
            if _glob.glob(f"temp/{ext}"):
                has_video = True
                break
        
        if has_video:
            print(f"[DOWNLOAD] yt-dlp exited with code {process.returncode} but video file exists, treating as success")
        else:
            print("\nShowing available formats for debugging:")
            debug_args = [yt_dlp_path, "--no-playlist", "--list-formats"]
            if os.path.exists(cookies_path):
                debug_args.extend(["--cookies", cookies_path])
            debug_args.append(url)
            formats_process = subprocess.Popen(
                debug_args,
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
    
    # Return video path, cleaned title, and actual file extension
    _, actual_ext = os.path.splitext(temp_video_path)
    if not actual_ext:
        actual_ext = ".mp4"
    
    print(f"Download completed successfully! Video saved as: {temp_video_path}")
    return temp_video_path, video_title_clean, actual_ext
