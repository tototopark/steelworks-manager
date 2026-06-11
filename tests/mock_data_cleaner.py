"""
tests/mock_data_cleaner.py
Cleans up temporary mock simulation data (created in 2026)
while preserving the legacy migrated database records.
"""

import os
import sys

# Set project root path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core import db_client

def clean_mock_data():
    print("Initiating Mock Data Cleanup...")
    print("Preserving all legacy migrated database records (pre-2026)...")
    print("-" * 50)
    
    try:
        # 1. Delete punchsheets created for mock employee IDs or temporary test employee 99
        # The mock generators create test accounts: damien, sam, felipe, grants, johan, and test_emp 99
        db_client.execute_query(
            """
            DELETE FROM tb_punchsheet 
            WHERE employee_id = 99 
               OR employee_id IN (SELECT id FROM tb_login WHERE login IN ('damien', 'sam', 'felipe', 'grants', 'johan'))
            """
        )
        print("Cleared mock punchsheets.")
        
        # 2. Delete mock details and WIP entries created for mock jobs (created in 2026)
        # We target jobs details where job_number corresponds to a job created in 2026
        mock_jobs = db_client.fetch_all("SELECT job_number FROM tb_jobs WHERE date_creation >= '2026-01-01'")
        mock_job_nums = [j["job_number"] for j in mock_jobs]
        
        if mock_job_nums:
            job_nums_str = ", ".join([str(n) for n in mock_job_nums])
            # Delete WIP records
            db_client.execute_query(
                f"DELETE FROM tb_wip WHERE tb_jobs_id IN (SELECT id FROM tb_jobs_details WHERE job_number IN ({job_nums_str}))"
            )
            # Delete job details
            db_client.execute_query(f"DELETE FROM tb_jobs_details WHERE job_number IN ({job_nums_str})")
            # Delete install status
            db_client.execute_query(f"DELETE FROM tb_jobs_date_install WHERE job_number IN ({job_nums_str})")
            # Delete job dates
            db_client.execute_query(f"DELETE FROM tb_jobs_dates WHERE job_number IN ({job_nums_str})")
            # Delete jobs
            db_client.execute_query(f"DELETE FROM tb_jobs WHERE job_number IN ({job_nums_str})")
            print(f"Cleared mock jobs and engineering details for: {job_nums_str}")
        
        # 3. Delete mock tasks (created for TestSitePipeline or without legacy origin)
        db_client.execute_query("DELETE FROM tb_tasks WHERE site = 'TestSitePipeline'")
        db_client.execute_query(
            "DELETE FROM tb_tasks_employees_affectation WHERE id NOT IN (SELECT id FROM tb_tasks)"
        )
        print("Cleared mock task assignments.")
        
        # 4. Delete mock login accounts
        db_client.execute_query("DELETE FROM tb_login WHERE login IN ('damien', 'sam', 'felipe', 'grants', 'johan')")
        print("Cleared mock login accounts.")
        
        # 5. Show statistics after cleanup
        print("-" * 50)
        print("Final Status Verification:")
        tables = ["tb_jobs", "tb_jobs_details", "tb_punchsheet", "tb_tasks", "tb_login", "tb_wip"]
        for table in tables:
            res = db_client.fetch_one(f"SELECT COUNT(*) as cnt FROM {table}")
            cnt = res["cnt"] if res else 0
            print(f"  {table:30} : {cnt} rows remaining")
        
        print("-" * 50)
        print("Mock Data Cleanup Completed Successfully.")
        
    except Exception as e:
        print(f"Error executing cleanup: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    clean_mock_data()
