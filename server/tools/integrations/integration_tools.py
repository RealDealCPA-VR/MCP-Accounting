"""
Integration Tools for Accounting Practice MCP
Handles integrations with QuickBooks, Excel, and other accounting software
"""

import json
import os
import csv
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import sqlite3

class IntegrationTools:
    def __init__(self):
        self.db_path = "server/data/client_profiles/integrations.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize the integrations database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create integration connections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS integration_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                integration_type TEXT NOT NULL,
                connection_name TEXT,
                connection_config TEXT,
                status TEXT DEFAULT 'active',
                last_sync TEXT,
                created_date TEXT,
                last_updated TEXT
            )
        ''')
        
        # Create sync history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                integration_type TEXT NOT NULL,
                sync_type TEXT,
                records_processed INTEGER,
                records_created INTEGER,
                records_updated INTEGER,
                records_errors INTEGER,
                sync_start TEXT,
                sync_end TEXT,
                status TEXT,
                error_details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def quickbooks_sync(self, client_id: str, sync_type: str, data_types: List[str]) -> Dict[str, Any]:
        """Synchronize data with QuickBooks Online or Desktop"""
        try:
            # This is a simplified implementation
            # In practice, would use QuickBooks API or SDK
            
            sync_results = {
                "client_id": client_id,
                "sync_type": sync_type,
                "data_types": data_types,
                "sync_start": datetime.now().isoformat(),
                "results": {},
                "total_processed": 0,
                "total_created": 0,
                "total_updated": 0,
                "errors": []
            }
            
            # Process each data type
            for data_type in data_types:
                if data_type == "customers":
                    result = await self._sync_customers(client_id, sync_type)
                elif data_type == "vendors":
                    result = await self._sync_vendors(client_id, sync_type)
                elif data_type == "items":
                    result = await self._sync_items(client_id, sync_type)
                elif data_type == "transactions":
                    result = await self._sync_transactions(client_id, sync_type)
                else:
                    result = {"error": f"Unsupported data type: {data_type}"}
                
                sync_results["results"][data_type] = result
                
                if "error" not in result:
                    sync_results["total_processed"] += result.get("processed", 0)
                    sync_results["total_created"] += result.get("created", 0)
                    sync_results["total_updated"] += result.get("updated", 0)
                else:
                    sync_results["errors"].append(result["error"])
            
            sync_results["sync_end"] = datetime.now().isoformat()
            sync_results["status"] = "completed" if not sync_results["errors"] else "completed_with_errors"
            
            # Save sync history
            await self._save_sync_history(client_id, "quickbooks", sync_results)
            
            return sync_results
            
        except Exception as e:
            return {"error": f"Failed to sync with QuickBooks: {str(e)}"}
    
    async def _sync_customers(self, client_id: str, sync_type: str) -> Dict[str, Any]:
        """Sync customer data with QuickBooks"""
        # Simplified implementation - would use actual QuickBooks API
        
        if sync_type == "import":
            # Import customers from QuickBooks
            # This would typically involve API calls to QuickBooks
            customers_data = [
                {"id": "1", "name": "ABC Company", "email": "contact@abc.com"},
                {"id": "2", "name": "XYZ Corp", "email": "info@xyz.com"}
            ]
            
            # Save to local database (simplified)
            processed = len(customers_data)
            created = processed  # All are new in this example
            
            return {
                "processed": processed,
                "created": created,
                "updated": 0,
                "data_sample": customers_data[:3]  # First 3 records as sample
            }
        
        elif sync_type == "export":
            # Export customers to QuickBooks
            # Get customers from local system
            customers_to_export = [
                {"name": "Local Customer 1", "email": "local1@example.com"},
                {"name": "Local Customer 2", "email": "local2@example.com"}
            ]
            
            processed = len(customers_to_export)
            created = processed  # All are new exports
            
            return {
                "processed": processed,
                "created": created,
                "updated": 0,
                "exported_data": customers_to_export
            }
        
        else:
            return {"error": f"Unsupported sync type: {sync_type}"}
    
    async def _sync_vendors(self, client_id: str, sync_type: str) -> Dict[str, Any]:
        """Sync vendor data with QuickBooks"""
        # Similar implementation to customers
        if sync_type == "import":
            vendors_data = [
                {"id": "V1", "name": "Office Supply Co", "email": "orders@officesupply.com"},
                {"id": "V2", "name": "Tech Services LLC", "email": "billing@techservices.com"}
            ]
            
            return {
                "processed": len(vendors_data),
                "created": len(vendors_data),
                "updated": 0,
                "data_sample": vendors_data
            }
        
        elif sync_type == "export":
            vendors_to_export = [
                {"name": "Local Vendor 1", "email": "vendor1@example.com"}
            ]
            
            return {
                "processed": len(vendors_to_export),
                "created": len(vendors_to_export),
                "updated": 0,
                "exported_data": vendors_to_export
            }
        
        else:
            return {"error": f"Unsupported sync type: {sync_type}"}
    
    async def _sync_items(self, client_id: str, sync_type: str) -> Dict[str, Any]:
        """Sync item/product data with QuickBooks"""
        if sync_type == "import":
            items_data = [
                {"id": "I1", "name": "Consulting Services", "type": "Service", "rate": 150.00},
                {"id": "I2", "name": "Software License", "type": "Product", "price": 299.99}
            ]
            
            return {
                "processed": len(items_data),
                "created": len(items_data),
                "updated": 0,
                "data_sample": items_data
            }
        
        elif sync_type == "export":
            items_to_export = [
                {"name": "Custom Service", "type": "Service", "rate": 200.00}
            ]
            
            return {
                "processed": len(items_to_export),
                "created": len(items_to_export),
                "updated": 0,
                "exported_data": items_to_export
            }
        
        else:
            return {"error": f"Unsupported sync type: {sync_type}"}
    
    async def _sync_transactions(self, client_id: str, sync_type: str) -> Dict[str, Any]:
        """Sync transaction data with QuickBooks"""
        if sync_type == "import":
            # Import transactions from QuickBooks
            transactions_data = [
                {
                    "id": "T1",
                    "type": "Invoice",
                    "customer": "ABC Company",
                    "amount": 1500.00,
                    "date": "2024-01-15"
                },
                {
                    "id": "T2",
                    "type": "Bill",
                    "vendor": "Office Supply Co",
                    "amount": 250.00,
                    "date": "2024-01-16"
                }
            ]
            
            # In practice, would save these to the bookkeeping database
            return {
                "processed": len(transactions_data),
                "created": len(transactions_data),
                "updated": 0,
                "data_sample": transactions_data
            }
        
        elif sync_type == "export":
            # Export transactions to QuickBooks
            # Get transactions from bookkeeping system
            bookkeeping_conn = sqlite3.connect("server/data/client_profiles/bookkeeping.db")
            cursor = bookkeeping_conn.cursor()
            
            cursor.execute('''
                SELECT transaction_date, description, amount, category
                FROM transactions
                WHERE client_id = ? AND transaction_date >= ?
                ORDER BY transaction_date DESC
                LIMIT 100
            ''', (client_id, (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')))
            
            transactions = cursor.fetchall()
            bookkeeping_conn.close()
            
            # Format for QuickBooks export
            export_data = []
            for trans in transactions:
                export_data.append({
                    "date": trans[0],
                    "description": trans[1],
                    "amount": trans[2],
                    "account": trans[3]
                })
            
            return {
                "processed": len(export_data),
                "created": len(export_data),
                "updated": 0,
                "exported_data": export_data[:5]  # Sample of first 5
            }
        
        else:
            return {"error": f"Unsupported sync type: {sync_type}"}
    
    async def _save_sync_history(self, client_id: str, integration_type: str, sync_results: Dict[str, Any]):
        """Save sync history to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sync_history (
                    client_id, integration_type, sync_type, records_processed,
                    records_created, records_updated, records_errors,
                    sync_start, sync_end, status, error_details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                client_id,
                integration_type,
                sync_results.get("sync_type", "unknown"),
                sync_results.get("total_processed", 0),
                sync_results.get("total_created", 0),
                sync_results.get("total_updated", 0),
                len(sync_results.get("errors", [])),
                sync_results.get("sync_start"),
                sync_results.get("sync_end"),
                sync_results.get("status", "unknown"),
                json.dumps(sync_results.get("errors", []))
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error saving sync history: {str(e)}")
    
    async def excel_processor(self, file_path: str, template_type: str) -> Dict[str, Any]:
        """Process Excel files with specific templates"""
        try:
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}
            
            # Load Excel file
            df = pd.read_excel(file_path)
            
            if template_type == "chart_of_accounts":
                result = await self._process_chart_of_accounts(df)
            elif template_type == "trial_balance":
                result = await self._process_trial_balance(df)
            elif template_type == "financial_statements":
                result = await self._process_financial_statements(df)
            elif template_type == "budget_vs_actual":
                result = await self._process_budget_vs_actual(df)
            elif template_type == "expense_report":
                result = await self._process_expense_report(df)
            else:
                result = await self._process_generic_excel(df, template_type)
            
            result["file_path"] = file_path
            result["template_type"] = template_type
            result["processed_date"] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to process Excel file: {str(e)}"}
    
    async def _process_chart_of_accounts(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Process Chart of Accounts Excel template"""
        required_columns = ['Account Code', 'Account Name', 'Account Type']
        
        # Validate columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return {"error": f"Missing required columns: {missing_columns}"}
        
        # Process accounts
        accounts = []
        for _, row in df.iterrows():
            if pd.notna(row['Account Code']) and pd.notna(row['Account Name']):
                accounts.append({
                    "code": str(row['Account Code']).strip(),
                    "name": str(row['Account Name']).strip(),
                    "type": str(row['Account Type']).strip(),
                    "parent": str(row.get('Parent Account', '')).strip() if pd.notna(row.get('Parent Account')) else None
                })
        
        # Validate account types
        valid_types = ['Asset', 'Liability', 'Equity', 'Income', 'Expense']
        invalid_accounts = [acc for acc in accounts if acc['type'] not in valid_types]
        
        return {
            "total_accounts": len(accounts),
            "valid_accounts": len(accounts) - len(invalid_accounts),
            "invalid_accounts": len(invalid_accounts),
            "accounts_data": accounts,
            "validation_errors": [f"Invalid account type '{acc['type']}' for {acc['name']}" for acc in invalid_accounts]
        }
    
    async def _process_trial_balance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Process Trial Balance Excel template"""
        required_columns = ['Account', 'Debit', 'Credit']
        
        # Validate columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return {"error": f"Missing required columns: {missing_columns}"}
        
        # Process trial balance
        total_debits = 0
        total_credits = 0
        accounts = []
        
        for _, row in df.iterrows():
            if pd.notna(row['Account']):
                debit = float(row['Debit']) if pd.notna(row['Debit']) else 0
                credit = float(row['Credit']) if pd.notna(row['Credit']) else 0
                
                accounts.append({
                    "account": str(row['Account']).strip(),
                    "debit": debit,
                    "credit": credit
                })
                
                total_debits += debit
                total_credits += credit
        
        # Check if trial balance balances
        difference = abs(total_debits - total_credits)
        is_balanced = difference < 0.01  # Allow for small rounding differences
        
        return {
            "total_accounts": len(accounts),
            "total_debits": total_debits,
            "total_credits": total_credits,
            "difference": difference,
            "is_balanced": is_balanced,
            "accounts_data": accounts,
            "balance_status": "Balanced" if is_balanced else f"Out of balance by ${difference:.2f}"
        }
    
    async def _process_financial_statements(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Process Financial Statements Excel template"""
        # This would process P&L, Balance Sheet, Cash Flow statements
        
        # Identify statement type based on content
        if 'Revenue' in df.columns or 'Income' in df.columns:
            statement_type = "Profit & Loss"
        elif 'Assets' in df.columns or 'Liabilities' in df.columns:
            statement_type = "Balance Sheet"
        elif 'Cash Flow' in df.columns or 'Operating Activities' in df.columns:
            statement_type = "Cash Flow"
        else:
            statement_type = "Unknown"
        
        # Basic processing
        total_rows = len(df)
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        
        summary = {}
        for col in numeric_columns:
            summary[col] = {
                "total": df[col].sum(),
                "count": df[col].count(),
                "average": df[col].mean()
            }
        
        return {
            "statement_type": statement_type,
            "total_rows": total_rows,
            "numeric_columns": numeric_columns,
            "summary": summary,
            "data_sample": df.head(10).to_dict('records')
        }
    
    async def _process_budget_vs_actual(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Process Budget vs Actual Excel template"""
        required_columns = ['Account', 'Budget', 'Actual']
        
        # Validate columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return {"error": f"Missing required columns: {missing_columns}"}
        
        # Process budget vs actual
        comparisons = []
        total_budget = 0
        total_actual = 0
        
        for _, row in df.iterrows():
            if pd.notna(row['Account']):
                budget = float(row['Budget']) if pd.notna(row['Budget']) else 0
                actual = float(row['Actual']) if pd.notna(row['Actual']) else 0
                variance = actual - budget
                variance_pct = (variance / budget * 100) if budget != 0 else 0
                
                comparisons.append({
                    "account": str(row['Account']).strip(),
                    "budget": budget,
                    "actual": actual,
                    "variance": variance,
                    "variance_percentage": variance_pct
                })
                
                total_budget += budget
                total_actual += actual
        
        total_variance = total_actual - total_budget
        total_variance_pct = (total_variance / total_budget * 100) if total_budget != 0 else 0
        
        return {
            "total_accounts": len(comparisons),
            "total_budget": total_budget,
            "total_actual": total_actual,
            "total_variance": total_variance,
            "total_variance_percentage": total_variance_pct,
            "comparisons": comparisons,
            "performance_summary": "Over budget" if total_variance > 0 else "Under budget"
        }
    
    async def _process_expense_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Process Expense Report Excel template"""
        required_columns = ['Date', 'Description', 'Amount']
        
        # Validate columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return {"error": f"Missing required columns: {missing_columns}"}
        
        # Process expenses
        expenses = []
        total_amount = 0
        categories = {}
        
        for _, row in df.iterrows():
            if pd.notna(row['Date']) and pd.notna(row['Amount']):
                amount = float(row['Amount'])
                category = str(row.get('Category', 'Uncategorized')).strip()
                
                expenses.append({
                    "date": str(row['Date']),
                    "description": str(row['Description']).strip(),
                    "amount": amount,
                    "category": category
                })
                
                total_amount += amount
                
                if category not in categories:
                    categories[category] = {"count": 0, "total": 0}
                categories[category]["count"] += 1
                categories[category]["total"] += amount
        
        return {
            "total_expenses": len(expenses),
            "total_amount": total_amount,
            "categories": categories,
            "expenses_data": expenses,
            "average_expense": total_amount / len(expenses) if expenses else 0
        }
    
    async def _process_generic_excel(self, df: pd.DataFrame, template_type: str) -> Dict[str, Any]:
        """Process generic Excel file"""
        return {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "data_types": df.dtypes.to_dict(),
            "sample_data": df.head(5).to_dict('records'),
            "summary": {
                "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
                "text_columns": df.select_dtypes(include=['object']).columns.tolist(),
                "date_columns": df.select_dtypes(include=['datetime']).columns.tolist()
            }
        }
    
    async def pdf_extractor(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """Extract data from PDF documents"""
        try:
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}
            
            # This is a simplified implementation
            # In practice, would use PDF parsing libraries like PyPDF2, pdfplumber, or OCR
            
            extraction_result = {
                "file_path": file_path,
                "document_type": document_type,
                "extraction_date": datetime.now().isoformat(),
                "status": "completed"
            }
            
            if document_type == "invoice":
                extraction_result.update(await self._extract_invoice_data(file_path))
            elif document_type == "receipt":
                extraction_result.update(await self._extract_receipt_data(file_path))
            elif document_type == "bank_statement":
                extraction_result.update(await self._extract_bank_statement_data(file_path))
            elif document_type == "tax_document":
                extraction_result.update(await self._extract_tax_document_data(file_path))
            else:
                extraction_result.update(await self._extract_generic_pdf_data(file_path))
            
            return extraction_result
            
        except Exception as e:
            return {"error": f"Failed to extract PDF data: {str(e)}"}
    
    async def _extract_invoice_data(self, file_path: str) -> Dict[str, Any]:
        """Extract data from invoice PDF"""
        # Simplified mock extraction
        return {
            "invoice_number": "INV-2024-001",
            "date": "2024-01-15",
            "vendor": "ABC Supply Company",
            "amount": 1250.00,
            "tax_amount": 100.00,
            "total_amount": 1350.00,
            "line_items": [
                {"description": "Office Supplies", "quantity": 10, "rate": 25.00, "amount": 250.00},
                {"description": "Software License", "quantity": 1, "rate": 1000.00, "amount": 1000.00}
            ],
            "confidence_score": 0.85
        }
    
    async def _extract_receipt_data(self, file_path: str) -> Dict[str, Any]:
        """Extract data from receipt PDF"""
        return {
            "merchant": "Office Depot",
            "date": "2024-01-16",
            "amount": 45.67,
            "tax_amount": 3.67,
            "items": [
                {"description": "Printer Paper", "amount": 15.99},
                {"description": "Pens (Pack of 12)", "amount": 8.99},
                {"description": "Folders", "amount": 17.02}
            ],
            "payment_method": "Credit Card",
            "confidence_score": 0.92
        }
    
    async def _extract_bank_statement_data(self, file_path: str) -> Dict[str, Any]:
        """Extract data from bank statement PDF"""
        return {
            "account_number": "****1234",
            "statement_period": "2024-01-01 to 2024-01-31",
            "beginning_balance": 5000.00,
            "ending_balance": 4750.00,
            "total_deposits": 2500.00,
            "total_withdrawals": 2750.00,
            "transaction_count": 25,
            "confidence_score": 0.78
        }
    
    async def _extract_tax_document_data(self, file_path: str) -> Dict[str, Any]:
        """Extract data from tax document PDF"""
        return {
            "document_type": "1099-NEC",
            "tax_year": 2023,
            "payer": "Client Company LLC",
            "recipient": "John Doe",
            "amount": 15000.00,
            "federal_tax_withheld": 0.00,
            "confidence_score": 0.88
        }
    
    async def _extract_generic_pdf_data(self, file_path: str) -> Dict[str, Any]:
        """Extract generic data from PDF"""
        return {
            "page_count": 3,
            "text_extracted": True,
            "contains_tables": True,
            "contains_images": False,
            "file_size_mb": 0.5,
            "confidence_score": 0.70
        }