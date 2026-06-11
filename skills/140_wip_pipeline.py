"""
skills/140_wip_pipeline.py
Records Welding Inspection (WIP) and NDT results.
"""

from core import db_client
from datetime import datetime

def record_wip(job_number, wps, inspector, inspector_type, pass_fail, comment=""):
    """
    Inserts a WIP (Welding Inspection) record.
    inspector_type: 'in_house' or 'third_party'
    pass_fail: 1 (Pass), -1 (Fail), 0 (Pending)
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    in_house = inspector if inspector_type == 'in_house' else None
    third_party = inspector if inspector_type == 'third_party' else None
    
    query = """
        INSERT INTO tb_wip (
            tb_jobs_id, wps, in_house_inspector, third_party_inspector, 
            inspection_date, inspection_pass_fail, comment
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    
    db_client.execute_query(query, (job_number, wps, in_house, third_party, date_str, pass_fail, comment))
    return True
