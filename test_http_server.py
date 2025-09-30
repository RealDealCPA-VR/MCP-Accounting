#!/usr/bin/env python3
"""
Test the HTTP MCP server directly
"""

import requests
import json

# Server URL (change to your Smithery deployment URL when deployed)
SERVER_URL = "http://localhost:8080/mcp"

def test_initialize():
    """Test initialize method"""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    
    response = requests.post(SERVER_URL, json=request)
    print("Initialize Response:")
    print(json.dumps(response.json(), indent=2))
    print()

def test_list_tools():
    """Test tools/list method"""
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response = requests.post(SERVER_URL, json=request)
    print("Tools List Response:")
    print(json.dumps(response.json(), indent=2))
    print()

def test_get_client_info():
    """Test calling get_client_info tool"""
    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "get_client_info",
            "arguments": {
                "client_id": "TEST001"
            }
        }
    }
    
    response = requests.post(SERVER_URL, json=request)
    print("Get Client Info Response:")
    print(json.dumps(response.json(), indent=2))
    print()

if __name__ == "__main__":
    print("Testing MCP HTTP Server...")
    print("=" * 50)
    print()
    
    try:
        test_initialize()
        test_list_tools()
        test_get_client_info()
        print("✅ All tests completed!")
    except Exception as e:
        print(f"❌ Error: {e}")
