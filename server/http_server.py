#!/usr/bin/env python3
"""
HTTP server for MCP accounting practice
Direct HTTP implementation without subprocess wrapper
"""

import asyncio
import json
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the MCP server components
from server.tools.client_mgmt.client_tools import ClientManagementTools
from server.tools.bookkeeping.bookkeeping_tools import BookkeepingTools
from server.tools.tax.tax_tools import TaxTools
from server.tools.payroll.payroll_tools import PayrollTools
from server.tools.sales_tax.sales_tax_tools import SalesTaxTools
from server.tools.integrations.integration_tools import IntegrationTools

# Initialize tool modules
client_mgmt = ClientManagementTools()
bookkeeping = BookkeepingTools()
tax = TaxTools()
payroll = PayrollTools()
sales_tax = SalesTaxTools()
integrations = IntegrationTools()

# Health check endpoint
async def health(request):
    """Health check endpoint for Smithery"""
    return JSONResponse({
        "status": "healthy",
        "service": "accounting-practice-mcp",
        "version": "1.0.0"
    })

# MCP endpoint handler
async def mcp_endpoint(request):
    """
    MCP protocol endpoint
    """
    try:
        # Parse the JSON-RPC request
        body = await request.json()
        
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id", 0)
        
        # Handle initialize
        if method == "initialize":
            result = {
                "protocolVersion": "2025-06-18",
                "capabilities": {
                    "logging": {},
                    "tools": {}
                },
                "serverInfo": {
                    "name": "accounting-practice-mcp",
                    "version": "1.0.0"
                }
            }
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            })
        
        # Handle tools/list
        elif method == "tools/list":
            tools = [
                {"name": "get_client_info", "description": "Retrieve comprehensive client information", "inputSchema": {"type": "object", "properties": {"client_id": {"type": "string"}}, "required": ["client_id"]}},
                {"name": "update_client_profile", "description": "Update client profile information", "inputSchema": {"type": "object", "properties": {"client_id": {"type": "string"}, "updates": {"type": "object"}}, "required": ["client_id", "updates"]}},
                {"name": "get_client_deadlines", "description": "Get upcoming tax and compliance deadlines", "inputSchema": {"type": "object", "properties": {"client_id": {"type": "string"}}, "required": ["client_id"]}},
                {"name": "process_bank_statement", "description": "Import and categorize bank statement transactions", "inputSchema": {"type": "object", "properties": {"client_id": {"type": "string"}, "file_path": {"type": "string"}}, "required": ["client_id", "file_path"]}},
                {"name": "reconcile_accounts", "description": "Perform automated bank reconciliation", "inputSchema": {"type": "object", "properties": {"client_id": {"type": "string"}, "account": {"type": "string"}, "period": {"type": "string"}}, "required": ["client_id", "account", "period"]}},
                {"name": "calculate_tax_liability", "description": "Calculate estimated tax liability", "inputSchema": {"type": "object", "properties": {"client_id": {"type": "string"}, "tax_year": {"type": "integer"}}, "required": ["client_id", "tax_year"]}},
                {"name": "optimize_deductions", "description": "Analyze and optimize business deductions", "inputSchema": {"type": "object", "properties": {"client_id": {"type": "string"}, "tax_year": {"type": "integer"}}, "required": ["client_id", "tax_year"]}},
                {"name": "calculate_payroll", "description": "Process payroll calculations", "inputSchema": {"type": "object", "properties": {"client_id": {"type": "string"}, "pay_period": {"type": "string"}, "employee_data": {"type": "array"}}, "required": ["client_id", "pay_period", "employee_data"]}},
                {"name": "sales_tax_calculation", "description": "Calculate sales tax by jurisdiction", "inputSchema": {"type": "object", "properties": {"client_id": {"type": "string"}, "period": {"type": "string"}, "transactions": {"type": "array"}}, "required": ["client_id", "period", "transactions"]}},
                {"name": "quickbooks_sync", "description": "Synchronize data with QuickBooks", "inputSchema": {"type": "object", "properties": {"client_id": {"type": "string"}, "sync_type": {"type": "string"}, "data_types": {"type": "array"}}, "required": ["client_id", "sync_type", "data_types"]}}
            ]
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools}
            })
        
        # Handle tools/call
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # Call the appropriate tool
            if tool_name == "get_client_info":
                result = await client_mgmt.get_client_info(arguments["client_id"])
            elif tool_name == "update_client_profile":
                result = await client_mgmt.update_client_profile(arguments["client_id"], arguments["updates"])
            elif tool_name == "get_client_deadlines":
                result = await client_mgmt.get_client_deadlines(arguments["client_id"], arguments.get("days_ahead", 90))
            elif tool_name == "process_bank_statement":
                result = await bookkeeping.process_bank_statement(arguments["client_id"], arguments["file_path"], arguments.get("account_type", "checking"))
            elif tool_name == "reconcile_accounts":
                result = await bookkeeping.reconcile_accounts(arguments["client_id"], arguments["account"], arguments["period"])
            elif tool_name == "calculate_tax_liability":
                result = await tax.calculate_tax_liability(arguments["client_id"], arguments["tax_year"], arguments.get("projection_method", "ytd_annualized"))
            elif tool_name == "optimize_deductions":
                result = await tax.optimize_deductions(arguments["client_id"], arguments["tax_year"], arguments.get("expense_data", {}))
            elif tool_name == "calculate_payroll":
                result = await payroll.calculate_payroll(arguments["client_id"], arguments["pay_period"], arguments["employee_data"])
            elif tool_name == "sales_tax_calculation":
                result = await sales_tax.calculate_sales_tax(arguments["client_id"], arguments["period"], arguments["transactions"])
            elif tool_name == "quickbooks_sync":
                result = await integrations.quickbooks_sync(arguments["client_id"], arguments["sync_type"], arguments["data_types"])
            else:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                })
            
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
            })
        
        # Unknown method
        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            })
        
    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": 0,
            "error": {"code": -32603, "message": str(e)}
        }, status_code=500)

# Root endpoint
async def root(request):
    """Root endpoint"""
    return JSONResponse({
        "service": "accounting-practice-mcp",
        "version": "1.0.0",
        "status": "running",
        "protocol": "MCP HTTP",
        "endpoints": {
            "/": "Service info",
            "/health": "Health check",
            "/mcp": "MCP protocol endpoint (POST)"
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    # Run the HTTP server
    # Use PORT environment variable if set (for deployment platforms like Smithery)
    import os
    port = int(os.environ.get("PORT", 8080))
    
    print(f"🚀 Starting MCP Accounting Server on port {port}")
    print(f"📡 Health check: http://0.0.0.0:{port}/health")
    print(f"🔧 MCP endpoint: http://0.0.0.0:{port}/mcp")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
