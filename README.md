# YouTube Transcript Summarizer

> This tool fetches YouTube video metadata and subtitles via `yt-dlp`, converts the subtitles to plain text, and uses the OpenAI API to generate a Markdown summary.

## Setup

```bash
./setup.sh
source .venv/bin/activate
export OPENAI_API_KEY="<your_openai_api_key>"
```

## Usage

```bash
./summarize_video.sh VIDEO_ID OUTPUT_SUMMARY.md
```

### Example

```bash
./summarize_video.sh qSGkJ_vsuUg summary.md
```

## Scripts

- `fetch_transcript.py`: Downloads metadata and subtitles (converted to plain text).
- `youtube_summary.py`: Sends transcript to OpenAI and writes a Markdown summary.
- `summarize_video.sh`: Convenience wrapper that runs both steps.