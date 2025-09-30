"""
Payroll Tools for Accounting Practice MCP
Handles payroll calculations, tax withholdings, and compliance reporting
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import sqlite3

class PayrollTools:
    def __init__(self):
        self.db_path = "server/data/client_profiles/payroll.db"
        self._init_database()
        self._load_payroll_tables()
    
    def _init_database(self):
        """Initialize the payroll database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create employees table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                employee_id TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                ssn TEXT,
                address TEXT,
                hire_date TEXT,
                salary_type TEXT,
                salary_amount REAL,
                hourly_rate REAL,
                filing_status TEXT,
                allowances INTEGER DEFAULT 0,
                additional_withholding REAL DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_date TEXT
            )
        ''')
        
        # Create payroll runs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payroll_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                pay_period_start TEXT NOT NULL,
                pay_period_end TEXT NOT NULL,
                pay_date TEXT NOT NULL,
                total_gross REAL,
                total_net REAL,
                total_taxes REAL,
                status TEXT DEFAULT 'draft',
                created_date TEXT,
                processed_date TEXT
            )
        ''')
        
        # Create payroll details table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payroll_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payroll_run_id INTEGER,
                employee_id TEXT NOT NULL,
                hours_worked REAL,
                overtime_hours REAL,
                gross_pay REAL,
                federal_withholding REAL,
                state_withholding REAL,
                social_security REAL,
                medicare REAL,
                unemployment_tax REAL,
                other_deductions REAL,
                net_pay REAL,
                FOREIGN KEY (payroll_run_id) REFERENCES payroll_runs (id)
            )
        ''')
        
        # Create tax deposits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tax_deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                quarter TEXT NOT NULL,
                deposit_date TEXT,
                federal_amount REAL,
                state_amount REAL,
                deposit_type TEXT,
                status TEXT DEFAULT 'pending',
                created_date TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_payroll_tables(self):
        """Load current payroll tax tables and rates"""
        # 2024 Federal tax withholding tables (simplified)
        self.federal_withholding_2024 = {
            'single': [
                {'min': 0, 'max': 3325, 'rate': 0.00, 'base': 0},
                {'min': 3325, 'max': 4817, 'rate': 0.10, 'base': 0},
                {'min': 4817, 'max': 9817, 'rate': 0.12, 'base': 149.20},
                {'min': 9817, 'max': 20817, 'rate': 0.22, 'base': 749.20},
                {'min': 20817, 'max': 43375, 'rate': 0.24, 'base': 3169.20},
                {'min': 43375, 'max': 95375, 'rate': 0.32, 'base': 8583.12},
                {'min': 95375, 'max': 200000, 'rate': 0.35, 'base': 25223.12},
                {'min': 200000, 'max': float('inf'), 'rate': 0.37, 'base': 61835.62}
            ],
            'married': [
                {'min': 0, 'max': 8600, 'rate': 0.00, 'base': 0},
                {'min': 8600, 'max': 11600, 'rate': 0.10, 'base': 0},
                {'min': 11600, 'max': 21600, 'rate': 0.12, 'base': 300},
                {'min': 21600, 'max': 43600, 'rate': 0.22, 'base': 1500},
                {'min': 43600, 'max': 88600, 'rate': 0.24, 'base': 6340},
                {'min': 88600, 'max': 192600, 'rate': 0.32, 'base': 17140},
                {'min': 192600, 'max': 400000, 'rate': 0.35, 'base': 50420},
                {'min': 400000, 'max': float('inf'), 'rate': 0.37, 'base': 123010}
            ]
        }
        
        # Payroll tax rates for 2024
        self.payroll_tax_rates_2024 = {
            'social_security': {'rate': 0.062, 'wage_base': 160200, 'employer_rate': 0.062},
            'medicare': {'rate': 0.0145, 'wage_base': float('inf'), 'employer_rate': 0.0145},
            'additional_medicare': {'rate': 0.009, 'threshold': 200000},
            'federal_unemployment': {'rate': 0.006, 'wage_base': 7000},
            'state_unemployment': {'rate': 0.054, 'wage_base': 7000}  # Varies by state
        }
        
        # Standard deduction amounts for withholding
        self.standard_deduction_2024 = {
            'single': 14600,
            'married': 29200,
            'head_of_household': 21900
        }
    
    async def calculate_payroll(self, client_id: str, pay_period: str, employee_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process payroll calculations including taxes and deductions"""
        try:
            # Parse pay period
            start_date, end_date = pay_period.split(' to ')
            pay_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=3)  # Pay 3 days after period end
            
            # Create payroll run
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO payroll_runs (client_id, pay_period_start, pay_period_end, pay_date, created_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (client_id, start_date, end_date, pay_date.strftime('%Y-%m-%d'), datetime.now().isoformat()))
            
            payroll_run_id = cursor.lastrowid
            
            # Process each employee
            payroll_results = []
            total_gross = 0
            total_net = 0
            total_taxes = 0
            
            for emp_data in employee_data:
                employee_result = await self._calculate_employee_payroll(
                    cursor, payroll_run_id, emp_data, start_date, end_date
                )
                payroll_results.append(employee_result)
                
                total_gross += employee_result['gross_pay']
                total_net += employee_result['net_pay']
                total_taxes += employee_result['total_taxes']
            
            # Update payroll run totals
            cursor.execute('''
                UPDATE payroll_runs 
                SET total_gross = ?, total_net = ?, total_taxes = ?
                WHERE id = ?
            ''', (total_gross, total_net, total_taxes, payroll_run_id))
            
            conn.commit()
            conn.close()
            
            # Generate tax deposit requirements
            deposit_requirements = self._calculate_deposit_requirements(total_taxes, pay_date)
            
            # Generate compliance alerts
            compliance_alerts = self._check_payroll_compliance(client_id, payroll_results)
            
            return {
                "payroll_run_id": payroll_run_id,
                "client_id": client_id,
                "pay_period": pay_period,
                "pay_date": pay_date.strftime('%Y-%m-%d'),
                "employee_count": len(employee_data),
                "total_gross": total_gross,
                "total_net": total_net,
                "total_taxes": total_taxes,
                "employee_details": payroll_results,
                "deposit_requirements": deposit_requirements,
                "compliance_alerts": compliance_alerts
            }
            
        except Exception as e:
            return {"error": f"Failed to calculate payroll: {str(e)}"}
    
    async def _calculate_employee_payroll(self, cursor, payroll_run_id: int, emp_data: Dict[str, Any], start_date: str, end_date: str) -> Dict[str, Any]:
        """Calculate payroll for a single employee"""
        employee_id = emp_data['employee_id']
        hours_worked = emp_data.get('hours_worked', 0)
        overtime_hours = emp_data.get('overtime_hours', 0)
        salary_type = emp_data.get('salary_type', 'hourly')
        
        # Get employee details
        cursor.execute('SELECT * FROM employees WHERE employee_id = ?', (employee_id,))
        employee = cursor.fetchone()
        
        if not employee:
            # Create employee record if doesn't exist
            cursor.execute('''
                INSERT INTO employees (client_id, employee_id, first_name, last_name, 
                                     salary_type, hourly_rate, filing_status, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                emp_data.get('client_id', ''),
                employee_id,
                emp_data.get('first_name', ''),
                emp_data.get('last_name', ''),
                salary_type,
                emp_data.get('hourly_rate', 0),
                emp_data.get('filing_status', 'single'),
                datetime.now().isoformat()
            ))
            
            # Fetch the newly created employee
            cursor.execute('SELECT * FROM employees WHERE employee_id = ?', (employee_id,))
            employee = cursor.fetchone()
        
        # Calculate gross pay
        if salary_type == 'salary':
            # Assume bi-weekly pay periods for salary
            annual_salary = emp_data.get('salary_amount', employee[9] if employee[9] else 0)
            gross_pay = annual_salary / 26  # 26 pay periods per year
        else:
            # Hourly calculation
            hourly_rate = emp_data.get('hourly_rate', employee[10] if employee[10] else 0)
            regular_pay = hours_worked * hourly_rate
            overtime_pay = overtime_hours * hourly_rate * 1.5
            gross_pay = regular_pay + overtime_pay
        
        # Calculate federal withholding
        filing_status = emp_data.get('filing_status', employee[12] if employee[12] else 'single')
        allowances = emp_data.get('allowances', employee[13] if employee[13] else 0)
        additional_withholding = emp_data.get('additional_withholding', employee[14] if employee[14] else 0)
        
        federal_withholding = self._calculate_federal_withholding(
            gross_pay * 26, filing_status, allowances, additional_withholding
        ) / 26  # Convert annual to per-pay-period
        
        # Calculate FICA taxes
        social_security = min(gross_pay, self.payroll_tax_rates_2024['social_security']['wage_base'] / 26) * \
                         self.payroll_tax_rates_2024['social_security']['rate']
        
        medicare = gross_pay * self.payroll_tax_rates_2024['medicare']['rate']
        
        # Additional Medicare tax (if applicable)
        additional_medicare = 0
        annual_gross = gross_pay * 26
        if annual_gross > self.payroll_tax_rates_2024['additional_medicare']['threshold']:
            additional_medicare = gross_pay * self.payroll_tax_rates_2024['additional_medicare']['rate']
        
        # State withholding (simplified - would need state-specific calculations)
        state_withholding = gross_pay * 0.05  # Simplified 5% state tax
        
        # Other deductions
        other_deductions = emp_data.get('other_deductions', 0)
        
        # Calculate net pay
        total_taxes = federal_withholding + social_security + medicare + additional_medicare + state_withholding
        net_pay = gross_pay - total_taxes - other_deductions
        
        # Insert payroll detail record
        cursor.execute('''
            INSERT INTO payroll_details (
                payroll_run_id, employee_id, hours_worked, overtime_hours, gross_pay,
                federal_withholding, state_withholding, social_security, medicare,
                unemployment_tax, other_deductions, net_pay
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            payroll_run_id, employee_id, hours_worked, overtime_hours, gross_pay,
            federal_withholding, state_withholding, social_security, medicare,
            0, other_deductions, net_pay
        ))
        
        return {
            "employee_id": employee_id,
            "employee_name": f"{emp_data.get('first_name', '')} {emp_data.get('last_name', '')}",
            "hours_worked": hours_worked,
            "overtime_hours": overtime_hours,
            "gross_pay": gross_pay,
            "federal_withholding": federal_withholding,
            "state_withholding": state_withholding,
            "social_security": social_security,
            "medicare": medicare,
            "additional_medicare": additional_medicare,
            "other_deductions": other_deductions,
            "total_taxes": total_taxes,
            "net_pay": net_pay
        }
    
    def _calculate_federal_withholding(self, annual_gross: float, filing_status: str, allowances: int, additional: float) -> float:
        """Calculate federal income tax withholding"""
        # Adjust for allowances (simplified)
        allowance_amount = allowances * 4300  # 2024 allowance amount
        taxable_income = max(0, annual_gross - allowance_amount - self.standard_deduction_2024.get(filing_status, 14600))
        
        # Use withholding tables
        brackets = self.federal_withholding_2024.get(filing_status, self.federal_withholding_2024['single'])
        
        withholding = 0
        for bracket in brackets:
            if taxable_income <= bracket['min']:
                break
            
            taxable_in_bracket = min(taxable_income, bracket['max']) - bracket['min']
            withholding = bracket['base'] + (taxable_in_bracket * bracket['rate'])
        
        return withholding + additional
    
    def _calculate_deposit_requirements(self, total_taxes: float, pay_date: datetime) -> Dict[str, Any]:
        """Calculate required tax deposits"""
        # Federal deposit requirements
        if total_taxes >= 100000:
            deposit_schedule = "next_business_day"
            deposit_date = pay_date + timedelta(days=1)
        elif total_taxes >= 50000:
            deposit_schedule = "semi_weekly"
            # Wednesday-Friday paydays deposit by next Wednesday
            # Saturday-Tuesday paydays deposit by next Friday
            if pay_date.weekday() in [2, 3, 4]:  # Wed-Fri
                deposit_date = pay_date + timedelta(days=(9 - pay_date.weekday()))
            else:  # Sat-Tue
                deposit_date = pay_date + timedelta(days=(11 - pay_date.weekday()) % 7)
        else:
            deposit_schedule = "monthly"
            # Deposit by 15th of following month
            next_month = pay_date.replace(day=1) + timedelta(days=32)
            deposit_date = next_month.replace(day=15)
        
        return {
            "total_amount": total_taxes,
            "deposit_schedule": deposit_schedule,
            "deposit_date": deposit_date.strftime('%Y-%m-%d'),
            "federal_amount": total_taxes * 0.9,  # Approximate federal portion
            "state_amount": total_taxes * 0.1     # Approximate state portion
        }
    
    def _check_payroll_compliance(self, client_id: str, payroll_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for payroll compliance issues"""
        alerts = []
        
        # Check for minimum wage violations
        federal_minimum_wage = 7.25
        for emp in payroll_results:
            if emp['hours_worked'] > 0:
                effective_rate = emp['gross_pay'] / emp['hours_worked']
                if effective_rate < federal_minimum_wage:
                    alerts.append({
                        "type": "minimum_wage_violation",
                        "severity": "high",
                        "employee_id": emp['employee_id'],
                        "message": f"Effective rate ${effective_rate:.2f} below federal minimum wage",
                        "recommendation": "Review hourly rate and ensure compliance"
                    })
        
        # Check for overtime compliance
        for emp in payroll_results:
            if emp['hours_worked'] > 40 and emp['overtime_hours'] == 0:
                alerts.append({
                    "type": "overtime_compliance",
                    "severity": "medium",
                    "employee_id": emp['employee_id'],
                    "message": f"Employee worked {emp['hours_worked']} hours with no overtime recorded",
                    "recommendation": "Verify overtime exemption status or correct hours"
                })
        
        # Check for large withholding amounts
        for emp in payroll_results:
            withholding_rate = emp['total_taxes'] / emp['gross_pay'] if emp['gross_pay'] > 0 else 0
            if withholding_rate > 0.5:  # More than 50% withholding
                alerts.append({
                    "type": "high_withholding",
                    "severity": "low",
                    "employee_id": emp['employee_id'],
                    "message": f"High withholding rate: {withholding_rate:.1%}",
                    "recommendation": "Review withholding elections and deductions"
                })
        
        return alerts