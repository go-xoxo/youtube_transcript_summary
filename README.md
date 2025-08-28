# YouTube Transcript Summarizer

> This tool fetches YouTube video metadata and subtitles via `yt-dlp`, converts the subtitles to plain text, and uses the OpenAI API to generate a Markdown summary.

**🚀 Now enhanced with Model Context Protocol (MCP) support!**

## 🏗️ Architecture

This repository now implements the **Model Context Protocol (MCP)** as the primary interface, making all tools discoverable, pluggable, and queryable through a standardized JSON-RPC protocol.

### Legacy Tools (Still Available)
- `fetch_transcript.py`: Downloads metadata and subtitles (converted to plain text)
- `youtube_summary.py`: Sends transcript to OpenAI and writes a Markdown summary
- `summarize_video.sh`: Convenience wrapper that runs both steps

### 🔥 NEW: MCP Server Implementation
- `mcp_server.py`: Full MCP server with JSON-RPC over HTTP
- `mcp_client.py`: MCP client for testing and interaction
- `mcp_demo.py`: Complete demonstration of MCP protocol features
- `start_mcp_server.sh`: Easy server startup script

## 🚀 Quick Start (MCP Mode)

### 1. Setup Environment
```bash
./setup.sh
source .venv/bin/activate
export OPENAI_API_KEY="<your_openai_api_key>"
```

### 2. Start MCP Server
```bash
./start_mcp_server.sh
```

### 3. Use MCP Client
```bash
# Run automated demo
python3 mcp_demo.py

# Interactive mode
python3 mcp_demo.py --interactive

# Basic client test
python3 mcp_client.py
```

## 🔧 MCP Tools Available

### `fetch_youtube_transcript`
Fetches transcript and metadata for a YouTube video by video ID.

### `summarize_transcript` 
Generates an AI summary from transcript text using OpenAI.

### `process_youtube_video`
Combined tool that fetches transcript and generates summary in one step.

## 📚 MCP Resources Available

- `youtube://transcript/{video_id}` - Access transcript data
- `youtube://metadata/{video_id}` - Access video metadata  
- `youtube://summary/{video_id}` - Access generated summaries

## 🎯 Key MCP Benefits

1. **Discoverability** - Clients can query what tools and resources exist
2. **Pluggability** - Easy to add/remove tools without changing AI models
3. **Composability** - Standard protocol for integration with other MCP servers
4. **Tool Schema** - Built-in input validation and documentation
5. **Resource Access** - URI-based patterns for data access

## 🔌 Integration Examples

### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "youtube-transcript": {
      "command": "python3",
      "args": ["/path/to/mcp_server.py"],
      "env": {
        "OPENAI_API_KEY": "your-key"
      }
    }
  }
}
```

### Custom MCP Client
```python
from mcp_client import MCPClient

async def use_youtube_tools():
    client = MCPClient("http://localhost:8000")
    await client.initialize()
    
    # Discover available tools
    tools = await client.list_tools()
    
    # Process a video end-to-end
    result = await client.process_youtube_video("dQw4w9WgXcQ")
```

## 📖 Legacy Usage (Original Tools)

```bash
./setup.sh
source .venv/bin/activate
export OPENAI_API_KEY="<your_openai_api_key>"
```

### Usage

```bash
./summarize_video.sh VIDEO_ID [OUTPUT_SUMMARY.md]
```
Note: By default, the summary will be saved to `summary_<VIDEO_ID>.md` and rendered in the terminal using `mdv` (installed via `requirements.txt`).

### Example

```bash
./summarize_video.sh qSGkJ_vsuUg summary.md
```

## 📁 Documentation

- `MCP_README.md` - Complete MCP implementation guide
- See existing `summary_*.md` files for examples of generated summaries

## 🔄 Migration Path

The MCP server provides the primary interface going forward, but all legacy tools remain functional. The MCP implementation follows the "MCP First" protocol approach as requested, making all functionality discoverable and pluggable through the standardized Model Context Protocol.