"""
skills/010_job_pipeline.py
Handles steelworks project jobs ingestion, milestone updates, and member status tracking.
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

def check_task_ncr_rfi(member_name):
    """
    Checks if a member name starts with 'task', 'ncr', or 'rfi'.
    """
    name_lower = member_name.lower().strip()
    return name_lower.startswith("task") or name_lower.startswith("ncr") or name_lower.startswith("rfi")

def create_job(job_number, company_name, site_address, date_creation=None):
    """
    Creates a new Job Master record and associated dates table entries.
    """
    if not date_creation:
        date_creation = datetime.now().strftime("%Y-%m-%d")
        
    year = date_creation.split("-")[0]
    
    print(f"Creating job: {job_number} ({company_name})")
    
    # 1. Insert into tb_jobs
    db_client.execute_query(
        """
        INSERT INTO tb_jobs (date_creation, job_number, quote_confirmed, company_name, site_address, superlot, lot_group, supervisor_name, builder_name, installer_name, date_last_update, WIP_Completed)
        VALUES (?, ?, 1, ?, ?, '', '', '', '', '', ?, 0)
        """,
        (date_creation, job_number, company_name, site_address, date_creation)
    )
    
    # 2. Insert into tb_jobs_dates
    db_client.execute_query(
        "INSERT INTO tb_jobs_dates (job_number, year) VALUES (?, ?)",
        (job_number, int(year))
    )
    
    # 3. Initialize install date status with lot 0
    db_client.execute_query(
        "INSERT INTO tb_jobs_date_install (date_creation, job_number, lot, status_install) VALUES (?, ?, 0, 'design')",
        (date_creation, job_number)
    )
    
    return True

def add_job_detail_member(job_number, page, lot, member_name, galv_and_paint=0, date_creation=None):
    """
    Adds a steelwork member detail to tb_jobs_details and applies automatic logic based on name and WIP requirements.
    """
    if not date_creation:
        date_creation = datetime.now().strftime("%Y-%m-%d")
        
    today_str = datetime.now().strftime("%Y-%m-%d")
    is_special = check_task_ncr_rfi(member_name)
    
    # Ensure install status configuration for the lot exists
    lot_exists = db_client.fetch_one(
        "SELECT id FROM tb_jobs_date_install WHERE job_number = ? AND lot = ?",
        (job_number, lot)
    )
    if not lot_exists:
        status = "temp installed" if is_special else "design"
        db_client.execute_query(
            "INSERT INTO tb_jobs_date_install (date_creation, job_number, lot, status_install) VALUES (?, ?, ?, ?)",
            (date_creation, job_number, lot, status)
        )
        # Delete dummy lot 0
        db_client.execute_query(
            "DELETE FROM tb_jobs_date_install WHERE job_number = ? AND lot = 0",
            (job_number,)
        )

    # Insert with automated rules
    if is_special:
        # Special components: immediately completed except for final finish
        db_client.execute_query(
            """
            INSERT INTO tb_jobs_details (date_creation, job_number, page, lot, member, GalvAndPaint, design, design_date_update, made, made_date_update, loaded, load_date_update, on_site, on_site_date_update, temp_fix, temp_fix_date_update, chemset, chemset_date_update, tightened, tightened_date_update, finish, finish_date_update)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, 1, ?, 1, ?, 1, ?, 1, ?, 1, ?, 1, ?, 0, ?)
            """,
            (date_creation, job_number, page, lot, member_name, galv_and_paint, today_str, today_str, today_str, today_str, today_str, today_str, today_str, today_str)
        )
    else:
        # Standard component: initialized as pending
        db_client.execute_query(
            """
            INSERT INTO tb_jobs_details (date_creation, job_number, page, lot, member, GalvAndPaint, design, design_date_update, made, loaded, on_site, temp_fix, chemset, tightened, finish)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, 0, 0, 0, 0, 0, 0, 0)
            """,
            (date_creation, job_number, page, lot, member_name, galv_and_paint, today_str)
        )
        
    # Get created detail ID to bind WIP record
    res = db_client.fetch_one(
        "SELECT id FROM tb_jobs_details WHERE job_number = ? AND page = ? AND lot = ? AND member = ?",
        (job_number, page, lot, member_name)
    )
    if res:
        detail_id = res["id"]
        # Automatic WIP initialization
        db_client.execute_query(
            """
            INSERT INTO tb_wip (tb_jobs_id, wps, in_house_inspector, third_party_inspector, inspection_pass_fail, wip_version)
            VALUES (?, 'PE GMAW 02, PE GMAW 03, PE GMAW 04', 'Matt Leitch', 'Weldtest (Paul Jensen)', 0, 0)
            """,
            (detail_id,)
        )
    return True

def update_member_made_status(detail_id, worker_name):
    """
    Marks a member as made (or finished if it's a task) and triggers Lot status ready updates.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Retrieve detail information
    detail = db_client.fetch_one(
        "SELECT job_number, lot, member, date_creation FROM tb_jobs_details WHERE id = ?",
        (detail_id,)
    )
    if not detail:
        print(f"Error: detail_id {detail_id} not found.")
        return False
        
    job_number = detail["job_number"]
    lot = detail["lot"]
    member_name = detail["member"]
    date_creation = detail["date_creation"]
    
    # Conditional logic based on name prefix (Task check)
    is_task = member_name.lower().strip().startswith("task")
    
    if is_task:
        # Mark task as completed in full
        db_client.execute_query(
            """
            UPDATE tb_jobs_details 
            SET made = 1, made_date_update = ?, made_by = ?,
                finish = 1, finish_date_update = ?, finish_by = ?
            WHERE id = ?
            """,
            (today_str, worker_name, today_str, worker_name, detail_id)
        )
    else:
        # Mark normal member as fabricated
        db_client.execute_query(
            "UPDATE tb_jobs_details SET made = 1, made_date_update = ?, made_by = ? WHERE id = ?",
            (today_str, worker_name, detail_id)
        )
        
    # Check if all members in the Lot are completed (Ready status logic)
    tot_res = db_client.fetch_one(
        "SELECT COUNT(*) as tot FROM tb_jobs_details WHERE job_number = ? AND lot = ? AND date_creation = ?",
        (job_number, lot, date_creation)
    )
    made_res = db_client.fetch_one(
        "SELECT COUNT(*) as made_cnt FROM tb_jobs_details WHERE job_number = ? AND lot = ? AND date_creation = ? AND made = 1",
        (job_number, lot, date_creation)
    )
    
    tot_cnt = tot_res["tot"] if tot_res else 0
    made_cnt = made_res["made_cnt"] if made_res else 0
    
    if tot_cnt > 0 and tot_cnt == made_cnt:
        print(f"All members in Job {job_number} Lot {lot} are made. Updating status to 'ready'.")
        db_client.execute_query(
            "UPDATE tb_jobs_date_install SET status_install = 'ready' WHERE job_number = ? AND lot = ? AND date_creation = ?",
            (job_number, lot, date_creation)
        )
        
    return True

def get_job_details(job_number):
    """
    Retrieves all details (members, lots, status) for a specific job number.
    """
    query = "SELECT id, lot, member, GalvAndPaint, design, made, loaded, on_site, finish FROM tb_jobs_details WHERE job_number = ? ORDER BY lot, member"
    return db_client.fetch_all(query, (job_number,))

def main():
    print("Running Job Ingestion Pipeline smoke test...")
    # Standalone verification run
    test_job_num = 9991
    # Clean up first
    db_client.execute_query("DELETE FROM tb_jobs WHERE job_number = ?", (test_job_num,))
    db_client.execute_query("DELETE FROM tb_jobs_dates WHERE job_number = ?", (test_job_num,))
    db_client.execute_query("DELETE FROM tb_jobs_date_install WHERE job_number = ?", (test_job_num,))
    db_client.execute_query("DELETE FROM tb_jobs_details WHERE job_number = ?", (test_job_num,))
    
    create_job(test_job_num, "Test Pipeline Corp", "77 Pipeline Way")
    add_job_detail_member(test_job_num, 1, 1, "B1")
    add_job_detail_member(test_job_num, 1, 1, "task_paint")
    
    # Retrieve details to get ID
    detail_res = db_client.fetch_one("SELECT id FROM tb_jobs_details WHERE job_number = ? AND member = 'B1'", (test_job_num,))
    if detail_res:
        update_member_made_status(detail_res["id"], "sam")
        
    print("Job Pipeline execution verification finished successfully.")

if __name__ == "__main__":
    main()
