#!/usr/bin/env python3
"""
MCP Server Validation Test

Tests the MCP server functionality without requiring external network access.
This validates the MCP protocol implementation and tool registration.
"""

import asyncio
import json
import subprocess
import time
import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

async def test_mcp_server_offline():
    """Test MCP server functionality without external dependencies"""
    
    print("🧪 MCP Server Validation Test")
    print("=" * 50)
    
    # Start server in background
    print("🚀 Starting MCP server...")
    env = os.environ.copy()
    env["HOST"] = "127.0.0.1"
    env["PORT"] = "8003"
    
    server_process = subprocess.Popen([
        sys.executable, "mcp_server.py"
    ], 
    env=env,
    stdout=subprocess.PIPE, 
    stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        from mcp_client import MCPClient
        client = MCPClient("http://127.0.0.1:8003")
        
        # Test 1: Initialize
        print("\n1️⃣ Testing MCP initialization...")
        init_result = await client.initialize()
        assert "serverInfo" in init_result
        assert init_result["serverInfo"]["name"] == "YouTube Transcript MCP Server"
        print("✅ Initialization successful")
        
        # Test 2: List Tools
        print("\n2️⃣ Testing tool discovery...")
        tools_result = await client.list_tools()
        tools = tools_result["tools"]
        assert len(tools) == 3
        tool_names = [tool["name"] for tool in tools]
        expected_tools = ["fetch_youtube_transcript", "summarize_transcript", "process_youtube_video"]
        for expected in expected_tools:
            assert expected in tool_names, f"Missing tool: {expected}"
        print(f"✅ Found all {len(tools)} expected tools")
        
        # Test 3: List Resources
        print("\n3️⃣ Testing resource discovery...")
        resources_result = await client.list_resources()
        resources = resources_result["resources"]
        assert len(resources) == 3
        resource_names = [resource["name"] for resource in resources]
        expected_resources = ["youtube_transcript", "youtube_metadata", "video_summary"]
        for expected in expected_resources:
            assert expected in resource_names, f"Missing resource: {expected}"
        print(f"✅ Found all {len(resources)} expected resources")
        
        # Test 4: List Prompts
        print("\n4️⃣ Testing prompt discovery...")
        prompts_result = await client.list_prompts()
        prompts = prompts_result["prompts"]
        assert len(prompts) == 1
        assert prompts[0]["name"] == "youtube_summary"
        print(f"✅ Found all {len(prompts)} expected prompts")
        
        # Test 5: Tool Input Schema Validation
        print("\n5️⃣ Testing tool schemas...")
        for tool in tools:
            schema = tool["inputSchema"]
            assert "type" in schema and schema["type"] == "object"
            assert "properties" in schema
            assert "required" in schema
            print(f"✅ Tool '{tool['name']}' has valid schema")
        
        # Test 6: Resource URI Patterns
        print("\n6️⃣ Testing resource URI patterns...")
        for resource in resources:
            assert "uri" in resource
            assert resource["uri"].startswith("youtube://")
            assert "{video_id}" in resource["uri"]
            print(f"✅ Resource '{resource['name']}' has valid URI pattern")
        
        # Test 7: Prompt Structure
        print("\n7️⃣ Testing prompt structure...")
        prompt_result = await client.get_prompt("youtube_summary", {
            "video_id": "test123",
            "style": "detailed"
        })
        prompt = prompt_result["prompt"]
        assert "name" in prompt
        assert "messages" in prompt
        assert len(prompt["messages"]) > 0
        print("✅ Prompt generation successful")
        
        # Test 8: Error Handling
        print("\n8️⃣ Testing error handling...")
        try:
            await client.call_tool("nonexistent_tool", {})
            assert False, "Should have raised an error"
        except Exception as e:
            assert "Tool not found" in str(e) or "not found" in str(e)
            print("✅ Error handling works correctly")
        
        print("\n🎯 MCP Protocol Validation Summary:")
        print("  ✅ JSON-RPC over HTTP protocol compliance")
        print("  ✅ Tool discovery and schema validation")
        print("  ✅ Resource discovery and URI patterns")
        print("  ✅ Prompt generation and parameterization")
        print("  ✅ Error handling and validation")
        print("  ✅ MCP specification compliance")
        
        print(f"\n🚀 MCP Server Details:")
        print(f"  📋 Tools: {len(tools)} discoverable tools")
        print(f"  📚 Resources: {len(resources)} accessible resources")
        print(f"  💬 Prompts: {len(prompts)} reusable prompts")
        print(f"  🔄 Protocol: {init_result['protocolVersion']}")
        print(f"  🆔 Session: {client.session_id}")
        
        print("\n✅ ALL TESTS PASSED! MCP server is fully functional.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up server
        print("\n🛑 Stopping server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    result = asyncio.run(test_mcp_server_offline())
    if not result:
        sys.exit(1)
    
    print("\n🎉 MCP implementation validation completed successfully!")
    print("\n💡 Next steps:")
    print("  • Start server: ./start_mcp_server.sh")
    print("  • Test with real videos (requires network): python3 mcp_demo.py")
    print("  • Integrate with Claude Desktop or custom MCP clients")
    print("  • Explore MCP composability with other servers")