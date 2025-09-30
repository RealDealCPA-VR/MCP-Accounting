"""
Tax Tools for Accounting Practice MCP
Handles tax calculations, planning, deduction optimization, and compliance
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import sqlite3

class TaxTools:
    def __init__(self):
        self.db_path = "server/data/client_profiles/tax_data.db"
        self.tax_tables_path = "server/data/tax_tables"
        self._init_database()
        self._load_tax_tables()
    
    def _init_database(self):
        """Initialize the tax database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tax calculations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tax_calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                tax_year INTEGER NOT NULL,
                entity_type TEXT,
                calculation_type TEXT,
                gross_income REAL,
                adjusted_gross_income REAL,
                taxable_income REAL,
                federal_tax REAL,
                state_tax REAL,
                self_employment_tax REAL,
                total_tax REAL,
                effective_rate REAL,
                marginal_rate REAL,
                calculation_date TEXT,
                notes TEXT
            )
        ''')
        
        # Create deductions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deductions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                tax_year INTEGER NOT NULL,
                deduction_type TEXT NOT NULL,
                category TEXT,
                description TEXT,
                amount REAL NOT NULL,
                documentation_status TEXT DEFAULT 'pending',
                created_date TEXT,
                notes TEXT
            )
        ''')
        
        # Create tax strategies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tax_strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                tax_year INTEGER NOT NULL,
                strategy_type TEXT NOT NULL,
                description TEXT,
                estimated_savings REAL,
                implementation_status TEXT DEFAULT 'recommended',
                deadline_date TEXT,
                created_date TEXT,
                notes TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_tax_tables(self):
        """Load current tax tables and rates"""
        os.makedirs(self.tax_tables_path, exist_ok=True)
        
        # 2024 Federal Tax Brackets (Single)
        self.federal_brackets_2024 = {
            'single': [
                {'min': 0, 'max': 11600, 'rate': 0.10},
                {'min': 11600, 'max': 47150, 'rate': 0.12},
                {'min': 47150, 'max': 100525, 'rate': 0.22},
                {'min': 100525, 'max': 191050, 'rate': 0.24},
                {'min': 191050, 'max': 243725, 'rate': 0.32},
                {'min': 243725, 'max': 609350, 'rate': 0.35},
                {'min': 609350, 'max': float('inf'), 'rate': 0.37}
            ],
            'married_joint': [
                {'min': 0, 'max': 23200, 'rate': 0.10},
                {'min': 23200, 'max': 94300, 'rate': 0.12},
                {'min': 94300, 'max': 201050, 'rate': 0.22},
                {'min': 201050, 'max': 383900, 'rate': 0.24},
                {'min': 383900, 'max': 487450, 'rate': 0.32},
                {'min': 487450, 'max': 731200, 'rate': 0.35},
                {'min': 731200, 'max': float('inf'), 'rate': 0.37}
            ]
        }
        
        # Standard deductions for 2024
        self.standard_deductions_2024 = {
            'single': 14600,
            'married_joint': 29200,
            'married_separate': 14600,
            'head_of_household': 21900
        }
        
        # Self-employment tax rates
        self.se_tax_rates = {
            'social_security': {'rate': 0.124, 'wage_base': 160200},
            'medicare': {'rate': 0.029, 'wage_base': float('inf')},
            'additional_medicare': {'rate': 0.009, 'threshold_single': 200000, 'threshold_joint': 250000}
        }
        
        # Section 179 limits for 2024
        self.section_179_2024 = {
            'max_deduction': 1220000,
            'phase_out_threshold': 3050000
        }
    
    async def calculate_tax_liability(self, client_id: str, tax_year: int, projection_method: str = "ytd_annualized") -> Dict[str, Any]:
        """Calculate estimated tax liability for current year"""
        try:
            # Get client information
            client_conn = sqlite3.connect("server/data/client_profiles/clients.db")
            client_cursor = client_conn.cursor()
            client_cursor.execute('SELECT entity_type, state FROM clients WHERE client_id = ?', (client_id,))
            client_info = client_cursor.fetchone()
            client_conn.close()
            
            if not client_info:
                return {"error": f"Client {client_id} not found"}
            
            entity_type, state = client_info
            
            # Get financial data based on projection method
            financial_data = await self._get_financial_projection(client_id, tax_year, projection_method)
            
            if "error" in financial_data:
                return financial_data
            
            # Calculate taxes based on entity type
            if entity_type.lower() in ['sole_proprietorship', 'single_member_llc']:
                tax_calc = self._calculate_individual_tax(financial_data, 'single', state)
            elif entity_type.lower() in ['s_corp', 's_corporation']:
                tax_calc = self._calculate_s_corp_tax(financial_data, state)
            elif entity_type.lower() in ['corporation', 'c_corp']:
                tax_calc = self._calculate_corporate_tax(financial_data, state)
            elif entity_type.lower() in ['partnership', 'multi_member_llc']:
                tax_calc = self._calculate_partnership_tax(financial_data, state)
            else:
                return {"error": f"Unsupported entity type: {entity_type}"}
            
            # Save calculation to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tax_calculations (
                    client_id, tax_year, entity_type, calculation_type, gross_income,
                    adjusted_gross_income, taxable_income, federal_tax, state_tax,
                    self_employment_tax, total_tax, effective_rate, marginal_rate,
                    calculation_date, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                client_id, tax_year, entity_type, projection_method,
                tax_calc['gross_income'], tax_calc['adjusted_gross_income'],
                tax_calc['taxable_income'], tax_calc['federal_tax'],
                tax_calc['state_tax'], tax_calc.get('self_employment_tax', 0),
                tax_calc['total_tax'], tax_calc['effective_rate'],
                tax_calc['marginal_rate'], datetime.now().isoformat(),
                f"Projection method: {projection_method}"
            ))
            conn.commit()
            conn.close()
            
            # Add quarterly estimate recommendations
            quarterly_estimates = self._calculate_quarterly_estimates(tax_calc['total_tax'])
            tax_calc['quarterly_estimates'] = quarterly_estimates
            
            # Add tax planning recommendations
            tax_calc['recommendations'] = await self._generate_tax_recommendations(
                client_id, tax_year, tax_calc, entity_type
            )
            
            return tax_calc
            
        except Exception as e:
            return {"error": f"Failed to calculate tax liability: {str(e)}"}
    
    async def _get_financial_projection(self, client_id: str, tax_year: int, method: str) -> Dict[str, Any]:
        """Get financial data projection based on method"""
        try:
            # Get transaction data from bookkeeping
            bookkeeping_conn = sqlite3.connect("server/data/client_profiles/bookkeeping.db")
            cursor = bookkeeping_conn.cursor()
            
            if method == "ytd_annualized":
                # Get YTD data and annualize
                current_date = datetime.now()
                start_date = f"{tax_year}-01-01"
                end_date = current_date.strftime('%Y-%m-%d')
                
                cursor.execute('''
                    SELECT category, SUM(amount) as total
                    FROM transactions
                    WHERE client_id = ? AND transaction_date >= ? AND transaction_date <= ?
                    GROUP BY category
                ''', (client_id, start_date, end_date))
                
                ytd_data = cursor.fetchall()
                
                # Annualize based on days elapsed
                days_elapsed = (current_date - datetime(tax_year, 1, 1)).days
                annualization_factor = 365 / days_elapsed if days_elapsed > 0 else 1
                
                income = 0
                expenses = 0
                
                for category, total in ytd_data:
                    annualized_amount = total * annualization_factor
                    if total > 0:  # Income
                        income += annualized_amount
                    else:  # Expenses
                        expenses += abs(annualized_amount)
                
            elif method == "prior_year":
                # Use prior year data
                prior_year = tax_year - 1
                start_date = f"{prior_year}-01-01"
                end_date = f"{prior_year}-12-31"
                
                cursor.execute('''
                    SELECT category, SUM(amount) as total
                    FROM transactions
                    WHERE client_id = ? AND transaction_date >= ? AND transaction_date <= ?
                    GROUP BY category
                ''', (client_id, start_date, end_date))
                
                prior_data = cursor.fetchall()
                
                income = 0
                expenses = 0
                
                for category, total in prior_data:
                    if total > 0:  # Income
                        income += total
                    else:  # Expenses
                        expenses += abs(total)
            
            else:
                return {"error": f"Unsupported projection method: {method}"}
            
            bookkeeping_conn.close()
            
            return {
                "gross_income": income,
                "total_expenses": expenses,
                "net_income": income - expenses,
                "projection_method": method
            }
            
        except Exception as e:
            return {"error": f"Failed to get financial projection: {str(e)}"}
    
    def _calculate_individual_tax(self, financial_data: Dict[str, Any], filing_status: str, state: str) -> Dict[str, Any]:
        """Calculate individual income tax"""
        gross_income = financial_data['gross_income']
        business_expenses = financial_data['total_expenses']
        
        # Calculate AGI
        adjusted_gross_income = gross_income - business_expenses
        
        # Standard deduction
        standard_deduction = self.standard_deductions_2024.get(filing_status, self.standard_deductions_2024['single'])
        
        # Taxable income
        taxable_income = max(0, adjusted_gross_income - standard_deduction)
        
        # Federal income tax
        federal_tax = self._calculate_federal_tax(taxable_income, filing_status)
        
        # Self-employment tax
        se_tax = self._calculate_self_employment_tax(financial_data['net_income'])
        
        # State tax (simplified - would need state-specific calculations)
        state_tax = taxable_income * 0.05 if state and state != 'TX' else 0  # Simplified
        
        total_tax = federal_tax + se_tax + state_tax
        effective_rate = total_tax / adjusted_gross_income if adjusted_gross_income > 0 else 0
        marginal_rate = self._get_marginal_rate(taxable_income, filing_status)
        
        return {
            "gross_income": gross_income,
            "business_expenses": business_expenses,
            "adjusted_gross_income": adjusted_gross_income,
            "standard_deduction": standard_deduction,
            "taxable_income": taxable_income,
            "federal_tax": federal_tax,
            "self_employment_tax": se_tax,
            "state_tax": state_tax,
            "total_tax": total_tax,
            "effective_rate": effective_rate,
            "marginal_rate": marginal_rate
        }
    
    def _calculate_federal_tax(self, taxable_income: float, filing_status: str) -> float:
        """Calculate federal income tax using tax brackets"""
        brackets = self.federal_brackets_2024.get(filing_status, self.federal_brackets_2024['single'])
        
        tax = 0
        for bracket in brackets:
            if taxable_income <= bracket['min']:
                break
            
            taxable_in_bracket = min(taxable_income, bracket['max']) - bracket['min']
            tax += taxable_in_bracket * bracket['rate']
        
        return tax
    
    def _calculate_self_employment_tax(self, net_earnings: float) -> float:
        """Calculate self-employment tax"""
        if net_earnings <= 0:
            return 0
        
        # 92.35% of net earnings subject to SE tax
        se_income = net_earnings * 0.9235
        
        # Social Security tax
        ss_tax = min(se_income, self.se_tax_rates['social_security']['wage_base']) * \
                 self.se_tax_rates['social_security']['rate']
        
        # Medicare tax
        medicare_tax = se_income * self.se_tax_rates['medicare']['rate']
        
        # Additional Medicare tax (if applicable)
        additional_medicare = 0
        if se_income > self.se_tax_rates['additional_medicare']['threshold_single']:
            additional_medicare = (se_income - self.se_tax_rates['additional_medicare']['threshold_single']) * \
                                self.se_tax_rates['additional_medicare']['rate']
        
        return ss_tax + medicare_tax + additional_medicare
    
    def _calculate_s_corp_tax(self, financial_data: Dict[str, Any], state: str) -> Dict[str, Any]:
        """Calculate S-Corp tax (pass-through entity)"""
        # S-Corp income passes through to owners
        # This is a simplified calculation - would need ownership percentages
        
        gross_income = financial_data['gross_income']
        business_expenses = financial_data['total_expenses']
        net_income = financial_data['net_income']
        
        # Assume reasonable salary for owner (simplified)
        reasonable_salary = min(net_income * 0.4, 100000)  # 40% or $100k max
        
        # Payroll taxes on salary
        payroll_tax = reasonable_salary * 0.153  # Combined employer/employee
        
        # Remaining income is distribution (no SE tax)
        distribution = net_income - reasonable_salary
        
        # Federal tax on pass-through income (at individual rates)
        federal_tax = self._calculate_federal_tax(net_income, 'single')  # Simplified
        
        # State tax
        state_tax = net_income * 0.05 if state and state != 'TX' else 0
        
        total_tax = federal_tax + payroll_tax + state_tax
        effective_rate = total_tax / gross_income if gross_income > 0 else 0
        
        return {
            "gross_income": gross_income,
            "business_expenses": business_expenses,
            "adjusted_gross_income": net_income,
            "taxable_income": net_income,
            "reasonable_salary": reasonable_salary,
            "distribution": distribution,
            "federal_tax": federal_tax,
            "payroll_tax": payroll_tax,
            "state_tax": state_tax,
            "total_tax": total_tax,
            "effective_rate": effective_rate,
            "marginal_rate": self._get_marginal_rate(net_income, 'single')
        }
    
    def _calculate_corporate_tax(self, financial_data: Dict[str, Any], state: str) -> Dict[str, Any]:
        """Calculate C-Corp tax"""
        gross_income = financial_data['gross_income']
        business_expenses = financial_data['total_expenses']
        taxable_income = financial_data['net_income']
        
        # Federal corporate tax rate (flat 21%)
        federal_tax = taxable_income * 0.21
        
        # State corporate tax (simplified)
        state_tax = taxable_income * 0.06 if state and state != 'TX' else 0
        
        total_tax = federal_tax + state_tax
        effective_rate = total_tax / gross_income if gross_income > 0 else 0
        
        return {
            "gross_income": gross_income,
            "business_expenses": business_expenses,
            "adjusted_gross_income": taxable_income,
            "taxable_income": taxable_income,
            "federal_tax": federal_tax,
            "state_tax": state_tax,
            "total_tax": total_tax,
            "effective_rate": effective_rate,
            "marginal_rate": 0.21  # Flat corporate rate
        }
    
    def _calculate_partnership_tax(self, financial_data: Dict[str, Any], state: str) -> Dict[str, Any]:
        """Calculate partnership tax (pass-through)"""
        # Similar to S-Corp but with SE tax on all income
        gross_income = financial_data['gross_income']
        business_expenses = financial_data['total_expenses']
        net_income = financial_data['net_income']
        
        # Federal tax (pass-through to partners)
        federal_tax = self._calculate_federal_tax(net_income, 'single')  # Simplified
        
        # Self-employment tax on all income
        se_tax = self._calculate_self_employment_tax(net_income)
        
        # State tax
        state_tax = net_income * 0.05 if state and state != 'TX' else 0
        
        total_tax = federal_tax + se_tax + state_tax
        effective_rate = total_tax / gross_income if gross_income > 0 else 0
        
        return {
            "gross_income": gross_income,
            "business_expenses": business_expenses,
            "adjusted_gross_income": net_income,
            "taxable_income": net_income,
            "federal_tax": federal_tax,
            "self_employment_tax": se_tax,
            "state_tax": state_tax,
            "total_tax": total_tax,
            "effective_rate": effective_rate,
            "marginal_rate": self._get_marginal_rate(net_income, 'single')
        }
    
    def _get_marginal_rate(self, taxable_income: float, filing_status: str) -> float:
        """Get marginal tax rate for given income"""
        brackets = self.federal_brackets_2024.get(filing_status, self.federal_brackets_2024['single'])
        
        for bracket in brackets:
            if taxable_income <= bracket['max']:
                return bracket['rate']
        
        return brackets[-1]['rate']  # Highest bracket
    
    def _calculate_quarterly_estimates(self, annual_tax: float) -> Dict[str, Any]:
        """Calculate quarterly estimated tax payments"""
        quarterly_amount = annual_tax / 4
        
        current_year = datetime.now().year
        
        return {
            "quarterly_amount": quarterly_amount,
            "annual_total": annual_tax,
            "due_dates": [
                f"{current_year}-04-15",  # Q1
                f"{current_year}-06-15",  # Q2
                f"{current_year}-09-15",  # Q3
                f"{current_year + 1}-01-15"  # Q4
            ],
            "safe_harbor_amount": annual_tax * 1.1  # 110% of prior year
        }
    
    async def _generate_tax_recommendations(self, client_id: str, tax_year: int, tax_calc: Dict[str, Any], entity_type: str) -> List[Dict[str, Any]]:
        """Generate tax planning recommendations"""
        recommendations = []
        
        # High-level recommendations based on tax calculation
        if tax_calc['effective_rate'] > 0.25:
            recommendations.append({
                "type": "tax_reduction",
                "priority": "high",
                "title": "High Tax Rate - Consider Tax Strategies",
                "description": "Your effective tax rate is above 25%. Consider retirement contributions, equipment purchases, or entity restructuring.",
                "estimated_savings": tax_calc['total_tax'] * 0.1
            })
        
        if entity_type.lower() in ['sole_proprietorship', 'single_member_llc'] and tax_calc['gross_income'] > 100000:
            recommendations.append({
                "type": "entity_election",
                "priority": "medium",
                "title": "Consider S-Corp Election",
                "description": "With your income level, an S-Corp election could save on self-employment taxes.",
                "estimated_savings": tax_calc.get('self_employment_tax', 0) * 0.5
            })
        
        if tax_calc['taxable_income'] > 50000:
            recommendations.append({
                "type": "retirement_planning",
                "priority": "medium",
                "title": "Maximize Retirement Contributions",
                "description": "Consider maximizing SEP-IRA or Solo 401(k) contributions to reduce taxable income.",
                "estimated_savings": min(66000, tax_calc['taxable_income'] * 0.25) * tax_calc['marginal_rate']
            })
        
        return recommendations
    
    async def optimize_deductions(self, client_id: str, tax_year: int, expense_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze expenses and recommend optimal deduction strategies"""
        try:
            # Get expense data from bookkeeping if not provided
            if not expense_data:
                bookkeeping_conn = sqlite3.connect("server/data/client_profiles/bookkeeping.db")
                cursor = bookkeeping_conn.cursor()
                
                cursor.execute('''
                    SELECT category, subcategory, SUM(ABS(amount)) as total
                    FROM transactions
                    WHERE client_id = ? AND transaction_date LIKE ? AND amount < 0
                    GROUP BY category, subcategory
                    ORDER BY total DESC
                ''', (client_id, f"{tax_year}%"))
                
                expense_data = {}
                for category, subcategory, total in cursor.fetchall():
                    if category not in expense_data:
                        expense_data[category] = {}
                    expense_data[category][subcategory] = total
                
                bookkeeping_conn.close()
            
            # Analyze deductions and provide recommendations
            deduction_analysis = {
                "total_expenses": sum(sum(subcats.values()) for subcats in expense_data.values()),
                "categories": {},
                "recommendations": [],
                "potential_issues": []
            }
            
            for category, subcategories in expense_data.items():
                category_total = sum(subcategories.values())
                deduction_analysis["categories"][category] = {
                    "total": category_total,
                    "subcategories": subcategories,
                    "deductibility": self._assess_deductibility(category, subcategories),
                    "documentation_needed": self._get_documentation_requirements(category)
                }
                
                # Generate specific recommendations
                recommendations = self._generate_deduction_recommendations(category, subcategories, category_total)
                deduction_analysis["recommendations"].extend(recommendations)
            
            # Check for potential Section 179 opportunities
            equipment_expenses = expense_data.get("Equipment", {})
            if equipment_expenses:
                section_179_analysis = self._analyze_section_179(equipment_expenses)
                if section_179_analysis["eligible_amount"] > 0:
                    deduction_analysis["recommendations"].append({
                        "type": "section_179",
                        "priority": "high",
                        "title": "Section 179 Deduction Opportunity",
                        "description": f"Consider Section 179 deduction for ${section_179_analysis['eligible_amount']:,.0f} in equipment purchases",
                        "estimated_savings": section_179_analysis["estimated_savings"]
                    })
            
            return deduction_analysis
            
        except Exception as e:
            return {"error": f"Failed to optimize deductions: {str(e)}"}
    
    def _assess_deductibility(self, category: str, subcategories: Dict[str, float]) -> Dict[str, Any]:
        """Assess the deductibility of expense categories"""
        deductibility_rules = {
            "Office Supplies": {"percentage": 100, "notes": "Fully deductible if used for business"},
            "Travel": {"percentage": 100, "notes": "Business travel is fully deductible"},
            "Meals & Entertainment": {"percentage": 50, "notes": "Generally 50% deductible for business meals"},
            "Vehicle Expenses": {"percentage": 100, "notes": "Business use percentage applies"},
            "Professional Services": {"percentage": 100, "notes": "Fully deductible business expenses"},
            "Utilities": {"percentage": 100, "notes": "Business portion is deductible"},
            "Insurance": {"percentage": 100, "notes": "Business insurance is fully deductible"},
            "Marketing": {"percentage": 100, "notes": "Advertising and marketing expenses are deductible"}
        }
        
        return deductibility_rules.get(category, {"percentage": 100, "notes": "Review for business purpose"})
    
    def _get_documentation_requirements(self, category: str) -> List[str]:
        """Get documentation requirements for expense categories"""
        doc_requirements = {
            "Travel": ["Receipts", "Business purpose", "Dates and locations"],
            "Meals & Entertainment": ["Receipts", "Business purpose", "Attendees", "Business relationship"],
            "Vehicle Expenses": ["Mileage log", "Business purpose", "Receipts for expenses"],
            "Equipment": ["Receipts", "Business use percentage", "Depreciation records"],
            "Professional Services": ["Invoices", "Contracts", "Business purpose"],
            "Office Supplies": ["Receipts", "Business use verification"]
        }
        
        return doc_requirements.get(category, ["Receipts", "Business purpose documentation"])
    
    def _generate_deduction_recommendations(self, category: str, subcategories: Dict[str, float], total: float) -> List[Dict[str, Any]]:
        """Generate specific recommendations for expense categories"""
        recommendations = []
        
        if category == "Meals & Entertainment" and total > 5000:
            recommendations.append({
                "type": "meals_optimization",
                "priority": "medium",
                "title": "Optimize Meal Deductions",
                "description": f"${total:,.0f} in meals - ensure proper documentation for 50% deduction",
                "estimated_impact": total * 0.5 * 0.25  # 50% deductible at 25% tax rate
            })
        
        if category == "Vehicle Expenses" and total > 10000:
            recommendations.append({
                "type": "vehicle_method",
                "priority": "medium",
                "title": "Compare Vehicle Deduction Methods",
                "description": "Compare actual expense method vs. standard mileage rate",
                "estimated_impact": total * 0.1  # Potential 10% improvement
            })
        
        if category == "Equipment" and total > 2500:
            recommendations.append({
                "type": "depreciation_strategy",
                "priority": "high",
                "title": "Equipment Depreciation Strategy",
                "description": f"${total:,.0f} in equipment - consider Section 179 vs. bonus depreciation",
                "estimated_impact": total * 0.25  # Immediate deduction vs. depreciation
            })
        
        return recommendations
    
    def _analyze_section_179(self, equipment_expenses: Dict[str, float]) -> Dict[str, Any]:
        """Analyze Section 179 deduction opportunities"""
        total_equipment = sum(equipment_expenses.values())
        
        # Section 179 limits for 2024
        max_deduction = self.section_179_2024['max_deduction']
        phase_out_threshold = self.section_179_2024['phase_out_threshold']
        
        eligible_amount = min(total_equipment, max_deduction)
        
        # Simplified tax savings calculation (would need actual tax rate)
        estimated_savings = eligible_amount * 0.25  # Assume 25% tax rate
        
        return {
            "total_equipment": total_equipment,
            "eligible_amount": eligible_amount,
            "max_deduction": max_deduction,
            "estimated_savings": estimated_savings,
            "phase_out_applies": total_equipment > phase_out_threshold
        }