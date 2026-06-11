"""
tests/mock_data_generator.py
Generates random, valid mock data (Jobs, Lots, Members, WIP entries, and Punchsheets)
matching business validation logic for testing and layout verification.
"""

import os
import sys
import random
from datetime import datetime, timedelta

# Set project root path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core import db_client

COMPANIES = ["Classic Builders", "Universal Homes", "Mike Greer Homes", "Jalcon Homes", "Mako Commercial"]
ADDRESSES = ["10 Hobsonville Rd", "45 Bonair Cres", "12 Lawrence St", "88 Albany Highway", "1195 Dominion Rd"]
EMPLOYEES = [
    {"login": "damien", "first": "Damien", "last": "Smith", "role": "Manager", "level": 9},
    {"login": "sam", "first": "Sam", "last": "Jones", "role": "Fabricator", "level": 1},
    {"login": "felipe", "first": "Felipe", "last": "Silva", "role": "Fabricator", "level": 1},
    {"login": "grants", "first": "Grants", "last": "Taylor", "role": "Supervisor", "level": 12},
    {"login": "johan", "first": "Johan", "last": "van der Merwe", "role": "Installer", "level": 2}
]

def generate_mock_data():
    print("Generating Mock Data for testing...")
    
    # 1. Insert mock employees into tb_login (if not exists)
    employee_ids = []
    for emp in EMPLOYEES:
        res = db_client.fetch_one("SELECT id FROM tb_login WHERE login = ?", (emp["login"],))
        if res:
            employee_ids.append(res["id"])
        else:
            db_client.execute_query(
                """
                INSERT INTO tb_login (login, password, firstname, surname, avatar, bay, date_creation, role, right_level, admin_validation)
                VALUES (?, 'password_hash', ?, ?, 'avatar.png', 1, '2026-01-01', ?, ?, 1)
                """,
                (emp["login"], emp["first"], emp["last"], emp["role"], emp["level"])
            )
            new_res = db_client.fetch_one("SELECT id FROM tb_login WHERE login = ?", (emp["login"],))
            if new_res:
                employee_ids.append(new_res["id"])

    # 2. Insert mock jobs (5 new jobs)
    for _ in range(5):
        job_number = random.randint(1000, 9999)
        company = random.choice(COMPANIES)
        address = random.choice(ADDRESSES)
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # Check if job already exists
        exists = db_client.fetch_one("SELECT id FROM tb_jobs WHERE job_number = ?", (job_number,))
        if exists:
            continue
            
        db_client.execute_query(
            """
            INSERT INTO tb_jobs (date_creation, job_number, quote_confirmed, company_name, site_address, superlot, lot_group, supervisor_name, builder_name, installer_name, date_last_update, WIP_Completed)
            VALUES (?, ?, 1, ?, ?, 'SuperLot A', 'Lot 1-5', 'Supervisor Mark', 'Builder John', 'Installer Peter', ?, 0)
            """,
            (today_str, job_number, company, address, today_str)
        )
        
        db_client.execute_query(
            "INSERT INTO tb_jobs_dates (job_number, year) VALUES (?, ?)",
            (job_number, datetime.now().year)
        )
        
        # 3. Insert details (members) for each job
        lots = [1, 2, 3]
        for lot in lots:
            # Add install date status
            db_client.execute_query(
                "INSERT INTO tb_jobs_date_install (date_creation, job_number, lot, status_install) VALUES (?, ?, ?, 'design')",
                (today_str, job_number, lot)
            )
            
            # Add member details
            num_members = random.randint(3, 8)
            for page in range(1, num_members + 1):
                member_name = f"B{page}" if random.choice([True, False]) else f"P{page}"
                
                # Check for Task/NCR/RFI logic check
                is_task = random.choice([True, False, False, False])
                if is_task:
                    member_name = f"task_{random.randint(10,99)}"
                    
                # DB init condition for Task or normal member
                if is_task:
                    db_client.execute_query(
                        """
                        INSERT INTO tb_jobs_details (date_creation, job_number, page, lot, member, GalvAndPaint, design, design_date_update, made, made_date_update, loaded, load_date_update, on_site, on_site_date_update, temp_fix, temp_fix_date_update, chemset, chemset_date_update, tightened, tightened_date_update, finish, finish_date_update)
                        VALUES (?, ?, ?, ?, ?, 0, 1, ?, 1, ?, 1, ?, 1, ?, 1, ?, 1, ?, 1, ?, 0, ?)
                        """,
                        (today_str, job_number, page, lot, member_name, today_str, today_str, today_str, today_str, today_str, today_str, today_str, today_str)
                    )
                else:
                    db_client.execute_query(
                        """
                        INSERT INTO tb_jobs_details (date_creation, job_number, page, lot, member, GalvAndPaint, design, design_date_update, made, loaded, on_site, temp_fix, chemset, tightened, finish)
                        VALUES (?, ?, ?, ?, ?, 1, 0, ?, 0, 0, 0, 0, 0, 0, 0)
                        """,
                        (today_str, job_number, page, lot, member_name, today_str)
                    )
                
                # Get the last detail ID
                detail = db_client.fetch_one(
                    "SELECT id FROM tb_jobs_details WHERE job_number = ? AND page = ? AND lot = ? AND member = ?",
                    (job_number, page, lot, member_name)
                )
                if detail:
                    detail_id = detail["id"]
                    # Add WIP inspection entry
                    db_client.execute_query(
                        """
                        INSERT INTO tb_wip (tb_jobs_id, wps, in_house_inspector, third_party_inspector, inspection_pass_fail, wip_version)
                        VALUES (?, 'PE GMAW 02', 'Matt Leitch', 'Weldtest (Paul Jensen)', 0, 0)
                        """,
                        (detail_id,)
                    )

    # 4. Generate some mock punchsheets for workers
    for emp_id in employee_ids:
        # Generate punch history for the past 5 days
        for i in range(5):
            date_to_punch = datetime.now() - timedelta(days=i)
            year = date_to_punch.year
            month = date_to_punch.strftime("%b")
            day = date_to_punch.day
            week = date_to_punch.strftime("%W")
            
            # Start job time
            start_hour = random.randint(7, 9)
            start_time = f"{start_hour:02d}:00:00"
            stop_hour = start_hour + random.randint(7, 9)
            stop_time = f"{stop_hour:02d}:00:00"
            
            db_client.execute_query(
                """
                INSERT INTO tb_punchsheet (year, month, day, week, employee_id, job_detail_id, startstop, start_time, start_time_AMPM, stop_time, stop_time_AMPM)
                VALUES (?, ?, ?, ?, ?, 'CLOCK IN', 'START', ?, 'AM', ?, 'PM')
                """,
                (year, month, day, int(week), emp_id, start_time, stop_time)
            )

    print("Mock Data Generation Finished Successfully.")

if __name__ == "__main__":
    generate_mock_data()
