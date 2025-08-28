#!/usr/bin/env python3
"""
MCP Server for YouTube Transcript Summarizer

This implements a Model Context Protocol server that exposes YouTube transcript
fetching and summarization tools via JSON-RPC over HTTP.
"""

import os
import sys
import json
import uuid
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
import uvicorn

# Import existing functionality
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
from openai import OpenAI
import pafy

# --- MCP Protocol Models ---

class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int, None] = None
    method: str
    params: Optional[Dict[str, Any]] = None

class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int, None] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

class MCPError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None

class ToolDefinition(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]

class ResourceDefinition(BaseModel):
    name: str
    description: str
    uri: str
    mimeType: Optional[str] = None

class PromptDefinition(BaseModel):
    name: str
    description: str
    arguments: Optional[List[Dict[str, Any]]] = None

# --- MCP Server Implementation ---

class MCPServer:
    def __init__(self):
        self.app = FastAPI(title="YouTube Transcript MCP Server", version="1.0.0")
        self.tools: Dict[str, ToolDefinition] = {}
        self.resources: Dict[str, ResourceDefinition] = {}
        self.prompts: Dict[str, PromptDefinition] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        # Fix for pafy backend
        pafy.backend_shared.backend = "internal"
        
        # Initialize OpenAI client
        self.openai_client = None
        if os.environ.get("OPENAI_API_KEY"):
            self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        self._register_tools()
        self._register_resources()
        self._register_prompts()
        self._setup_routes()

    def _register_tools(self):
        """Register available MCP tools"""
        
        # Tool: Fetch YouTube Transcript
        self.tools["fetch_youtube_transcript"] = ToolDefinition(
            name="fetch_youtube_transcript",
            description="Fetches transcript and metadata for a YouTube video by video ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "string",
                        "description": "YouTube video ID (e.g., 'dQw4w9WgXcQ')"
                    },
                    "language": {
                        "type": "string", 
                        "description": "Preferred language code (default: 'en')",
                        "default": "en"
                    }
                },
                "required": ["video_id"]
            }
        )
        
        # Tool: Summarize Transcript
        self.tools["summarize_transcript"] = ToolDefinition(
            name="summarize_transcript",
            description="Generates an AI summary from transcript text using OpenAI",
            inputSchema={
                "type": "object",
                "properties": {
                    "transcript": {
                        "type": "string",
                        "description": "Transcript text to summarize"
                    },
                    "video_id": {
                        "type": "string",
                        "description": "YouTube video ID for context"
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum tokens for summary (default: 3000)",
                        "default": 3000
                    }
                },
                "required": ["transcript", "video_id"]
            }
        )
        
        # Tool: Process YouTube Video (Combined)
        self.tools["process_youtube_video"] = ToolDefinition(
            name="process_youtube_video", 
            description="Fetches transcript and generates summary for a YouTube video in one step",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "string",
                        "description": "YouTube video ID"
                    },
                    "language": {
                        "type": "string",
                        "description": "Preferred language code (default: 'en')",
                        "default": "en"
                    },
                    "max_tokens": {
                        "type": "integer", 
                        "description": "Maximum tokens for summary (default: 3000)",
                        "default": 3000
                    }
                },
                "required": ["video_id"]
            }
        )

    def _register_resources(self):
        """Register available MCP resources"""
        
        self.resources["youtube_transcript"] = ResourceDefinition(
            name="youtube_transcript",
            description="Access to YouTube transcript data by video ID",
            uri="youtube://transcript/{video_id}",
            mimeType="text/plain"
        )
        
        self.resources["youtube_metadata"] = ResourceDefinition(
            name="youtube_metadata", 
            description="Access to YouTube video metadata by video ID",
            uri="youtube://metadata/{video_id}",
            mimeType="application/json"
        )
        
        self.resources["video_summary"] = ResourceDefinition(
            name="video_summary",
            description="Access to generated video summaries by video ID", 
            uri="youtube://summary/{video_id}",
            mimeType="text/markdown"
        )

    def _register_prompts(self):
        """Register available MCP prompts"""
        
        self.prompts["youtube_summary"] = PromptDefinition(
            name="youtube_summary",
            description="Prompt template for generating YouTube video summaries",
            arguments=[
                {"name": "video_id", "description": "YouTube video ID", "required": True},
                {"name": "style", "description": "Summary style (detailed|brief|technical)", "required": False}
            ]
        )

    def _setup_routes(self):
        """Setup FastAPI routes for MCP protocol"""
        
        @self.app.post("/mcp")
        async def mcp_endpoint(request: MCPRequest):
            """Main MCP JSON-RPC endpoint"""
            try:
                return await self._handle_mcp_request(request)
            except Exception as e:
                return MCPResponse(
                    id=request.id,
                    error={"code": -32603, "message": f"Internal error: {str(e)}"}
                )

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "service": "YouTube Transcript MCP Server"}

    async def _handle_mcp_request(self, request: MCPRequest) -> MCPResponse:
        """Handle incoming MCP requests based on method"""
        
        method = request.method
        params = request.params or {}
        
        if method == "initialize":
            return await self._handle_initialize(request.id, params)
        elif method == "list_tools":
            return await self._handle_list_tools(request.id)
        elif method == "list_resources":
            return await self._handle_list_resources(request.id)
        elif method == "list_prompts":
            return await self._handle_list_prompts(request.id)
        elif method == "call_tool":
            return await self._handle_call_tool(request.id, params)
        elif method == "read_resource":
            return await self._handle_read_resource(request.id, params)
        elif method == "get_prompt":
            return await self._handle_get_prompt(request.id, params)
        else:
            return MCPResponse(
                id=request.id,
                error={"code": -32601, "message": f"Method not found: {method}"}
            )

    async def _handle_initialize(self, request_id: Union[str, int, None], params: Dict[str, Any]) -> MCPResponse:
        """Handle MCP initialize request"""
        
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "created_at": datetime.now(),
            "client_info": params.get("clientInfo", {}),
            "capabilities": params.get("capabilities", {})
        }
        
        return MCPResponse(
            id=request_id,
            result={
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "YouTube Transcript MCP Server",
                    "version": "1.0.0",
                    "description": "MCP server for YouTube transcript fetching and summarization"
                },
                "capabilities": {
                    "tools": {"list": True, "call": True},
                    "resources": {"list": True, "read": True},
                    "prompts": {"list": True, "get": True}
                },
                "sessionId": session_id
            }
        )

    async def _handle_list_tools(self, request_id: Union[str, int, None]) -> MCPResponse:
        """Handle list_tools request"""
        
        tools_list = [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            }
            for tool in self.tools.values()
        ]
        
        return MCPResponse(
            id=request_id,
            result={"tools": tools_list}
        )

    async def _handle_list_resources(self, request_id: Union[str, int, None]) -> MCPResponse:
        """Handle list_resources request"""
        
        resources_list = [
            {
                "name": resource.name,
                "description": resource.description, 
                "uri": resource.uri,
                "mimeType": resource.mimeType
            }
            for resource in self.resources.values()
        ]
        
        return MCPResponse(
            id=request_id,
            result={"resources": resources_list}
        )

    async def _handle_list_prompts(self, request_id: Union[str, int, None]) -> MCPResponse:
        """Handle list_prompts request"""
        
        prompts_list = [
            {
                "name": prompt.name,
                "description": prompt.description,
                "arguments": prompt.arguments or []
            }
            for prompt in self.prompts.values()
        ]
        
        return MCPResponse(
            id=request_id,
            result={"prompts": prompts_list}
        )

    async def _handle_call_tool(self, request_id: Union[str, int, None], params: Dict[str, Any]) -> MCPResponse:
        """Handle call_tool request"""
        
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            return MCPResponse(
                id=request_id,
                error={"code": -32602, "message": f"Tool not found: {tool_name}"}
            )
        
        try:
            if tool_name == "fetch_youtube_transcript":
                result = await self._fetch_youtube_transcript(arguments)
            elif tool_name == "summarize_transcript":
                result = await self._summarize_transcript(arguments)
            elif tool_name == "process_youtube_video":
                result = await self._process_youtube_video(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            return MCPResponse(
                id=request_id,
                result={
                    "toolResult": {
                        "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                        "isError": False
                    }
                }
            )
            
        except Exception as e:
            return MCPResponse(
                id=request_id,
                result={
                    "toolResult": {
                        "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                        "isError": True
                    }
                }
            )

    async def _fetch_youtube_transcript(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch YouTube transcript and metadata"""
        
        video_id = args.get("video_id")
        language = args.get("language", "en")
        
        if not video_id:
            raise ValueError("video_id is required")
        
        # Fetch metadata
        metadata = {}
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            video = pafy.new(video_url)
            metadata = {
                "title": video.title,
                "author": video.author,
                "duration": video.duration,
                "views": video.viewcount,
                "description": video.description,
                "url": video_url
            }
        except Exception as e:
            metadata = {"error": f"Failed to fetch metadata: {str(e)}"}
        
        # Fetch transcript
        transcript_text = ""
        transcript_error = None
        
        try:
            transcript_list = YouTubeTranscriptApi().list(video_id)
            transcript = transcript_list.find_transcript([language])
            fetched = transcript.fetch()
            transcript_text = "\n".join([snippet['text'] for snippet in fetched])
        except (NoTranscriptFound, TranscriptsDisabled) as e:
            transcript_error = f"No transcript found: {str(e)}"
        except Exception as e:
            transcript_error = f"Error fetching transcript: {str(e)}"
        
        return {
            "video_id": video_id,
            "language": language,
            "metadata": metadata,
            "transcript": transcript_text,
            "transcript_error": transcript_error,
            "success": transcript_error is None
        }

    async def _summarize_transcript(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize transcript using OpenAI"""
        
        transcript = args.get("transcript")
        video_id = args.get("video_id")
        max_tokens = args.get("max_tokens", 3000)
        
        if not transcript:
            raise ValueError("transcript is required")
        if not video_id:
            raise ValueError("video_id is required")
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are a helpful assistant skilled at summarizing YouTube transcripts. "
                            f"Summarize the provided transcript in markdown format as detailed as possible, "
                            f"using relevant emojis to enhance readability. "
                            f"Start with a clear, engaging title that incorporates the video ID ({video_id}). "
                            f"Structure the summary with appropriate headings, bullet points, or numbered lists. "
                            f"Do NOT include any explanations or comments before or after the summary; "
                            f"only output the summary itself. Summarize in the language of the transcript."
                        )
                    },
                    {
                        "role": "user", 
                        "content": transcript
                    }
                ],
                max_tokens=max_tokens
            )
            
            summary = response.choices[0].message.content
            
            return {
                "video_id": video_id,
                "summary": summary,
                "tokens_used": response.usage.total_tokens if response.usage else None,
                "model": "gpt-4-turbo-preview",
                "success": True
            }
            
        except Exception as e:
            return {
                "video_id": video_id,
                "error": str(e),
                "success": False
            }

    async def _process_youtube_video(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Process YouTube video: fetch transcript and generate summary"""
        
        video_id = args.get("video_id")
        language = args.get("language", "en")
        max_tokens = args.get("max_tokens", 3000)
        
        # First fetch transcript
        transcript_result = await self._fetch_youtube_transcript({
            "video_id": video_id,
            "language": language
        })
        
        if not transcript_result["success"]:
            return {
                "video_id": video_id,
                "transcript_result": transcript_result,
                "summary_result": {"error": "Cannot summarize without transcript", "success": False},
                "overall_success": False
            }
        
        # Then summarize 
        summary_result = await self._summarize_transcript({
            "transcript": transcript_result["transcript"],
            "video_id": video_id,
            "max_tokens": max_tokens
        })
        
        return {
            "video_id": video_id,
            "transcript_result": transcript_result,
            "summary_result": summary_result,
            "overall_success": transcript_result["success"] and summary_result["success"]
        }

    async def _handle_read_resource(self, request_id: Union[str, int, None], params: Dict[str, Any]) -> MCPResponse:
        """Handle read_resource request"""
        
        uri = params.get("uri")
        if not uri:
            return MCPResponse(
                id=request_id,
                error={"code": -32602, "message": "uri parameter is required"}
            )
        
        # Parse URI to extract resource type and video_id
        # Expected format: youtube://transcript/{video_id}, youtube://metadata/{video_id}, etc.
        
        try:
            if uri.startswith("youtube://transcript/"):
                video_id = uri.split("/")[-1]
                result = await self._fetch_youtube_transcript({"video_id": video_id})
                content = result["transcript"] if result["success"] else f"Error: {result['transcript_error']}"
                
            elif uri.startswith("youtube://metadata/"):
                video_id = uri.split("/")[-1]
                result = await self._fetch_youtube_transcript({"video_id": video_id})
                content = json.dumps(result["metadata"], indent=2)
                
            elif uri.startswith("youtube://summary/"):
                # This would require storing summaries, for now return error
                return MCPResponse(
                    id=request_id,
                    error={"code": -32602, "message": "Summary resource requires prior generation via tools"}
                )
            else:
                return MCPResponse(
                    id=request_id,
                    error={"code": -32602, "message": f"Unknown resource URI: {uri}"}
                )
            
            return MCPResponse(
                id=request_id,
                result={
                    "resource": {
                        "uri": uri,
                        "mimeType": "text/plain",
                        "text": content
                    }
                }
            )
            
        except Exception as e:
            return MCPResponse(
                id=request_id,
                error={"code": -32603, "message": f"Error reading resource: {str(e)}"}
            )

    async def _handle_get_prompt(self, request_id: Union[str, int, None], params: Dict[str, Any]) -> MCPResponse:
        """Handle get_prompt request"""
        
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if name == "youtube_summary":
            video_id = arguments.get("video_id")
            style = arguments.get("style", "detailed")
            
            if not video_id:
                return MCPResponse(
                    id=request_id,
                    error={"code": -32602, "message": "video_id argument is required for youtube_summary prompt"}
                )
            
            style_instructions = {
                "detailed": "Create a comprehensive, detailed summary with sections, timestamps, and key insights.",
                "brief": "Create a concise summary highlighting only the most important points.",
                "technical": "Focus on technical concepts, code examples, and implementation details."
            }.get(style, "Create a detailed summary.")
            
            prompt_text = f"""You are summarizing a YouTube video with ID: {video_id}

{style_instructions}

Please structure your response in markdown format with:
- Clear title including the video ID
- Overview section
- Key points and highlights with emojis
- Relevant timestamps if available
- Final thoughts

Summarize in the same language as the transcript."""
            
            return MCPResponse(
                id=request_id,
                result={
                    "prompt": {
                        "name": name,
                        "description": "Prompt for YouTube video summarization",
                        "messages": [
                            {
                                "role": "system",
                                "content": {
                                    "type": "text",
                                    "text": prompt_text
                                }
                            }
                        ]
                    }
                }
            )
        else:
            return MCPResponse(
                id=request_id,
                error={"code": -32602, "message": f"Unknown prompt: {name}"}
            )

def main():
    """Main entry point"""
    server = MCPServer()
    
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"🚀 Starting YouTube Transcript MCP Server on {host}:{port}")
    print("📋 Available tools: fetch_youtube_transcript, summarize_transcript, process_youtube_video")
    print("📚 Available resources: youtube_transcript, youtube_metadata, video_summary")
    print("🔧 Make sure to set OPENAI_API_KEY environment variable for summarization")
    
    uvicorn.run(
        server.app,
        host=host,
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main()