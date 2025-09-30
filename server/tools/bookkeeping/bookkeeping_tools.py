"""
Bookkeeping Tools for Accounting Practice MCP
Handles bank statement processing, reconciliation, and transaction categorization
"""

import csv
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import sqlite3
import pandas as pd

class BookkeepingTools:
    def __init__(self):
        self.db_path = "server/data/client_profiles/bookkeeping.db"
        self.rules_path = "server/data/categorization_rules.json"
        self._init_database()
        self._load_categorization_rules()
    
    def _init_database(self):
        """Initialize the bookkeeping database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                account_name TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL,
                transaction_type TEXT,
                category TEXT,
                subcategory TEXT,
                reference_number TEXT,
                cleared_status TEXT DEFAULT 'uncleared',
                created_date TEXT,
                last_updated TEXT,
                source_file TEXT,
                confidence_score REAL DEFAULT 0.0
            )
        ''')
        
        # Create reconciliation table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reconciliations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                account_name TEXT NOT NULL,
                period TEXT NOT NULL,
                beginning_balance REAL,
                ending_balance REAL,
                statement_balance REAL,
                reconciled_balance REAL,
                difference REAL,
                status TEXT DEFAULT 'in_progress',
                reconciled_date TEXT,
                created_date TEXT,
                notes TEXT
            )
        ''')
        
        # Create chart of accounts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chart_of_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                account_code TEXT,
                account_name TEXT NOT NULL,
                account_type TEXT NOT NULL,
                parent_account TEXT,
                is_active INTEGER DEFAULT 1,
                created_date TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_categorization_rules(self):
        """Load transaction categorization rules"""
        default_rules = {
            "patterns": [
                {"pattern": r"(?i)amazon|amzn", "category": "Office Supplies", "subcategory": "General"},
                {"pattern": r"(?i)gas|fuel|shell|exxon|bp", "category": "Vehicle Expenses", "subcategory": "Fuel"},
                {"pattern": r"(?i)office depot|staples|best buy", "category": "Office Supplies", "subcategory": "Equipment"},
                {"pattern": r"(?i)restaurant|cafe|food|dining", "category": "Meals & Entertainment", "subcategory": "Business Meals"},
                {"pattern": r"(?i)hotel|motel|lodging|airbnb", "category": "Travel", "subcategory": "Lodging"},
                {"pattern": r"(?i)airline|flight|airport", "category": "Travel", "subcategory": "Airfare"},
                {"pattern": r"(?i)internet|phone|verizon|att|comcast", "category": "Utilities", "subcategory": "Communications"},
                {"pattern": r"(?i)electric|power|gas company|water", "category": "Utilities", "subcategory": "Basic Utilities"},
                {"pattern": r"(?i)insurance", "category": "Insurance", "subcategory": "General"},
                {"pattern": r"(?i)bank fee|service charge", "category": "Bank Charges", "subcategory": "Fees"},
                {"pattern": r"(?i)payroll|salary|wages", "category": "Payroll", "subcategory": "Wages"},
                {"pattern": r"(?i)rent|lease", "category": "Rent", "subcategory": "Office Rent"},
                {"pattern": r"(?i)legal|attorney|law", "category": "Professional Services", "subcategory": "Legal"},
                {"pattern": r"(?i)accounting|bookkeeping|cpa", "category": "Professional Services", "subcategory": "Accounting"},
                {"pattern": r"(?i)marketing|advertising|google ads", "category": "Marketing", "subcategory": "Advertising"},
                {"pattern": r"(?i)software|subscription|saas", "category": "Software", "subcategory": "Subscriptions"}
            ],
            "amount_rules": [
                {"min_amount": 5000, "category": "Equipment", "subcategory": "Major Equipment"},
                {"max_amount": 25, "category": "Office Supplies", "subcategory": "Miscellaneous"}
            ]
        }
        
        if not os.path.exists(self.rules_path):
            os.makedirs(os.path.dirname(self.rules_path), exist_ok=True)
            with open(self.rules_path, 'w') as f:
                json.dump(default_rules, f, indent=2)
        
        with open(self.rules_path, 'r') as f:
            self.categorization_rules = json.load(f)
    
    async def process_bank_statement(self, client_id: str, file_path: str, account_type: str = "checking") -> Dict[str, Any]:
        """Import and automatically categorize bank statement transactions"""
        try:
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}
            
            # Detect file format and parse
            transactions = []
            if file_path.lower().endswith('.csv'):
                transactions = self._parse_csv_statement(file_path)
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                transactions = self._parse_excel_statement(file_path)
            else:
                return {"error": "Unsupported file format. Please use CSV or Excel files."}
            
            if not transactions:
                return {"error": "No transactions found in the file"}
            
            # Process and categorize transactions
            processed_transactions = []
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for trans in transactions:
                # Categorize transaction
                category, subcategory, confidence = self._categorize_transaction(
                    trans['description'], trans['amount']
                )
                
                # Determine transaction type
                trans_type = "debit" if trans['amount'] < 0 else "credit"
                
                # Insert into database
                cursor.execute('''
                    INSERT INTO transactions (
                        client_id, account_name, transaction_date, description, amount,
                        transaction_type, category, subcategory, reference_number,
                        created_date, last_updated, source_file, confidence_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    client_id, account_type, trans['date'], trans['description'], 
                    trans['amount'], trans_type, category, subcategory,
                    trans.get('reference', ''), datetime.now().isoformat(),
                    datetime.now().isoformat(), file_path, confidence
                ))
                
                processed_transactions.append({
                    "date": trans['date'],
                    "description": trans['description'],
                    "amount": trans['amount'],
                    "type": trans_type,
                    "category": category,
                    "subcategory": subcategory,
                    "confidence": confidence
                })
            
            conn.commit()
            conn.close()
            
            # Generate summary statistics
            total_debits = sum(t['amount'] for t in processed_transactions if t['amount'] < 0)
            total_credits = sum(t['amount'] for t in processed_transactions if t['amount'] > 0)
            
            # Category breakdown
            category_summary = {}
            for trans in processed_transactions:
                cat = trans['category']
                if cat not in category_summary:
                    category_summary[cat] = {"count": 0, "total": 0}
                category_summary[cat]["count"] += 1
                category_summary[cat]["total"] += abs(trans['amount'])
            
            return {
                "client_id": client_id,
                "account_type": account_type,
                "transactions_processed": len(processed_transactions),
                "total_debits": total_debits,
                "total_credits": total_credits,
                "net_change": total_credits + total_debits,
                "category_summary": category_summary,
                "low_confidence_count": len([t for t in processed_transactions if t['confidence'] < 0.7]),
                "source_file": file_path
            }
            
        except Exception as e:
            return {"error": f"Failed to process bank statement: {str(e)}"}
    
    def _parse_csv_statement(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse CSV bank statement file"""
        transactions = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            # Try to detect the CSV format
            sample = f.read(1024)
            f.seek(0)
            
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            reader = csv.DictReader(f, delimiter=delimiter)
            
            for row in reader:
                # Common field mappings
                date_fields = ['Date', 'Transaction Date', 'Posted Date', 'date']
                desc_fields = ['Description', 'Memo', 'Transaction', 'description']
                amount_fields = ['Amount', 'Debit', 'Credit', 'amount']
                
                # Find the correct fields
                date_val = None
                desc_val = None
                amount_val = None
                
                for field in date_fields:
                    if field in row and row[field]:
                        date_val = self._parse_date(row[field])
                        break
                
                for field in desc_fields:
                    if field in row and row[field]:
                        desc_val = row[field].strip()
                        break
                
                # Handle amount (could be in separate debit/credit columns)
                if 'Debit' in row and 'Credit' in row:
                    debit = float(row['Debit'] or 0)
                    credit = float(row['Credit'] or 0)
                    amount_val = credit - debit
                else:
                    for field in amount_fields:
                        if field in row and row[field]:
                            amount_val = float(row[field].replace('$', '').replace(',', ''))
                            break
                
                if date_val and desc_val and amount_val is not None:
                    transactions.append({
                        'date': date_val,
                        'description': desc_val,
                        'amount': amount_val,
                        'reference': row.get('Reference', row.get('Check Number', ''))
                    })
        
        return transactions
    
    def _parse_excel_statement(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse Excel bank statement file"""
        try:
            df = pd.read_excel(file_path)
            transactions = []
            
            # Common column name mappings
            date_cols = ['Date', 'Transaction Date', 'Posted Date']
            desc_cols = ['Description', 'Memo', 'Transaction']
            amount_cols = ['Amount', 'Debit', 'Credit']
            
            # Find the correct columns
            date_col = next((col for col in date_cols if col in df.columns), None)
            desc_col = next((col for col in desc_cols if col in df.columns), None)
            
            if not date_col or not desc_col:
                return []
            
            for _, row in df.iterrows():
                if pd.isna(row[date_col]) or pd.isna(row[desc_col]):
                    continue
                
                # Handle amount
                amount = 0
                if 'Debit' in df.columns and 'Credit' in df.columns:
                    debit = float(row['Debit'] or 0)
                    credit = float(row['Credit'] or 0)
                    amount = credit - debit
                elif 'Amount' in df.columns:
                    amount = float(row['Amount'] or 0)
                
                transactions.append({
                    'date': row[date_col].strftime('%Y-%m-%d') if hasattr(row[date_col], 'strftime') else str(row[date_col]),
                    'description': str(row[desc_col]).strip(),
                    'amount': amount,
                    'reference': str(row.get('Reference', row.get('Check Number', '')))
                })
            
            return transactions
            
        except Exception as e:
            print(f"Error parsing Excel file: {str(e)}")
            return []
    
    def _parse_date(self, date_str: str) -> str:
        """Parse various date formats to ISO format"""
        date_formats = [
            '%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d', '%m/%d/%y', '%m-%d-%y',
            '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return date_str  # Return as-is if no format matches
    
    def _categorize_transaction(self, description: str, amount: float) -> Tuple[str, str, float]:
        """Categorize a transaction based on description and amount"""
        description_lower = description.lower()
        
        # Check pattern rules
        for rule in self.categorization_rules.get('patterns', []):
            if re.search(rule['pattern'], description):
                return rule['category'], rule['subcategory'], 0.9
        
        # Check amount-based rules
        for rule in self.categorization_rules.get('amount_rules', []):
            if 'min_amount' in rule and abs(amount) >= rule['min_amount']:
                return rule['category'], rule['subcategory'], 0.7
            elif 'max_amount' in rule and abs(amount) <= rule['max_amount']:
                return rule['category'], rule['subcategory'], 0.6
        
        # Default categorization
        if amount > 0:
            return "Income", "Unclassified Income", 0.3
        else:
            return "Expenses", "Unclassified Expenses", 0.3
    
    async def reconcile_accounts(self, client_id: str, account: str, period: str) -> Dict[str, Any]:
        """Perform automated bank reconciliation"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Parse period (YYYY-MM format)
            year, month = period.split('-')
            start_date = f"{year}-{month}-01"
            
            # Calculate end date
            if month == '12':
                end_date = f"{int(year)+1}-01-01"
            else:
                end_date = f"{year}-{int(month)+1:02d}-01"
            
            # Get transactions for the period
            cursor.execute('''
                SELECT * FROM transactions
                WHERE client_id = ? AND account_name = ?
                AND transaction_date >= ? AND transaction_date < ?
                ORDER BY transaction_date
            ''', (client_id, account, start_date, end_date))
            
            transactions = cursor.fetchall()
            
            if not transactions:
                return {"error": f"No transactions found for {account} in {period}"}
            
            # Calculate balances
            beginning_balance = 0  # This should come from previous reconciliation
            total_debits = sum(t[5] for t in transactions if t[5] < 0)  # amount column
            total_credits = sum(t[5] for t in transactions if t[5] > 0)
            ending_balance = beginning_balance + total_credits + total_debits
            
            # Identify potential issues
            issues = []
            
            # Check for duplicate transactions
            duplicates = self._find_duplicate_transactions(transactions)
            if duplicates:
                issues.append({
                    "type": "duplicates",
                    "count": len(duplicates),
                    "transactions": duplicates
                })
            
            # Check for unusual amounts
            unusual_amounts = [t for t in transactions if abs(t[5]) > 10000]  # Over $10k
            if unusual_amounts:
                issues.append({
                    "type": "large_amounts",
                    "count": len(unusual_amounts),
                    "transactions": [{"id": t[0], "amount": t[5], "description": t[4]} for t in unusual_amounts]
                })
            
            # Check for round numbers (potential manual entries)
            round_numbers = [t for t in transactions if t[5] % 100 == 0 and abs(t[5]) >= 100]
            if round_numbers:
                issues.append({
                    "type": "round_amounts",
                    "count": len(round_numbers),
                    "transactions": [{"id": t[0], "amount": t[5], "description": t[4]} for t in round_numbers]
                })
            
            # Save reconciliation record
            cursor.execute('''
                INSERT INTO reconciliations (
                    client_id, account_name, period, beginning_balance, ending_balance,
                    reconciled_balance, difference, status, created_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                client_id, account, period, beginning_balance, ending_balance,
                ending_balance, 0, 'completed', datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            return {
                "client_id": client_id,
                "account": account,
                "period": period,
                "beginning_balance": beginning_balance,
                "ending_balance": ending_balance,
                "total_transactions": len(transactions),
                "total_debits": total_debits,
                "total_credits": total_credits,
                "issues_found": len(issues),
                "issues": issues,
                "reconciliation_status": "completed" if not issues else "needs_review"
            }
            
        except Exception as e:
            return {"error": f"Failed to reconcile account: {str(e)}"}
    
    def _find_duplicate_transactions(self, transactions: List[Tuple]) -> List[Dict[str, Any]]:
        """Find potential duplicate transactions"""
        duplicates = []
        seen = {}
        
        for trans in transactions:
            # Create a key based on date, amount, and description
            key = (trans[3], trans[5], trans[4][:50])  # date, amount, description (first 50 chars)
            
            if key in seen:
                duplicates.append({
                    "original_id": seen[key],
                    "duplicate_id": trans[0],
                    "date": trans[3],
                    "amount": trans[5],
                    "description": trans[4]
                })
            else:
                seen[key] = trans[0]
        
        return duplicates