# YouTube Transcript Summarizer 🤖✨

> This tool fetches YouTube video metadata and subtitles via `yt-dlp`, converts the subtitles to plain text, and uses advanced AI to generate comprehensive summaries and analysis.

## 🚀 NEW: Superhuman AI Capabilities

This repository now includes **superhuman multimodal AI capabilities** that can analyze videos with advanced reasoning, multi-perspective understanding, and comprehensive insights!

### 🧠 AI Capabilities

- **🧠 Advanced reasoning and analysis** - Deep cognitive analysis and critical thinking
- **🎯 Multi-perspective content understanding** - Multiple viewpoints and interpretations  
- **📊 Structured data extraction** - Key themes, arguments, and evidence
- **🌍 Multilingual processing** - Support for multiple languages
- **🔍 Fact-checking and verification** - Identify claims that can be verified
- **📈 Sentiment and emotion analysis** - Emotional undertones and sentiment patterns
- **🎨 Visual content analysis** - Future support for thumbnail and visual content
- **📋 Multiple output formats** - Executive summaries, detailed reports, JSON, bullets
- **🔗 Knowledge graph generation** - Connect related concepts and ideas
- **🎭 Persona-based analysis** - Different analytical perspectives

## Setup

```bash
./setup.sh
source .venv/bin/activate
export OPENAI_API_KEY="<your_openai_api_key>"
```

## Usage

### Standard Analysis
```bash
./summarize_video.sh VIDEO_ID [OUTPUT_SUMMARY.md]
```

### 🤖 Superhuman AI Analysis
```bash
./summarize_video.sh VIDEO_ID [OUTPUT_SUMMARY.md] --superhuman
```

### 🚀 Advanced Superhuman Analysis (Multiple Formats)
```bash
./superhuman_analyze.sh VIDEO_ID [OPTIONS]

# Options:
--format FORMAT         # executive_summary, detailed_markdown, json_structured, quick_bullets, social_media
--analysis-type TYPE    # comprehensive, quick, academic, business  
--output FILE          # custom output file
```

### Examples

```bash
# Standard summary
./summarize_video.sh qSGkJ_vsuUg

# Superhuman AI analysis
./summarize_video.sh qSGkJ_vsuUg --superhuman

# Comprehensive business analysis in JSON format
./superhuman_analyze.sh qSGkJ_vsuUg --analysis-type business --format json_structured

# Executive summary for leadership
./superhuman_analyze.sh abc123 --format executive_summary --output executive_brief.md
```

## Scripts

- `fetch_transcript.py`: Downloads metadata and subtitles (converted to plain text)
- `youtube_summary.py`: Original OpenAI-based summarization
- `youtube_summary_enhanced.py`: Enhanced version with superhuman AI mode
- `superhuman_ai_summary.py`: Full superhuman AI analyzer with multiple formats
- `summarize_video.sh`: Convenience wrapper for standard and superhuman modes
- `superhuman_analyze.sh`: Advanced superhuman AI analysis with all options
- `test_superhuman_ai.py`: Test suite for validating AI capabilities

## Output Formats

The superhuman AI system generates multiple output formats automatically:

1. **Executive Summary** - Concise overview for busy executives
2. **Detailed Markdown** - Comprehensive analysis with insights
3. **JSON Structured** - Machine-readable structured data
4. **Quick Bullets** - Fast bullet-point overview
5. **Social Media** - Social media friendly summary

## Testing

Run the test suite to validate superhuman AI capabilities:

```bash
python3 test_superhuman_ai.py
```

## Requirements

See `requirements.txt` for all dependencies. Key additions for superhuman AI:
- Advanced OpenAI models (GPT-4 Turbo)
- Multiple output format support
- Enhanced error handling and fallback systems