"""
tests/db_inspector.py
Interactive CLI Database Inspector to view table structures and records.
Supports viewing schemas, total records, and top/bottom N rows.
"""

import os
import sys

# Set project root path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core import db_client

TABLES = [
    "tb_export_data", "tb_jobs", "tb_jobs_date_install", "tb_jobs_dates",
    "tb_jobs_details", "tb_keys_remote_devices", "tb_leaves", "tb_login",
    "tb_photos", "tb_production_plan", "tb_public_holidays", "tb_punchsheet",
    "tb_reminder_other", "tb_reminder_vehicle", "tb_tasks",
    "tb_tasks_employees_affectation", "tb_week_notes", "tb_wip"
]

def show_tables_list():
    print("\n--- Available Database Tables Summary ---")
    for idx, table in enumerate(TABLES, 1):
        try:
            # Fetch count
            count_res = db_client.fetch_one(f"SELECT COUNT(*) as cnt FROM {table}")
            cnt = count_res["cnt"] if count_res else 0
            
            # Fetch table columns info
            info = db_client.fetch_all(f"PRAGMA table_info({table})")
            cols = [col["name"] for col in info]
            
            # Fetch last 10 records
            last_records = db_client.fetch_all(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 10")
            
            print(f"\n [{idx:2d}] {table} (Total rows: {cnt})")
            print("      Last 10 records preview:")
            if not last_records:
                print("      (No records)")
            else:
                # Print header preview of first few columns
                preview_cols = cols[:4]
                header_line = " | ".join(preview_cols)
                print(f"      [{header_line}]")
                for r in last_records:
                    vals = [str(r[c])[:15] for c in preview_cols if c in r]
                    print(f"      - {', '.join(vals)}")
        except Exception as e:
            print(f" [{idx:2d}] {table} : ERROR -> {str(e)}")
    print("\n ---------------------------------")

def inspect_table_structure(table_name):
    """
    Fetches and displays column names and types for the table.
    """
    print(f"\nStructure of table: {table_name}")
    print("=" * 60)
    try:
        # PRAGMA table_info is SQLite specific
        info = db_client.fetch_all(f"PRAGMA table_info({table_name})")
        print(f"{'CID':<4} | {'COLUMN NAME':<30} | {'TYPE':<15} | {'NOT NULL':<8} | {'PK':<3}")
        print("-" * 60)
        for col in info:
            pk = "YES" if col["pk"] else "NO"
            notnull = "YES" if col["notnull"] else "NO"
            print(f"{col['cid']:<4} | {col['name']:<30} | {col['type']:<15} | {notnull:<8} | {pk:<3}")
    except Exception as e:
        print(f"Error reading structure: {str(e)}")
    print("=" * 60)

def query_records(table_name, mode, limit=10):
    """
    Queries records: All, Top N, or Bottom N.
    """
    print(f"\nQuerying {table_name} (Mode: {mode}, Limit: {limit})")
    print("=" * 80)
    try:
        # Get column names
        info = db_client.fetch_all(f"PRAGMA table_info({table_name})")
        cols = [col["name"] for col in info]
        
        # Determine query order
        if mode == "top":
            query = f"SELECT * FROM {table_name} ORDER BY id ASC LIMIT {limit}"
        elif mode == "bottom":
            query = f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT {limit}"
        else:
            query = f"SELECT * FROM {table_name}"
            
        records = db_client.fetch_all(query)
        
        if not records:
            print("No records found.")
            print("=" * 80)
            return
            
        # Display column header line
        header_str = " | ".join(cols[:6]) # Display first 6 columns for readability
        if len(cols) > 6:
            header_str += " | ... (more)"
        print(header_str)
        print("-" * 80)
        
        for r in records:
            vals = [str(r[c])[:18] for c in cols[:6]]
            row_str = " | ".join(vals)
            if len(cols) > 6:
                row_str += " | ..."
            print(row_str)
            
        print("-" * 80)
        print(f"Total returned rows: {len(records)}")
    except Exception as e:
        print(f"Error querying table: {str(e)}")
    print("=" * 80)

def main():
    while True:
        show_tables_list()
        choice = input("Select table number to inspect (1-18) or '0' to return: ").strip()
        if choice == "0" or not choice:
            break
            
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(TABLES):
                print("Invalid table index.")
                continue
            table_name = TABLES[idx]
        except ValueError:
            print("Please enter a numeric choice.")
            continue
            
        print(f"\nSelected Table: {table_name}")
        print(" [1] View Table Columns & Types (Schema)")
        print(" [2] View Top Records")
        print(" [3] View Bottom Records")
        print(" [4] View All Records")
        op = input("Select operation (1-4): ").strip()
        
        if op == "1":
            inspect_table_structure(table_name)
        elif op in ["2", "3"]:
            limit_input = input("Enter number of rows to retrieve (Default is 10): ").strip()
            limit = int(limit_input) if limit_input.isdigit() else 10
            mode = "top" if op == "2" else "bottom"
            query_records(table_name, mode, limit)
        elif op == "4":
            query_records(table_name, "all")
        else:
            print("Invalid operation.")
        
        input("\nPress Enter to continue inspecting...")

if __name__ == "__main__":
    main()
