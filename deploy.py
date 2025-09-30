#!/usr/bin/env python3
"""
Deployment script for Accounting Practice MCP Server
Handles initialization and health checks for Smithery deployment
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add the server directory to the path
sys.path.append('server')

def check_health() -> Dict[str, Any]:
    """Health check endpoint for deployment monitoring"""
    try:
        # Check if required directories exist
        required_dirs = [
            'server/data/client_profiles',
            'server/data/tax_tables',
            'server/tools'
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_path)
        
        # Check if required files exist
        required_files = [
            'server/main.py',
            'requirements.txt',
            'smithery.yaml'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        health_status = {
            "status": "healthy" if not missing_dirs and not missing_files else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "service": "accounting-practice-mcp",
            "checks": {
                "directories": {
                    "status": "ok" if not missing_dirs else "error",
                    "missing": missing_dirs
                },
                "files": {
                    "status": "ok" if not missing_files else "error", 
                    "missing": missing_files
                }
            }
        }
        
        return health_status
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

def initialize_directories():
    """Initialize required directories for deployment"""
    directories = [
        'server/data/client_profiles',
        'server/data/tax_tables'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def main():
    """Main deployment initialization"""
    print("🚀 Initializing Accounting Practice MCP Server for Smithery deployment...")
    
    # Initialize directories
    initialize_directories()
    
    # Run health check
    health = check_health()
    print(f"📊 Health Status: {health['status']}")
    
    if health['status'] == 'healthy':
        print("✅ Server is ready for deployment!")
        return 0
    else:
        print("❌ Server health check failed:")
        print(json.dumps(health, indent=2))
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
