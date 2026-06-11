"""
skills/110_employee_master.py
Employee Master Register Pipeline.
Provides CLI functionalities to register, view, and modify employee (tb_login) records.
"""

import os
import sys
from datetime import date
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Set project root path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core import db_client

def print_header():
    print("=" * 60)
    print("             EMPLOYEE MASTER REGISTRATION PIPELINE")
    print("=" * 60)

def create_employee(login, password, firstname, surname, role="Welder", right_level=1, bay=None, shop_label=None, site_safe=None):
    exists = db_client.fetch_one("SELECT id FROM tb_login WHERE login = ?", (login,))
    if exists:
        raise ValueError(f"Login ID '{login}' already exists.")
        
    hashed_pw = pwd_context.hash(password)
    db_client.execute_query(
        """
        INSERT INTO tb_login (
            login, password, firstname, surname, avatar, bay, 
            date_creation, role, right_level, shop_label, admin_validation,
            site_safe_passport, first_aid
        ) VALUES (?, ?, ?, ?, 'default.png', ?, ?, ?, ?, ?, 1, ?, 0)
        """,
        (login, hashed_pw, firstname, surname, bay, date.today().isoformat(), role, right_level, shop_label, site_safe)
    )

def register_employee():
    print("\n--- Register New Employee ---")
    login = input("Enter Login ID: ").strip()
    if not login:
        print("Login ID cannot be empty.")
        return
        
    print("Password will be automatically set to: 12345678")
    password = "12345678"
    firstname = input("Enter First Name: ").strip()
    surname = input("Enter Surname: ").strip()
    role = input("Enter Role (e.g., Welder, Supervisor, Admin): ").strip()
    
    right_level_str = input("Enter Right Level (1 for User, 10 for Admin): ").strip()
    right_level = int(right_level_str) if right_level_str.isdigit() else 1
    
    bay_str = input("Enter Bay Number (integer or press enter for NULL): ").strip()
    bay = int(bay_str) if bay_str.isdigit() else None
    
    shop_label = input("Enter Shop Label (1 character, e.g. A, B, or enter for NULL): ").strip()
    shop_label = shop_label[0] if shop_label else None
    
    site_safe = input("Enter Site Safe Passport (or press enter): ").strip()
    site_safe = site_safe if site_safe else None
    
    print("\nRegistering employee...")
    try:
        create_employee(login, password, firstname, surname, role, right_level, bay, shop_label, site_safe)
        print("Employee registered successfully.")
    except Exception as e:
        print(f"Error registering employee: {str(e)}")

def view_employees():
    print("\n--- Employee List ---")
    try:
        employees = db_client.fetch_all(
            "SELECT id, login, firstname, surname, role, right_level, bay FROM tb_login ORDER BY id ASC"
        )
        if not employees:
            print("No employees found.")
            return
            
        print(f"{'ID':<4} | {'LOGIN':<15} | {'NAME':<20} | {'ROLE':<15} | {'LEVEL':<5} | {'BAY'}")
        print("-" * 70)
        for emp in employees:
            name = f"{emp['firstname']} {emp['surname']}"
            bay_val = emp['bay'] if emp['bay'] is not None else "NULL"
            print(f"{emp['id']:<4} | {emp['login']:<15} | {name:<20} | {str(emp['role']):<15} | {emp['right_level']:<5} | {bay_val}")
    except Exception as e:
        print(f"Error reading employees: {str(e)}")

def main():
    while True:
        print_header()
        print(" [1] View Employee List")
        print(" [2] Register New Employee")
        print(" [0] Return to Main Menu")
        choice = input("Select operation: ").strip()
        
        if choice == "1":
            view_employees()
        elif choice == "2":
            register_employee()
        elif choice == "0" or not choice:
            break
        else:
            print("Invalid choice.")
        
        input("\nPress Enter to continue...")
        print("\n" * 2)

if __name__ == "__main__":
    main()
