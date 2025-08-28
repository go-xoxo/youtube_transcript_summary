#!/usr/bin/env python3
"""
MCP Client for YouTube Transcript Summarizer

This is a simple client that demonstrates how to interact with the
MCP server for YouTube transcript processing.
"""

import json
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from pydantic import BaseModel

class MCPClient:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.mcp_endpoint = f"{server_url}/mcp"
        self.session_id: Optional[str] = None
        self.request_id = 0

    def _get_next_id(self) -> int:
        """Get next request ID"""
        self.request_id += 1
        return self.request_id

    async def _make_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an MCP JSON-RPC request"""
        request_data = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": method,
            "params": params or {}
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.mcp_endpoint,
                json=request_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {await response.text()}")
                
                result = await response.json()
                
                if "error" in result and result["error"] is not None:
                    raise Exception(f"MCP Error: {result['error']}")
                
                return result.get("result", {})

    async def initialize(self) -> Dict[str, Any]:
        """Initialize MCP session"""
        result = await self._make_request("initialize", {
            "protocolVersion": "2024-11-05",
            "clientInfo": {
                "name": "YouTube Transcript MCP Client",
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": {"call": True},
                "resources": {"read": True},
                "prompts": {"get": True}
            }
        })
        
        self.session_id = result.get("sessionId")
        return result

    async def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        return await self._make_request("list_tools")

    async def list_resources(self) -> Dict[str, Any]:
        """List available resources"""
        return await self._make_request("list_resources")

    async def list_prompts(self) -> Dict[str, Any]:
        """List available prompts"""
        return await self._make_request("list_prompts")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool"""
        return await self._make_request("call_tool", {
            "name": tool_name,
            "arguments": arguments
        })

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource"""
        return await self._make_request("read_resource", {
            "uri": uri
        })

    async def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get a prompt"""
        return await self._make_request("get_prompt", {
            "name": name,
            "arguments": arguments or {}
        })

    async def fetch_youtube_transcript(self, video_id: str, language: str = "en") -> Dict[str, Any]:
        """High-level method to fetch YouTube transcript"""
        result = await self.call_tool("fetch_youtube_transcript", {
            "video_id": video_id,
            "language": language
        })
        
        # Parse the JSON content from tool result
        content = result["toolResult"]["content"][0]["text"]
        return json.loads(content)

    async def summarize_transcript(self, transcript: str, video_id: str, max_tokens: int = 3000) -> Dict[str, Any]:
        """High-level method to summarize transcript"""
        result = await self.call_tool("summarize_transcript", {
            "transcript": transcript,
            "video_id": video_id,
            "max_tokens": max_tokens
        })
        
        # Parse the JSON content from tool result
        content = result["toolResult"]["content"][0]["text"]
        return json.loads(content)

    async def process_youtube_video(self, video_id: str, language: str = "en", max_tokens: int = 3000) -> Dict[str, Any]:
        """High-level method to process YouTube video end-to-end"""
        result = await self.call_tool("process_youtube_video", {
            "video_id": video_id,
            "language": language,
            "max_tokens": max_tokens
        })
        
        # Parse the JSON content from tool result
        content = result["toolResult"]["content"][0]["text"]
        return json.loads(content)

