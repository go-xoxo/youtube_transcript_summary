#!/usr/bin/env bash
set -euo pipefail

# YouTube Transcript MCP Server Startup Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check for OpenAI API key
if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set. Summarization will not work."
    echo "   Set it with: export OPENAI_API_KEY='your-key-here'"
    echo ""
fi

# Set default host and port
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

echo "🚀 Starting YouTube Transcript MCP Server..."
echo "📍 Server will be available at: http://${HOST}:${PORT}"
echo "🔧 MCP endpoint: http://${HOST}:${PORT}/mcp"
echo "❤️  Health check: http://${HOST}:${PORT}/health"
echo ""
echo "📋 Available tools:"
echo "  • fetch_youtube_transcript - Fetch transcript and metadata"
echo "  • summarize_transcript - Generate AI summary"
echo "  • process_youtube_video - Fetch + summarize in one step"
echo ""
echo "📚 Available resources:"
echo "  • youtube://transcript/{video_id} - Access transcript data"
echo "  • youtube://metadata/{video_id} - Access video metadata"
echo "  • youtube://summary/{video_id} - Access generated summaries"
echo ""
echo "💬 Available prompts:"
echo "  • youtube_summary - Prompt template for video summaries"
echo ""
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Start the MCP server
python3 mcp_server.py