# =====================================================================
# Auto-Installer for Retail Demand Forecasting System
# =====================================================================
from __future__ import annotations
import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / ".venv"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

RESET = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
BOLD = "\033[1m"


def banner(text: str):
    print(f"\n{BOLD}{BLUE}{'='*60}\n  {text}\n{'='*60}{RESET}")


def step(text: str):
    print(f"{BOLD}{GREEN}[+]{RESET} {text}")


def warn(text: str):
    print(f"{YELLOW}[!] {text}{RESET}")


def error(text: str):
    print(f"{RED}[X] {text}{RESET}")


def find_python() -> str:
    candidates = [sys.executable, "python3", "python", "py"]
    for c in candidates:
        try:
            r = subprocess.run([c, "--version"], capture_output=True, text=True)
            if r.returncode == 0 and "Python 3" in (r.stdout + r.stderr):
                parts = (r.stdout + r.stderr).split()[1].split(".")
                if (int(parts[0]), int(parts[1])) >= (3, 8):
                    return c
        except FileNotFoundError:
            continue
    return None


def find_npm() -> str:
    for c in ["npm", "npm.cmd"]:
        path = shutil.which(c)
        if path:
            return path
    return None


def create_venv():
    if VENV_DIR.exists():
        step(f"Virtual env already exists at {VENV_DIR}")
        return
    step(f"Creating virtual environment at {VENV_DIR}")
    subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
    step("Virtual environment created")


def venv_python() -> str:
    if os.name == "nt":
        return str(VENV_DIR / "Scripts" / "python.exe")
    return str(VENV_DIR / "bin" / "python")


def venv_pip() -> str:
    if os.name == "nt":
        return str(VENV_DIR / "Scripts" / "pip.exe")
    return str(VENV_DIR / "bin" / "pip")


def install_python_deps(skip_ml: bool = False):
    step("Upgrading pip...")
    subprocess.check_call([venv_pip(), "install", "--upgrade", "pip"])

    req_file = PROJECT_ROOT / "requirements.txt"
    if skip_ml:
        warn("Skipping heavy ML packages (prophet, tensorflow) due to --skip-ml")
        tmp_req = PROJECT_ROOT / "requirements_core.txt"
        with open(req_file) as f:
            lines = [
                line for line in f
                if not any(pkg in line.lower() for pkg in ["prophet", "tensorflow", "xgboost"])
            ]
        tmp_req.write_text("".join(lines))
        req_file = tmp_req

    step(f"Installing Python dependencies from {req_file}...")
    subprocess.check_call([venv_pip(), "install", "-r", str(req_file)])

    if skip_ml:
        (PROJECT_ROOT / "requirements_core.txt").unlink(missing_ok=True)


def install_frontend_deps():
    npm = find_npm()
    if not npm:
        warn("Node.js/npm not found. Skipping frontend install.")
        warn("Install Node.js 18+ from https://nodejs.org/ to enable the dashboard UI.")
        warn("You can still use the backend API at http://localhost:8000/docs")
        return False
    if not FRONTEND_DIR.exists():
        warn(f"Frontend directory not found at {FRONTEND_DIR}")
        return False
    step("Installing frontend npm dependencies (this may take 1-2 min)...")
    subprocess.check_call([npm, "install"], cwd=str(FRONTEND_DIR))
    step("Frontend dependencies installed")
    return True


def init_database():
    step("Initializing database and seeding sample data...")
    py = venv_python()
    r = subprocess.run(
        [py, "-c", "from backend.seed_data import seed; seed()"],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    )
    if r.returncode == 0:
        for line in r.stdout.splitlines():
            print(f"    {line}")
    else:
        warn("Seed output:")
        print(r.stdout)
        print(r.stderr)
        error("Database seed failed. Check error above.")


def verify():
    step("Verifying installation...")
    py = venv_python()
    checks = [
        ("FastAPI",    "import fastapi"),
        ("SQLAlchemy", "import sqlalchemy"),
        ("Pandas",     "import pandas"),
        ("NumPy",      "import numpy"),
        ("XGBoost",    "import xgboost"),
        ("Prophet",    "from prophet import Prophet"),
        ("TensorFlow", "import tensorflow"),
        ("Passlib",    "import passlib"),
        ("JOSE",       "import jose"),
    ]
    for name, stmt in checks:
        r = subprocess.run([py, "-c", stmt], capture_output=True, text=True)
        if r.returncode == 0:
            print(f"    {GREEN}OK{RESET}   {name}")
        else:
            print(f"    {YELLOW}MISS{RESET} {name}")


def print_next_steps(frontend_ok: bool):
    banner("INSTALLATION COMPLETE")
    print(f"""
  {BOLD}To start the system:{RESET}
    {GREEN}python run.py{RESET}

  {BOLD}Default login:{RESET}
    username:  admin
    password:  Admin@123
    (change immediately after first login!)

  {BOLD}Backend API:{RESET}     http://localhost:8000
  {BOLD}API docs (Swagger):{RESET}  http://localhost:8000/docs
  {BOLD}Dashboard UI:{RESET}    http://localhost:5173  {"(if Node.js was installed)" if frontend_ok else "(install Node.js to enable)"}

  {BOLD}Manual commands (if needed):{RESET}
    Activate venv:    {"call .venv\\Scripts\\activate" if os.name == "nt" else "source .venv/bin/activate"}
    Run backend only: uvicorn backend.main:app --reload --port 8000
    Run frontend:     cd frontend && npm run dev
""")


def main():
    banner("Retail Demand Forecasting System - Auto Installer")
    print(f"  Project root : {PROJECT_ROOT}")
    print(f"  Platform     : {platform.system()} {platform.release()}")
    print(f"  Python       : {sys.version.split()[0]}")

    skip_frontend = "--skip-frontend" in sys.argv
    skip_ml = "--skip-ml" in sys.argv

    py = find_python()
    if not py:
        error("Python 3.8+ not found. Please install from https://www.python.org/")
        sys.exit(1)

    create_venv()
    install_python_deps(skip_ml=skip_ml)

    frontend_ok = False
    if not skip_frontend:
        frontend_ok = install_frontend_deps()

    init_database()
    verify()
    print_next_steps(frontend_ok)


if __name__ == "__main__":
    main()
