"""
skills/999_db_seeder.py
Injects mock data into the database for testing purposes.
"""
import os
import sys
from datetime import datetime, timedelta

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core import db_client
import importlib
job_pipeline = importlib.import_module("skills.010_job_pipeline")
emp_master = importlib.import_module("skills.110_employee_master")
task_pipeline = importlib.import_module("skills.020_task_pipeline")
punch_pipeline = importlib.import_module("skills.030_punch_pipeline")

def seed_database():
    print("Seeding database with mock data...")
    
    # 1. Add Employees
    employees = [
        ("admin", "12345678", "Super", "Admin", "Admin", 10),
        ("worker1", "12345678", "John", "Doe", "Welder", 1),
        ("worker2", "12345678", "Jane", "Smith", "Fabricator", 1),
        ("supervisor1", "12345678", "Mike", "Johnson", "Supervisor", 2)
    ]
    
    for emp in employees:
        try:
            emp_master.create_employee(
                login=emp[0], password=emp[1], firstname=emp[2], 
                surname=emp[3], role=emp[4], right_level=emp[5]
            )
        except Exception as e:
            print(f"Error adding {emp[0]}: {e}")
            
    print("Employees seeded.")
    
    # 2. Add Jobs
    jobs = [
        (9001, "Acme Corp", "123 Main St"),
        (9002, "Global Tech", "456 Tech Blvd")
    ]
    
    for j in jobs:
        try:
            job_pipeline.create_job(job_number=j[0], company_name=j[1], site_address=j[2])
            # Add some details
            job_pipeline.add_job_detail_member(job_number=j[0], page=1, lot=1, member_name="B1", galv_and_paint=1)
            job_pipeline.add_job_detail_member(job_number=j[0], page=1, lot=1, member_name="B2", galv_and_paint=0)
        except Exception as e:
            print(f"Error adding Job {j[0]}: {e}")
            
    print("Jobs seeded.")
    
    # 3. Add Active Tasks
    # Find John Doe ID
    john = db_client.fetch_all("SELECT id FROM tb_login WHERE login='worker1'")
    if john:
        john_id = john[0]['id']
        task_pipeline.create_task("Acme Corp Site", "Weld B1 components", employee_id=john_id)
        
    print("Tasks seeded.")
    
    # 4. Add Punch Data
    if john:
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        # We bypass the standard pipeline for date overrides just for seeding, or we can use raw inserts.
        db_client.execute_query(
            "INSERT INTO tb_punchsheet (year, month, day, week, employee_id, startstop, start_time, start_time_AMPM, stop_time, stop_time_AMPM) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (yesterday.year, yesterday.strftime("%b"), yesterday.day, int(yesterday.strftime("%W")), john_id, 'start', '08:00:00', 'AM', '17:00:00', 'PM')
        )
        
    print("Punch records seeded.")
    return True

if __name__ == "__main__":
    seed_database()
