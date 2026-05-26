import argparse
import os
import glob
import shutil
from config import MODEL_PROVIDER, SUMMARY_STYLE, set_paths

VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv', '.wmv', '.ts', '.mp3', '.wav', '.m4a', '.flac'}

def find_video_in_dir(directory):
    for ext in sorted(VIDEO_EXTENSIONS):
        matches = glob.glob(os.path.join(directory, f"*{ext}"))
        if matches:
            matches.sort(key=os.path.getmtime, reverse=True)
            return matches[0]
    return None

def process_video(video_path, video_name, args):
    from config import VIDEO_PATH, TRANSCRIPT_PATH, OUTPUT_PATH
    from pipeline.transcribe import transcribe_video
    from pipeline.correct import correct_transcript
    from pipeline.chunker import chunk_transcript
    from pipeline.summarize import generate_summary
    from pipeline.output import write_output

    if os.path.exists(OUTPUT_PATH):
        print(f"Summary already exists: {OUTPUT_PATH}")
        print("Skipping. Use --force to reprocess.")
        return

    if not os.path.exists(TRANSCRIPT_PATH):
        transcript_path = transcribe_video(video_path)
    else:
        print(f"Transcript already exists: {TRANSCRIPT_PATH}, skipping transcription...")
        transcript_path = TRANSCRIPT_PATH

    if not getattr(args, 'no_correct', False):
        try:
            corrected_path = correct_transcript(transcript_path, llm_provider=args.llm)
            transcript_path = corrected_path
        except Exception as e:
            print(f"[CORRECT] Correction failed: {e}, using original transcript")
    else:
        print("[CORRECT] Skipping correction (--no-correct)")

    chunks = chunk_transcript(transcript_path, llm_provider=args.llm)
    summary = generate_summary(chunks, args.llm, args.mode, args.detail_level, args.bullet_count)
    write_output(summary, args.mode)

def handle_command(input_str, llm, mode, detail_level, bullet_count, force=False):
    """处理单条命令，返回是否继续"""
    input_str = input_str.strip()
    # 去除用户可能输入的反引号包裹（Markdown 习惯）
    if input_str.startswith('`') and input_str.endswith('`') and len(input_str) > 2:
        input_str = input_str[1:-1].strip()
    if not input_str:
        return True

    parts = input_str.split(maxsplit=1)
    cmd = parts[0].lower()
    raw_cmd = parts[0]  # 保留原始大小写，URL/路径不能小写
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd in ("exit", "quit", "q"):
        print("Bye!")
        return False

    if cmd == "help":
        print("""
可用命令：
  url <视频链接>       从URL下载并处理视频
  download <视频链接>  仅下载视频，不转录和总结
  local <目录路径>     处理本地视频目录
  file <文件路径>      处理本地视频文件
  llm <ollama|kimi|deepseek>  切换LLM模型
  mode <outline|timeline|mapreduce>  切换摘要模式
  force                切换强制重处理模式
  help                 显示帮助
  exit / quit / q      退出程序
""")
        return True

    if cmd == "llm":
        if arg in ("ollama", "kimi", "deepseek"):
            llm = arg
            print(f"LLM 切换为: {llm}")
        else:
            print(f"无效的LLM: {arg}，可选: ollama, kimi, deepseek")
        return True

    if cmd == "mode":
        if arg in ("outline", "timeline", "mapreduce"):
            mode = arg
            print(f"摘要模式切换为: {mode}")
        else:
            print(f"无效的模式: {arg}，可选: outline, timeline, mapreduce")
        return True

    if cmd == "force":
        force = not force
        print(f"强制重处理模式: {'开启' if force else '关闭'}")
        return True

    class Args:
        pass

    args = Args()
    args.llm = llm
    args.mode = mode
    args.detail_level = detail_level
    args.bullet_count = bullet_count
    args.force = force
    args.download_only = False

    try:
        if cmd == "download":
            if not arg:
                print("错误: 请提供视频URL")
                return True
            args.url = arg
            args.file = None
            args.local = None
            args.download_only = True
            _process_url(args)

        elif cmd == "url":
            if not arg:
                print("错误: 请提供视频URL")
                return True
            args.url = arg
            args.file = None
            args.local = None
            _process_url(args)

        elif cmd == "local":
            if not arg:
                print("错误: 请提供本地目录路径")
                return True
            args.url = None
            args.file = None
            args.local = arg
            _process_local(args)

        elif cmd == "file":
            if not arg:
                print("错误: 请提供视频文件路径")
                return True
            args.url = None
            args.file = arg
            args.local = None
            _process_file(args)

        else:
            # 自动判断：使用原始大小写，URL/路径不能小写
            if arg:
                full = f"{raw_cmd} {arg}"
            else:
                full = raw_cmd

            if full.startswith("http://") or full.startswith("https://"):
                args.url = full
                args.file = None
                args.local = None
                _process_url(args)
            elif os.path.isdir(full):
                args.url = None
                args.file = None
                args.local = full
                _process_local(args)
            elif os.path.isfile(full):
                args.url = None
                args.file = full
                args.local = None
                _process_file(args)
            else:
                print(f"未知命令或路径: {full}")
                print("输入 help 查看可用命令")
    except Exception as e:
        print(f"\n处理出错: {e}")
        print("可以继续输入下一条命令")

    return True

