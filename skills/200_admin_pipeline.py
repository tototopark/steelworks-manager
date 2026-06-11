"""
skills/200_admin_pipeline.py
Pipeline for Admin related utilities (Migration, Password reset, DB inspection)
"""
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core import db_client
from passlib.context import CryptContext

TABLE_METADATA = {
    "tb_export_data": {"desc": "Exported data records for external systems", "rel": "None"},
    "tb_jobs": {"desc": "Core job/project information", "rel": "1:N with tb_jobs_details, tb_tasks"},
    "tb_jobs_date_install": {"desc": "Installation scheduling for jobs", "rel": "N:1 with tb_jobs"},
    "tb_jobs_dates": {"desc": "Key timeline dates for jobs", "rel": "N:1 with tb_jobs"},
    "tb_jobs_details": {"desc": "Detailed items/components belonging to a job", "rel": "N:1 with tb_jobs"},
    "tb_keys_remote_devices": {"desc": "Keys/Access control for remote devices", "rel": "None"},
    "tb_leaves": {"desc": "Employee leave/holiday records", "rel": "N:1 with tb_login"},
    "tb_login": {"desc": "Employee master accounts & roles", "rel": "1:N with tb_tasks, tb_punchsheet"},
    "tb_photos": {"desc": "Job site or inspection photos", "rel": "N:1 with tb_jobs"},
    "tb_production_plan": {"desc": "Production planning schedules", "rel": "N:1 with tb_jobs"},
    "tb_public_holidays": {"desc": "Public holidays reference table", "rel": "None"},
    "tb_punchsheet": {"desc": "Employee clock-in / clock-out records", "rel": "N:1 with tb_login"},
    "tb_reminder_other": {"desc": "General system reminders", "rel": "None"},
    "tb_reminder_vehicle": {"desc": "Vehicle maintenance reminders", "rel": "None"},
    "tb_tasks": {"desc": "Specific tasks assigned to jobs/sites", "rel": "N:1 with tb_jobs, N:M with tb_login"},
    "tb_tasks_employees_affectation": {"desc": "Task-Employee assignment mapping", "rel": "N:1 with tb_tasks, tb_login"},
    "tb_week_notes": {"desc": "Weekly production/manager notes", "rel": "None"},
    "tb_wip": {"desc": "Work in progress & QA inspection records", "rel": "N:1 with tb_jobs"}
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def migrate_legacy_data():
    """
    Triggers the legacy migration script logic.
    Automatically resets all passwords to 12345678 after migration to prevent admin lockout.
    """
    try:
        from tests import import_legacy
        import_legacy.import_legacy_data()
        
        # Auto-reset passwords
        reset_res = reset_all_passwords()
        if reset_res["status"] == "error":
            return {"status": "error", "message": f"Migration succeeded, but password reset failed: {reset_res['message']}"}
            
        return {"status": "success", "message": "Legacy database successfully migrated and all passwords have been reset to 12345678."}
    except Exception as e:
        return {"status": "error", "message": f"Migration failed: {str(e)}"}

def reset_all_passwords():
    """
    Resets all employee passwords to '12345678'.
    """
    try:
        hashed_pw = pwd_context.hash("12345678")
        db_client.execute_query("UPDATE tb_login SET password = ?", (hashed_pw,))
        return {"status": "success", "message": "All passwords have been reset to 12345678."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to reset passwords: {str(e)}"}

def get_tables_list():
    """
    Returns the list of tables we care about.
    """
    from tests.db_inspector import TABLES
    result = []
    for table in TABLES:
        meta = TABLE_METADATA.get(table, {"desc": "", "rel": ""})
        try:
            count_res = db_client.fetch_one(f"SELECT COUNT(*) as cnt FROM {table}")
            cnt = count_res["cnt"] if count_res else 0
            result.append({"table_name": table, "row_count": cnt, "desc": meta["desc"], "rel": meta["rel"]})
        except Exception:
            result.append({"table_name": table, "row_count": -1, "error": True, "desc": meta["desc"], "rel": meta["rel"]})
    return result

def get_table_data(table_name, limit=10, offset=0, sort_order="desc"):
    """
    Returns schema and data for a specific table with pagination.
    """
    try:
        # Schema
        info = db_client.fetch_all(f"PRAGMA table_info({table_name})")
        columns = [{"cid": col["cid"], "name": col["name"], "type": col["type"], "notnull": col["notnull"], "pk": col["pk"]} for col in info]
        
        # Order
        order_clause = "DESC" if sort_order.lower() == "desc" else "ASC"
        
        # Records
        query = f"SELECT * FROM {table_name} ORDER BY id {order_clause} LIMIT ? OFFSET ?"
        records = db_client.fetch_all(query, (limit, offset))
        
        count_res = db_client.fetch_one(f"SELECT COUNT(*) as cnt FROM {table_name}")
        cnt = count_res["cnt"] if count_res else 0
        
        meta = TABLE_METADATA.get(table_name, {"desc": "", "rel": ""})

        return {
            "status": "success", 
            "table_name": table_name,
            "desc": meta["desc"],
            "rel": meta["rel"],
            "total_rows": cnt,
            "columns": columns, 
            "data": records
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_system_health():
    """
    Performs a quick smoke check on the server and database status.
    """
    import datetime
    from configs import app_config
    
    health = {
        "status": "success",
        "server_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "python_version": sys.version.split(' ')[0],
        "db_type": app_config.DB_TYPE,
        "db_status": "Unknown",
        "db_size_mb": 0,
        "schema_integrity": "Unknown"
    }
    
    try:
        # Check DB connectivity
        db_client.fetch_one("SELECT 1")
        health["db_status"] = "Connected / OK"
        
        # Check DB file size for sqlite
        if app_config.DB_TYPE == "sqlite" and os.path.exists(app_config.SQLITE_DB_PATH):
            size_bytes = os.path.getsize(app_config.SQLITE_DB_PATH)
            health["db_size_mb"] = round(size_bytes / (1024 * 1024), 2)
            
        # Quick schema check (count tables)
        tables = db_client.fetch_one("SELECT COUNT(*) as cnt FROM sqlite_master WHERE type='table'")
        health["schema_integrity"] = f"{tables['cnt']} tables verified" if tables else "Error"
        
    except Exception as e:
        health["db_status"] = f"Error: {str(e)}"
        
    return health

def factory_reset_database():
    """
    WARNING: DESTRUCTIVE ACTION.
    Deletes all operational data from the database, retaining only:
    - Master configurations (holidays, vehicles)
    - Admin users (right_level >= 10)
    """
    try:
        tables_to_clear = [
            "tb_jobs", "tb_jobs_details", "tb_wip", 
            "tb_punchsheet", "tb_task", "tb_week_notes", 
            "tb_production_plan"
        ]
        
        # 1. Clear operational tables
        for table in tables_to_clear:
            db_client.execute_query(f"DELETE FROM {table}")
            
        # 2. Clear non-admin employees
        db_client.execute_query("DELETE FROM tb_login WHERE right_level < 10")
        
        # 3. Reset auto-increment sequences for cleared tables
        for table in tables_to_clear:
            db_client.execute_query("DELETE FROM sqlite_sequence WHERE name = ?", (table,))
        
        # Also reset sequence for tb_login
        db_client.execute_query("DELETE FROM sqlite_sequence WHERE name = 'tb_login'")
            
        return {"status": "success", "message": "Factory reset completed. All operational data has been wiped."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_integrity_check(fix=False):
    """
    Checks for referential integrity violations and optionally repairs them.
    Returns JSON structured result instead of printing to console.
    """
    try:
        from tests import db_integrity_checker
        
        # 1. Backup first
        if fix:
            success = db_integrity_checker.perform_db_backup()
            if not success:
                return {"status": "error", "message": "Failed to create DB backup before repair."}
        
        violations = {}
        total_violations = 0
        
        # Query 1: Orphan tb_jobs_details
        orphan_details = db_client.fetch_all(
            "SELECT d.id FROM tb_jobs_details d LEFT JOIN tb_jobs j ON d.job_number = j.job_number WHERE j.job_number IS NULL"
        )
        violations["Orphan tb_jobs_details"] = len(orphan_details)
        total_violations += len(orphan_details)
        
        # Query 2: Orphan tb_wip
        orphan_wip = db_client.fetch_all(
            "SELECT w.id FROM tb_wip w LEFT JOIN tb_jobs_details d ON w.tb_jobs_id = d.id WHERE d.id IS NULL"
        )
        violations["Orphan tb_wip"] = len(orphan_wip)
        total_violations += len(orphan_wip)
        
        # Query 3: Orphan tb_punchsheet
        orphan_punch = db_client.fetch_all(
            "SELECT p.id FROM tb_punchsheet p LEFT JOIN tb_jobs_details d ON CAST(p.job_detail_id AS INTEGER) = d.id WHERE d.id IS NULL AND p.job_detail_id IS NOT NULL AND p.job_detail_id != ''"
        )
        violations["Orphan tb_punchsheet"] = len(orphan_punch)
        total_violations += len(orphan_punch)

        # Query 4: Orphan tb_tasks_employees_affectation
        orphan_tasks_aff = db_client.fetch_all(
            "SELECT a.id FROM tb_tasks_employees_affectation a LEFT JOIN tb_tasks t ON a.id = t.id WHERE t.id IS NULL"
        )
        violations["Orphan tb_tasks_employees_affectation"] = len(orphan_tasks_aff)
        total_violations += len(orphan_tasks_aff)

        messages = []
        
        if total_violations == 0:
            messages.append("All database relations are healthy. No issues found.")
        elif not fix:
            messages.append(f"Found {total_violations} integrity violations. Run with repair mode to fix these violations.")
        else:
            # Execute Repairs
            if orphan_details:
                ids = [str(item["id"]) for item in orphan_details]
                db_client.execute_query(f"DELETE FROM tb_jobs_details WHERE id IN ({', '.join(ids)})")
                messages.append(f"Deleted {len(orphan_details)} orphan tb_jobs_details records.")
                
            if orphan_wip:
                ids = [str(item["id"]) for item in orphan_wip]
                db_client.execute_query(f"DELETE FROM tb_wip WHERE id IN ({', '.join(ids)})")
                messages.append(f"Deleted {len(orphan_wip)} orphan tb_wip records.")
                
            if orphan_punch:
                ids = [str(item["id"]) for item in orphan_punch]
                db_client.execute_query(f"UPDATE tb_punchsheet SET job_detail_id = NULL WHERE id IN ({', '.join(ids)})")
                messages.append(f"Cleared job_detail_id reference for {len(orphan_punch)} orphan punchsheets.")
                
            if orphan_tasks_aff:
                ids = [str(item["id"]) for item in orphan_tasks_aff]
                db_client.execute_query(f"DELETE FROM tb_tasks_employees_affectation WHERE id IN ({', '.join(ids)})")
                messages.append(f"Deleted {len(orphan_tasks_aff)} orphan affectation records.")
                
            messages.append("Database repair successfully completed.")

        return {
            "status": "success",
            "total_violations": total_violations,
            "violations": violations,
            "messages": messages,
            "repaired": fix and total_violations > 0
        }
    except Exception as e:
        return {"status": "error", "message": f"Integrity check failed: {str(e)}"}
