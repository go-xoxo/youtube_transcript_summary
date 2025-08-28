#!/usr/bin/env python3
"""
Complete MCP Integration Demo

This script demonstrates the full Model Context Protocol implementation
for YouTube transcript processing, showing "MCP First" approach.
"""

import asyncio
import json
import sys
import signal
import time
from pathlib import Path
from typing import Optional

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp_client import MCPClient

class MCPDemo:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.client = MCPClient(server_url)
        self.running = True
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n🛑 Shutting down MCP demo...")
        self.running = False

    async def demonstrate_mcp_protocol(self):
        """Demonstrate complete MCP protocol workflow"""
        
        print("🚀 MCP Protocol Demonstration")
        print("=" * 50)
        
        try:
            # 1. Initialize MCP Connection
            print("\n1️⃣ INITIALIZE MCP CONNECTION")
            print("-" * 30)
            result = await self.client.initialize()
            print(f"✅ Connected to: {result['serverInfo']['name']}")
            print(f"📝 Description: {result['serverInfo']['description']}")
            print(f"🔄 Protocol Version: {result['protocolVersion']}")
            print(f"🆔 Session ID: {self.client.session_id}")
            
            # 2. Discover Available Tools
            print("\n2️⃣ DISCOVER AVAILABLE TOOLS")
            print("-" * 30)
            tools_result = await self.client.list_tools()
            tools = tools_result["tools"]
            print(f"📋 Found {len(tools)} discoverable tools:")
            for i, tool in enumerate(tools, 1):
                print(f"  {i}. {tool['name']}")
                print(f"     📝 {tool['description']}")
                print(f"     🔧 Schema: {json.dumps(tool['inputSchema']['properties'], indent=6)}")
                print()
            
            # 3. Discover Available Resources
            print("\n3️⃣ DISCOVER AVAILABLE RESOURCES")
            print("-" * 30)
            resources_result = await self.client.list_resources()
            resources = resources_result["resources"]
            print(f"📚 Found {len(resources)} accessible resources:")
            for i, resource in enumerate(resources, 1):
                print(f"  {i}. {resource['name']}")
                print(f"     📝 {resource['description']}")
                print(f"     🔗 URI Pattern: {resource['uri']}")
                print(f"     📄 MIME Type: {resource['mimeType']}")
                print()
            
            # 4. Discover Available Prompts
            print("\n4️⃣ DISCOVER AVAILABLE PROMPTS")
            print("-" * 30)
            prompts_result = await self.client.list_prompts()
            prompts = prompts_result["prompts"]
            print(f"💬 Found {len(prompts)} reusable prompts:")
            for i, prompt in enumerate(prompts, 1):
                print(f"  {i}. {prompt['name']}")
                print(f"     📝 {prompt['description']}")
                if prompt.get('arguments'):
                    print(f"     ⚙️  Arguments: {json.dumps(prompt['arguments'], indent=6)}")
                print()
            
            # 5. Demonstrate Tool Usage
            print("\n5️⃣ DEMONSTRATE TOOL USAGE")
            print("-" * 30)
            
            # Use a short, public video for demo
            demo_video_id = "dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up (classic!)
            print(f"🎬 Demo Video ID: {demo_video_id}")
            
            # 5.1 Fetch Transcript Tool
            print(f"\n🔧 Calling tool: fetch_youtube_transcript")
            transcript_result = await self.client.fetch_youtube_transcript(demo_video_id)
            
            if transcript_result["success"]:
                print(f"✅ Transcript fetched successfully!")
                metadata = transcript_result["metadata"]
                print(f"📹 Title: {metadata.get('title', 'N/A')}")
                print(f"👤 Author: {metadata.get('author', 'N/A')}")
                print(f"⏱️ Duration: {metadata.get('duration', 'N/A')}")
                print(f"👀 Views: {metadata.get('views', 'N/A')}")
                print(f"📝 Transcript Length: {len(transcript_result['transcript'])} characters")
                print(f"📄 Transcript Preview: {transcript_result['transcript'][:200]}...")
            else:
                print(f"❌ Transcript fetch failed: {transcript_result['transcript_error']}")
                return
            
            # 6. Demonstrate Resource Access
            print("\n6️⃣ DEMONSTRATE RESOURCE ACCESS")
            print("-" * 30)
            
            # 6.1 Access transcript resource
            transcript_uri = f"youtube://transcript/{demo_video_id}"
            print(f"📚 Reading resource: {transcript_uri}")
            transcript_resource = await self.client.read_resource(transcript_uri)
            resource_text = transcript_resource["resource"]["text"]
            print(f"✅ Resource accessed: {len(resource_text)} characters")
            print(f"📄 Resource preview: {resource_text[:150]}...")
            
            # 6.2 Access metadata resource
            metadata_uri = f"youtube://metadata/{demo_video_id}"
            print(f"\n📚 Reading resource: {metadata_uri}")
            metadata_resource = await self.client.read_resource(metadata_uri)
            metadata_text = metadata_resource["resource"]["text"]
            print(f"✅ Metadata resource accessed: {len(metadata_text)} characters")
            metadata_obj = json.loads(metadata_text)
            print(f"📊 Metadata keys: {list(metadata_obj.keys())}")
            
            # 7. Demonstrate Prompt Usage
            print("\n7️⃣ DEMONSTRATE PROMPT USAGE")
            print("-" * 30)
            
            # 7.1 Get prompt with arguments
            print(f"💬 Getting prompt: youtube_summary")
            prompt_result = await self.client.get_prompt("youtube_summary", {
                "video_id": demo_video_id,
                "style": "detailed"
            })
            
            prompt_content = prompt_result["prompt"]["messages"][0]["content"]["text"]
            print(f"✅ Prompt generated: {len(prompt_content)} characters")
            print(f"📝 Prompt preview:")
            print("   " + "\n   ".join(prompt_content.split("\n")[:5]))
            print("   ...")
            
            # 8. Demonstrate Advanced Workflow
            print("\n8️⃣ DEMONSTRATE ADVANCED WORKFLOW")
            print("-" * 30)
            
            print("🚀 Using 'process_youtube_video' tool for end-to-end processing...")
            print("⚠️  Note: This requires OPENAI_API_KEY for summarization")
            
            try:
                process_result = await self.client.process_youtube_video(demo_video_id)
                
                if process_result["overall_success"]:
                    print("✅ End-to-end processing successful!")
                    
                    summary_result = process_result["summary_result"]
                    if summary_result["success"]:
                        print(f"🤖 AI Model: {summary_result['model']}")
                        print(f"🔢 Tokens Used: {summary_result['tokens_used']}")
                        print(f"📄 Summary Length: {len(summary_result['summary'])} characters")
                        print("\n📋 GENERATED SUMMARY:")
                        print("=" * 40)
                        print(summary_result["summary"][:500] + "..." if len(summary_result["summary"]) > 500 else summary_result["summary"])
                        print("=" * 40)
                    else:
                        print(f"❌ Summary generation failed: {summary_result['error']}")
                else:
                    print("❌ End-to-end processing failed")
                    
            except Exception as e:
                print(f"⚠️  Advanced workflow skipped: {str(e)}")
                print("   (Likely missing OPENAI_API_KEY - this is expected for demo)")
            
            # 9. Summary
            print("\n9️⃣ MCP PROTOCOL SUMMARY")
            print("-" * 30)
            print("🎯 MCP Key Benefits Demonstrated:")
            print("  ✅ Discoverability - All tools/resources/prompts are queryable")
            print("  ✅ Pluggability - Tools can be added/removed without client changes")
            print("  ✅ Composability - Standard JSON-RPC protocol for integration")
            print("  ✅ Tool Schema - Input validation and documentation built-in")
            print("  ✅ Resource Access - URI-based data access patterns")
            print("  ✅ Prompt Templates - Reusable, parameterized prompts")
            
            print("\n🚀 MCP Implementation Status:")
            print("  📋 Tools: 3 discoverable tools implemented")
            print("  📚 Resources: 3 accessible resource types")
            print("  💬 Prompts: 1 parameterizable prompt template")
            print("  🔄 Protocol: Full JSON-RPC over HTTP compliance")
            print("  🔧 Integration: Ready for Claude Desktop, custom clients")
            
            print("\n✅ MCP Protocol demonstration completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during MCP demonstration: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        return True

    async def interactive_mode(self):
        """Interactive mode for hands-on MCP exploration"""
        
        print("\n🎮 MCP Interactive Mode")
        print("=" * 50)
        
        await self.client.initialize()
        print(f"✅ Connected! Session: {self.client.session_id}")
        
        while self.running:
            print("\n" + "─" * 40)
            print("🔧 MCP Tools & Resources Explorer")
            print("─" * 40)
            print("1. List all tools")
            print("2. List all resources") 
            print("3. List all prompts")
            print("4. Call fetch_youtube_transcript")
            print("5. Call process_youtube_video (requires OPENAI_API_KEY)")
            print("6. Read transcript resource")
            print("7. Read metadata resource")
            print("8. Get youtube_summary prompt")
            print("9. Run full MCP protocol demo")
            print("0. Exit")
            
            try:
                choice = input("\n🎯 Select option (0-9): ").strip()
                
                if choice == "0":
                    print("👋 Goodbye!")
                    break
                elif choice == "1":
                    tools = await self.client.list_tools()
                    print(f"\n🔧 {len(tools['tools'])} Tools Available:")
                    for tool in tools['tools']:
                        print(f"  • {tool['name']}: {tool['description']}")
                        
                elif choice == "2":
                    resources = await self.client.list_resources()
                    print(f"\n📚 {len(resources['resources'])} Resources Available:")
                    for resource in resources['resources']:
                        print(f"  • {resource['name']}: {resource['uri']}")
                        
                elif choice == "3":
                    prompts = await self.client.list_prompts()
                    print(f"\n💬 {len(prompts['prompts'])} Prompts Available:")
                    for prompt in prompts['prompts']:
                        print(f"  • {prompt['name']}: {prompt['description']}")
                        
                elif choice == "4":
                    video_id = input("📹 Enter YouTube video ID: ").strip()
                    if video_id:
                        result = await self.client.fetch_youtube_transcript(video_id)
                        print(json.dumps(result, indent=2))
                        
                elif choice == "5":
                    video_id = input("📹 Enter YouTube video ID: ").strip()
                    if video_id:
                        print("🚀 Processing video (this may take a moment)...")
                        result = await self.client.process_youtube_video(video_id)
                        print(json.dumps(result, indent=2))
                        
                elif choice == "6":
                    video_id = input("📹 Enter YouTube video ID: ").strip()
                    if video_id:
                        result = await self.client.read_resource(f"youtube://transcript/{video_id}")
                        print(f"📝 Transcript: {result['resource']['text'][:500]}...")
                        
                elif choice == "7":
                    video_id = input("📹 Enter YouTube video ID: ").strip()
                    if video_id:
                        result = await self.client.read_resource(f"youtube://metadata/{video_id}")
                        print(f"📊 Metadata: {result['resource']['text']}")
                        
                elif choice == "8":
                    video_id = input("📹 Enter YouTube video ID: ").strip()
                    style = input("🎨 Enter style (detailed/brief/technical): ").strip() or "detailed"
                    result = await self.client.get_prompt("youtube_summary", {
                        "video_id": video_id,
                        "style": style
                    })
                    print(f"💬 Prompt: {result['prompt']['messages'][0]['content']['text']}")
                    
                elif choice == "9":
                    await self.demonstrate_mcp_protocol()
                    
                else:
                    print("❌ Invalid choice. Please select 0-9.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

async def main():
    """Main entry point"""
    
    import argparse
    parser = argparse.ArgumentParser(description="MCP Protocol Demo for YouTube Transcript Tools")
    parser.add_argument("--server", default="http://localhost:8000", help="MCP server URL")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    args = parser.parse_args()
    
    demo = MCPDemo(args.server)
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, demo.signal_handler)
    
    print("🎬 YouTube Transcript MCP Protocol Demo")
    print("=" * 50)
    print(f"📡 Server: {args.server}")
    print("🔧 Protocol: Model Context Protocol (JSON-RPC over HTTP)")
    print("📋 Features: Discoverable tools, accessible resources, reusable prompts")
    
    if args.interactive:
        await demo.interactive_mode()
    else:
        print("\n🚀 Running automated MCP protocol demonstration...")
        success = await demo.demonstrate_mcp_protocol()
        
        if success:
            print("\n✅ Demo completed successfully!")
            print("\n💡 Next steps:")
            print("  • Run with --interactive for hands-on exploration")
            print("  • Set OPENAI_API_KEY for full summarization features")
            print("  • Integrate with Claude Desktop or custom MCP clients")
            print("  • Explore MCP composability with other servers")
        else:
            print("\n❌ Demo failed!")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())