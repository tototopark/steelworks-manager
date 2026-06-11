"""
core/api_router.py
Defines the FastAPI REST API endpoints to support frontend integration.
Maps HTTP endpoints to database tables and backend processes.
"""

import os
import sys
from datetime import date
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel
from typing import Optional, List
import shutil
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

SECRET_KEY = "my_super_secret_jwt_key_for_steelworks"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Set project root path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core import db_client

app = FastAPI(title="Steelworks Manager API Backend", version="1.0.0")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles

# Create static directory if not exists
static_dir = os.path.join(project_root, "static")
os.makedirs(static_dir, exist_ok=True)

# Mount the static directory to serve frontend HTML/JS/CSS files
# The html=True parameter allows serving index.html automatically at the root path '/'


@app.get("/api/dashboard/job_progress")
async def api_dashboard_job_progress(limit: int = 10):
    try:
        from skills import _300_dashboard_pipeline as dashboard_pipeline
    except ImportError:
        import importlib
        dashboard_pipeline = importlib.import_module("skills.300_dashboard_pipeline")
        
    res = dashboard_pipeline.get_active_jobs_progress(limit)
    if res["status"] == "error":
        raise HTTPException(status_code=500, detail=res["message"])
    return res

@app.get("/api/config/dev_features")
async def api_get_dev_features():
    try:
        from configs.app_config import AUTO_FILL_ENABLED, SHOW_DEV_HINTS
        return {"status": "success", "auto_fill": AUTO_FILL_ENABLED, "dev_hints": SHOW_DEV_HINTS}
    except ImportError:
        return {"status": "success", "auto_fill": False, "dev_hints": False}

# --- Pydantic Schemas ---
class JobCreate(BaseModel):
    job_number: int
    company_name: str
    site_address: str
    superlot: Optional[str] = ""
    lot_group: Optional[str] = ""
    supervisor_name: Optional[str] = ""
    builder_name: Optional[str] = ""
    installer_name: Optional[str] = ""

class JobIngestRequest(BaseModel):
    job_number: int
    company_name: str
    site_address: str
    supervisor_name: Optional[str] = ""
    raw_excel_data: str

class EmployeeCreate(BaseModel):
    login: str
    password: str
    firstname: str
    surname: str
    role: Optional[str] = "Welder"
    right_level: Optional[int] = 1
    bay: Optional[int] = None
    shop_label: Optional[str] = None

class EmployeeUpdate(BaseModel):
    firstname: str
    surname: str
    role: Optional[str] = "Welder"
    right_level: Optional[int] = 1
    bay: Optional[int] = None
    shop_label: Optional[str] = None

class VehicleCreate(BaseModel):
    vehicle: str
    plate: str
    wof: Optional[str] = None
    rego: Optional[str] = None
    service: Optional[int] = None
    ruc: Optional[int] = None
    current_odo: Optional[int] = None

class QAInspectRequest(BaseModel):
    wip_id: int
    is_pass: bool
    comment: Optional[str] = ""

class NoteRequest(BaseModel):
    date: str
    note: str
    note2: Optional[str] = ""

class PlanRequest(BaseModel):
    date: str
    employee_id: int
    job_number: int
    lot: int
    priority: int

class HolidayRequest(BaseModel):
    name: str
    date_start: str
    date_stop: str

class EmployeeCreateRequest(BaseModel):
    firstname: str
    surname: str
    login: str
    password: str
    role: str
    right_level: int

class LoginRequest(BaseModel):
    login: str
    password: str

