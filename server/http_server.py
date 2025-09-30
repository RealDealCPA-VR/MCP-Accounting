#!/usr/bin/env python3
"""
HTTP wrapper for MCP stdio server
Wraps the stdio-based MCP server to work with Smithery's HTTP requirements
"""

import asyncio
import subprocess
import sys
from starlette.applications import Starlette
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route
from sse_starlette.sse import EventSourceResponse
import uvicorn

# Health check endpoint
async def health(request):
    """Health check endpoint for Smithery"""
    return JSONResponse({
        "status": "healthy",
        "service": "accounting-practice-mcp",
        "version": "1.0.0"
    })

# MCP endpoint that wraps stdio communication
async def mcp_endpoint(request):
    """
    MCP endpoint that communicates with the stdio server
    """
    try:
        # Start the MCP server as a subprocess
        process = await asyncio.create_subprocess_exec(
            sys.executable, "server/main.py",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Read the request body
        body = await request.body()
        
        # Send to the MCP server
        process.stdin.write(body)
        await process.stdin.drain()
        process.stdin.close()
        
        # Read the response
        stdout, stderr = await process.communicate()
        
        if stderr:
            return JSONResponse(
                {"error": stderr.decode()},
                status_code=500
            )
        
        return JSONResponse(
            {"response": stdout.decode()},
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )

# Root endpoint
async def root(request):
    """Root endpoint"""
    return JSONResponse({
        "service": "accounting-practice-mcp",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "/health": "Health check",
            "/mcp": "MCP protocol endpoint"
        }
    })

# Create the Starlette app
app = Starlette(
    debug=False,
    routes=[
        Route("/", root),
        Route("/health", health),
        Route("/mcp", mcp_endpoint, methods=["POST"]),
    ]
)

if __name__ == "__main__":
    # Run the HTTP server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
