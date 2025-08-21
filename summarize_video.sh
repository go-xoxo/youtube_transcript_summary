#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 VIDEO_ID [OUTPUT_SUMMARY.md]"
  exit 1
fi

VIDEO_ID=$1
if [[ $# -eq 2 ]]; then
  OUTPUT_SUMMARY=$2
else
  OUTPUT_SUMMARY="summary_${VIDEO_ID}.md"
fi

TRANSCRIPT_FILE=$(mktemp "${VIDEO_ID}.XXXXXX.txt")

echo "[INFO] Fetching transcript and metadata..."
python3 fetch_transcript.py --video_id "$VIDEO_ID" --output "$TRANSCRIPT_FILE"

echo "[INFO] Generating summary via OpenAI..."
python3 youtube_summary.py --video_id "$VIDEO_ID" --input "$TRANSCRIPT_FILE" --output "$OUTPUT_SUMMARY"


echo "[INFO] Summary written to $OUTPUT_SUMMARY"

if command -v mdv >/dev/null 2>&1; then
  echo "[INFO] Rendering summary..."
  mdv "$OUTPUT_SUMMARY"
else
  echo "[WARNING] 'mdv' not found; install it with 'pip install mdv' to render markdown"
fi