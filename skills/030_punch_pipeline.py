"""
skills/030_punch_pipeline.py
Processes timesheets and punchsheets to record man-hours and compute job costs.
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

def record_punch(employee_id, job_detail_id, startstop, time_str=None, ampm_str=None, date_obj=None):
    """
    Inserts a standard record into tb_punchsheet.
    """
    if not date_obj:
        date_obj = datetime.now()
        
    year = date_obj.year
    month = date_obj.strftime("%b")
    day = date_obj.day
    week = date_obj.strftime("%W")
    
    if not time_str:
        time_str = date_obj.strftime("%H:%M:00")
    if not ampm_str:
        ampm_str = date_obj.strftime("%A")
        
    db_client.execute_query(
        """
        INSERT INTO tb_punchsheet (year, month, day, week, employee_id, job_detail_id, startstop, start_time, start_time_AMPM)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (year, month, day, int(week), employee_id, str(job_detail_id), startstop, time_str, ampm_str)
    )
    return True

def clock_in(employee_id):
    """
    Records daily entry attendance.
    """
    print(f"Clocking in Employee ID {employee_id}")
    return record_punch(employee_id, "CLOCK IN", "START")

def clock_out(employee_id):
    """
    Records daily exit attendance.
    """
    print(f"Clocking out Employee ID {employee_id}")
    # Insert STOP record for CLOCK OUT
    now = datetime.now()
    year = now.year
    month = now.strftime("%b")
    day = now.day
    week = now.strftime("%W")
    time_str = now.strftime("%H:%M:00")
    ampm_str = now.strftime("%A")
    
    db_client.execute_query(
        """
        INSERT INTO tb_punchsheet (year, month, day, week, employee_id, job_detail_id, startstop, stop_time, stop_time_AMPM)
        VALUES (?, ?, ?, ?, ?, 'CLOCK OUT', 'STOP', ?, ?)
        """,
        (year, month, day, int(week), employee_id, time_str, ampm_str)
    )
    return True

def start_task_work(employee_id, detail_id):
    """
    Records worker start of assembly/fabrication on a specific job detail item.
    """
    print(f"Starting work on Detail ID {detail_id} for Employee {employee_id}")
    return record_punch(employee_id, detail_id, "START")

def stop_task_work(employee_id, detail_id):
    """
    Records worker pause or stop on a specific job detail item.
    """
    print(f"Stopping work on Detail ID {detail_id} for Employee {employee_id}")
    now = datetime.now()
    year = now.year
    month = now.strftime("%b")
    day = now.day
    week = now.strftime("%W")
    time_str = now.strftime("%H:%M:00")
    ampm_str = now.strftime("%A")
    
    db_client.execute_query(
        """
        INSERT INTO tb_punchsheet (year, month, day, week, employee_id, job_detail_id, startstop, stop_time, stop_time_AMPM)
        VALUES (?, ?, ?, ?, ?, ?, 'STOP', ?, ?)
        """,
        (year, month, day, int(week), employee_id, str(detail_id), time_str, ampm_str)
    )
    return True

def calculate_daily_man_hours(employee_id, year, month, day):
    """
    Calculates elapsed hours worked on task details for an employee on a specific date.
    Parses START and STOP punch times and returns sum in hours.
    """
    # Fetch all punches for this employee on the specified day
    punches = db_client.fetch_all(
        """
        SELECT job_detail_id, startstop, start_time, stop_time 
        FROM tb_punchsheet 
        WHERE employee_id = ? AND year = ? AND month = ? AND day = ?
        ORDER BY id ASC
        """,
        (employee_id, year, month, day)
    )
    
    total_seconds = 0
    active_starts = {}
    
    for p in punches:
        detail_id = p["job_detail_id"]
        # Skip general clock-in/out
        if detail_id in ["CLOCK IN", "CLOCK OUT"]:
            continue
            
        startstop = p["startstop"]
        
        if startstop == "START" and p["start_time"]:
            try:
                t_start = datetime.strptime(p["start_time"], "%H:%M:%S")
                active_starts[detail_id] = t_start
            except ValueError:
                pass
        elif startstop == "STOP" and p["stop_time"]:
            if detail_id in active_starts:
                try:
                    t_stop = datetime.strptime(p["stop_time"], "%H:%M:%S")
                    t_start = active_starts[detail_id]
                    elapsed = (t_stop - t_start).total_seconds()
                    if elapsed > 0:
                        total_seconds += elapsed
                    del active_starts[detail_id]
                except ValueError:
                    pass
                    
    return round(total_seconds / 3600.0, 2)

def main():
    print("Running Punch Pipeline verification test...")
    # Test data setup (Employee ID: 99, Date: 2026 Jun 11)
    test_emp = 99
    db_client.execute_query("DELETE FROM tb_punchsheet WHERE employee_id = ?", (test_emp,))
    
    # Simulate Clock In
    clock_in(test_emp)
    
    # Simulate start and stop on Detail ID 501
    # We pass fixed time variables for reliable math checks
    base_date = datetime(2026, 6, 11, 8, 0, 0)
    record_punch(test_emp, 501, "START", "08:00:00", "AM", base_date)
    
    stop_date = datetime(2026, 6, 11, 12, 30, 0)
    # Simulate stop manually with stop time
    db_client.execute_query(
        """
        INSERT INTO tb_punchsheet (year, month, day, week, employee_id, job_detail_id, startstop, stop_time, stop_time_AMPM)
        VALUES (2026, 'Jun', 11, 23, ?, '501', 'STOP', '12:30:00', 'PM')
        """,
        (test_emp,)
    )
    
    # Simulate Clock Out
    clock_out(test_emp)
    
    # Verify man-hour calculations
    hours = calculate_daily_man_hours(test_emp, 2026, "Jun", 11)
    print(f"Calculated worked hours for Employee {test_emp}: {hours} hours (Expected: 4.5 hours)")
    
    if hours == 4.5:
        print("Punch Pipeline verification completed successfully.")
    else:
        print("ERROR: Inconsistent man-hours result.")
        sys.exit(1)

if __name__ == "__main__":
    main()
