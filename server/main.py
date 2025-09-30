#!/usr/bin/env python3
"""
Accounting Practice MCP Server
A custom MCP server for accounting, bookkeeping, tax planning, and compliance automation.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# Import our custom tools
from tools.client_mgmt.client_tools import ClientManagementTools
from tools.bookkeeping.bookkeeping_tools import BookkeepingTools
from tools.tax.tax_tools import TaxTools
from tools.payroll.payroll_tools import PayrollTools
from tools.sales_tax.sales_tax_tools import SalesTaxTools
from tools.integrations.integration_tools import IntegrationTools

class AccountingMCPServer:
    def __init__(self):
        self.server = Server("accounting-practice-mcp")
        self.client_mgmt = ClientManagementTools()
        self.bookkeeping = BookkeepingTools()
        self.tax = TaxTools()
        self.payroll = PayrollTools()
        self.sales_tax = SalesTaxTools()
        self.integrations = IntegrationTools()
        
        # Register all tools
        self._register_tools()
        
    def _register_tools(self):
        """Register all accounting tools with the MCP server"""
        
        # Client Management Tools
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return [
                Tool(
                    name="get_client_info",
                    description="Retrieve comprehensive client information including entity type, tax elections, and contact details",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "client_id": {"type": "string", "description": "Unique client identifier"}
                        },
                        "required": ["client_id"]
                    }
                ),
                Tool(
                    name="update_client_profile",
                    description="Update client profile information and preferences",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "client_id": {"type": "string", "description": "Unique client identifier"},
                            "updates": {"type": "object", "description": "Client data updates"}
                        },
                        "required": ["client_id", "updates"]
                    }
                ),
                Tool(
                    name="get_client_deadlines",
                    description="Get upcoming tax and compliance deadlines for a client",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "client_id": {"type": "string", "description": "Unique client identifier"},
                            "days_ahead": {"type": "integer", "description": "Number of days to look ahead", "default": 90}
                        },
                        "required": ["client_id"]
                    }
                ),
                Tool(
                    name="process_bank_statement",
                    description="Import and automatically categorize bank statement transactions",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "client_id": {"type": "string", "description": "Unique client identifier"},
                            "file_path": {"type": "string", "description": "Path to bank statement file"},
                            "account_type": {"type": "string", "description": "Type of account (checking, savings, credit)"}
                        },
                        "required": ["client_id", "file_path"]
                    }
                ),
                Tool(
                    name="reconcile_accounts",
                    description="Perform automated bank reconciliation with exception reporting",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "client_id": {"type": "string", "description": "Unique client identifier"},
                            "account": {"type": "string", "description": "Account to reconcile"},
                            "period": {"type": "string", "description": "Period to reconcile (YYYY-MM)"}
                        },
                        "required": ["client_id", "account", "period"]
                    }
                ),
                Tool(
                    name="calculate_tax_liability",
                    description="Calculate estimated tax liability for current year",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "client_id": {"type": "string", "description": "Unique client identifier"},
                            "tax_year": {"type": "integer", "description": "Tax year for calculation"},
                            "projection_method": {"type": "string", "description": "Projection method (ytd_annualized, budget, prior_year)", "default": "ytd_annualized"}
                        },
                        "required": ["client_id", "tax_year"]
                    }
                ),
                Tool(
                    name="optimize_deductions",
                    description="Analyze expenses and recommend optimal deduction strategies",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "client_id": {"type": "string", "description": "Unique client identifier"},
                            "tax_year": {"type": "integer", "description": "Tax year for optimization"},
                            "expense_data": {"type": "object", "description": "Expense data to analyze"}
                        },
                        "required": ["client_id", "tax_year"]
                    }
                ),
                Tool(
                    name="calculate_payroll",
                    description="Process payroll calculations including taxes and deductions",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "client_id": {"type": "string", "description": "Unique client identifier"},
                            "pay_period": {"type": "string", "description": "Pay period (YYYY-MM-DD to YYYY-MM-DD)"},
                            "employee_data": {"type": "array", "description": "Employee payroll data"}
                        },
                        "required": ["client_id", "pay_period", "employee_data"]
                    }
                ),
                Tool(
                    name="sales_tax_calculation",
                    description="Calculate sales tax liability by jurisdiction",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "client_id": {"type": "string", "description": "Unique client identifier"},
                            "period": {"type": "string", "description": "Period for calculation (YYYY-MM)"},
                            "transactions": {"type": "array", "description": "Sales transactions data"}
                        },
                        "required": ["client_id", "period", "transactions"]
                    }
                ),
                Tool(
                    name="quickbooks_sync",
                    description="Synchronize data with QuickBooks Online or Desktop",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "client_id": {"type": "string", "description": "Unique client identifier"},
                            "sync_type": {"type": "string", "description": "Type of sync (import, export, bidirectional)"},
                            "data_types": {"type": "array", "description": "Data types to sync (customers, vendors, items, transactions)"}
                        },
                        "required": ["client_id", "sync_type", "data_types"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls and route to appropriate handlers"""
            
            try:
                if name == "get_client_info":
                    result = await self.client_mgmt.get_client_info(arguments["client_id"])
                elif name == "update_client_profile":
                    result = await self.client_mgmt.update_client_profile(
                        arguments["client_id"], arguments["updates"]
                    )
                elif name == "get_client_deadlines":
                    result = await self.client_mgmt.get_client_deadlines(
                        arguments["client_id"], arguments.get("days_ahead", 90)
                    )
                elif name == "process_bank_statement":
                    result = await self.bookkeeping.process_bank_statement(
                        arguments["client_id"], 
                        arguments["file_path"],
                        arguments.get("account_type", "checking")
                    )
                elif name == "reconcile_accounts":
                    result = await self.bookkeeping.reconcile_accounts(
                        arguments["client_id"],
                        arguments["account"],
                        arguments["period"]
                    )
                elif name == "calculate_tax_liability":
                    result = await self.tax.calculate_tax_liability(
                        arguments["client_id"],
                        arguments["tax_year"],
                        arguments.get("projection_method", "ytd_annualized")
                    )
                elif name == "optimize_deductions":
                    result = await self.tax.optimize_deductions(
                        arguments["client_id"],
                        arguments["tax_year"],
                        arguments.get("expense_data", {})
                    )
                elif name == "calculate_payroll":
                    result = await self.payroll.calculate_payroll(
                        arguments["client_id"],
                        arguments["pay_period"],
                        arguments["employee_data"]
                    )
                elif name == "sales_tax_calculation":
                    result = await self.sales_tax.calculate_sales_tax(
                        arguments["client_id"],
                        arguments["period"],
                        arguments["transactions"]
                    )
                elif name == "quickbooks_sync":
                    result = await self.integrations.quickbooks_sync(
                        arguments["client_id"],
                        arguments["sync_type"],
                        arguments["data_types"]
                    )
                else:
                    result = {"error": f"Unknown tool: {name}"}
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                error_result = {"error": str(e), "tool": name, "arguments": arguments}
                return [TextContent(type="text", text=json.dumps(error_result, indent=2))]

async def main():
    """Main entry point for the MCP server"""
    server_instance = AccountingMCPServer()
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="accounting-practice-mcp",
                server_version="1.0.0",
                capabilities={
                    "tools": {},
                    "logging": {}
                }
            )
        )

if __name__ == "__main__":
    asyncio.run(main())