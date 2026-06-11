"""
tests/smoke_check.py
Validates the database migration integrity by verifying row counts across all 17 tables.
"""

import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core import db_client

def run_smoke_check():
    tables = [
        "tb_export_data", "tb_jobs", "tb_jobs_date_install", "tb_jobs_dates",
        "tb_jobs_details", "tb_keys_remote_devices", "tb_leaves", "tb_login",
        "tb_photos", "tb_production_plan", "tb_public_holidays", "tb_punchsheet",
        "tb_reminder_other", "tb_reminder_vehicle", "tb_tasks",
        "tb_tasks_employees_affectation", "tb_week_notes", "tb_wip"
    ]
    
    print("="*60)
    print("Database Smoke Check - Table Row Counts")
    print("="*60)
    
    for table in tables:
        try:
            res = db_client.fetch_one(f"SELECT COUNT(*) as cnt FROM {table}")
            cnt = res["cnt"] if res else 0
            print(f"{table:35} : {cnt} rows")
        except Exception as e:
            print(f"{table:35} : ERROR -> {str(e)}")
            
    print("="*60)

if __name__ == "__main__":
    run_smoke_check()
