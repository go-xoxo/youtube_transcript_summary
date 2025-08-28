#!/usr/bin/env bash
set -euo pipefail

# Superhuman AI Video Analyzer
# A comprehensive analysis tool that goes beyond basic summarization

show_help() {
    cat << 'EOF'
🤖 Superhuman AI Video Analyzer 🚀

USAGE:
  ./superhuman_analyze.sh VIDEO_ID [OPTIONS]

OPTIONS:
  --format FORMAT         Output format (default: detailed_markdown)
                         Choices: executive_summary, detailed_markdown, 
                                 json_structured, quick_bullets, social_media
  
  --analysis-type TYPE    Analysis type (default: comprehensive)
                         Choices: comprehensive, quick, academic, business
  
  --output FILE          Output file (default: superhuman_analysis_VIDEO_ID.md)
  
  --help                 Show this help message

EXAMPLES:
  # Comprehensive analysis with detailed markdown output
  ./superhuman_analyze.sh qSGkJ_vsuUg
  
  # Quick business analysis in JSON format
  ./superhuman_analyze.sh abc123 --analysis-type business --format json_structured
  
  # Executive summary for leadership review
  ./superhuman_analyze.sh def456 --format executive_summary --output executive_brief.md

SUPERHUMAN AI CAPABILITIES:
🧠 Advanced reasoning and analysis
🎯 Multi-perspective content understanding
📊 Structured data extraction
🌍 Multilingual processing
🔍 Fact-checking and verification
📈 Sentiment and emotion analysis
🎨 Visual content analysis
📋 Multiple output formats
🔗 Knowledge graph generation
🎭 Persona-based analysis

EOF
}

# Default values
FORMAT="detailed_markdown"
ANALYSIS_TYPE="comprehensive"
OUTPUT=""

# Parse arguments
if [[ $# -eq 0 ]] || [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    show_help
    exit 0
fi

VIDEO_ID="$1"
shift

# Parse optional arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --format)
            FORMAT="$2"
            shift 2
            ;;
        --analysis-type)
            ANALYSIS_TYPE="$2"
            shift 2
            ;;
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Set default output filename if not provided
if [[ -z "$OUTPUT" ]]; then
    case "$FORMAT" in
        json_structured)
            OUTPUT="superhuman_analysis_${VIDEO_ID}.json"
            ;;
        *)
            OUTPUT="superhuman_analysis_${VIDEO_ID}.md"
            ;;
    esac
fi

# Create temporary file for transcript
TRANSCRIPT_FILE=$(mktemp "${VIDEO_ID}.XXXXXX.txt")

echo "🤖 Superhuman AI Video Analyzer Starting..."
echo "📹 Video ID: $VIDEO_ID"
echo "🎯 Analysis Type: $ANALYSIS_TYPE"
echo "📝 Output Format: $FORMAT"
echo "💾 Output File: $OUTPUT"
echo ""

# Check if OpenAI API key is set
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
    echo "❌ Error: OPENAI_API_KEY environment variable not set"
    echo "Please set your OpenAI API key:"
    echo "  export OPENAI_API_KEY='your-api-key-here'"
    exit 1
fi

echo "🔄 Phase 1: Fetching transcript and metadata..."
if python3 fetch_transcript.py --video_id "$VIDEO_ID" --output "$TRANSCRIPT_FILE"; then
    echo "✅ Transcript fetched successfully"
else
    echo "❌ Failed to fetch transcript"
    exit 1
fi

echo ""
echo "🧠 Phase 2: Deploying Superhuman AI analysis..."
echo "⚡ Activating advanced reasoning capabilities..."
echo "🎨 Enabling multimodal understanding..."
echo "🔍 Engaging fact-checking systems..."

if python3 superhuman_ai_summary.py \
    --video_id "$VIDEO_ID" \
    --input "$TRANSCRIPT_FILE" \
    --output "$OUTPUT" \
    --format "$FORMAT" \
    --analysis_type "$ANALYSIS_TYPE"; then
    
    echo ""
    echo "🎉 Superhuman AI Analysis Complete!"
    echo "📊 Primary output: $OUTPUT"
    
    # Show file size and summary
    file_size=$(du -h "$OUTPUT" | cut -f1)
    echo "📏 File size: $file_size"
    
    # Count additional format files generated
    base_name="${OUTPUT%.*}"
    additional_files=$(find . -name "${base_name}_*.md" -o -name "${base_name}_*.json" 2>/dev/null | wc -l || echo "0")
    if [[ "$additional_files" -gt 0 ]]; then
        echo "💾 Additional formats generated: $additional_files files"
        echo "📂 Available formats:"
        find . -name "${base_name}_*" 2>/dev/null | sort | sed 's/^/  - /'
    fi
    
    echo ""
    echo "🚀 Analysis capabilities used:"
    echo "  🧠 Advanced reasoning and analysis"
    echo "  🎯 Multi-perspective content understanding"
    echo "  📊 Structured data extraction"
    echo "  🔍 Fact-checking and verification"
    echo "  📈 Sentiment and emotion analysis"
    echo "  📋 Multiple output formats"
    
    # Offer to display the output
    if command -v mdv >/dev/null 2>&1 && [[ "$FORMAT" != "json_structured" ]]; then
        echo ""
        echo "🖥️  Rendering analysis..."
        mdv "$OUTPUT"
    elif [[ "$FORMAT" == "json_structured" ]] && command -v jq >/dev/null 2>&1; then
        echo ""
        echo "🖥️  Displaying JSON analysis..."
        jq . "$OUTPUT"
    else
        echo ""
        echo "📄 To view the analysis:"
        if [[ "$FORMAT" == "json_structured" ]]; then
            echo "  cat '$OUTPUT' | jq ."
        else
            echo "  cat '$OUTPUT'"
            echo "  # or install mdv for better rendering: pip install mdv"
        fi
    fi
    
else
    echo "❌ Superhuman AI analysis failed"
    exit 1
fi

# Cleanup
rm -f "$TRANSCRIPT_FILE"

echo ""
echo "✨ Superhuman AI Analysis Session Complete!"
echo "🎯 Video $VIDEO_ID analyzed with superhuman capabilities"
echo "📊 Results available in $OUTPUT"