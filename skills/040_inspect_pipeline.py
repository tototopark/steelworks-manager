"""
skills/040_inspect_pipeline.py
Manages weld quality inspection sheets and third-party inspection metadata.
Executable as a standalone python pipeline stage.
"""

import os
import sys
from datetime import datetime

# Set project root path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core import db_client

def record_in_house_inspection(tb_jobs_id, inspector, exam_type, report_num, is_passed, comment=None):
    """
    Updates internal weld inspection status and increments inspection version.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"Recording In-House Inspection for Job Detail ID {tb_jobs_id} (Passed: {is_passed})")
    
    # Retrieve current version to increment it
    wip = db_client.fetch_one("SELECT wip_version FROM tb_wip WHERE tb_jobs_id = ?", (tb_jobs_id,))
    curr_version = wip["wip_version"] if wip and wip["wip_version"] else 0
    next_version = curr_version + 1
    
    db_client.execute_query(
        """
        UPDATE tb_wip
        SET in_house_inspector = ?, in_house_exam_type = ?, in_house_report_number = ?,
            inspection_pass_fail = ?, inspection_date = ?, wip_version = ?, wip_version_date = ?, comment = ?
        WHERE tb_jobs_id = ?
        """,
        (inspector, exam_type, report_num, 1 if is_passed else 0, today_str, next_version, today_str, comment, tb_jobs_id)
    )
    return True

def record_third_party_inspection(tb_jobs_id, inspector, exam_type, report_num, is_passed, comment=None):
    """
    Updates external third-party weld inspection status and increments inspection version.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"Recording Third-Party Inspection for Job Detail ID {tb_jobs_id} (Passed: {is_passed})")
    
    # Retrieve current version to increment it
    wip = db_client.fetch_one("SELECT wip_version FROM tb_wip WHERE tb_jobs_id = ?", (tb_jobs_id,))
    curr_version = wip["wip_version"] if wip and wip["wip_version"] else 0
    next_version = curr_version + 1
    
    db_client.execute_query(
        """
        UPDATE tb_wip
        SET third_party_inspector = ?, third_party_exam_type = ?, third_party_report_number = ?,
            inspection_pass_fail = ?, inspection_date = ?, wip_version = ?, wip_version_date = ?, comment = ?
        WHERE tb_jobs_id = ?
        """,
        (inspector, exam_type, report_num, 1 if is_passed else 0, today_str, next_version, today_str, comment, tb_jobs_id)
    )
    return True

def get_inspect_report(job_number):
    """
    Aggregates inspection passes/fails for all details under a job.
    """
    print(f"\nGenerating Weld Quality Inspection Audit for Job: {job_number}")
    print("-" * 60)
    
    try:
        # Join details with WIP information
        records = db_client.fetch_all(
            """
            SELECT d.member, d.lot, w.in_house_inspector, w.third_party_inspector, w.inspection_pass_fail, w.wip_version
            FROM tb_jobs_details d
            INNER JOIN tb_wip w ON d.id = w.tb_jobs_id
            WHERE d.job_number = ?
            """,
            (job_number,)
        )
        
        if not records:
            print("No weld inspection records found for this job.")
            return
            
        passed = 0
        failed = 0
        
        for r in records:
            status = "PASS" if r["inspection_pass_fail"] == 1 else "FAIL/PENDING"
            if r["inspection_pass_fail"] == 1:
                passed += 1
            else:
                failed += 1
            print(f"Lot {r['lot']:<2} | Member: {r['member']:<10} | Ver: {r['wip_version']:<2} | Weld Audit Status: {status}")
            
        print("-" * 60)
        total = passed + failed
        pass_rate = round((passed / total) * 100.0, 1) if total > 0 else 0
        print(f"Audit Summary -> Total: {total} | Passed: {passed} | Pending/Fail: {failed} | Pass Rate: {pass_rate}%")
        
    except Exception as e:
        print(f"Error compiling inspection audit: {str(e)}")
    print("-" * 60)

def main():
    print("Running Quality Inspection Pipeline verification test...")
    # Setup test detail dummy
    test_detail_id = 99991
    db_client.execute_query("DELETE FROM tb_wip WHERE tb_jobs_id = ?", (test_detail_id,))
    
    # Initialize WIP row
    db_client.execute_query(
        "INSERT INTO tb_wip (tb_jobs_id, wps, inspection_pass_fail, wip_version) VALUES (?, 'PE GMAW 02', 0, 0)",
        (test_detail_id,)
    )
    
    # Test In-House
    record_in_house_inspection(test_detail_id, "Matt Leitch", "Visual", "IH-REP-01", True, "Visual test okay")
    
    # Test Third-Party
    record_third_party_inspection(test_detail_id, "Paul Jensen", "UT", "3P-REP-99", True, "UT testing passed")
    
    # Fetch to verify version and status
    wip = db_client.fetch_one("SELECT inspection_pass_fail, wip_version FROM tb_wip WHERE tb_jobs_id = ?", (test_detail_id,))
    if wip and wip["inspection_pass_fail"] == 1 and wip["wip_version"] == 2:
        print("Inspection Pipeline verification completed successfully.")
    else:
        print(f"ERROR: Inconsistent inspection version or status. Received: {wip}")
        sys.exit(1)

if __name__ == "__main__":
    main()