def _process_url(args):
    from pipeline.download import download_video
    temp_video_path, video_name = download_video(args.url)

    print(f"Setting paths for video: {video_name}")
    video_dir = set_paths(video_name)
    print(f"Video directory: {video_dir}")

    from config import VIDEO_PATH, OUTPUT_PATH
    print(f"VIDEO_PATH: {VIDEO_PATH}")

    if not args.force and os.path.exists(VIDEO_PATH):
        if getattr(args, 'download_only', False):
            print(f"Video already exists: {VIDEO_PATH}")
            print("[DOWNLOAD-ONLY] Skipping download. Use --force to re-download.")
            return
        if os.path.exists(OUTPUT_PATH):
            print(f"Video already processed: {VIDEO_PATH}")
            print(f"Summary already exists: {OUTPUT_PATH}")
            print("Skipping. Use --force to reprocess.")
            return

    print(f"Moving temp video from {temp_video_path} to {VIDEO_PATH}")
    os.makedirs(video_dir, exist_ok=True)
    shutil.move(temp_video_path, VIDEO_PATH)
    video_path = VIDEO_PATH
    print(f"Video moved to: {VIDEO_PATH}")

    if getattr(args, 'download_only', False):
        print(f"[DOWNLOAD-ONLY] Video downloaded to: {VIDEO_PATH}")
        print("[DOWNLOAD-ONLY] Skipping transcription and summarization")
    else:
        process_video(video_path, video_name, args)

    if os.path.exists("temp"):
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

def _process_local(args):
    local_dir = os.path.abspath(args.local)
    if not os.path.isdir(local_dir):
        print(f"Error: {local_dir} is not a valid directory")
        return

    video_name = os.path.basename(local_dir.rstrip(os.sep))
    video_file = find_video_in_dir(local_dir)

    if not video_file:
        print(f"Error: No video/audio file found in {local_dir}")
        print(f"Supported formats: {', '.join(sorted(VIDEO_EXTENSIONS))}")
        return

    print(f"[LOCAL] Directory: {local_dir}")
    print(f"[LOCAL] Video found: {video_file}")
    print(f"[LOCAL] Video name: {video_name}")

    video_dir = set_paths(video_name)

    import config
    config.VIDEO_PATH = video_file
    config.TRANSCRIPT_PATH = os.path.join(local_dir, "transcript.json")
    config.CHUNKS_PATH = os.path.join(local_dir, "chunks.json")
    config.PARTIAL_SUMMARY_PATH = os.path.join(local_dir, "partial_summary.json")
    config.OUTPUT_PATH = os.path.join(local_dir, "summary.md")

    print(f"[LOCAL] Output paths:")
    print(f"  VIDEO_PATH: {config.VIDEO_PATH}")
    print(f"  TRANSCRIPT_PATH: {config.TRANSCRIPT_PATH}")
    print(f"  OUTPUT_PATH: {config.OUTPUT_PATH}")

    if not args.force and os.path.exists(config.OUTPUT_PATH):
        print(f"Summary already exists: {config.OUTPUT_PATH}")
        print("Skipping. Use --force to reprocess.")
        return

    process_video(video_file, video_name, args)

