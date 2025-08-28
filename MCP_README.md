# MCP Server Configuration for YouTube Transcript Summarizer

## Overview

This directory contains a complete **Model Context Protocol (MCP)** implementation for YouTube transcript fetching and summarization. The MCP server exposes discoverable, pluggable tools that can be used by any MCP-compatible client.

## 🏗️ Architecture

Following the MCP architecture pattern:

1. **MCP Server** (`mcp_server.py`) - Manages tools, resources & prompts, exposes capabilities via JSON-RPC over HTTP
2. **Tools** - Callable functions for transcript processing
3. **Resources** - Data sources for accessing transcript/metadata
4. **Prompts** - Reusable prompt templates
5. **Client** (`mcp_client.py`) - Example client for testing and interaction

## 🔧 Available Tools

### `fetch_youtube_transcript`
Fetches transcript and metadata for a YouTube video by video ID.

**Input Schema:**
```json
{
  "video_id": "string (required) - YouTube video ID",
  "language": "string (optional, default: 'en') - Language code"
}
```

**Returns:**
- Video metadata (title, author, duration, views, description)
- Transcript text
- Success/error status

### `summarize_transcript`
Generates an AI summary from transcript text using OpenAI.

**Input Schema:**
```json
{
  "transcript": "string (required) - Transcript text to summarize",
  "video_id": "string (required) - YouTube video ID for context",
  "max_tokens": "integer (optional, default: 3000) - Maximum tokens for summary"
}
```

**Returns:**
- Generated markdown summary
- Token usage information
- Model used
- Success/error status

### `process_youtube_video`
Combined tool that fetches transcript and generates summary in one step.

**Input Schema:**
```json
{
  "video_id": "string (required) - YouTube video ID",
  "language": "string (optional, default: 'en') - Language code",
  "max_tokens": "integer (optional, default: 3000) - Maximum tokens for summary"
}
```

**Returns:**
- Complete transcript result
- Complete summary result
- Overall success status

## 📚 Available Resources

### `youtube_transcript`
**URI Pattern:** `youtube://transcript/{video_id}`
**MIME Type:** `text/plain`
**Description:** Access to YouTube transcript data by video ID

### `youtube_metadata`
**URI Pattern:** `youtube://metadata/{video_id}`
**MIME Type:** `application/json`
**Description:** Access to YouTube video metadata by video ID

### `video_summary`
**URI Pattern:** `youtube://summary/{video_id}`
**MIME Type:** `text/markdown`
**Description:** Access to generated video summaries by video ID

## 💬 Available Prompts

### `youtube_summary`
Prompt template for generating YouTube video summaries.

**Arguments:**
- `video_id` (required) - YouTube video ID
- `style` (optional) - Summary style: "detailed", "brief", or "technical"

## 🚀 Quick Start

### 1. Setup Environment
```bash
./setup.sh
source .venv/bin/activate
export OPENAI_API_KEY="your-openai-api-key"
```

### 2. Start MCP Server
```bash
./start_mcp_server.sh
```

The server will start on `http://localhost:8000` with the MCP endpoint at `/mcp`.

### 3. Test with Client
```bash
# Run demo
python3 mcp_client.py

# Interactive mode
python3 mcp_client.py --interactive
```

## 🔍 MCP Protocol Usage

### Initialize Connection
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "clientInfo": {"name": "Your Client", "version": "1.0.0"},
    "capabilities": {"tools": {"call": true}}
  }
}
```

### List Available Tools
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "list_tools"
}
```

### Call a Tool
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "call_tool",
  "params": {
    "name": "process_youtube_video",
    "arguments": {
      "video_id": "dQw4w9WgXcQ",
      "language": "en"
    }
  }
}
```

### Read a Resource
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "read_resource",
  "params": {
    "uri": "youtube://transcript/dQw4w9WgXcQ"
  }
}
```

## 🔐 Environment Variables

- `OPENAI_API_KEY` - Required for transcript summarization
- `HOST` - Server host (default: `127.0.0.1`)
- `PORT` - Server port (default: `8000`)

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### MCP Protocol Test
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "list_tools"
  }'
```

## 🔌 Integration Examples

### Claude Desktop Configuration
Add to your Claude Desktop MCP settings:

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
    
    # Process a video end-to-end
    result = await client.process_youtube_video("dQw4w9WgXcQ")
    
    if result["overall_success"]:
        print("Summary:", result["summary_result"]["summary"])
```

## 🎯 Key MCP Benefits

1. **Discoverability** - Clients can query what tools and resources are available
2. **Pluggability** - Easy to add/remove tools without changing the AI model
3. **Composability** - Server can be client of other MCP servers
4. **Standardization** - Uses JSON-RPC over HTTP standard protocol
5. **Tool-Agnostic** - Works with any MCP-compatible client (Claude, custom apps, etc.)

## 🛠️ Development

### Adding New Tools
1. Define tool schema in `_register_tools()`
2. Implement tool handler method
3. Add method to `_handle_call_tool()`

### Adding New Resources
1. Define resource schema in `_register_resources()`
2. Add URI parsing logic to `_handle_read_resource()`

### Adding New Prompts
1. Define prompt schema in `_register_prompts()`
2. Add prompt generation logic to `_handle_get_prompt()`

## 📖 MCP Specification

This implementation follows the Model Context Protocol specification for creating discoverable, pluggable AI tools. For more information:

- MCP creates standardized interfaces between AI applications and external tools/data
- Uses JSON-RPC over HTTP for communication
- Supports tools, resources, and prompts as first-class entities
- Enables true "agentic" AI microservices that can act, solve real problems, and integrate deeply

## 🔄 Migration from Legacy Tools

The original tools (`fetch_transcript.py`, `youtube_summary.py`, `summarize_video.sh`) are preserved but the MCP server now provides the primary interface. All functionality is available through MCP with enhanced discoverability and pluggability.