"""
Sales Tax Tools for Accounting Practice MCP
Handles sales tax calculations, nexus analysis, and compliance monitoring
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import sqlite3

class SalesTaxTools:
    def __init__(self):
        self.db_path = "server/data/client_profiles/sales_tax.db"
        self.rates_path = "server/data/tax_tables/sales_tax_rates.json"
        self._init_database()
        self._load_sales_tax_rates()
    
    def _init_database(self):
        """Initialize the sales tax database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create nexus tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nexus_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                state TEXT NOT NULL,
                nexus_type TEXT,
                threshold_amount REAL,
                threshold_transactions INTEGER,
                current_sales REAL DEFAULT 0,
                current_transactions INTEGER DEFAULT 0,
                nexus_date TEXT,
                registration_number TEXT,
                status TEXT DEFAULT 'monitoring',
                created_date TEXT,
                last_updated TEXT
            )
        ''')
        
        # Create sales tax calculations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_tax_calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                period TEXT NOT NULL,
                state TEXT NOT NULL,
                jurisdiction TEXT,
                gross_sales REAL,
                taxable_sales REAL,
                exempt_sales REAL,
                tax_rate REAL,
                tax_due REAL,
                calculation_date TEXT,
                status TEXT DEFAULT 'draft'
            )
        ''')
        
        # Create sales tax returns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_tax_returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                state TEXT NOT NULL,
                period TEXT NOT NULL,
                filing_frequency TEXT,
                due_date TEXT,
                total_sales REAL,
                taxable_sales REAL,
                tax_due REAL,
                penalty REAL DEFAULT 0,
                interest REAL DEFAULT 0,
                total_due REAL,
                filed_date TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        # Create compliance monitoring table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_monitoring (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                state TEXT NOT NULL,
                compliance_type TEXT,
                due_date TEXT,
                description TEXT,
                status TEXT DEFAULT 'pending',
                created_date TEXT,
                completed_date TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_sales_tax_rates(self):
        """Load current sales tax rates by state and jurisdiction"""
        # Default sales tax rates (simplified - in practice, would need comprehensive database)
        default_rates = {
            "AL": {"state_rate": 0.04, "avg_local": 0.051, "combined_avg": 0.091},
            "AK": {"state_rate": 0.00, "avg_local": 0.018, "combined_avg": 0.018},
            "AZ": {"state_rate": 0.056, "avg_local": 0.027, "combined_avg": 0.083},
            "AR": {"state_rate": 0.065, "avg_local": 0.029, "combined_avg": 0.094},
            "CA": {"state_rate": 0.0725, "avg_local": 0.0275, "combined_avg": 0.10},
            "CO": {"state_rate": 0.029, "avg_local": 0.048, "combined_avg": 0.077},
            "CT": {"state_rate": 0.0635, "avg_local": 0.00, "combined_avg": 0.0635},
            "DE": {"state_rate": 0.00, "avg_local": 0.00, "combined_avg": 0.00},
            "FL": {"state_rate": 0.06, "avg_local": 0.012, "combined_avg": 0.072},
            "GA": {"state_rate": 0.04, "avg_local": 0.033, "combined_avg": 0.073},
            "HI": {"state_rate": 0.04, "avg_local": 0.005, "combined_avg": 0.045},
            "ID": {"state_rate": 0.06, "avg_local": 0.003, "combined_avg": 0.063},
            "IL": {"state_rate": 0.0625, "avg_local": 0.0264, "combined_avg": 0.0889},
            "IN": {"state_rate": 0.07, "avg_local": 0.00, "combined_avg": 0.07},
            "IA": {"state_rate": 0.06, "avg_local": 0.008, "combined_avg": 0.068},
            "KS": {"state_rate": 0.065, "avg_local": 0.021, "combined_avg": 0.086},
            "KY": {"state_rate": 0.06, "avg_local": 0.00, "combined_avg": 0.06},
            "LA": {"state_rate": 0.0445, "avg_local": 0.051, "combined_avg": 0.0955},
            "ME": {"state_rate": 0.055, "avg_local": 0.00, "combined_avg": 0.055},
            "MD": {"state_rate": 0.06, "avg_local": 0.00, "combined_avg": 0.06},
            "MA": {"state_rate": 0.0625, "avg_local": 0.00, "combined_avg": 0.0625},
            "MI": {"state_rate": 0.06, "avg_local": 0.00, "combined_avg": 0.06},
            "MN": {"state_rate": 0.06875, "avg_local": 0.005, "combined_avg": 0.07375},
            "MS": {"state_rate": 0.07, "avg_local": 0.001, "combined_avg": 0.071},
            "MO": {"state_rate": 0.04225, "avg_local": 0.0395, "combined_avg": 0.08175},
            "MT": {"state_rate": 0.00, "avg_local": 0.00, "combined_avg": 0.00},
            "NE": {"state_rate": 0.055, "avg_local": 0.014, "combined_avg": 0.069},
            "NV": {"state_rate": 0.0685, "avg_local": 0.013, "combined_avg": 0.0815},
            "NH": {"state_rate": 0.00, "avg_local": 0.00, "combined_avg": 0.00},
            "NJ": {"state_rate": 0.06625, "avg_local": 0.00, "combined_avg": 0.06625},
            "NM": {"state_rate": 0.05125, "avg_local": 0.026, "combined_avg": 0.07725},
            "NY": {"state_rate": 0.04, "avg_local": 0.048, "combined_avg": 0.088},
            "NC": {"state_rate": 0.0475, "avg_local": 0.022, "combined_avg": 0.0695},
            "ND": {"state_rate": 0.05, "avg_local": 0.018, "combined_avg": 0.068},
            "OH": {"state_rate": 0.0575, "avg_local": 0.014, "combined_avg": 0.0715},
            "OK": {"state_rate": 0.045, "avg_local": 0.044, "combined_avg": 0.089},
            "OR": {"state_rate": 0.00, "avg_local": 0.00, "combined_avg": 0.00},
            "PA": {"state_rate": 0.06, "avg_local": 0.003, "combined_avg": 0.063},
            "RI": {"state_rate": 0.07, "avg_local": 0.00, "combined_avg": 0.07},
            "SC": {"state_rate": 0.06, "avg_local": 0.015, "combined_avg": 0.075},
            "SD": {"state_rate": 0.045, "avg_local": 0.019, "combined_avg": 0.064},
            "TN": {"state_rate": 0.07, "avg_local": 0.025, "combined_avg": 0.095},
            "TX": {"state_rate": 0.0625, "avg_local": 0.0195, "combined_avg": 0.082},
            "UT": {"state_rate": 0.0485, "avg_local": 0.014, "combined_avg": 0.0625},
            "VT": {"state_rate": 0.06, "avg_local": 0.001, "combined_avg": 0.061},
            "VA": {"state_rate": 0.053, "avg_local": 0.005, "combined_avg": 0.058},
            "WA": {"state_rate": 0.065, "avg_local": 0.028, "combined_avg": 0.093},
            "WV": {"state_rate": 0.06, "avg_local": 0.007, "combined_avg": 0.067},
            "WI": {"state_rate": 0.05, "avg_local": 0.004, "combined_avg": 0.054},
            "WY": {"state_rate": 0.04, "avg_local": 0.015, "combined_avg": 0.055}
        }
        
        # Economic nexus thresholds (post-Wayfair)
        self.nexus_thresholds = {
            "AL": {"sales": 250000, "transactions": 200},
            "AK": {"sales": 100000, "transactions": 200},
            "AZ": {"sales": 100000, "transactions": 200},
            "AR": {"sales": 100000, "transactions": 200},
            "CA": {"sales": 500000, "transactions": None},
            "CO": {"sales": 100000, "transactions": 200},
            "CT": {"sales": 100000, "transactions": 200},
            "DE": {"sales": None, "transactions": None},  # No sales tax
            "FL": {"sales": 100000, "transactions": None},
            "GA": {"sales": 100000, "transactions": 200},
            "HI": {"sales": 100000, "transactions": 200},
            "ID": {"sales": 100000, "transactions": None},
            "IL": {"sales": 100000, "transactions": 200},
            "IN": {"sales": 100000, "transactions": 200},
            "IA": {"sales": 100000, "transactions": 200},
            "KS": {"sales": 100000, "transactions": None},
            "KY": {"sales": 100000, "transactions": 200},
            "LA": {"sales": 100000, "transactions": 200},
            "ME": {"sales": 100000, "transactions": 200},
            "MD": {"sales": 100000, "transactions": 200},
            "MA": {"sales": 100000, "transactions": None},
            "MI": {"sales": 100000, "transactions": 200},
            "MN": {"sales": 100000, "transactions": 200},
            "MS": {"sales": 250000, "transactions": None},
            "MO": {"sales": 100000, "transactions": None},
            "MT": {"sales": None, "transactions": None},  # No sales tax
            "NE": {"sales": 100000, "transactions": 200},
            "NV": {"sales": 100000, "transactions": 200},
            "NH": {"sales": None, "transactions": None},  # No sales tax
            "NJ": {"sales": 100000, "transactions": 200},
            "NM": {"sales": 100000, "transactions": None},
            "NY": {"sales": 500000, "transactions": 100},
            "NC": {"sales": 100000, "transactions": 200},
            "ND": {"sales": 100000, "transactions": None},
            "OH": {"sales": 100000, "transactions": 200},
            "OK": {"sales": 100000, "transactions": None},
            "OR": {"sales": None, "transactions": None},  # No sales tax
            "PA": {"sales": 100000, "transactions": None},
            "RI": {"sales": 100000, "transactions": 200},
            "SC": {"sales": 100000, "transactions": None},
            "SD": {"sales": 100000, "transactions": 200},
            "TN": {"sales": 100000, "transactions": None},
            "TX": {"sales": 500000, "transactions": None},
            "UT": {"sales": 100000, "transactions": 200},
            "VT": {"sales": 100000, "transactions": 200},
            "VA": {"sales": 100000, "transactions": 200},
            "WA": {"sales": 100000, "transactions": 200},
            "WV": {"sales": 100000, "transactions": 200},
            "WI": {"sales": 100000, "transactions": 200},
            "WY": {"sales": 100000, "transactions": 200}
        }
        
        # Save to file if doesn't exist
        if not os.path.exists(self.rates_path):
            os.makedirs(os.path.dirname(self.rates_path), exist_ok=True)
            with open(self.rates_path, 'w') as f:
                json.dump(default_rates, f, indent=2)
        
        # Load rates
        with open(self.rates_path, 'r') as f:
            self.sales_tax_rates = json.load(f)
    
    async def calculate_sales_tax(self, client_id: str, period: str, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate sales tax liability by jurisdiction"""
        try:
            # Group transactions by state/jurisdiction
            tax_calculations = {}
            
            for transaction in transactions:
                state = transaction.get('state', 'Unknown')
                jurisdiction = transaction.get('jurisdiction', 'State')
                sale_amount = transaction.get('amount', 0)
                is_taxable = transaction.get('taxable', True)
                
                key = f"{state}_{jurisdiction}"
                
                if key not in tax_calculations:
                    tax_calculations[key] = {
                        'state': state,
                        'jurisdiction': jurisdiction,
                        'gross_sales': 0,
                        'taxable_sales': 0,
                        'exempt_sales': 0,
                        'tax_due': 0
                    }
                
                tax_calculations[key]['gross_sales'] += sale_amount
                
                if is_taxable:
                    tax_calculations[key]['taxable_sales'] += sale_amount
                    
                    # Get tax rate
                    tax_rate = self._get_tax_rate(state, jurisdiction)
                    tax_calculations[key]['tax_due'] += sale_amount * tax_rate
                else:
                    tax_calculations[key]['exempt_sales'] += sale_amount
            
            # Save calculations to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            calculation_results = []
            total_tax_due = 0
            
            for calc in tax_calculations.values():
                tax_rate = self._get_tax_rate(calc['state'], calc['jurisdiction'])
                
                cursor.execute('''
                    INSERT INTO sales_tax_calculations (
                        client_id, period, state, jurisdiction, gross_sales,
                        taxable_sales, exempt_sales, tax_rate, tax_due, calculation_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    client_id, period, calc['state'], calc['jurisdiction'],
                    calc['gross_sales'], calc['taxable_sales'], calc['exempt_sales'],
                    tax_rate, calc['tax_due'], datetime.now().isoformat()
                ))
                
                calc['tax_rate'] = tax_rate
                calculation_results.append(calc)
                total_tax_due += calc['tax_due']
            
            conn.commit()
            conn.close()
            
            # Check for nexus implications
            nexus_alerts = await self._check_nexus_implications(client_id, calculation_results)
            
            # Generate filing requirements
            filing_requirements = self._generate_filing_requirements(client_id, period, calculation_results)
            
            return {
                "client_id": client_id,
                "period": period,
                "total_transactions": len(transactions),
                "total_tax_due": total_tax_due,
                "calculations_by_jurisdiction": calculation_results,
                "nexus_alerts": nexus_alerts,
                "filing_requirements": filing_requirements
            }
            
        except Exception as e:
            return {"error": f"Failed to calculate sales tax: {str(e)}"}
    
    def _get_tax_rate(self, state: str, jurisdiction: str = "State") -> float:
        """Get tax rate for state and jurisdiction"""
        if state not in self.sales_tax_rates:
            return 0.0
        
        state_rates = self.sales_tax_rates[state]
        
        if jurisdiction == "State":
            return state_rates.get('state_rate', 0.0)
        else:
            # For local jurisdictions, use combined average
            return state_rates.get('combined_avg', state_rates.get('state_rate', 0.0))
    
    async def _check_nexus_implications(self, client_id: str, calculations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check if sales create nexus obligations"""
        alerts = []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for calc in calculations:
            state = calc['state']
            
            if state not in self.nexus_thresholds:
                continue
            
            thresholds = self.nexus_thresholds[state]
            
            if thresholds['sales'] is None:  # No sales tax in this state
                continue
            
            # Get current nexus tracking
            cursor.execute('''
                SELECT * FROM nexus_tracking 
                WHERE client_id = ? AND state = ?
            ''', (client_id, state))
            
            nexus_record = cursor.fetchone()
            
            if not nexus_record:
                # Create new nexus tracking record
                cursor.execute('''
                    INSERT INTO nexus_tracking (
                        client_id, state, threshold_amount, threshold_transactions,
                        current_sales, status, created_date, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    client_id, state, thresholds['sales'], thresholds.get('transactions'),
                    calc['gross_sales'], 'monitoring', datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
            else:
                # Update existing record
                new_sales = nexus_record[7] + calc['gross_sales']  # current_sales column
                cursor.execute('''
                    UPDATE nexus_tracking 
                    SET current_sales = ?, last_updated = ?
                    WHERE client_id = ? AND state = ?
                ''', (new_sales, datetime.now().isoformat(), client_id, state))
                
                # Check if thresholds are exceeded
                if new_sales >= thresholds['sales']:
                    alerts.append({
                        "type": "nexus_threshold_exceeded",
                        "state": state,
                        "threshold_type": "sales",
                        "threshold_amount": thresholds['sales'],
                        "current_amount": new_sales,
                        "message": f"Sales threshold exceeded in {state}",
                        "action_required": "Register for sales tax collection"
                    })
                elif new_sales >= thresholds['sales'] * 0.8:  # 80% warning
                    alerts.append({
                        "type": "nexus_threshold_warning",
                        "state": state,
                        "threshold_type": "sales",
                        "threshold_amount": thresholds['sales'],
                        "current_amount": new_sales,
                        "message": f"Approaching sales threshold in {state}",
                        "action_required": "Monitor sales closely"
                    })
        
        conn.commit()
        conn.close()
        
        return alerts
    
    def _generate_filing_requirements(self, client_id: str, period: str, calculations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate filing requirements based on calculations"""
        requirements = []
        
        for calc in calculations:
            state = calc['state']
            
            if calc['tax_due'] > 0:
                # Determine filing frequency based on tax liability
                if calc['tax_due'] > 20000:  # Monthly filers
                    filing_frequency = "monthly"
                    due_date = self._calculate_due_date(period, "monthly")
                elif calc['tax_due'] > 1200:  # Quarterly filers
                    filing_frequency = "quarterly"
                    due_date = self._calculate_due_date(period, "quarterly")
                else:  # Annual filers
                    filing_frequency = "annually"
                    due_date = self._calculate_due_date(period, "annually")
                
                requirements.append({
                    "state": state,
                    "period": period,
                    "filing_frequency": filing_frequency,
                    "due_date": due_date,
                    "tax_due": calc['tax_due'],
                    "taxable_sales": calc['taxable_sales'],
                    "status": "pending"
                })
        
        return requirements
    
    def _calculate_due_date(self, period: str, frequency: str) -> str:
        """Calculate filing due date based on period and frequency"""
        # Parse period (assuming YYYY-MM format)
        year, month = map(int, period.split('-'))
        period_date = datetime(year, month, 1)
        
        if frequency == "monthly":
            # Due 20th of following month
            if month == 12:
                due_date = datetime(year + 1, 1, 20)
            else:
                due_date = datetime(year, month + 1, 20)
        elif frequency == "quarterly":
            # Due 20th of month following quarter end
            quarter_end_months = [3, 6, 9, 12]
            quarter_end = next(m for m in quarter_end_months if m >= month)
            if quarter_end == 12:
                due_date = datetime(year + 1, 1, 20)
            else:
                due_date = datetime(year, quarter_end + 1, 20)
        else:  # annually
            # Due January 31st of following year
            due_date = datetime(year + 1, 1, 31)
        
        return due_date.strftime('%Y-%m-%d')
    
    async def nexus_analysis(self, client_id: str) -> Dict[str, Any]:
        """Analyze nexus obligations across all states"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all nexus tracking records
            cursor.execute('''
                SELECT * FROM nexus_tracking WHERE client_id = ?
                ORDER BY current_sales DESC
            ''', (client_id,))
            
            nexus_records = cursor.fetchall()
            
            # Analyze nexus status
            nexus_analysis = {
                "client_id": client_id,
                "total_states_monitored": len(nexus_records),
                "states_with_nexus": 0,
                "states_approaching_nexus": 0,
                "registration_required": [],
                "monitoring_states": [],
                "compliance_summary": {}
            }
            
            for record in nexus_records:
                state = record[2]  # state column
                current_sales = record[7]  # current_sales column
                threshold_amount = record[4]  # threshold_amount column
                status = record[10]  # status column
                
                state_info = {
                    "state": state,
                    "current_sales": current_sales,
                    "threshold_amount": threshold_amount,
                    "threshold_percentage": (current_sales / threshold_amount * 100) if threshold_amount else 0,
                    "status": status
                }
                
                if current_sales >= threshold_amount:
                    nexus_analysis["states_with_nexus"] += 1
                    nexus_analysis["registration_required"].append(state_info)
                elif current_sales >= threshold_amount * 0.8:
                    nexus_analysis["states_approaching_nexus"] += 1
                    nexus_analysis["monitoring_states"].append(state_info)
                else:
                    nexus_analysis["monitoring_states"].append(state_info)
            
            # Get compliance status
            cursor.execute('''
                SELECT state, COUNT(*) as pending_items
                FROM compliance_monitoring 
                WHERE client_id = ? AND status = 'pending'
                GROUP BY state
            ''', (client_id,))
            
            compliance_data = cursor.fetchall()
            for state, pending_count in compliance_data:
                nexus_analysis["compliance_summary"][state] = {
                    "pending_items": pending_count,
                    "status": "attention_needed" if pending_count > 0 else "compliant"
                }
            
            conn.close()
            
            # Generate recommendations
            recommendations = self._generate_nexus_recommendations(nexus_analysis)
            nexus_analysis["recommendations"] = recommendations
            
            return nexus_analysis
            
        except Exception as e:
            return {"error": f"Failed to analyze nexus: {str(e)}"}
    
    def _generate_nexus_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate nexus-related recommendations"""
        recommendations = []
        
        # Registration recommendations
        for state_info in analysis["registration_required"]:
            recommendations.append({
                "type": "registration_required",
                "priority": "high",
                "state": state_info["state"],
                "title": f"Sales Tax Registration Required - {state_info['state']}",
                "description": f"Sales of ${state_info['current_sales']:,.0f} exceed threshold of ${state_info['threshold_amount']:,.0f}",
                "action": "Register for sales tax collection immediately",
                "deadline": "ASAP - may have retroactive obligations"
            })
        
        # Monitoring recommendations
        for state_info in analysis["monitoring_states"]:
            if state_info["threshold_percentage"] > 50:
                recommendations.append({
                    "type": "nexus_monitoring",
                    "priority": "medium",
                    "state": state_info["state"],
                    "title": f"Monitor Sales Activity - {state_info['state']}",
                    "description": f"Sales at {state_info['threshold_percentage']:.0f}% of nexus threshold",
                    "action": "Continue monitoring sales activity",
                    "deadline": "Ongoing"
                })
        
        # Compliance recommendations
        if analysis["states_with_nexus"] > 0:
            recommendations.append({
                "type": "compliance_system",
                "priority": "high",
                "title": "Implement Sales Tax Compliance System",
                "description": f"Active nexus in {analysis['states_with_nexus']} states requires systematic compliance",
                "action": "Set up automated sales tax calculation and filing system",
                "deadline": "Within 30 days"
            })
        
        return recommendations