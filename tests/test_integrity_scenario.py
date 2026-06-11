"""
tests/test_integrity_scenario.py
Test script to simulate database integrity violations and verify repair behavior.
Inserts orphan records and triggers db_integrity_checker.
"""

import os
import sys

# Set project root path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core import db_client
from tests import db_integrity_checker

def setup_orphan_scenarios():
    print("\n[1/3] Setting up orphan test records...")
    
    # Insert orphan details (job_number 999999 does not exist in tb_jobs)
    db_client.execute_query(
        """
        INSERT INTO tb_jobs_details (date_creation, job_number, page, lot, member, GalvAndPaint, made)
        VALUES ('2026-06-11', 999999, 1, 1, 'TEST-ORPHAN-MEMBER', 0, 0)
        """
    )
    # Get the last detail ID to link orphan WIP and Punch
    last_detail = db_client.fetch_one("SELECT id FROM tb_jobs_details WHERE job_number = 999999")
    detail_id = last_detail["id"]
    print(f"  - Created orphan job detail with ID: {detail_id}")
    
    # Insert orphan WIP (referencing id that will be orphaned)
    # We will also insert another orphan WIP referencing a non-existent detail id like 888888
    db_client.execute_query(
        """
        INSERT INTO tb_wip (tb_jobs_id, wps, inspection_pass_fail, wip_version)
        VALUES (888888, 'WPS-ORPHAN', 0, 1)
        """
    )
    print("  - Created orphan WIP record referencing non-existent detail ID 888888")

    # Insert orphan punchsheet referencing non-existent detail ID 888888
    db_client.execute_query(
        """
        INSERT INTO tb_punchsheet (year, week, employee_id, job_detail_id, startstop)
        VALUES (2026, 24, 99, '888888', 'START')
        """
    )
    print("  - Created orphan punchsheet record referencing non-existent detail ID 888888")

def verify_and_repair():
    print("\n[2/3] Running database integrity audit (Detection phase)...")
    # Verify that issues are detected (without fix)
    db_integrity_checker.audit_and_repair(fix=False)
    
    print("\n[3/3] Running database integrity repair (Execution phase)...")
    # Execute repair
    db_integrity_checker.audit_and_repair(fix=True)
    
    # Verify cleanup results
    print("\n[Verification after repair]")
    orphan_detail_check = db_client.fetch_all("SELECT id FROM tb_jobs_details WHERE job_number = 999999")
    orphan_wip_check = db_client.fetch_all("SELECT id FROM tb_wip WHERE tb_jobs_id = 888888")
    orphan_punch_check = db_client.fetch_all("SELECT id FROM tb_punchsheet WHERE job_detail_id = '888888'")
    
    print(f"  - Orphan details count remaining: {len(orphan_detail_check)} (Expected: 0)")
    print(f"  - Orphan WIP count remaining: {len(orphan_wip_check)} (Expected: 0)")
    print(f"  - Orphan punchsheets count with '888888' remaining: {len(orphan_punch_check)} (Expected: 0)")
    
    if len(orphan_detail_check) == 0 and len(orphan_wip_check) == 0 and len(orphan_punch_check) == 0:
        print("\nINTEGRITY REPAIR TEST SUCCESSFUL.")
    else:
        print("\nINTEGRITY REPAIR TEST FAILED.")

def main():
    # Make backup copy of DB state first
    db_integrity_checker.perform_db_backup()
    
    # Setup test case
    setup_orphan_scenarios()
    
    # Perform audit and repair test
    verify_and_repair()

if __name__ == "__main__":
    main()
