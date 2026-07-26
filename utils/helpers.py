import os
import random
import pandas as pd

CSV_FILE = "reports_ledger.csv"

def generate_tracking_id():
    return f"UE-2026-{random.randint(1000, 9999)}"

def calculate_severity_and_sla(counts: dict) -> tuple[str, str, str]:
    total_objects = sum(counts.values())
    if total_objects == 0:
        return "LOW", "#28a745", "48 Hours"

    has_critical = any(k.lower() in ["fallen tree", "open manhole", "fire hazard"] for k in counts.keys())
    potholes = sum(v for k, v in counts.items() if "pothole" in k.lower())

    if total_objects >= 5 or has_critical or potholes >= 3:
        return "CRITICAL", "#dc3545", "4 Hours (Immediate)"
    elif total_objects >= 2:
        return "MEDIUM", "#ffc107", "12 Hours"
    else:
        return "LOW", "#28a745", "24 Hours"

def initialize_mock_history():
    if "incident_ledger" not in __import__("streamlit").session_state:
        if os.path.exists(CSV_FILE):
            try:
                __import__("streamlit").session_state["incident_ledger"] = pd.read_csv(CSV_FILE)
            except Exception:
                __import__("streamlit").session_state["incident_ledger"] = get_default_ledger()
        else:
            df = get_default_ledger()
            df.to_csv(CSV_FILE, index=False)
            __import__("streamlit").session_state["incident_ledger"] = df

def get_default_ledger():
    return pd.DataFrame([
        {
            "Tracking ID": "UE-2026-1001", "Hazard": "Pothole", "Severity": "CRITICAL",
            "SLA Target": "4 Hours", "Status": "In Progress", "Assigned Dept": "Road Maintenance Dept",
            "Latitude": 31.5204, "Longitude": 74.3587, "Location Name": "Iqbal Sector, Block AA", "Timestamp": "2026-07-23 08:15"
        },
        {
            "Tracking ID": "UE-2026-1002", "Hazard": "Garbage Dump", "Severity": "MEDIUM",
            "SLA Target": "12 Hours", "Status": "Pending", "Assigned Dept": "Waste Management Dept",
            "Latitude": 31.5100, "Longitude": 74.3400, "Location Name": "Gulberg III Main Blvd", "Timestamp": "2026-07-23 11:30"
        },
        {
            "Tracking ID": "UE-2026-1003", "Hazard": "Fallen Tree", "Severity": "CRITICAL",
            "SLA Target": "4 Hours", "Status": "Resolved", "Assigned Dept": "Parks & Horticulture Authority",
            "Latitude": 31.5300, "Longitude": 74.3600, "Location Name": "Model Town Link Road", "Timestamp": "2026-07-22 09:00"
        }
    ])
