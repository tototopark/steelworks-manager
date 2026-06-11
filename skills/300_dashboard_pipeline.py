"""
skills/300_dashboard_pipeline.py
Pipeline for aggregating dashboard analytics and progress visualization metrics.
"""

from core import db_client

def get_active_jobs_progress(limit=10):
    """
    Fetches the most recent active jobs and calculates their progress percentage
    based on the number of completed (made) job details vs total job details.
    """
    try:
        # Fetch most recent jobs
        jobs_query = """
            SELECT job_number, company_name, site_address, date_creation 
            FROM tb_jobs 
            ORDER BY date_creation DESC 
            LIMIT ?
        """
        jobs = db_client.fetch_all(jobs_query, (limit,))
        
        if not jobs:
            return {"status": "success", "data": []}
            
        results = []
        for j in jobs:
            job_num = j["job_number"]
            company = j["company_name"]
            address = j["site_address"]
            
            # Aggregate details
            details_query = """
                SELECT COUNT(*) as tot, SUM(made) as completed 
                FROM tb_jobs_details 
                WHERE job_number = ?
            """
            details = db_client.fetch_one(details_query, (job_num,))
            
            tot = details["tot"] if details and details["tot"] else 0
            completed = details["completed"] if details and details["completed"] else 0
            
            progress = 0
            if tot > 0:
                progress = round((completed / tot) * 100)
                
            results.append({
                "job_number": job_num,
                "company_name": company,
                "site_address": address,
                "total_details": tot,
                "completed_details": completed,
                "progress_percent": progress
            })
            
        return {"status": "success", "data": results}
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch job progress: {str(e)}"}
