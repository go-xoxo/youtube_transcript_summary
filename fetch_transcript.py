#!/usr/bin/env python3
import argparse
import subprocess
import glob
import os
import re
import sys

def detect_language(video_url: str) -> str:
    print("[INFO] Detecting transcript language")
    try:
        proc = subprocess.run(
            ["yt-dlp", "-O", "%(language)s", video_url],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        lang = proc.stdout.strip() or "en"
    except Exception as e:
        print(f"[WARN] Could not detect language, defaulting to 'en': {e}", file=sys.stderr)
        lang = "en"

    primary = lang.split("-")[0]
    if primary != lang:
        print(f"[INFO] Using language '{lang}', normalized to '{primary}'")
    else:
        print(f"[INFO] Using language: {primary}")
    return primary

def fetch_metadata(video_url: str) -> str:
    # Description is wrapped in a fenced code block; the closing ``` is emitted by the template itself.
    print(f"[INFO] Fetching metadata for video: {video_url.split('=')[-1]}")
    template = (
        "id: %(id)s\n"
        "title: %(title)s\n"
        "uploader: %(uploader)s\n"
        "channel: %(channel)s\n"
        "upload_date: %(upload_date)s\n"
        "duration: %(duration_string)s\n"
        "view_count: %(view_count)s\n"
        "like_count: %(like_count)s\n"
        "categories: %(categories)s\n"
        "tags: %(tags)s\n"
        "webpage_url: %(webpage_url)s\n"
        "description: ```%(description)s\n```\n"   # <-- wrap description in code fence
    )
    try:
        proc = subprocess.run(
            ["yt-dlp", "-O", template, video_url],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return proc.stdout.strip() + "\n"
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] yt-dlp metadata fetch failed: {e.stderr}", file=sys.stderr)
        sys.exit(1)

def download_srt(video_url: str, video_id: str, lang: str, srt_dir: str) -> str:
    print("[INFO] Downloading subtitles via yt-dlp")
    os.makedirs(srt_dir, exist_ok=True)

    cmd = [
        "yt-dlp",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs", lang,
        "--skip-download",
        "--convert-subs", "srt",
        "-o", "%(id)s.%(ext)s",
        video_url,
    ]
    try:
        subprocess.run(
            cmd,
            cwd=srt_dir,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] yt-dlp subtitle download failed: {e.stderr}", file=sys.stderr)
        sys.exit(1)

    patterns = [
        os.path.join(srt_dir, f"{video_id}.srt"),
        os.path.join(srt_dir, f"{video_id}.*.srt"),
        os.path.join(srt_dir, "*.srt"),
    ]
    for pat in patterns:
        matches = sorted(glob.glob(pat))
        if matches:
            srt_path = matches[0]
            print(f"[INFO] Saved .srt to: {srt_path}")
            return srt_path

    print("[ERROR] No .srt subtitle file found", file=sys.stderr)
    sys.exit(1)

def srt_to_text(srt_path: str) -> str:
    print(f"[INFO] Converting subtitles to plain text: {os.path.basename(srt_path)}")
    lines_out = []
    window = []

    with open(srt_path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if re.fullmatch(r"\d+", line):
                continue
            if "-->" in line:
                continue
            if not line.strip():
                continue
            if line in window:
                continue

            lines_out.append(line)
            window.append(line)
            if len(window) > 3:
                window.pop(0)

    return "\n".join(lines_out)

def main():
    parser = argparse.ArgumentParser(
        description="Fetch YouTube video metadata and transcript via yt-dlp, convert to plain text, and keep .srt"
    )
    parser.add_argument("--video_id", required=True, help="YouTube video ID")
    parser.add_argument("--output", required=True, help="Path to output transcript file")
    parser.add_argument("--srt-dir", default=None, help="Directory to save the .srt (default: alongside output)")
    args = parser.parse_args()

    video_id = args.video_id
    output_path = args.output
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    srt_dir = args.srt_dir or os.path.dirname(os.path.abspath(output_path)) or "."

    metadata_str = fetch_metadata(video_url)
    lang = detect_language(video_url)
    srt_path = download_srt(video_url, video_id, lang, srt_dir)
    transcript_text = srt_to_text(srt_path)

    print(f"[INFO] Writing combined text to {output_path}")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(metadata_str)
        f.write("\ntranscript:\n")   # <-- add transcript header
        f.write(transcript_text)
        f.write("\n")

    print("[DONE] Transcript written and .srt preserved.")

if __name__ == "__main__":
    main()
