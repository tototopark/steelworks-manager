"""
skills/310_schedule_pipeline.py
Pipeline for Weekly Notes and Production Plan assignments.
"""

import os
import sys

# Set project root path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core import db_client

def get_weekly_schedule(start_date, end_date):
    """
    Fetches tb_week_notes and tb_production_plan within a date range.
    """
    try:
        # Fetch notes
        notes_query = "SELECT * FROM tb_week_notes WHERE date >= ? AND date <= ? ORDER BY date ASC"
        notes = db_client.fetch_all(notes_query, (start_date, end_date))
        
        # Organize notes by date
        notes_dict = {n['date']: {"note": n.get("note", ""), "note2": n.get("note2", "")} for n in notes}
        
        # Fetch production plans joined with employee and job
        plan_query = """
            SELECT 
                p.id, p.date_creation as date, p.priority, p.job_number, p.lot, p.employee_id,
                l.firstname, l.surname,
                j.company_name
            FROM tb_production_plan p
            LEFT JOIN tb_login l ON p.employee_id = l.id
            LEFT JOIN tb_jobs j ON p.job_number = j.job_number
            WHERE p.date_creation >= ? AND p.date_creation <= ?
            ORDER BY p.date_creation ASC, p.priority ASC
        """
        plans = db_client.fetch_all(plan_query, (start_date, end_date))
        
        # Group plans by date
        plans_dict = {}
        for p in plans:
            d = p['date']
            if d not in plans_dict:
                plans_dict[d] = []
            plans_dict[d].append(p)
            
        return {"status": "success", "data": {"notes": notes_dict, "plans": plans_dict}}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def update_daily_note(date_str, note, note2=""):
    """
    Creates or updates tb_week_notes for a specific date.
    """
    try:
        existing = db_client.fetch_one("SELECT id FROM tb_week_notes WHERE date = ?", (date_str,))
        if existing:
            query = "UPDATE tb_week_notes SET note = ?, note2 = ? WHERE id = ?"
            db_client.execute_query(query, (note, note2, existing['id']))
        else:
            query = "INSERT INTO tb_week_notes (date, note, note2) VALUES (?, ?, ?)"
            db_client.execute_query(query, (date_str, note, note2))
        return {"status": "success", "message": "Note updated successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def assign_production_plan(date_str, employee_id, job_number, lot, priority):
    """
    Inserts a new assignment into tb_production_plan.
    """
    try:
        query = """
            INSERT INTO tb_production_plan (employee_id, priority, job_number, date_creation, lot)
            VALUES (?, ?, ?, ?, ?)
        """
        db_client.execute_query(query, (employee_id, priority, job_number, date_str, lot))
        return {"status": "success", "message": "Task assigned successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_job_options():
    """
    Returns active jobs and lots for the assignment dropdown.
    """
    try:
        # Get active jobs
        jobs = db_client.fetch_all("SELECT job_number, company_name FROM tb_jobs WHERE WIP_Completed = 0 ORDER BY job_number DESC")
        return {"status": "success", "data": jobs}
    except Exception as e:
        return {"status": "error", "message": str(e)}
