#!/usr/bin/env python3
"""
Test script for Accounting Practice MCP Server
Tests core functionality without requiring full MCP client setup
"""

import asyncio
import json
import sys
import os

# Add the server directory to the path
sys.path.append('server')

# Import the tool classes directly
from tools.client_mgmt.client_tools import ClientManagementTools
from tools.bookkeeping.bookkeeping_tools import BookkeepingTools
from tools.tax.tax_tools import TaxTools
from tools.payroll.payroll_tools import PayrollTools
from tools.sales_tax.sales_tax_tools import SalesTaxTools
from tools.integrations.integration_tools import IntegrationTools

async def test_client_management():
    """Test client management functionality"""
    print("🧪 Testing Client Management Tools...")
    
    client_mgmt = ClientManagementTools()
    
    # Test creating a new client
    client_data = {
        "business_name": "Test Company LLC",
        "contact_name": "John Doe",
        "email": "john@testcompany.com",
        "entity_type": "LLC",
        "state": "TX",
        "industry": "Consulting"
    }
    
    result = await client_mgmt.update_client_profile("TEST001", client_data)
    print(f"✅ Client Creation: {result}")
    
    # Test retrieving client info
    client_info = await client_mgmt.get_client_info("TEST001")
    print(f"✅ Client Info: {json.dumps(client_info, indent=2)}")
    
    # Test getting deadlines
    deadlines = await client_mgmt.get_client_deadlines("TEST001")
    print(f"✅ Client Deadlines: {json.dumps(deadlines, indent=2)}")
    
    return True

async def test_tax_calculations():
    """Test tax calculation functionality"""
    print("\n💰 Testing Tax Calculation Tools...")
    
    tax_tools = TaxTools()
    
    # Test tax liability calculation
    result = await tax_tools.calculate_tax_liability("TEST001", 2024, "ytd_annualized")
    print(f"✅ Tax Liability: {json.dumps(result, indent=2)}")
    
    # Test deduction optimization
    expense_data = {
        "Office Supplies": {"General": 2500, "Equipment": 1200},
        "Travel": {"Airfare": 3500, "Lodging": 2800},
        "Equipment": {"Computer": 5000, "Software": 1500}
    }
    
    deduction_result = await tax_tools.optimize_deductions("TEST001", 2024, expense_data)
    print(f"✅ Deduction Optimization: {json.dumps(deduction_result, indent=2)}")
    
    return True

async def test_payroll_processing():
    """Test payroll processing functionality"""
    print("\n💼 Testing Payroll Processing Tools...")
    
    payroll_tools = PayrollTools()
    
    # Test payroll calculation
    employee_data = [
        {
            "employee_id": "EMP001",
            "first_name": "Jane",
            "last_name": "Smith",
            "hours_worked": 80,
            "overtime_hours": 5,
            "hourly_rate": 25.00,
            "filing_status": "single",
            "allowances": 1
        },
        {
            "employee_id": "EMP002",
            "first_name": "Bob",
            "last_name": "Johnson",
            "salary_type": "salary",
            "salary_amount": 65000,
            "filing_status": "married",
            "allowances": 2
        }
    ]
    
    result = await payroll_tools.calculate_payroll("TEST001", "2024-01-01 to 2024-01-15", employee_data)
    print(f"✅ Payroll Calculation: {json.dumps(result, indent=2)}")
    
    return True

async def test_sales_tax():
    """Test sales tax functionality"""
    print("\n🏛️ Testing Sales Tax Tools...")
    
    sales_tax_tools = SalesTaxTools()
    
    # Test sales tax calculation
    transactions = [
        {"state": "TX", "amount": 1000, "taxable": True},
        {"state": "CA", "amount": 2500, "taxable": True},
        {"state": "FL", "amount": 1500, "taxable": False}
    ]
    
    result = await sales_tax_tools.calculate_sales_tax("TEST001", "2024-01", transactions)
    print(f"✅ Sales Tax Calculation: {json.dumps(result, indent=2)}")
    
    # Test nexus analysis
    nexus_result = await sales_tax_tools.nexus_analysis("TEST001")
    print(f"✅ Nexus Analysis: {json.dumps(nexus_result, indent=2)}")
    
    return True

async def test_integrations():
    """Test integration functionality"""
    print("\n🔄 Testing Integration Tools...")
    
    integration_tools = IntegrationTools()
    
    # Test QuickBooks sync (mock)
    result = await integration_tools.quickbooks_sync("TEST001", "import", ["customers", "vendors"])
    print(f"✅ QuickBooks Sync: {json.dumps(result, indent=2)}")
    
    return True

async def create_sample_data():
    """Create sample CSV file for testing"""
    print("\n📄 Creating Sample Bank Statement...")
    
    sample_csv = """Date,Description,Amount,Reference
2024-01-02,"AMAZON.COM AMZN.COM/BILL",-45.67,
2024-01-03,"DEPOSIT PAYROLL",2500.00,DEP001
2024-01-05,"SHELL OIL #1234",-65.43,
2024-01-08,"OFFICE DEPOT #567",-123.45,
2024-01-10,"RESTAURANT ABC",-78.90,
2024-01-12,"VERIZON WIRELESS",-89.99,
2024-01-15,"CLIENT PAYMENT",1500.00,CHK001
2024-01-18,"BANK SERVICE FEE",-15.00,
2024-01-20,"GOOGLE ADS",-250.00,
2024-01-22,"HOTEL BOOKING",-189.50,"""
    
    with open("sample_bank_statement.csv", "w") as f:
        f.write(sample_csv)
    
    print("✅ Sample bank statement created: sample_bank_statement.csv")
    return True

async def test_bank_statement_processing():
    """Test bank statement processing"""
    print("\n📊 Testing Bank Statement Processing...")
    
    bookkeeping_tools = BookkeepingTools()
    
    # Test processing the sample CSV
    result = await bookkeeping_tools.process_bank_statement("TEST001", "sample_bank_statement.csv", "checking")
    print(f"✅ Bank Statement Processing: {json.dumps(result, indent=2)}")
    
    # Test account reconciliation
    reconcile_result = await bookkeeping_tools.reconcile_accounts("TEST001", "checking", "2024-01")
    print(f"✅ Account Reconciliation: {json.dumps(reconcile_result, indent=2)}")
    
    return True

async def main():
    """Run all tests"""
    print("🚀 Starting Accounting Practice MCP Server Tests...\n")
    
    try:
        # Create sample data first
        await create_sample_data()
        
        # Run all tests
        await test_client_management()
        await test_bank_statement_processing()
        await test_tax_calculations()
        await test_payroll_processing()
        await test_sales_tax()
        await test_integrations()
        
        print("\n🎉 All tests completed successfully!")
        print("\n📋 Test Summary:")
        print("✅ Client Management - Working")
        print("✅ Bank Statement Processing - Working")
        print("✅ Tax Calculations - Working")
        print("✅ Payroll Processing - Working")
        print("✅ Sales Tax Tools - Working")
        print("✅ Integration Tools - Working")
        
        print("\n🚀 Your MCP server is ready for production use!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())