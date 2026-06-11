import os
import sys
import subprocess

# Set project root path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

def print_header():
    print("="*60)
    print("            STEELWORKS MANAGER - BACKEND CONTROL PANEL")
    print("="*60)

def print_menu():
    print(" --- RUNTIME PIPELINES ---")
    print(" [1] Run Job Ingestion Pipeline (skills/010_job_pipeline.py)")
    print(" [2] Run Task Assignment Pipeline (skills/020_task_pipeline.py)")
    print(" [3] Run Work Punchsheet Pipeline (skills/030_punch_pipeline.py)")
    print(" [4] Run Quality Inspection Pipeline (skills/040_inspect_pipeline.py)")
    print(" [5] Show Active Job Progress (Pipeline Status View)")
    print("")
    print(" --- MASTER REGISTRATION (UNDER DEVELOPMENT) ---")
    print(" [110] Employee Master Register (future implementation)")
    print(" [120] Vehicle & Reminder Master Register (future implementation)")
    print("")
    print(" --- ONETIME UTILITIES ---")
    print(" [100] Database Viewer & Inspector (tests/db_inspector.py)")
    print(" [101] Initialize Database (tests/db_init.py)")
    print(" [102] Import Legacy MariaDB Data (tests/import_legacy.py)")
    print(" [103] Generate Random Mock Data (tests/mock_data_generator.py)")
    print(" [104] Run Database Smoke Check (tests/smoke_check.py)")
    print(" [105] Reset Mock Data Only (tests/mock_data_cleaner.py)")
    print(" [106] Run Database Integrity Checker (tests/db_integrity_checker.py)")
    print(" [107] Show Web API Server Connection URL Info")
    print("")
    print(" [0] Exit")
    print("="*60)

def run_script(script_path):
    print(f"\nExecuting: {script_path}")
    print("-" * 50)
    try:
        # Resolve path to ensure correct file execution
        full_path = os.path.join(project_root, script_path)
        result = subprocess.run([sys.executable, full_path], check=True)
        print("-" * 50)
        print("Execution finished successfully.")
    except subprocess.CalledProcessError as e:
        print("-" * 50)
        print(f"Execution failed with return code {e.returncode}")
    except Exception as e:
        print(f"Error executing script: {str(e)}")
    print("\nPress Enter to return to menu...")
    input()

def show_active_jobs():
    from core import db_client
    print("\nFetching Job Progress from Database...")
    print("-" * 60)
    try:
        # Get active jobs
        jobs = db_client.fetch_all(
            "SELECT job_number, company_name, site_address, date_creation FROM tb_jobs ORDER BY date_creation DESC LIMIT 10"
        )
        if not jobs:
            print("No jobs found in the database. Please import or generate mock data first.")
        else:
            print(f"{'JOB NO':<8} | {'COMPANY':<20} | {'SITE ADDRESS':<25} | {'DETAILS'}")
            print("-" * 60)
            for j in jobs:
                job_num = j["job_number"]
                company = j["company_name"][:20]
                address = j["site_address"][:25]
                
                # Fetch details count
                details = db_client.fetch_one(
                    "SELECT COUNT(*) as tot, SUM(made) as completed FROM tb_jobs_details WHERE job_number = ?",
                    (job_num,)
                )
                tot_members = details["tot"] if details else 0
                completed_members = details["completed"] if details and details["completed"] else 0
                
                progress = f"{completed_members}/{tot_members} made" if tot_members > 0 else "0/0 details"
                print(f"{job_num:<8} | {company:<20} | {address:<25} | {progress}")
    except Exception as e:
        print(f"Error fetching job data: {str(e)}")
    print("-" * 60)
    print("\nPress Enter to return to menu...")
    input()

def main():
    while True:
        # Clear screen on Windows
        os.system('cls' if os.name == 'nt' else 'clear')
        print_header()
        print_menu()
        choice = input("Enter choice: ").strip()
        
        if choice == "1":
            run_script(os.path.join("skills", "010_job_pipeline.py"))
        elif choice == "2":
            run_script(os.path.join("skills", "020_task_pipeline.py"))
        elif choice == "3":
            run_script(os.path.join("skills", "030_punch_pipeline.py"))
        elif choice == "4":
            run_script(os.path.join("skills", "040_inspect_pipeline.py"))
        elif choice == "5":
            show_active_jobs()
        elif choice == "100":
            run_script(os.path.join("tests", "db_inspector.py"))
        elif choice == "101":
            run_script(os.path.join("tests", "db_init.py"))
        elif choice == "102":
            run_script(os.path.join("tests", "import_legacy.py"))
        elif choice == "103":
            run_script(os.path.join("tests", "mock_data_generator.py"))
        elif choice == "104":
            run_script(os.path.join("tests", "smoke_check.py"))
        elif choice == "105":
            run_script(os.path.join("tests", "mock_data_cleaner.py"))
        elif choice == "106":
            run_script(os.path.join("tests", "db_integrity_checker.py"))
        elif choice == "107":
            print("\n" + "="*50)
            print("         WEB API SERVER CONNECTION INFO")
            print("="*50)
            print("  Main Base URL    : http://127.0.0.1:3600")
            print("  API Docs (Swagger): http://127.0.0.1:3600/docs")
            print("  Alternative Host : http://localhost:3600")
            print("="*50)
            print("  * Web API is currently running in background.")
            print("  * Access the URLs above via web browser to interact.")
            input("\nPress Enter to return to menu...")
        elif choice == "110":
            run_script(os.path.join("skills", "110_employee_master.py"))
        elif choice == "120":
            run_script(os.path.join("skills", "120_reminder_master.py"))
        elif choice == "0":
            print("\nExiting Control Panel. Goodbye.")
            sys.exit(0)
        else:
            print("\nInvalid choice. Press Enter to try again...")
            input()

if __name__ == "__main__":
    main()
