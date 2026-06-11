"""
skills/020_task_pipeline.py
Manages shop/site task instructions and assignments to workforce groups.
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

def create_task(site, task_instruction, employee_group=None, employee_id=None, expiry_date=None):
    """
    Creates a new task instruction in tb_tasks and sets initial pending states.
    """
    if not expiry_date:
        # Default expiry date set to 7 days from now
        from datetime import timedelta
        expiry_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
    print(f"Creating task instruction: '{task_instruction}' for site '{site}'")
    
    # 1. Insert into tb_tasks
    db_client.execute_query(
        """
        INSERT INTO tb_tasks (site, task, employee_group, employee, published, expiry_date, finished)
        VALUES (?, ?, ?, ?, 1, ?, 0)
        """,
        (site, task_instruction, employee_group, employee_id, expiry_date)
    )
    
    # Get the last inserted task ID
    res = db_client.fetch_one("SELECT MAX(id) as last_id FROM tb_tasks")
    task_id = res["last_id"] if res else None
    
    if task_id:
        # 2. Insert blank workforce affectation row matching the task ID
        db_client.execute_query(
            "INSERT INTO tb_tasks_employees_affectation (id) VALUES (?)",
            (task_id,)
        )
        return task_id
    return None

def assign_workers_to_task(task_id, workers_list):
    """
    Assigns a list of up to 10 workers to a specific task.
    """
    if not workers_list:
        return False
        
    # Standardize workers list size to 10 slots
    workers_padded = workers_list[:10] + [None] * (10 - len(workers_list))
    
    print(f"Assigning workers to Task ID {task_id}: {', '.join([w for w in workers_list if w])}")
    
    db_client.execute_query(
        """
        UPDATE tb_tasks_employees_affectation
        SET employee_1 = ?, employee_2 = ?, employee_3 = ?, employee_4 = ?, employee_5 = ?,
            employee_6 = ?, employee_7 = ?, employee_8 = ?, employee_9 = ?, employee_10 = ?
        WHERE id = ?
        """,
        (*workers_padded, task_id)
    )
    return True

def complete_task(task_id, finished_by):
    """
    Marks a task as finished and registers the completion date.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"Completing Task ID {task_id} by worker '{finished_by}'")
    
    db_client.execute_query(
        """
        UPDATE tb_tasks
        SET finished = 1, finished_by = ?, finished_date = ?
        WHERE id = ?
        """,
        (finished_by, today_str, task_id)
    )
    return True

def get_active_tasks():
    """
    Retrieves all active (unfinished) tasks and their employee assignments.
    """
    query = """
        SELECT t.id, t.site, t.task, t.employee, t.expiry_date
        FROM tb_tasks t
        WHERE t.finished IS NULL OR t.finished = 0
    """
    return db_client.fetch_all(query)

def get_tasks_by_date(target_date):
    """
    Retrieves tasks that were active on or around a specific historical date.
    """
    query = """
        SELECT t.id, t.site, t.task, t.employee, t.expiry_date
        FROM tb_tasks t
        WHERE (t.finished IS NULL OR t.finished = 0 OR t.finished_date >= ?)
          AND (t.expiry_date >= ? OR t.expiry_date IS NULL)
    """
    return db_client.fetch_all(query, (target_date, target_date))

def main():
    print("Running Task Pipeline verification test...")
    # Clean up previous test task if exist
    db_client.execute_query("DELETE FROM tb_tasks WHERE site = 'TestSitePipeline'")
    
    # Verify creation
    task_id = create_task("TestSitePipeline", "Verify welding seam quality on portal frames")
    if task_id:
        # Verify assignment
        assign_workers_to_task(task_id, ["sam", "felipe"])
        # Verify completion
        complete_task(task_id, "grants")
        
    print("Task Pipeline verification completed successfully.")

if __name__ == "__main__":
    main()
