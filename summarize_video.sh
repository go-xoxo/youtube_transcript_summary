#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 3 ]]; then
  echo "Usage: $0 VIDEO_ID [OUTPUT_SUMMARY.md] [--superhuman]"
  echo ""
  echo "OPTIONS:"
  echo "  --superhuman    Enable superhuman AI capabilities for advanced analysis"
  echo ""
  echo "EXAMPLES:"
  echo "  $0 qSGkJ_vsuUg                    # Standard analysis"
  echo "  $0 qSGkJ_vsuUg summary.md        # Standard analysis with custom output"
  echo "  $0 qSGkJ_vsuUg summary.md --superhuman  # Superhuman AI analysis"
  exit 1
fi

VIDEO_ID=$1
SUPERHUMAN_MODE=""

# Parse arguments
if [[ $# -ge 2 ]]; then
  if [[ "$2" == "--superhuman" ]]; then
    OUTPUT_SUMMARY="summary_${VIDEO_ID}.md"
    SUPERHUMAN_MODE="--superhuman"
  else
    OUTPUT_SUMMARY=$2
    if [[ $# -eq 3 && "$3" == "--superhuman" ]]; then
      SUPERHUMAN_MODE="--superhuman"
    fi
  fi
else
  OUTPUT_SUMMARY="summary_${VIDEO_ID}.md"
fi

TRANSCRIPT_FILE=$(mktemp "${VIDEO_ID}.XXXXXX.txt")

if [[ -n "$SUPERHUMAN_MODE" ]]; then
  echo "🤖 Superhuman AI Mode Activated!"
  echo "📹 Video ID: $VIDEO_ID"
  echo "🧠 Enhanced capabilities: Advanced reasoning, multi-perspective analysis, fact-checking"
else
  echo "[INFO] Standard AI Mode"
  echo "[INFO] Video ID: $VIDEO_ID"
fi

echo "[INFO] Fetching transcript and metadata..."
python3 fetch_transcript.py --video_id "$VIDEO_ID" --output "$TRANSCRIPT_FILE"

if [[ -n "$SUPERHUMAN_MODE" ]]; then
  echo "🚀 Generating superhuman AI summary..."
  python3 youtube_summary_enhanced.py --video_id "$VIDEO_ID" --input "$TRANSCRIPT_FILE" --output "$OUTPUT_SUMMARY" $SUPERHUMAN_MODE
else
  echo "[INFO] Generating summary via OpenAI..."
  python3 youtube_summary.py --video_id "$VIDEO_ID" --input "$TRANSCRIPT_FILE" --output "$OUTPUT_SUMMARY"
fi

echo "[INFO] Summary written to $OUTPUT_SUMMARY"

if command -v mdv >/dev/null 2>&1; then
  echo "[INFO] Rendering summary..."
  mdv "$OUTPUT_SUMMARY"
else
  echo "[WARNING] 'mdv' not found; install it with 'pip install mdv' to render markdown"
fi