# --- API Endpoints ---
@app.post("/api/auth/login")
async def auth_login(payload: LoginRequest):
    try:
        from configs import app_config
        
        # 1. Super Admin Fallback (Bypass DB entirely)
        enable_super_admin = getattr(app_config, "ENABLE_SUPER_ADMIN", False)
        if enable_super_admin and \
           payload.login == getattr(app_config, "SUPER_ADMIN_LOGIN", "admin") and \
           payload.password == getattr(app_config, "SUPER_ADMIN_PASS", "12345678"):
            
            expire = datetime.utcnow() + timedelta(hours=24)
            # Give highest right_level (e.g. 99)
            to_encode = {"sub": payload.login, "right_level": 99, "exp": expire}
            token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            return {"status": "success", "token": token, "right_level": 99}
            
        # 2. Standard DB Check
        user = db_client.fetch_one("SELECT id, login, password, right_level FROM tb_login WHERE login = ?", (payload.login,))
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
            
        # If it's the exact plaintext "11111111" before hashing, or standard hashed compare
        valid_password = False
        if payload.password == user['password']: # Fallback for unmigrated plain text just in case
            valid_password = True
        else:
            try:
                valid_password = pwd_context.verify(payload.password, user['password'])
            except Exception as e:
                print(f"Login verify exception: {e}")
                valid_password = False
                
        if not valid_password:
            raise HTTPException(status_code=401, detail="Invalid username or password")
            
        if payload.password == "12345678":
            expire = datetime.utcnow() + timedelta(minutes=10)
            to_encode = {"sub": user['login'], "right_level": user['right_level'], "exp": expire, "require_change": True}
            temp_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            return {"status": "require_change", "temp_token": temp_token, "message": "Initial password detected. Please change your password."}
            
        # Create JWT token
        expire = datetime.utcnow() + timedelta(hours=24)
        to_encode = {"sub": user['login'], "right_level": user['right_level'], "exp": expire}
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        return {"status": "success", "token": token, "right_level": user['right_level']}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
async def get_config():
    try:
        from configs import app_config
        return {"status": "success", "data": {"AUTO_FILL_ENABLED": getattr(app_config, "AUTO_FILL_ENABLED", False)}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChangePasswordRequest(BaseModel):
    temp_token: str
    new_password: str

@app.post("/api/auth/change_password")
async def change_password(payload: ChangePasswordRequest):
    try:
        decoded = jwt.decode(payload.temp_token, SECRET_KEY, algorithms=[ALGORITHM])
        if not decoded.get("require_change"):
            raise HTTPException(status_code=400, detail="Invalid token for password change")
        
        login_id = decoded.get("sub")
        if not login_id:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        if len(payload.new_password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
            
        if payload.new_password == "12345678":
            raise HTTPException(status_code=400, detail="New password cannot be the default password")
            
        hashed_pw = pwd_context.hash(payload.new_password)
        db_client.execute_query("UPDATE tb_login SET password = ? WHERE login = ?", (hashed_pw, login_id))
        
        right_level = decoded.get("right_level")
        expire = datetime.utcnow() + timedelta(hours=24)
        to_encode = {"sub": login_id, "right_level": right_level, "exp": expire}
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        return {"status": "success", "token": token, "right_level": right_level}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# [경고] 새로운 API 라우트(@app.get, @app.post 등)는 반드시 파일 맨 아래의
# `app.mount("/", StaticFiles(...))` 코드 **위쪽**에 추가해야 합니다.
# 아래쪽에 추가하면 StaticFiles가 요청을 가로채어 POST 요청 시 405 에러가 발생합니다.
@app.get("/api/jobs")
async def get_jobs():
    query = "SELECT job_number, company_name, site_address, date_creation FROM tb_jobs ORDER BY date_creation DESC LIMIT 50"
    rows = db_client.fetch_all(query)
    return {"status": "success", "data": rows}

@app.get("/api/jobs/{job_number}/details")
async def api_get_job_details(job_number: int):
    try:
        from skills import _010_job_pipeline as job_pipeline
    except ImportError:
        import importlib
        job_pipeline = importlib.import_module("skills.010_job_pipeline")
        
    details = job_pipeline.get_job_details(job_number)
    return {"status": "success", "data": details}

class JobUpdate(BaseModel):
    company_name: str
    site_address: Optional[str] = None

@app.put("/api/jobs/{job_number}")
async def update_job(job_number: int, payload: JobUpdate):
    try:
        db_client.execute_query(
            "UPDATE tb_jobs SET company_name = ?, site_address = ? WHERE job_number = ?",
            (payload.company_name, payload.site_address, job_number)
        )
        return {"status": "success", "message": "Job updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/jobs/{job_number}")
async def delete_job(job_number: int):
    try:
        # Admin restricted action. The frontend should only show this to Admin.
        # Cascade delete (lots, members, dates, wip, punch etc.)
        db_client.execute_query("DELETE FROM tb_wip WHERE job_number = ?", (job_number,))
        db_client.execute_query("DELETE FROM tb_punchsheet WHERE job_number = ?", (job_number,))
        db_client.execute_query("DELETE FROM tb_job_dates WHERE job_number = ?", (job_number,))
        db_client.execute_query("DELETE FROM tb_job_members WHERE job_number = ?", (job_number,))
        db_client.execute_query("DELETE FROM tb_job_lots WHERE job_number = ?", (job_number,))
        db_client.execute_query("DELETE FROM tb_jobs WHERE job_number = ?", (job_number,))
        return {"status": "success", "message": "Job and all related data deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/ingest")
async def api_jobs_ingest(payload: JobIngestRequest):
    try:
        from skills import _010_job_pipeline as job_pipeline
    except ImportError:
        import importlib
        job_pipeline = importlib.import_module("skills.010_job_pipeline")
        
    try:
        # 1. Create the base job
        job_pipeline.create_job(payload.job_number, payload.company_name, payload.site_address)
        
        # 2. Parse the raw excel data
        lines = payload.raw_excel_data.strip().split('\n')
        ingested_count = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            cols = line.split('\t')
            # Expecting Page \t Lot \t Member
            if len(cols) >= 3:
                page = cols[0].strip()
                lot = cols[1].strip()
                member = cols[2].strip()
                
                # Basic validation / fallback to 1 if not int
                page_val = int(page) if page.isdigit() else 1
                lot_val = int(lot) if lot.isdigit() else 1
                
                job_pipeline.add_job_detail_member(payload.job_number, page_val, lot_val, member)
                ingested_count += 1
                
        return {"status": "success", "message": f"Job {payload.job_number} created with {ingested_count} members ingested."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/api/jobs")
async def create_job(payload: JobCreate):
    try:
        # Check if job already exists
        exists = db_client.fetch_one("SELECT id FROM tb_jobs WHERE job_number = ?", (payload.job_number,))
        if exists:
            raise HTTPException(status_code=400, detail=f"Job number {payload.job_number} already exists.")
            
        db_client.execute_query(
            """
            INSERT INTO tb_jobs (
                date_creation, job_number, company_name, site_address, superlot,
                lot_group, supervisor_name, builder_name, installer_name, date_last_update
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                date.today().isoformat(), payload.job_number, payload.company_name, 
                payload.site_address, payload.superlot, payload.lot_group, 
                payload.supervisor_name, payload.builder_name, payload.installer_name, 
                date.today().isoformat()
            )
        )
        return {"status": "success", "message": f"Job {payload.job_number} created successfully."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PunchAction(BaseModel):
    employee_id: int
    action: str  # "in" or "out"

@app.post("/api/punch")
async def process_punch(payload: PunchAction):
    try:
        from skills import _030_punch_pipeline as punch_pipeline
    except ImportError:
        import importlib
        punch_pipeline = importlib.import_module("skills.030_punch_pipeline")
        
    try:
        if payload.action == "in":
            punch_pipeline.clock_in(payload.employee_id)
        elif payload.action == "out":
            punch_pipeline.clock_out(payload.employee_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        return {"status": "success", "message": f"Successfully punched {payload.action}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class WIPAction(BaseModel):
    job_number: int
    wps: str
    inspector: str
    inspector_type: str  # "in_house" or "third_party"
    pass_fail: int
    comment: Optional[str] = ""

@app.post("/api/wip")
async def process_wip(payload: WIPAction):
    try:
        from skills import _140_wip_pipeline as wip_pipeline
    except ImportError:
        import importlib
        wip_pipeline = importlib.import_module("skills.140_wip_pipeline")
        
    try:
        wip_pipeline.record_wip(
            payload.job_number, payload.wps, payload.inspector, 
            payload.inspector_type, payload.pass_fail, payload.comment
        )
        return {"status": "success", "message": "WIP record saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/active")
async def get_active_tasks_api(date: Optional[str] = None):
    try:
        from skills import _020_task_pipeline as task_pipeline
    except ImportError:
        import importlib
        task_pipeline = importlib.import_module("skills.020_task_pipeline")
        
    try:
        if date:
            tasks = task_pipeline.get_tasks_by_date(date)
        else:
            tasks = task_pipeline.get_active_tasks()
        return {"status": "success", "data": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dev/random-date")
async def get_random_data_date(type: str):
    """Fetches a random date from the database that contains data, useful for UI testing with old data."""
    try:
        if type == "weekly":
            # Just find a date that has either a note or a production plan (from an active employee)
            query = "SELECT date FROM tb_week_notes WHERE date IS NOT NULL AND note != '' ORDER BY RANDOM() LIMIT 1"
            res = db_client.fetch_one(query)
            if not res:
                query = """
                    SELECT p.date 
                    FROM tb_production_plan p
                    JOIN tb_login e ON p.employee_id = e.id
                    WHERE p.date IS NOT NULL AND e.is_active = 1 AND e.admin_validation = 1
                    ORDER BY RANDOM() LIMIT 1
                """
                res = db_client.fetch_one(query)
            return {"status": "success", "date": res["date"] if res else None}
        elif type == "whiteboard":
            query = """
                SELECT t.expiry_date as date 
                FROM tb_tasks t 
                JOIN tb_login e ON t.employee = e.id 
                WHERE t.expiry_date IS NOT NULL 
                  AND e.is_active = 1 AND e.admin_validation = 1 
                  AND e.right_level IN (1, 2, 12)
                ORDER BY RANDOM() LIMIT 1
            """
            res = db_client.fetch_one(query)
            # Fallback if no active tasks found
            if not res:
                query = "SELECT expiry_date as date FROM tb_tasks WHERE expiry_date IS NOT NULL ORDER BY RANDOM() LIMIT 1"
                res = db_client.fetch_one(query)
            return {"status": "success", "date": res["date"] if res else None}
        return {"status": "error", "message": "Invalid type"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dev/qa-test-data")
async def generate_qa_test_data():
    """Sets a few random WIP items to pending (inspection_pass_fail=0) for QA dashboard testing."""
    try:
        db_client.execute_query("""
            UPDATE tb_wip 
            SET inspection_pass_fail = 0 
            WHERE id IN (SELECT id FROM tb_wip ORDER BY RANDOM() LIMIT 5)
        """)
        return {"status": "success", "message": "Test data generated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TaskCreate(BaseModel):
    employee_id: int
    site: str
    task_instruction: str

class TaskUpdate(BaseModel):
    employee_id: int
    site: str
    task_instruction: str

@app.post("/api/tasks")
async def create_task_api(payload: TaskCreate):
    try:
        from skills import _020_task_pipeline as task_pipeline
    except ImportError:
        import importlib
        task_pipeline = importlib.import_module("skills.020_task_pipeline")
        
    try:
        task_pipeline.create_task(payload.site, payload.task_instruction, employee_id=payload.employee_id)
        return {"status": "success", "message": "Task created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/tasks/{task_id}")
async def update_task_api(task_id: int, payload: TaskUpdate):
    try:
        db_client.execute_query(
            "UPDATE tb_tasks SET employee = ?, site = ?, task = ? WHERE id = ?",
            (payload.employee_id, payload.site, payload.task_instruction, task_id)
        )
        return {"status": "success", "message": "Task updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/tasks/{task_id}")
async def delete_task_api(task_id: int):
    try:
        db_client.execute_query("DELETE FROM tb_tasks WHERE id = ?", (task_id,))
        return {"status": "success", "message": "Task deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/employees")
async def get_employees(status: str = "active"):
    try:
        if status == "retired":
            query = "SELECT id, login, firstname, surname, role, right_level, bay, shop_label, avatar FROM tb_login WHERE is_active = 0 OR admin_validation = 0 ORDER BY firstname ASC, surname ASC"
        else:
            # Active (default)
            query = "SELECT id, login, firstname, surname, role, right_level, bay, shop_label, avatar FROM tb_login WHERE (is_active = 1 OR is_active IS NULL) AND admin_validation = 1 ORDER BY firstname ASC, surname ASC"
        
        employees = db_client.fetch_all(query)
        return {"status": "success", "data": employees}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/employees")
async def create_employee(payload: EmployeeCreate):
    try:
        exists = db_client.fetch_one("SELECT id FROM tb_login WHERE login = ?", (payload.login,))
        if exists:
            raise HTTPException(status_code=400, detail=f"Login ID '{payload.login}' already exists.")
            
        hashed_pw = pwd_context.hash("12345678")
        db_client.execute_query(
            """
            INSERT INTO tb_login (
                login, password, firstname, surname, avatar, bay,
                date_creation, role, right_level, shop_label, admin_validation, first_aid
            ) VALUES (?, ?, ?, ?, 'default.png', ?, ?, ?, ?, ?, 1, 0)
            """,
            (
                payload.login, hashed_pw, payload.firstname, payload.surname,
                payload.bay, date.today().isoformat(), payload.role, payload.right_level,
                payload.shop_label
            )
        )
        return {"status": "success", "message": f"Employee {payload.login} registered."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/employees/{emp_id}")
async def update_employee(emp_id: int, payload: EmployeeUpdate):
    try:
        db_client.execute_query(
            """
            UPDATE tb_login 
            SET firstname = ?, surname = ?, role = ?, right_level = ?, bay = ?, shop_label = ?
            WHERE id = ?
            """,
            (payload.firstname, payload.surname, payload.role, payload.right_level, payload.bay, payload.shop_label, emp_id)
        )
        return {"status": "success", "message": "Employee updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/employees/{emp_id}")
async def delete_employee(emp_id: int):
    try:
        db_client.execute_query("UPDATE tb_login SET is_active = 0, admin_validation = 0 WHERE id = ?", (emp_id,))
        return {"status": "success", "message": "Employee deactivated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import random
import string

@app.post("/api/employees/{emp_id}/random-password")
async def generate_random_password(emp_id: int):
    try:
        user = db_client.fetch_one("SELECT id, login FROM tb_login WHERE id = ?", (emp_id,))
        if not user:
            raise HTTPException(status_code=404, detail="Employee not found")
            
        # Generate 8 char alphanumeric random password
        chars = string.ascii_letters + string.digits
        new_password = ''.join(random.choice(chars) for _ in range(8))
        
        # Hash it and save
        hashed_pw = pwd_context.hash(new_password)
        db_client.execute_query("UPDATE tb_login SET password = ? WHERE id = ?", (hashed_pw, emp_id))
        
        return {
            "status": "success", 
            "message": "Random password generated and saved.",
            "new_password": new_password
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Employee Avatar Upload ---
@app.post("/api/employees/{emp_id}/avatar")
async def upload_employee_avatar(emp_id: int, file: UploadFile = File(...)):
    """
    Uploads an avatar photo for an employee.
    Saves to static/uploads/avatars/<emp_id>.<ext> and updates tb_login.avatar.
    """
    try:
        user = db_client.fetch_one("SELECT id, login FROM tb_login WHERE id = ?", (emp_id,))
        if not user:
            raise HTTPException(status_code=404, detail="Employee not found")

        # Validate extension
        allowed = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed:
            raise HTTPException(status_code=400, detail=f"Invalid file type: {ext}. Allowed: {', '.join(allowed)}")

        # Save file
        upload_dir = os.path.join(project_root, "static", "uploads", "avatars")
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"{emp_id}{ext}"
        file_path = os.path.join(upload_dir, filename)

        with open(file_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        # Store relative URL in DB
        avatar_url = f"/uploads/avatars/{filename}"
        db_client.execute_query("UPDATE tb_login SET avatar = ? WHERE id = ?", (avatar_url, emp_id))

        return {"status": "success", "message": "Avatar uploaded.", "avatar_url": avatar_url}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reminders/vehicles")
async def get_vehicles():
    try:
        vehicles = db_client.fetch_all("SELECT * FROM tb_reminder_vehicle")
        return {"status": "success", "data": vehicles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reminders/vehicles")
async def create_vehicle(payload: VehicleCreate):
    try:
        db_client.execute_query(
            """
            INSERT INTO tb_reminder_vehicle (
                Vehicle, Plate, WOF, REGO, SERVICE, RUC, Current_ODO, VeederEroad
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (payload.vehicle, payload.plate, payload.wof, payload.rego, payload.service, payload.ruc, payload.current_odo)
        )
        return {"status": "success", "message": f"Vehicle {payload.vehicle} registered."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/reminders/vehicles/{v_id}")
async def update_vehicle(v_id: int, payload: VehicleCreate):
    try:
        db_client.execute_query(
            """
            UPDATE tb_reminder_vehicle 
            SET Vehicle = ?, Plate = ?, WOF = ?, REGO = ?, SERVICE = ?, RUC = ?, Current_ODO = ?
            WHERE id = ?
            """,
            (payload.vehicle, payload.plate, payload.wof, payload.rego, payload.service, payload.ruc, payload.current_odo, v_id)
        )
        return {"status": "success", "message": "Vehicle updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/reminders/vehicles/{v_id}")
async def delete_vehicle(v_id: int):
    try:
        db_client.execute_query("DELETE FROM tb_reminder_vehicle WHERE id = ?", (v_id,))
        return {"status": "success", "message": "Vehicle deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reminders/vehicles/expiry-check")
async def api_vehicle_expiry_check():
    """
    Returns vehicles with WOF or REGO expiring within 30 days (or already expired).
    """
    try:
        from datetime import date as dt_date, timedelta
        today = dt_date.today()
        warn_date = today + timedelta(days=30)
        today_str = today.isoformat()
        warn_str = warn_date.isoformat()

        vehicles = db_client.fetch_all("SELECT * FROM tb_reminder_vehicle")
        warnings = []
        for v in vehicles:
            alerts = []
            if v.get("WOF") and v["WOF"] <= warn_str:
                status = "expired" if v["WOF"] < today_str else "expiring"
                alerts.append({"type": "WOF", "date": v["WOF"], "status": status})
            if v.get("REGO") and v["REGO"] <= warn_str:
                status = "expired" if v["REGO"] < today_str else "expiring"
                alerts.append({"type": "REGO", "date": v["REGO"], "status": status})
            if alerts:
                warnings.append({"vehicle": v["Vehicle"], "plate": v["Plate"], "id": v["id"], "alerts": alerts})

        return {"status": "success", "data": warnings, "count": len(warnings)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Admin Pipeline Endpoints ---
@app.post("/api/admin/migrate_legacy")
async def api_migrate_legacy():
    try:
        from skills import _200_admin_pipeline as admin_pipeline
    except ImportError:
        import importlib
        admin_pipeline = importlib.import_module("skills.200_admin_pipeline")
        
    res = admin_pipeline.migrate_legacy_data()
    if res["status"] == "error":
        raise HTTPException(status_code=500, detail=res["message"])
    return res

@app.post("/api/admin/reset_passwords")
async def api_reset_passwords():
    try:
        from skills import _200_admin_pipeline as admin_pipeline
    except ImportError:
        import importlib
        admin_pipeline = importlib.import_module("skills.200_admin_pipeline")
        
    res = admin_pipeline.reset_all_passwords()
    if res["status"] == "error":
        raise HTTPException(status_code=500, detail=res["message"])
    return res

@app.get("/api/admin/db_inspect/tables")
async def api_db_inspect_tables():
    try:
        from skills import _200_admin_pipeline as admin_pipeline
    except ImportError:
        import importlib
        admin_pipeline = importlib.import_module("skills.200_admin_pipeline")
        
    return {"status": "success", "data": admin_pipeline.get_tables_list()}

@app.get("/api/admin/db_inspect/{table_name}")
async def api_db_inspect_table(table_name: str, limit: int = 10, offset: int = 0, sort_order: str = "desc"):
    try:
        from skills import _200_admin_pipeline as admin_pipeline
    except ImportError:
        import importlib
        admin_pipeline = importlib.import_module("skills.200_admin_pipeline")
        
    res = admin_pipeline.get_table_data(table_name, limit, offset, sort_order)
    if res["status"] == "error":
        raise HTTPException(status_code=500, detail=res["message"])
    return res

class IntegrityCheckRequest(BaseModel):
    fix: bool = False

@app.post("/api/admin/db_integrity")
async def api_db_integrity(payload: IntegrityCheckRequest):
    try:
        from skills import _200_admin_pipeline as admin_pipeline
    except ImportError:
        import importlib
        admin_pipeline = importlib.import_module("skills.200_admin_pipeline")
        
    res = admin_pipeline.run_integrity_check(fix=payload.fix)
    if res["status"] == "error":
        raise HTTPException(status_code=500, detail=res["message"])
    return res

from fastapi import Response

@app.post("/api/admin/db_reset")
async def admin_db_reset():
    try:
        import tests.db_init as db_init
        db_init.create_tables()
        return {"status": "success", "message": "Database reset successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/db_seed")
async def admin_db_seed():
    try:
        import importlib
        db_seeder = importlib.import_module("skills.999_db_seeder")
        db_seeder.seed_database()
        return {"status": "success", "message": "Database seeded with mock data."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/punch")
async def export_punch():
    try:
        query = """
            SELECT p.year, p.month, p.day, l.firstname, l.surname, p.startstop, p.start_time, p.stop_time 
            FROM tb_punchsheet p 
            JOIN tb_login l ON p.employee_id = l.id 
            ORDER BY p.id DESC LIMIT 100
        """
        records = db_client.fetch_all(query)
        
        csv_content = "Year,Month,Day,Firstname,Surname,Action,StartTime,StopTime\n"
        for r in records:
            csv_content += f"{r['year']},{r['month']},{r['day']},{r['firstname']},{r['surname']},{r['startstop']},{r.get('start_time','')},{r.get('stop_time','')}\n"
            
        return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=punch_export.csv"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Vehicles Endpoints ---
@app.get("/api/reminders/vehicles")
async def api_get_vehicles():
    try:
        from core import db_client
        vehicles = db_client.fetch_all("SELECT * FROM tb_reminder_vehicle ORDER BY id DESC")
        return {"status": "success", "data": vehicles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reminders/vehicles")
async def api_create_vehicle(data: VehicleCreate):
    try:
        from core import db_client
        query = """
            INSERT INTO tb_reminder_vehicle (Vehicle, Plate, WOF, REGO, SERVICE, RUC, Current_ODO)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        db_client.execute_query(query, (data.vehicle, data.plate, data.wof, data.rego, data.service, data.ruc, data.current_odo))
        return {"status": "success", "message": "Vehicle registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/health")
async def api_admin_health():
    try:
        from skills import _200_admin_pipeline as admin_pipeline
    except ImportError:
        import importlib
        admin_pipeline = importlib.import_module("skills.200_admin_pipeline")
    return admin_pipeline.get_system_health()

@app.post("/api/admin/clean-data")
async def api_admin_clean_data():
    try:
        from skills import _200_admin_pipeline as admin_pipeline
        # Note: True authentication should be injected via Depends,
        # but for this standalone implementation we proceed via the UI button
        # which is only visible to Level 10 users.
        res = admin_pipeline.factory_reset_database()
        if res["status"] == "error":
            raise HTTPException(status_code=500, detail=res["message"])
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- QA / WIP Endpoints ---
@app.get("/api/qa/jobs")
async def api_get_qa_jobs():
    try:
        from skills import _015_qa_pipeline as qa_pipeline
    except ImportError:
        import importlib
        qa_pipeline = importlib.import_module("skills.015_qa_pipeline")
        
    res = qa_pipeline.get_pending_qa_jobs()
    if res["status"] == "error":
        raise HTTPException(status_code=500, detail=res["message"])
    return res

@app.get("/api/qa/wip/{job_number}")
async def api_get_qa_wip(job_number: int):
    try:
        from skills import _015_qa_pipeline as qa_pipeline
    except ImportError:
        import importlib
        qa_pipeline = importlib.import_module("skills.015_qa_pipeline")
        
    res = qa_pipeline.get_wip_list_by_job(job_number)
    if res["status"] == "error":
        raise HTTPException(status_code=500, detail=res["message"])
    return res

@app.post("/api/qa/inspect")
async def api_post_qa_inspect(data: QAInspectRequest):
    try:
        from skills import _015_qa_pipeline as qa_pipeline
    except ImportError:
        import importlib
        qa_pipeline = importlib.import_module("skills.015_qa_pipeline")
        
    res = qa_pipeline.process_qa_inspection(data.wip_id, data.is_pass, data.comment)
    if res["status"] == "error":
        raise HTTPException(status_code=500, detail=res["message"])
    return res

# --- Weekly Schedule Endpoints ---
@app.get("/api/schedule/weekly")
async def api_get_schedule_weekly(start_date: str, end_date: str):
    try:
        from skills import _310_schedule_pipeline as schedule_pipeline
    except ImportError:
        import importlib
        schedule_pipeline = importlib.import_module("skills.310_schedule_pipeline")
    
    res = schedule_pipeline.get_weekly_schedule(start_date, end_date)
    if res["status"] == "error":
        raise HTTPException(status_code=500, detail=res["message"])
    return res

@app.post("/api/schedule/notes")
async def api_post_schedule_notes(data: NoteRequest):
    try:
        from skills import _310_schedule_pipeline as schedule_pipeline
    except ImportError:
        import importlib
        schedule_pipeline = importlib.import_module("skills.310_schedule_pipeline")
        
    res = schedule_pipeline.update_daily_note(data.date, data.note, data.note2)
    if res["status"] == "error":
        raise HTTPException(status_code=500, detail=res["message"])
    return res

@app.post("/api/schedule/plan")
async def api_post_schedule_plan(data: PlanRequest):
    try:
        from skills import _310_schedule_pipeline as schedule_pipeline
    except ImportError:
        import importlib
        schedule_pipeline = importlib.import_module("skills.310_schedule_pipeline")
        
    res = schedule_pipeline.assign_production_plan(data.date, data.employee_id, data.job_number, data.lot, data.priority)
    if res["status"] == "error":
        raise HTTPException(status_code=500, detail=res["message"])
    return res

@app.get("/api/schedule/job-options")
async def api_get_schedule_job_options():
    try:
        from skills import _310_schedule_pipeline as schedule_pipeline
    except ImportError:
        import importlib
        schedule_pipeline = importlib.import_module("skills.310_schedule_pipeline")
    return schedule_pipeline.get_job_options()

# --- Public Holidays Endpoints ---
@app.get("/api/holidays")
async def api_get_holidays():
    try:
        from core import db_client
        holidays = db_client.fetch_all("SELECT * FROM tb_public_holidays ORDER BY date_start ASC")
        return {"status": "success", "data": holidays}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/holidays")
async def api_create_holiday(data: HolidayRequest):
    try:
        from core import db_client
        query = "INSERT INTO tb_public_holidays (name, date_start, date_stop) VALUES (?, ?, ?)"
        db_client.execute_query(query, (data.name, data.date_start, data.date_stop))
        return {"status": "success", "message": "Holiday added successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/holidays/{holiday_id}")
async def api_delete_holiday(holiday_id: int):
    try:
        from core import db_client
        query = "DELETE FROM tb_public_holidays WHERE id = ?"
        db_client.execute_query(query, (holiday_id,))
        return {"status": "success", "message": "Holiday deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Job Photos (Drawings / Site Photos) Endpoints ---
@app.get("/api/jobs/{job_number}/photos")
async def get_job_photos(job_number: int):
    try:
        photos = db_client.fetch_all("SELECT * FROM tb_photos WHERE job_number = ? ORDER BY id DESC", (job_number,))
        return {"status": "success", "data": photos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/{job_number}/photos")
async def upload_job_photo(job_number: int, file: UploadFile = File(...)):
    try:
        # Check if job exists
        job = db_client.fetch_one("SELECT job_number, date_creation FROM tb_jobs WHERE job_number = ?", (job_number,))
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Validate extension
        allowed = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf", ".dwg", ".dxf"]
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed:
            raise HTTPException(status_code=400, detail=f"Invalid file type: {ext}. Allowed: {', '.join(allowed)}")

        # Extract creation year
        # Fallback to current year if date_creation is missing/invalid
        year = "2026"
        if job.get("date_creation"):
            try:
                year = job["date_creation"].split("-")[0]
            except Exception:
                pass

        # Save file
        upload_dir = os.path.join(project_root, "static", "uploads", "jobs", year)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename to avoid collision
        import uuid
        filename = f"{job_number}_{uuid.uuid4().hex[:8]}{ext}"
        file_path = os.path.join(upload_dir, filename)

        with open(file_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        # Store relative URL / path in db
        photo_url = f"/uploads/jobs/{year}/{filename}"
        db_client.execute_query(
            "INSERT INTO tb_photos (job_number, year_creation, photo_name) VALUES (?, ?, ?)",
            (job_number, year, photo_url)
        )

        return {"status": "success", "message": "Photo uploaded.", "photo_name": photo_url}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ==============================================================================
# [CRITICAL WARNING - ROUTING ORDER]
# ==============================================================================
# FastAPI evaluates routes from top to bottom. 
# `app.mount("/", StaticFiles(...))` acts as a catch-all for the root path.
# If ANY API endpoints (e.g., @app.post, @app.get) are defined BELOW this line, 
# the static router will catch the request first. Since StaticFiles only allows 
# GET requests, it will return a '405 Method Not Allowed' error for POST requests.
#
# Rule: ALWAYS add new API endpoints ABOVE this line!
# ==============================================================================
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

# Empty favicon to avoid 404 (optional if you have a real favicon in static later)
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)
