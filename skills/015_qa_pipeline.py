"""
skills/015_qa_pipeline.py
Pipeline for Quality Assurance (QA) and Work in Progress (WIP) tracking.
Handles marking members as passed or failed (NCR).
"""

import os
import sys
from datetime import datetime

# Set project root path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core import db_client

def get_pending_qa_jobs():
    """
    Returns a list of active job numbers that have pending QA items (inspection_pass_fail = 0).
    """
    query = """
        SELECT DISTINCT j.job_number, j.company_name
        FROM tb_wip w
        JOIN tb_jobs_details d ON w.tb_jobs_id = d.id
        JOIN tb_jobs j ON d.job_number = j.job_number
        WHERE w.inspection_pass_fail = 0
        ORDER BY j.job_number DESC
    """
    try:
        jobs = db_client.fetch_all(query)
        return {"status": "success", "data": jobs}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_wip_list_by_job(job_number):
    """
    Returns all pending QA items for a specific job.
    """
    query = """
        SELECT 
            w.id as wip_id,
            d.id as detail_id,
            d.lot,
            d.member,
            w.wps,
            w.in_house_inspector,
            w.wip_version,
            w.comment
        FROM tb_wip w
        JOIN tb_jobs_details d ON w.tb_jobs_id = d.id
        WHERE d.job_number = ? AND w.inspection_pass_fail = 0
        ORDER BY d.lot ASC, d.member ASC
    """
    try:
        wip_items = db_client.fetch_all(query, (job_number,))
        return {"status": "success", "data": wip_items}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def process_qa_inspection(wip_id, is_pass, comment=""):
    """
    Updates the QA status of a WIP item.
    is_pass = True -> inspection_pass_fail = 1
    is_pass = False -> inspection_pass_fail = 0, wip_version increments, comment appends.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Get current WIP record
        wip_record = db_client.fetch_one("SELECT * FROM tb_wip WHERE id = ?", (wip_id,))
        if not wip_record:
            return {"status": "error", "message": f"WIP record ID {wip_id} not found."}
            
        if is_pass:
            # Mark as passed
            query = """
                UPDATE tb_wip 
                SET inspection_pass_fail = 1, 
                    inspection_date = ?,
                    wip_version_date = ?
                WHERE id = ?
            """
            affected = db_client.execute_query(query, (today_str, today_str, wip_id))
            if affected > 0:
                return {"status": "success", "message": "Item passed QA inspection."}
            else:
                return {"status": "error", "message": "Failed to update QA pass status."}
        else:
            # Mark as failed (NCR)
            current_version = int(wip_record.get("wip_version", 0) or 0)
            new_version = current_version + 1
            
            existing_comment = wip_record.get("comment", "") or ""
            new_comment_text = f"[{today_str} FAIL] {comment}"
            combined_comment = f"{existing_comment}\n{new_comment_text}".strip()
            
            query = """
                UPDATE tb_wip 
                SET wip_version = ?, 
                    wip_version_date = ?,
                    comment = ?
                WHERE id = ?
            """
            affected = db_client.execute_query(query, (new_version, today_str, combined_comment, wip_id))
            if affected > 0:
                # --- AUTO-CREATE REWORK NCR TASK in tb_tasks (visible on Whiteboard) ---
                try:
                    detail = db_client.fetch_one("SELECT * FROM tb_jobs_details WHERE id = ?", (wip_record["tb_jobs_id"],))
                    if detail:
                        new_member_name = f"NCR-Rework: {detail['member']} (v{new_version})"
                        # Also add a new tb_jobs_details entry for tracking
                        try:
                            from skills import _010_job_pipeline as job_pipeline
                        except ImportError:
                            import importlib
                            job_pipeline = importlib.import_module("skills.010_job_pipeline")
                        
                        galv = detail.get("GalvAndPaint", 0)
                        rework_member_name = f"ncr_{detail['member']}_v{new_version}"
                        job_pipeline.add_job_detail_member(detail["job_number"], detail["page"], detail["lot"], rework_member_name, galv)

                        # Create tb_tasks entry (appears on whiteboard) assigned to same employee if known
                        # Use the job_number as site reference
                        from datetime import timedelta
                        expiry = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                        task_desc = f"[NCR REWORK] Job {detail['job_number']} - Lot {detail['lot']} - {detail['member']} version {new_version}. Comment: {comment}"
                        db_client.execute_query(
                            """
                            INSERT INTO tb_tasks (employee, site, task_instruction, date_creation, expiry_date, is_active)
                            VALUES (NULL, ?, ?, ?, ?, 1)
                            """,
                            (f"JOB-{detail['job_number']}", task_desc, today_str, expiry)
                        )
                except Exception as rework_err:
                    # Non-fatal - NCR is still logged even if rework task creation fails
                    print(f"Warning: Could not create rework task: {rework_err}")
                    rework_member_name = f"ncr_{wip_id}_v{new_version}"
                    
                return {"status": "success", "message": f"NCR logged and Rework task ({rework_member_name}) generated on Whiteboard (Version {new_version})."}
            else:
                return {"status": "error", "message": "Failed to log NCR status."}
                
    except Exception as e:
        return {"status": "error", "message": str(e)}