async def demo_mcp_client():
    """Demonstrate MCP client functionality"""
    
    client = MCPClient()
    
    try:
        print("🚀 Initializing MCP connection...")
        init_result = await client.initialize()
        print(f"✅ Connected! Session ID: {client.session_id}")
        print(f"📄 Server: {init_result['serverInfo']['name']} v{init_result['serverInfo']['version']}")
        
        print("\n📋 Listing available tools...")
        tools = await client.list_tools()
        for tool in tools["tools"]:
            print(f"  🔧 {tool['name']}: {tool['description']}")
        
        print("\n📚 Listing available resources...")
        resources = await client.list_resources()
        for resource in resources["resources"]:
            print(f"  📦 {resource['name']}: {resource['description']}")
        
        print("\n🔧 Listing available prompts...")
        prompts = await client.list_prompts()
        for prompt in prompts["prompts"]:
            print(f"  💬 {prompt['name']}: {prompt['description']}")
        
        # Example video ID for demonstration (a short video)
        demo_video_id = "dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
        
        print(f"\n🎬 Testing with video ID: {demo_video_id}")
        
        print("\n📥 Fetching transcript...")
        transcript_result = await client.fetch_youtube_transcript(demo_video_id)
        
        if transcript_result["success"]:
            print(f"✅ Successfully fetched transcript!")
            print(f"📹 Title: {transcript_result['metadata'].get('title', 'N/A')}")
            print(f"👤 Author: {transcript_result['metadata'].get('author', 'N/A')}")
            print(f"⏱️ Duration: {transcript_result['metadata'].get('duration', 'N/A')}")
            print(f"📝 Transcript length: {len(transcript_result['transcript'])} characters")
            
            if transcript_result["transcript"]:
                print("\n📝 Generating summary...")
                summary_result = await client.summarize_transcript(
                    transcript_result["transcript"],
                    demo_video_id
                )
                
                if summary_result["success"]:
                    print("✅ Summary generated!")
                    print(f"🤖 Model: {summary_result['model']}")
                    print(f"🔢 Tokens used: {summary_result['tokens_used']}")
                    print("\n📄 Summary:")
                    print("=" * 50)
                    print(summary_result["summary"])
                    print("=" * 50)
                else:
                    print(f"❌ Summary failed: {summary_result['error']}")
            else:
                print("⚠️ No transcript text available for summary")
        else:
            print(f"❌ Failed to fetch transcript: {transcript_result['transcript_error']}")
        
        print("\n🔍 Testing resource access...")
        try:
            transcript_resource = await client.read_resource(f"youtube://transcript/{demo_video_id}")
            print(f"✅ Read transcript resource: {len(transcript_resource['resource']['text'])} characters")
        except Exception as e:
            print(f"⚠️ Could not read transcript resource: {e}")
        
        try:
            metadata_resource = await client.read_resource(f"youtube://metadata/{demo_video_id}")
            print(f"✅ Read metadata resource: {len(metadata_resource['resource']['text'])} characters")
        except Exception as e:
            print(f"⚠️ Could not read metadata resource: {e}")
        
        print("\n💬 Testing prompt generation...")
        try:
            prompt_result = await client.get_prompt("youtube_summary", {
                "video_id": demo_video_id,
                "style": "detailed"
            })
            prompt_text = prompt_result["prompt"]["messages"][0]["content"]["text"]
            print(f"✅ Generated prompt: {len(prompt_text)} characters")
            print(f"📝 Prompt preview: {prompt_text[:200]}...")
        except Exception as e:
            print(f"⚠️ Could not get prompt: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

async def interactive_mode():
    """Interactive mode for testing specific video IDs"""
    
    client = MCPClient()
    
    try:
        await client.initialize()
        print("🚀 MCP Client initialized!")
        
        while True:
            print("\n" + "="*50)
            print("YouTube Transcript MCP Client - Interactive Mode")
            print("="*50)
            print("1. Fetch transcript only")
            print("2. Process video (fetch + summarize)")
            print("3. List available tools")
            print("4. Exit")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                video_id = input("Enter YouTube video ID: ").strip()
                if video_id:
                    print(f"\n📥 Fetching transcript for {video_id}...")
                    result = await client.fetch_youtube_transcript(video_id)
                    print(json.dumps(result, indent=2))
            
            elif choice == "2":
                video_id = input("Enter YouTube video ID: ").strip()
                if video_id:
                    print(f"\n🎬 Processing video {video_id}...")
                    result = await client.process_youtube_video(video_id)
                    if result["overall_success"]:
                        print("✅ Processing complete!")
                        if "summary" in result["summary_result"]:
                            print("\n📄 Summary:")
                            print("-" * 40)
                            print(result["summary_result"]["summary"])
                            print("-" * 40)
                    else:
                        print("❌ Processing failed:")
                        print(json.dumps(result, indent=2))
            
            elif choice == "3":
                tools = await client.list_tools()
                print("\n🔧 Available tools:")
                for tool in tools["tools"]:
                    print(f"  • {tool['name']}: {tool['description']}")
            
            elif choice == "4":
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please select 1-4.")
                
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        asyncio.run(interactive_mode())
    else:
        print("🧪 Running MCP Client Demo...")
        success = asyncio.run(demo_mcp_client())
        if success:
            print("\n✅ Demo completed successfully!")
            print("\n💡 To run in interactive mode: python mcp_client.py --interactive")
        else:
            print("\n❌ Demo failed!")
            sys.exit(1)

if __name__ == "__main__":
    main()