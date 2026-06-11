import requests
import json

BASE_URL = "http://127.0.0.1:3600/api"

def print_result(name, passed, msg=""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name} {msg}")

def test_jobs_api():
    print("\n--- Testing Jobs API ---")
    # 1. GET Jobs
    try:
        res = requests.get(f"{BASE_URL}/jobs")
        print_result("GET /jobs status code is 200", res.status_code == 200)
        data = res.json()
        print_result("GET /jobs returns success format", data.get("status") == "success")
        print_result("GET /jobs returns data list", isinstance(data.get("data"), list))
    except Exception as e:
        print_result("GET /jobs", False, f"Exception: {e}")

    # 2. POST Job (Mock data)
    try:
        payload = {
            "job_number": 99999,
            "company_name": "Test Company",
            "site_address": "123 Test St",
            "superlot": "A1",
            "lot_group": "B1",
            "supervisor_name": "Test Supervisor",
            "builder_name": "Test Builder",
            "installer_name": "Test Installer"
        }
        res = requests.post(f"{BASE_URL}/jobs", json=payload)
        # 200 OK or 400 Bad Request if already exists
        if res.status_code == 200:
            print_result("POST /jobs created new job successfully", True)
        elif res.status_code == 400 and "already exists" in res.text:
            print_result("POST /jobs handled existing job gracefully (400)", True, res.text)
        else:
            print_result(f"POST /jobs unexpected status: {res.status_code}", False, res.text)
    except Exception as e:
        print_result("POST /jobs", False, f"Exception: {e}")

def test_employees_api():
    print("\n--- Testing Employees API ---")
    # 1. GET Employees
    try:
        res = requests.get(f"{BASE_URL}/employees")
        print_result("GET /employees status code is 200", res.status_code == 200)
        data = res.json()
        print_result("GET /employees returns success format", data.get("status") == "success")
    except Exception as e:
        print_result("GET /employees", False, f"Exception: {e}")

    # 2. POST Employee
    try:
        payload = {
            "login": "testuser99",
            "password": "password123",
            "firstname": "Test",
            "surname": "User",
            "role": "Welder",
            "right_level": 1,
            "bay": 1,
            "shop_label": "Shop A"
        }
        res = requests.post(f"{BASE_URL}/employees", json=payload)
        if res.status_code == 200:
            print_result("POST /employees created new user successfully", True)
        elif res.status_code == 400 and "already exists" in res.text:
            print_result("POST /employees handled existing user gracefully (400)", True, res.text)
        else:
            print_result(f"POST /employees unexpected status: {res.status_code}", False, res.text)
    except Exception as e:
        print_result("POST /employees", False, f"Exception: {e}")

def test_vehicles_api():
    print("\n--- Testing Vehicles API ---")
    # 1. GET Vehicles
    try:
        res = requests.get(f"{BASE_URL}/reminders/vehicles")
        print_result("GET /reminders/vehicles status code is 200", res.status_code == 200)
        data = res.json()
        print_result("GET /reminders/vehicles returns success format", data.get("status") == "success")
    except Exception as e:
        print_result("GET /reminders/vehicles", False, f"Exception: {e}")

    # 2. POST Vehicle
    try:
        payload = {
            "vehicle": "Test Truck",
            "plate": "TST-999",
            "wof": "2026-12-31",
            "rego": "2026-12-31",
            "service": 100000,
            "ruc": 150000,
            "current_odo": 95000
        }
        res = requests.post(f"{BASE_URL}/reminders/vehicles", json=payload)
        if res.status_code == 200:
            print_result("POST /reminders/vehicles created successfully", True)
        else:
            print_result(f"POST /reminders/vehicles unexpected status: {res.status_code}", False, res.text)
    except Exception as e:
        print_result("POST /reminders/vehicles", False, f"Exception: {e}")

if __name__ == "__main__":
    print("Starting API Endpoint Automated Tests...")
    test_jobs_api()
    test_employees_api()
    test_vehicles_api()
    print("\nTests completed.")
