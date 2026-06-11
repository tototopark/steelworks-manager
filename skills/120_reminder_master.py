"""
skills/120_reminder_master.py
Vehicle & Reminder Master Register Pipeline.
Provides CLI functionalities to register and monitor vehicles (tb_reminder_vehicle) and general reminders (tb_reminder_other).
"""

import os
import sys
from datetime import date

# Set project root path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core import db_client

def print_header():
    print("=" * 60)
    print("         VEHICLE & REMINDER MASTER REGISTRATION PIPELINE")
    print("=" * 60)

def register_vehicle():
    print("\n--- Register New Vehicle ---")
    vehicle = input("Enter Vehicle Model/Name: ").strip()
    plate = input("Enter License Plate: ").strip()
    if not vehicle or not plate:
        print("Vehicle name and License Plate cannot be empty.")
        return
        
    wof = input("Enter WOF Expiry Date (YYYY-MM-DD, or enter for NULL): ").strip()
    rego = input("Enter REGO Expiry Date (YYYY-MM-DD, or enter for NULL): ").strip()
    service_str = input("Enter Service Odometer Limit (integer, or enter for NULL): ").strip()
    ruc_str = input("Enter RUC Odometer Limit (integer, or enter for NULL): ").strip()
    current_odo_str = input("Enter Current Odometer (integer, or enter for NULL): ").strip()
    
    wof = wof if wof else None
    rego = rego if rego else None
    service = int(service_str) if service_str.isdigit() else None
    ruc = int(ruc_str) if ruc_str.isdigit() else None
    current_odo = int(current_odo_str) if current_odo_str.isdigit() else None
    
    print("\nRegistering vehicle...")
    try:
        db_client.execute_query(
            """
            INSERT INTO tb_reminder_vehicle (
                Vehicle, Plate, WOF, REGO, SERVICE, RUC, Current_ODO, VeederEroad
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (vehicle, plate, wof, rego, service, ruc, current_odo)
        )
        print("Vehicle registered successfully.")
    except Exception as e:
        print(f"Error registering vehicle: {str(e)}")

def register_other_reminder():
    print("\n--- Register General Reminder ---")
    name = input("Enter Reminder Title/Name: ").strip()
    comment = input("Enter Comment/Details: ").strip()
    expiry = input("Enter Expiry Date (YYYY-MM-DD, or enter for NULL): ").strip()
    
    name = name if name else None
    comment = comment if comment else None
    expiry = expiry if expiry else None
    
    try:
        db_client.execute_query(
            """
            INSERT INTO tb_reminder_other (name, comment, expiry_date)
            VALUES (?, ?, ?)
            """,
            (name, comment, expiry)
        )
        print("General reminder registered successfully.")
    except Exception as e:
        print(f"Error registering reminder: {str(e)}")

def view_reminders():
    print("\n--- Vehicles Reminders List ---")
    try:
        vehicles = db_client.fetch_all("SELECT * FROM tb_reminder_vehicle ORDER BY id ASC")
        if not vehicles:
            print("No vehicles registered.")
        else:
            print(f"{'ID':<3} | {'VEHICLE':<15} | {'PLATE':<8} | {'WOF EXP':<10} | {'REGO EXP':<10} | {'ODO':<8}")
            print("-" * 70)
            for v in vehicles:
                print(f"{v['id']:<3} | {v['Vehicle'][:15]:<15} | {v['Plate']:<8} | {str(v['WOF']):<10} | {str(v['REGO']):<10} | {str(v['Current_ODO']):<8}")
                
        print("\n--- General Reminders List ---")
        others = db_client.fetch_all("SELECT * FROM tb_reminder_other ORDER BY id ASC")
        if not others:
            print("No general reminders.")
        else:
            print(f"{'ID':<3} | {'TITLE':<20} | {'EXPIRY':<10} | {'COMMENT'}")
            print("-" * 70)
            for o in others:
                print(f"{o['id']:<3} | {o['name'][:20]:<20} | {str(o['expiry_date']):<10} | {str(o['comment'])}")
    except Exception as e:
        print(f"Error reading reminders: {str(e)}")

def main():
    while True:
        print_header()
        print(" [1] View Vehicles & Reminders List")
        print(" [2] Register New Vehicle")
        print(" [3] Register General Reminder")
        print(" [0] Return to Main Menu")
        choice = input("Select operation: ").strip()
        
        if choice == "1":
            view_reminders()
        elif choice == "2":
            register_vehicle()
        elif choice == "3":
            register_other_reminder()
        elif choice == "0" or not choice:
            break
        else:
            print("Invalid choice.")
        
        input("\nPress Enter to continue...")
        print("\n" * 2)

if __name__ == "__main__":
    main()
