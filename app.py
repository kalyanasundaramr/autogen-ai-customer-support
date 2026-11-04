
"""Entry point for the AI Customer Support Dashboard."""

from pathlib import Path
import runpy
import sys

BASE_DIR = Path(__file__).resolve().parent
DASHBOARD_PATH = BASE_DIR / "ui" / "support_dashboard.py"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

runpy.run_path(str(DASHBOARD_PATH), run_name="__main__")
