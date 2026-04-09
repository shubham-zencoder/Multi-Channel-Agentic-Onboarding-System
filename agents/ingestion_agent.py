import csv
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import DB_PATH

MANDATORY_COLUMNS = [
    "lead_id",
    "name",
    "phone",
    "email",
    "city",
    "vehicle_type",
    "vehicle_count",
    "aadhaar_status",
    "bank_status",
    "rc_status",
    "app_installed",
    "preferred_channel",
    "remarks",
]


def _clean_phone(value):
    return re.sub(r"\D", "", str(value or ""))


def _clean_email(value):
    return (str(value or "") or "").lower().strip()


def _parse_vehicle_count(value):
    if value in (None, ""):
        return None
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


def _parse_app_installed(value):
    if value in (None, ""):
        return 0
    s = str(value).strip().lower()
    if s in ("1", "true", "yes", "y"):
        return 1
    if s in ("0", "false", "no", "n"):
        return 0
    try:
        return 1 if int(float(s)) else 0
    except (TypeError, ValueError):
        return 0


def _read_leads_csv(file_path):
    rows = []
    with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row = {}
            for col in MANDATORY_COLUMNS:
                v = raw.get(col)
                row[col] = None if v in ("", None) else v
            row["phone"] = _clean_phone(row.get("phone"))
            row["email"] = _clean_email(row.get("email"))
            row["vehicle_count"] = _parse_vehicle_count(row.get("vehicle_count"))
            row["app_installed"] = _parse_app_installed(row.get("app_installed"))
            rows.append(row)
    return rows


def ingest_leads(file_path="samples/leads.csv"):
    try:
        if not os.path.exists(file_path):
            print(f"[ERROR] File not found at {file_path}")
            return

        rows = _read_leads_csv(file_path)
        print(f"[READ] Loaded {len(rows)} rows from {file_path}.")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for r in rows:
            r["latest_update_source"] = "Excel/CSV"
            r["last_updated"] = now
            r["onboarding_stage"] = "Lead Captured"
            r["lead_score"] = 10

        conn = sqlite3.connect(DB_PATH)
        try:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT lead_id FROM leads")
                existing = {row[0] for row in cursor.fetchall()}
            except sqlite3.OperationalError:
                existing = set()

            new_rows = [r for r in rows if r.get("lead_id") and r["lead_id"] not in existing]

            if new_rows:
                db_columns = MANDATORY_COLUMNS + [
                    "onboarding_stage",
                    "lead_score",
                    "last_updated",
                    "latest_update_source",
                ]
                placeholders = ", ".join(["?"] * len(db_columns))
                col_names = ", ".join(db_columns)
                insert_sql = f"INSERT INTO leads ({col_names}) VALUES ({placeholders})"
                batch = [tuple(r[c] for c in db_columns) for r in new_rows]
                cursor.executemany(insert_sql, batch)
                conn.commit()
                print(f"[OK] {len(new_rows)} new leads added. Source: Excel/CSV")
            else:
                print("[WARN] No new leads found.")
        finally:
            conn.close()

    except Exception as e:
        print(f"[ERROR] Error during ingestion: {e}")


if __name__ == "__main__":
    ingest_leads("samples/leads.csv")
