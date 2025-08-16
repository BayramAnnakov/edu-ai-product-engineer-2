#!/usr/bin/env python3
"""
YouTrack MCP Server - HTTP Transport version for Docker deployments
"""

from youtrack_server import mcp

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8002, path="/mcp/", show_banner=True)