"""
tests/db_init.py
Database Initialization Utility. Recreates database schemas for both SQLite and MySQL.
Runs as a one-time environment setup script.
"""

import re
import sys
import os

# Set project root path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core import db_client
from configs import app_config

TABLE_SCHEMAS = {
    "tb_export_data": """
        CREATE TABLE tb_export_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name VARCHAR(100) NOT NULL,
            export_date DATE NOT NULL,
            export_time TIME NOT NULL,
            export_by VARCHAR(255) NOT NULL
        )
    """,
    "tb_jobs": """
        CREATE TABLE tb_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_creation DATE NOT NULL,
            job_number INTEGER NOT NULL,
            quote_confirmed INT DEFAULT NULL,
            company_name VARCHAR(255) NOT NULL,
            site_address VARCHAR(255) NOT NULL,
            superlot VARCHAR(255) NOT NULL,
            lot_group VARCHAR(255) NOT NULL,
            supervisor_name VARCHAR(255) NOT NULL,
            builder_name VARCHAR(255) NOT NULL,
            installer_name VARCHAR(255) NOT NULL,
            date_last_update DATE NOT NULL,
            install_type TEXT DEFAULT NULL,
            note_unfinished_work TEXT DEFAULT NULL,
            note_other TEXT DEFAULT NULL,
            WIP_Completed INT DEFAULT NULL,
            WIP_Completed_Date DATE DEFAULT NULL,
            WIP_Issue_Date DATE DEFAULT NULL,
            WIP_Revision_Date DATE DEFAULT NULL,
            WIP_Revision VARCHAR(2) DEFAULT NULL,
            WIP_Revision_comment TEXT DEFAULT NULL,
            PAINT_CSP_KEY INT DEFAULT NULL,
            PAINT_CSP_DATE DATE DEFAULT NULL,
            PAINT_CSP_PO VARCHAR(6) DEFAULT NULL,
            PAINT_ASB_KEY INT DEFAULT NULL,
            PAINT_ASB_DATE DATE DEFAULT NULL,
            PAINT_ASB_PO VARCHAR(6) DEFAULT NULL,
            PAINT_MET_KEY INT DEFAULT NULL,
            PAINT_MET_DATE DATE DEFAULT NULL,
            PAINT_MET_PO VARCHAR(6) DEFAULT NULL,
            PAINT_OTHER_KEY INT DEFAULT NULL,
            PAINT_OTHER_DATE DATE DEFAULT NULL,
            PAINT_OTHER_PO VARCHAR(6) DEFAULT NULL,
            PAINT_COMMENT TEXT DEFAULT NULL,
            FASTENER_SUP INT DEFAULT NULL,
            FASTENER_PO INTEGER DEFAULT NULL,
            FASTENER_EMPLOYEE VARCHAR(15) DEFAULT NULL,
            FASTENER_KEY INT DEFAULT NULL,
            FASTENER_DATE DATE DEFAULT NULL
        )
    """,
    "tb_jobs_date_install": """
        CREATE TABLE tb_jobs_date_install (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_creation DATE DEFAULT NULL,
            job_number INTEGER NOT NULL,
            lot INTEGER NOT NULL,
            date_install DATE DEFAULT NULL,
            status_install VARCHAR(255) NOT NULL
        )
    """,
    "tb_jobs_dates": """
        CREATE TABLE tb_jobs_dates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_number INTEGER NOT NULL,
            year INTEGER NOT NULL,
            inq_consented_plans DATE DEFAULT NULL,
            rec_consented_plans DATE DEFAULT NULL,
            com_consented_plans VARCHAR(25) DEFAULT NULL,
            inq_prenail_digital_files DATE DEFAULT NULL,
            rec_prenail_digital_files DATE DEFAULT NULL,
            com_prenail_digital_files VARCHAR(25) DEFAULT NULL,
            inq_RFI DATE DEFAULT NULL,
            rec_RFI DATE DEFAULT NULL,
            com_RFI VARCHAR(25) DEFAULT NULL,
            inq_coating_schedule DATE DEFAULT NULL,
            rec_coating_schedule DATE DEFAULT NULL,
            com_coating_schedule VARCHAR(25) DEFAULT NULL,
            inq_approval_archi DATE DEFAULT NULL,
            rec_approval_archi DATE DEFAULT NULL,
            com_approval_archi VARCHAR(25) DEFAULT NULL,
            inq_approval_engineers DATE DEFAULT NULL,
            rec_approval_engineers DATE DEFAULT NULL,
            com_approval_engineers VARCHAR(25) DEFAULT NULL,
            inq_steel_purchase DATE DEFAULT NULL,
            rec_steel_purchase DATE DEFAULT NULL,
            com_steel_purchase VARCHAR(25) DEFAULT NULL,
            inq_QA_doc DATE DEFAULT NULL,
            rec_QA_doc DATE DEFAULT NULL,
            com_QA_doc VARCHAR(25) DEFAULT NULL,
            inq_SSSP DATE DEFAULT NULL,
            rec_SSSP DATE DEFAULT NULL,
            com_SSSP VARCHAR(25) DEFAULT NULL,
            inq_invoice DATE DEFAULT NULL,
            rec_invoice DATE DEFAULT NULL,
            com_invoice VARCHAR(25) DEFAULT NULL
        )
    """,
    "tb_jobs_details": """
        CREATE TABLE tb_jobs_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_creation DATE NOT NULL,
            job_number INTEGER NOT NULL,
            page INTEGER NOT NULL,
            lot INTEGER NOT NULL,
            member VARCHAR(255) NOT NULL,
            GalvAndPaint INT DEFAULT NULL,
            quoted_det_hours DECIMAL(5,2) DEFAULT NULL,
            quoted_fab_hours DECIMAL(5,2) DEFAULT NULL,
            quoted_install_hours DECIMAL(5,2) DEFAULT NULL,
            quoted_truck_hours DECIMAL(5,2) DEFAULT NULL,
            design INT DEFAULT NULL,
            design_date_update DATE DEFAULT NULL,
            approved INT DEFAULT NULL,
            approved_date DATE DEFAULT NULL,
            made INT DEFAULT NULL,
            made_date_update DATE DEFAULT NULL,
            made_by VARCHAR(255) DEFAULT NULL,
            loaded INT DEFAULT NULL,
            load_date_update DATE DEFAULT NULL,
            on_site INT DEFAULT NULL,
            on_site_date_update DATE DEFAULT NULL,
            temp_fix INT DEFAULT NULL,
            temp_fix_date_update DATE DEFAULT NULL,
            chemset INT DEFAULT NULL,
            chemset_date_update DATE DEFAULT NULL,
            tightened INT DEFAULT NULL,
            tightened_date_update DATE DEFAULT NULL,
            finish INT DEFAULT NULL,
            finish_date_update DATE DEFAULT NULL,
            finish_by VARCHAR(255) DEFAULT NULL
        )
    """,
    "tb_keys_remote_devices": """
        CREATE TABLE tb_keys_remote_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_device VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            private_key VARCHAR(255) NOT NULL,
            ip VARCHAR(15) DEFAULT NULL,
            attempt_connection INT DEFAULT NULL,
            admin_validation INT NOT NULL
        )
    """,
    "tb_leaves": """
        CREATE TABLE tb_leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            comment TEXT NOT NULL,
            date_start DATE NOT NULL,
            date_stop DATE NOT NULL
        )
    """,
    "tb_login": """
        CREATE TABLE tb_login (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            firstname VARCHAR(255) NOT NULL,
            surname VARCHAR(255) NOT NULL,
            avatar VARCHAR(255) NOT NULL,
            bay INTEGER DEFAULT NULL,
            date_creation DATE NOT NULL,
            role VARCHAR(255) DEFAULT NULL,
            right_level INT NOT NULL,
            shop_label VARCHAR(1) DEFAULT NULL,
            admin_validation INT NOT NULL,
            site_safe_passport VARCHAR(15) DEFAULT NULL,
            site_safe_category VARCHAR(15) DEFAULT NULL,
            site_safe_exp_date DATE DEFAULT NULL,
            first_aid INT DEFAULT NULL,
            ip_1 VARCHAR(15) DEFAULT NULL,
            ip_2 VARCHAR(15) DEFAULT NULL,
            ip_3 VARCHAR(15) DEFAULT NULL
        )
    """,
    "tb_photos": """
        CREATE TABLE tb_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_number VARCHAR(4) NOT NULL,
            year_creation VARCHAR(4) NOT NULL,
            photo_name VARCHAR(50) NOT NULL
        )
    """,
    "tb_production_plan": """
        CREATE TABLE tb_production_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            priority INTEGER NOT NULL,
            job_number INTEGER NOT NULL,
            date_creation DATE NOT NULL,
            lot INTEGER NOT NULL
        )
    """,
    "tb_public_holidays": """
        CREATE TABLE tb_public_holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date_start DATE NOT NULL,
            date_stop DATE NOT NULL
        )
    """,
    "tb_punchsheet": """
        CREATE TABLE tb_punchsheet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            month VARCHAR(3) DEFAULT NULL,
            day INTEGER DEFAULT NULL,
            week INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            job_detail_id VARCHAR(255) DEFAULT NULL,
            startstop TEXT DEFAULT NULL,
            start_time TIME DEFAULT NULL,
            start_time_AMPM VARCHAR(2) DEFAULT NULL,
            stop_time TIME DEFAULT NULL,
            stop_time_AMPM VARCHAR(2) DEFAULT NULL
        )
    """,
    "tb_reminder_other": """
        CREATE TABLE tb_reminder_other (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) DEFAULT NULL,
            comment VARCHAR(255) DEFAULT NULL,
            expiry_date DATE DEFAULT NULL
        )
    """,
    "tb_reminder_vehicle": """
        CREATE TABLE tb_reminder_vehicle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Vehicle VARCHAR(50) NOT NULL,
            Plate VARCHAR(10) NOT NULL,
            WOF DATE DEFAULT NULL,
            REGO DATE DEFAULT NULL,
            SERVICE INTEGER DEFAULT NULL,
            RUC INTEGER DEFAULT NULL,
            Current_ODO INTEGER DEFAULT NULL,
            VeederEroad INTEGER DEFAULT NULL
        )
    """,
    "tb_tasks": """
        CREATE TABLE tb_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site VARCHAR(255) DEFAULT NULL,
            task VARCHAR(255) NOT NULL,
            employee_group INT DEFAULT NULL,
            employee INT DEFAULT NULL,
            published INT DEFAULT NULL,
            expiry_date DATE DEFAULT NULL,
            finished INT DEFAULT NULL,
            finished_by VARCHAR(100) DEFAULT NULL,
            finished_date DATE DEFAULT NULL
        )
    """,
    "tb_tasks_employees_affectation": """
        CREATE TABLE tb_tasks_employees_affectation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_1 VARCHAR(255) DEFAULT NULL,
            employee_2 VARCHAR(255) DEFAULT NULL,
            employee_3 VARCHAR(255) DEFAULT NULL,
            employee_4 VARCHAR(255) DEFAULT NULL,
            employee_5 VARCHAR(255) DEFAULT NULL,
            employee_6 VARCHAR(255) DEFAULT NULL,
            employee_7 VARCHAR(255) DEFAULT NULL,
            employee_8 VARCHAR(255) DEFAULT NULL,
            employee_9 VARCHAR(255) DEFAULT NULL,
            employee_10 VARCHAR(255) DEFAULT NULL
        )
    """,
    "tb_week_notes": """
        CREATE TABLE tb_week_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            note TEXT DEFAULT NULL,
            note2 TEXT DEFAULT NULL
        )
    """,
    "tb_wip": """
        CREATE TABLE tb_wip (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tb_jobs_id INTEGER NOT NULL,
            wps VARCHAR(255) NOT NULL,
            in_house_inspector VARCHAR(255) DEFAULT NULL,
            in_house_exam_type VARCHAR(255) DEFAULT NULL,
            in_house_report_number VARCHAR(255) DEFAULT NULL,
            third_party_inspector VARCHAR(255) DEFAULT NULL,
            third_party_exam_type VARCHAR(255) DEFAULT NULL,
            third_party_report_number VARCHAR(255) DEFAULT NULL,
            inspection_date DATE DEFAULT NULL,
            inspection_pass_fail INT NOT NULL,
            wip_version INTEGER DEFAULT NULL,
            wip_version_date DATE DEFAULT NULL,
            comment TEXT DEFAULT NULL
        )
    """
}

def convert_mysql_to_sqlite(schema_sql):
    """
    Transforms clean SQL script to match SQLite syntax if necessary.
    Since templates are already SQLite-compatible, this ensures safety.
    """
    return schema_sql

def create_tables():
    print(f"Initializing Database... (Type: {app_config.DB_TYPE})")
    
    for table_name, schema in TABLE_SCHEMAS.items():
        # Drop existing tables to guarantee fresh setup
        print(f"Recreating table: {table_name}")
        db_client.execute_query(f"DROP TABLE IF EXISTS {table_name}")
        
        # Adjust SQL syntax for sqlite if needed
        sql = schema
        if app_config.DB_TYPE == "sqlite":
            sql = convert_mysql_to_sqlite(schema)
        else:
            # For MySQL, replace AUTOINCREMENT with AUTO_INCREMENT and set engine
            sql = sql.replace("AUTOINCREMENT", "AUTO_INCREMENT")
            sql = sql.replace("INTEGER PRIMARY KEY AUTO_INCREMENT", "int(11) NOT NULL AUTO_INCREMENT")
            sql += " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
            
        db_client.execute_query(sql)
    
    print("Database Initialization Completed Successfully.")

if __name__ == "__main__":
    create_tables()
