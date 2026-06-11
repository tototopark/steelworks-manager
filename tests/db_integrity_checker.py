"""
tests/db_integrity_checker.py
Database Integrity Checker & Repair Tool.
Backs up the SQLite database with a timestamp prefix and performs data integrity audit/cleansing.
"""

import os
import sys
import shutil
from datetime import datetime

# Set project root path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core import db_client
from configs import app_config

def perform_db_backup():
    """
    Creates a timestamped backup of the current SQLite database file.
    """
    db_path = app_config.SQLITE_DB_PATH
    if not os.path.exists(db_path):
        print("Error: Database file does not exist. No backup created.")
        return False
        
    db_dir = os.path.dirname(db_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"steelworks_backup_{timestamp}.db"
    backup_path = os.path.join(db_dir, backup_filename)
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"Database backed up successfully to: {os.path.basename(backup_path)}")
        return True
    except Exception as e:
        print(f"Backup failed: {str(e)}")
        return False

def audit_and_repair(fix=False):
    """
    Checks for referential integrity violations and optionally repairs them.
    """
    print("\nStarting integrity audit...")
    violations = {}
    
    # 1. Orphan tb_jobs_details
    orphan_details = db_client.fetch_all(
        """
        SELECT d.id, d.job_number, d.member 
        FROM tb_jobs_details d 
        LEFT JOIN tb_jobs j ON d.job_number = j.job_number 
        WHERE j.job_number IS NULL
        """
    )
    violations["Orphan tb_jobs_details"] = orphan_details
    
    # 2. Orphan tb_wip
    orphan_wip = db_client.fetch_all(
        """
        SELECT w.id, w.tb_jobs_id, w.wps 
        FROM tb_wip w 
        LEFT JOIN tb_jobs_details d ON w.tb_jobs_id = d.id 
        WHERE d.id IS NULL
        """
    )
    violations["Orphan tb_wip"] = orphan_wip
    
    # 3. Orphan tb_punchsheet (referencing missing tb_jobs_details)
    # Cast to handle potential varchar/integer difference safely
    orphan_punch = db_client.fetch_all(
        """
        SELECT p.id, p.job_detail_id, p.employee_id 
        FROM tb_punchsheet p 
        LEFT JOIN tb_jobs_details d ON CAST(p.job_detail_id AS INTEGER) = d.id 
        WHERE d.id IS NULL AND p.job_detail_id IS NOT NULL AND p.job_detail_id != ''
        """
    )
    violations["Orphan tb_punchsheet"] = orphan_punch

    # 4. Orphan tb_tasks_employees_affectation
    orphan_tasks_aff = db_client.fetch_all(
        """
        SELECT a.id 
        FROM tb_tasks_employees_affectation a 
        LEFT JOIN tb_tasks t ON a.id = t.id 
        WHERE t.id IS NULL
        """
    )
    violations["Orphan tb_tasks_employees_affectation"] = orphan_tasks_aff

    # Print Report
    print("\n--- INTEGRITY AUDIT REPORT ---")
    total_violations = 0
    for name, items in violations.items():
        print(f" * {name}: {len(items)} issues detected")
        total_violations += len(items)
        
    if total_violations == 0:
        print("All database relations are healthy. No issues found.")
        return
        
    if not fix:
        print("\nVerification completed. Run with repair mode to fix these violations.")
        return

    # Executing Repairs
    print("\nExecuting repairs...")
    try:
        # Repair 1: Delete orphan details
        if orphan_details:
            ids = [str(item["id"]) for item in orphan_details]
            db_client.execute_query(f"DELETE FROM tb_jobs_details WHERE id IN ({', '.join(ids)})")
            print(f"  - Deleted {len(orphan_details)} orphan tb_jobs_details records.")
            
        # Repair 2: Delete orphan wip
        if orphan_wip:
            ids = [str(item["id"]) for item in orphan_wip]
            db_client.execute_query(f"DELETE FROM tb_wip WHERE id IN ({', '.join(ids)})")
            print(f"  - Deleted {len(orphan_wip)} orphan tb_wip records.")
            
        # Repair 3: Clean orphan punchsheets by setting detail relation to NULL
        if orphan_punch:
            ids = [str(item["id"]) for item in orphan_punch]
            db_client.execute_query(f"UPDATE tb_punchsheet SET job_detail_id = NULL WHERE id IN ({', '.join(ids)})")
            print(f"  - Cleared job_detail_id reference for {len(orphan_punch)} orphan punchsheets.")
            
        # Repair 4: Delete orphan tasks affectation
        if orphan_tasks_aff:
            ids = [str(item["id"]) for item in orphan_tasks_aff]
            db_client.execute_query(f"DELETE FROM tb_tasks_employees_affectation WHERE id IN ({', '.join(ids)})")
            print(f"  - Deleted {len(orphan_tasks_aff)} orphan affectation records.")
            
        print("Database repair successfully completed.")
    except Exception as e:
        print(f"Error occurred during database repair: {str(e)}")

def main():
    print("=" * 60)
    print("           DATABASE INTEGRITY CHECK & REPAIR TOOL")
    print("=" * 60)
    
    # Force backup before anything else
    if not perform_db_backup():
        print("Terminating audit due to backup failure.")
        return
        
    # Audit mode first
    audit_and_repair(fix=False)
    
    # Prompt for repair
    choice = input("\nDo you want to automatically repair detected violations? (y/n): ").strip().lower()
    if choice == "y":
        audit_and_repair(fix=True)
    else:
        print("No repairs executed.")

if __name__ == "__main__":
    main()
