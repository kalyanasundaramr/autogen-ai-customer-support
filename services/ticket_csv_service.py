import csv
import os
import tempfile
from pathlib import Path

from services.ticket_export_service import export_tickets_csv
from database.db import DB_PATH

CSV_PATH = Path(
    os.environ.get(
        "SUPPORT_CSV_PATH",
        str(DB_PATH.parent / "tickets.csv")
    )
).resolve()


def sync_tickets_csv() -> Path:
    """Synchronize the CSV log with committed SQLite tickets."""
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    csv_content = export_tickets_csv()

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8-sig",
            newline="",
            dir=CSV_PATH.parent,
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_file.write(csv_content)
            temporary_path = Path(temporary_file.name)

        os.replace(temporary_path, CSV_PATH)

    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return CSV_PATH
