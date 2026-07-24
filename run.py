import os
import sys
import subprocess
import uvicorn
import platform
from pathlib import Path

# Project Configuration
PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_MODULE = "backend.main:app"

def banner():
    print(f"\n{'='*50}")
    print("   Retail Demand Forecasting System - Runner")
    print(f"{'='*50}\n")

def check_venv():
    """Ensure script is running in the virtual environment."""
    if sys.prefix == sys.base_prefix:
        print("[!] WARNING: You are not running inside the virtual environment.")
        print("    Please activate it: .venv\\Scripts\\activate (Windows) or source .venv/bin/activate (Linux)")
        # Continue anyway or sys.exit(1) based on preference

def run_backend():
    print("[+] Starting Backend API...")
    try:
        # Using uvicorn run directly
        uvicorn.run(
            BACKEND_MODULE,
            host="0.0.0.0",
            port=8000,
            reload=True,  # Set to False for production
            log_level="info"
        )
    except Exception as e:
        print(f"[X] Backend Error: {e}")

if __name__ == "__main__":
    banner()
    check_venv()
    
    # Check if database needs seeding or migration (Optional)
    # subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"])
    
    print("[+] System initializing...")
    run_backend()