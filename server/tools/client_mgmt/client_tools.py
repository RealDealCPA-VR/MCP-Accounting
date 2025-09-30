"""
Client Management Tools for Accounting Practice MCP
Handles client information, deadlines, and profile management
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sqlite3

class ClientManagementTools:
    def __init__(self):
        self.db_path = "server/data/client_profiles/clients.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize the client database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create clients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                client_id TEXT PRIMARY KEY,
                business_name TEXT NOT NULL,
                contact_name TEXT,
                email TEXT,
                phone TEXT,
                entity_type TEXT,
                tax_year_end TEXT,
                industry TEXT,
                state TEXT,
                federal_ein TEXT,
                created_date TEXT,
                last_updated TEXT,
                preferences TEXT
            )
        ''')
        
        # Create deadlines table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_deadlines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT,
                deadline_type TEXT,
                deadline_date TEXT,
                description TEXT,
                status TEXT DEFAULT 'pending',
                created_date TEXT,
                FOREIGN KEY (client_id) REFERENCES clients (client_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def get_client_info(self, client_id: str) -> Dict[str, Any]:
        """Retrieve comprehensive client information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get client basic info
            cursor.execute('SELECT * FROM clients WHERE client_id = ?', (client_id,))
            client_row = cursor.fetchone()
            
            if not client_row:
                return {"error": f"Client {client_id} not found"}
            
            # Convert to dictionary
            columns = [desc[0] for desc in cursor.description]
            client_data = dict(zip(columns, client_row))
            
            # Get upcoming deadlines
            cursor.execute('''
                SELECT deadline_type, deadline_date, description, status 
                FROM client_deadlines 
                WHERE client_id = ? AND deadline_date >= date('now')
                ORDER BY deadline_date
            ''', (client_id,))
            
            deadlines = []
            for row in cursor.fetchall():
                deadlines.append({
                    "type": row[0],
                    "date": row[1],
                    "description": row[2],
                    "status": row[3]
                })
            
            client_data["upcoming_deadlines"] = deadlines
            
            # Parse preferences if they exist
            if client_data.get("preferences"):
                try:
                    client_data["preferences"] = json.loads(client_data["preferences"])
                except:
                    client_data["preferences"] = {}
            
            conn.close()
            return client_data
            
        except Exception as e:
            return {"error": f"Failed to retrieve client info: {str(e)}"}
    
    async def update_client_profile(self, client_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update client profile information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if client exists
            cursor.execute('SELECT client_id FROM clients WHERE client_id = ?', (client_id,))
            if not cursor.fetchone():
                # Create new client
                client_data = {
                    "client_id": client_id,
                    "business_name": updates.get("business_name", ""),
                    "contact_name": updates.get("contact_name", ""),
                    "email": updates.get("email", ""),
                    "phone": updates.get("phone", ""),
                    "entity_type": updates.get("entity_type", ""),
                    "tax_year_end": updates.get("tax_year_end", "12-31"),
                    "industry": updates.get("industry", ""),
                    "state": updates.get("state", ""),
                    "federal_ein": updates.get("federal_ein", ""),
                    "created_date": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "preferences": json.dumps(updates.get("preferences", {}))
                }
                
                cursor.execute('''
                    INSERT INTO clients (client_id, business_name, contact_name, email, phone,
                                       entity_type, tax_year_end, industry, state, federal_ein,
                                       created_date, last_updated, preferences)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(client_data.values()))
                
                result = {"action": "created", "client_id": client_id}
            else:
                # Update existing client
                update_fields = []
                update_values = []
                
                for field, value in updates.items():
                    if field == "preferences":
                        value = json.dumps(value)
                    update_fields.append(f"{field} = ?")
                    update_values.append(value)
                
                update_fields.append("last_updated = ?")
                update_values.append(datetime.now().isoformat())
                update_values.append(client_id)
                
                cursor.execute(f'''
                    UPDATE clients SET {", ".join(update_fields)}
                    WHERE client_id = ?
                ''', update_values)
                
                result = {"action": "updated", "client_id": client_id}
            
            conn.commit()
            conn.close()
            
            # Generate standard deadlines for new clients
            if result["action"] == "created":
                await self._generate_standard_deadlines(client_id, updates.get("entity_type", ""))
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to update client profile: {str(e)}"}
    
    async def get_client_deadlines(self, client_id: str, days_ahead: int = 90) -> Dict[str, Any]:
        """Get upcoming deadlines for a client"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            end_date = (datetime.now() + timedelta(days=days_ahead)).date()
            
            cursor.execute('''
                SELECT deadline_type, deadline_date, description, status
                FROM client_deadlines
                WHERE client_id = ? AND deadline_date BETWEEN date('now') AND ?
                ORDER BY deadline_date
            ''', (client_id, end_date.isoformat()))
            
            deadlines = []
            for row in cursor.fetchall():
                days_until = (datetime.fromisoformat(row[1]).date() - datetime.now().date()).days
                deadlines.append({
                    "type": row[0],
                    "date": row[1],
                    "description": row[2],
                    "status": row[3],
                    "days_until": days_until,
                    "urgency": "critical" if days_until <= 7 else "warning" if days_until <= 30 else "normal"
                })
            
            conn.close()
            
            return {
                "client_id": client_id,
                "deadlines": deadlines,
                "total_count": len(deadlines),
                "critical_count": len([d for d in deadlines if d["urgency"] == "critical"]),
                "warning_count": len([d for d in deadlines if d["urgency"] == "warning"])
            }
            
        except Exception as e:
            return {"error": f"Failed to retrieve deadlines: {str(e)}"}
    
    async def _generate_standard_deadlines(self, client_id: str, entity_type: str):
        """Generate standard tax and compliance deadlines for a new client"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            current_year = datetime.now().year
            deadlines = []
            
            # Common deadlines for all entities
            deadlines.extend([
                ("quarterly_estimates", f"{current_year}-01-15", "Q4 Estimated Tax Payment"),
                ("quarterly_estimates", f"{current_year}-04-15", "Q1 Estimated Tax Payment"),
                ("quarterly_estimates", f"{current_year}-06-15", "Q2 Estimated Tax Payment"),
                ("quarterly_estimates", f"{current_year}-09-15", "Q3 Estimated Tax Payment"),
                ("payroll_deposits", f"{current_year}-01-31", "Q4 Payroll Tax Deposits"),
                ("payroll_941", f"{current_year}-01-31", "Form 941 Q4 Filing"),
                ("payroll_941", f"{current_year}-04-30", "Form 941 Q1 Filing"),
                ("payroll_941", f"{current_year}-07-31", "Form 941 Q2 Filing"),
                ("payroll_941", f"{current_year}-10-31", "Form 941 Q3 Filing"),
            ])
            
            # Entity-specific deadlines
            if entity_type.lower() in ["corporation", "c-corp"]:
                deadlines.extend([
                    ("corporate_return", f"{current_year}-03-15", "Form 1120 Corporate Tax Return"),
                    ("corporate_estimates", f"{current_year}-04-15", "Corporate Estimated Tax Q1"),
                    ("corporate_estimates", f"{current_year}-06-15", "Corporate Estimated Tax Q2"),
                    ("corporate_estimates", f"{current_year}-09-15", "Corporate Estimated Tax Q3"),
                    ("corporate_estimates", f"{current_year}-12-15", "Corporate Estimated Tax Q4"),
                ])
            elif entity_type.lower() in ["s-corp", "s-corporation"]:
                deadlines.extend([
                    ("s_corp_return", f"{current_year}-03-15", "Form 1120S S-Corp Tax Return"),
                    ("k1_distribution", f"{current_year}-03-15", "K-1 Distribution to Shareholders"),
                ])
            elif entity_type.lower() in ["partnership", "llc"]:
                deadlines.extend([
                    ("partnership_return", f"{current_year}-03-15", "Form 1065 Partnership Return"),
                    ("k1_distribution", f"{current_year}-03-15", "K-1 Distribution to Partners"),
                ])
            
            # Insert deadlines
            for deadline_type, date, description in deadlines:
                cursor.execute('''
                    INSERT INTO client_deadlines (client_id, deadline_type, deadline_date, description, created_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (client_id, deadline_type, date, description, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error generating standard deadlines: {str(e)}")