def _process_file(args):
    video_path = args.file
    video_name = os.path.basename(video_path).split('.')[0]

    print(f"Setting paths for video: {video_name}")
    video_dir = set_paths(video_name)
    print(f"Video directory: {video_dir}")

    from config import VIDEO_PATH, OUTPUT_PATH
    print(f"VIDEO_PATH: {VIDEO_PATH}")

    if not args.force and os.path.exists(VIDEO_PATH) and os.path.exists(OUTPUT_PATH):
        print(f"Video already processed: {VIDEO_PATH}")
        print(f"Summary already exists: {OUTPUT_PATH}")
        print("Skipping. Use --force to reprocess.")
        return

    print(f"Copying local video from {video_path} to {VIDEO_PATH}")
    os.makedirs(video_dir, exist_ok=True)

    try:
        shutil.copy2(video_path, VIDEO_PATH)
        print(f"Video copied to: {VIDEO_PATH}")
    except Exception as e:
        print(f"Error copying video: {e}")
        abs_src = os.path.abspath(video_path)
        abs_dst = os.path.abspath(VIDEO_PATH)
        print(f"Trying with absolute paths:")
        print(f"  Source: {abs_src}")
        print(f"  Destination: {abs_dst}")
        shutil.copy2(abs_src, abs_dst)
        print(f"Video copied to: {abs_dst}")

    process_video(VIDEO_PATH, video_name, args)

def interactive_mode(llm, mode, detail_level, bullet_count, force=False):
    """交互式循环模式"""
    print(f"\n{'='*50}")
    print(f"  Video Summarizer 交互模式")
    print(f"  LLM: {llm} | 模式: {mode} | 强制重处理: {'开' if force else '关'}")
    print(f"  输入 help 查看命令，exit 退出")
    print(f"{'='*50}\n")

    while True:
        try:
            user_input = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue

        result = handle_command(user_input, llm, mode, detail_level, bullet_count, force)
        if not result:
            break

        # 从命令中获取可能更新的 llm/mode/force 状态
        parts = user_input.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""
        if cmd == "llm" and arg in ("ollama", "kimi", "deepseek"):
            llm = arg
        elif cmd == "mode" and arg in ("outline", "timeline", "mapreduce"):
            mode = arg
        elif cmd == "force":
            force = not force

def main():
    parser = argparse.ArgumentParser(description="Video Summarizer")
    parser.add_argument("--url", type=str, help="Video URL")
    parser.add_argument("--file", type=str, help="Local video file path")
    parser.add_argument("--local", type=str, help="Local video directory path")
    parser.add_argument("--llm", type=str, choices=["ollama", "kimi", "deepseek"], default=MODEL_PROVIDER, help="LLM provider")
    parser.add_argument("--mode", type=str, choices=["outline", "timeline", "mapreduce"], default=SUMMARY_STYLE, help="Summarization mode")
    parser.add_argument("--detail-level", type=int, default=2, help="Summary detail level (1-5)")
    parser.add_argument("--bullet-count", type=int, default=10, help="Number of bullet points")
    parser.add_argument("--force", action="store_true", help="Force reprocess even if output exists")
    parser.add_argument("--no-correct", action="store_true", help="Skip transcript correction step")
    parser.add_argument("--download-only", action="store_true", help="Only download video, skip transcription and summarization")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode (keep running after processing)")

    args = parser.parse_args()

    has_input = args.url or args.file or args.local

    # 如果指定了 --interactive 或没有提供任何输入，进入交互模式
    if args.interactive or not has_input:
        interactive_mode(args.llm, args.mode, args.detail_level, args.bullet_count, args.force)
        return

    # 单次命令模式（兼容原有行为）
    class SingleArgs:
        pass

    single_args = SingleArgs()
    single_args.llm = args.llm
    single_args.mode = args.mode
    single_args.detail_level = args.detail_level
    single_args.bullet_count = args.bullet_count
    single_args.force = args.force
    single_args.download_only = args.download_only

    if args.local:
        single_args.url = None
        single_args.file = None
        single_args.local = args.local
        _process_local(single_args)
    elif args.url:
        single_args.url = args.url
        single_args.file = None
        single_args.local = None
        _process_url(single_args)
    elif args.file:
        single_args.url = None
        single_args.file = args.file
        single_args.local = None
        _process_file(single_args)

if __name__ == "__main__":
    main()
