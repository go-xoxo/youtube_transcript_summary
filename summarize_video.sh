#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 VIDEO_ID OUTPUT_SUMMARY.md"
  exit 1
fi

VIDEO_ID=$1
OUTPUT_SUMMARY=$2

TRANSCRIPT_FILE=$(mktemp "${VIDEO_ID}.XXXXXX.txt")

echo "[INFO] Fetching transcript and metadata..."
python3 fetch_transcript.py --video_id "$VIDEO_ID" --output "$TRANSCRIPT_FILE"

echo "[INFO] Generating summary via OpenAI..."
python3 youtube_summary.py --video_id "$VIDEO_ID" --input "$TRANSCRIPT_FILE" --output "$OUTPUT_SUMMARY"

rm -f "$TRANSCRIPT_FILE"

echo "[INFO] Summary written to $OUTPUT_SUMMARY"