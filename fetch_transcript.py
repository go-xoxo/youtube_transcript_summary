import argparse
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
from xml.etree.ElementTree import ParseError
import pafy
from pytube import YouTube

# --- Fix for pafy: Use youtube_dl backend ---
pafy.backend_shared.backend = "internal"  # This avoids broken 'set_backend' call

parser = argparse.ArgumentParser()
parser.add_argument("--video_id", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

video_id = args.video_id
output_path = args.output

print(f"[INFO] Fetching transcript for video: {video_id}")

# --- Fetch metadata ---
try:
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    video = pafy.new(video_url)

    print("[INFO] Video Metadata:")
    print(f"Title: {video.title}")
    print(f"Author: {video.author}")
    print(f"Duration: {video.duration}")
    print(f"Views: {video.viewcount}")
    print(f"Description: {video.description[:300]}...")

    metadata_str = f"""Title: {video.title}
Author: {video.author}
Duration: {video.duration}
Views: {video.viewcount}
Description: {video.description}
"""
except Exception as e:
    print(f"[WARN] Failed to fetch metadata: {e}")
    metadata_str = "[WARN] Metadata not available.\n"

# --- Fetch transcript ---
try:
    # `youtube_transcript_api` version 1.2+ exposes an instance method `list`
    # instead of the old static `list_transcripts`. Instantiate the API client
    # and call `.list` to retrieve available transcripts.
    transcript_list = YouTubeTranscriptApi().list(video_id)
    print("[INFO] Available transcripts:")
    for t in transcript_list:
        t_type = "generated" if t.is_generated else "manual"
        print(f"[INFO]  - {t.language_code} ({t_type})")

    print(f"[INFO] Attempting to fetch transcript (languages = ['en'])...")
    transcript = transcript_list.find_transcript(['en'])

    try:
        fetched = transcript.fetch()
    except ParseError:
        print("[INFO] [WARN] Broken XML detected. Trying to translate transcript...")
        if transcript.is_translatable:
            try:
                transcript = transcript.translate("en")
                fetched = transcript.fetch()
            except Exception as e:
                print(f"[ERROR] [ERROR] Failed to fetch translated transcript: {e}")
                raise e
        else:
            raise

    if fetched is None:
        raise ValueError("Transcript object is None or broken.")

    text = "\n".join([snippet.text for snippet in fetched])
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(metadata_str + "\n" + text)

except (NoTranscriptFound, TranscriptsDisabled) as e:
    print(f"[ERROR] No transcript found: {e}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("TRANSCRIPT_NOT_FOUND")

except Exception as e:
    print(f"[WARN] YouTubeTranscriptApi failed: {e}. Trying pytube fallback...")
    try:
        yt = YouTube(video_url)
        # select English captions (manual or auto)
        caption = (
            yt.captions.get_by_language_code('en')
            or yt.captions.get_by_language_code('a.en')
            or yt.captions.get_by_language_code('en-US')
            or yt.captions.get_by_language_code('en-GB')
            # `yt.captions` behaves like a dict where iterating yields language
            # codes. Previously we tried `next(iter(yt.captions), None)` which
            # returned a language code string. Attempting to call
            # `generate_srt_captions()` on that string would raise an
            # AttributeError. Instead, iterate over the values to get an actual
            # Caption object.
            or next(iter(yt.captions.values()), None)
        )
        if not caption:
            raise ValueError('No captions available via pytube')
        srt_captions = caption.generate_srt_captions()
        lines = []
        for line in srt_captions.splitlines():
            if line.strip().isdigit() or '-->' in line:
                continue
            lines.append(line)
        text = "\n".join(lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(metadata_str + "\n" + text)
    except Exception as e2:
        print(f"[ERROR] Pytube fallback failed: {e2}")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("TRANSCRIPT_NOT_FOUND")
