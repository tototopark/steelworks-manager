"""
run_api.py
Web API host starter script.
Runs the FastAPI app inside core/api_router.py using Uvicorn.
"""

import os
import sys
import uvicorn

# Set project root path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

def main():
    print("Starting Steelworks Manager Web API server...")
    print("Documentation will be available at: http://127.0.0.1:3600/docs")
    print("Press Ctrl+C to stop the server.\n")
    
    # Run uvicorn server mapping to api_router app
    uvicorn.run("core.api_router:app", host="127.0.0.1", port=3600, reload=True)

if __name__ == "__main__":
    main()
