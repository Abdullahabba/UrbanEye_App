import random
import string
import pandas as pd
import streamlit as st

def generate_tracking_id() -> str:
    """
    Generates a unique alpha-numeric tracking ID for civic incidents.
    """
    letters = "".join(random.choices(string.ascii_uppercase, k=2))
    digits = "".join(random.choices(string.digits, k=4))
    return f"UE-{letters}-{digits}"

def initialize_mock_history():
    """
    Initializes mock incident history/ledger in Streamlit session state if not already present.
    """
    if "incident_ledger" not in st.session_state or not isinstance(st.session_state["incident_ledger"], pd.DataFrame):
        mock_data = [
            {
                "tracking_id": "UE-AB-5541",
                "issue_type": "Pothole / Road Damage",
                "severity": "HIGH",
                "sla_target": "12 Hours",
                "status": "Pending Dispatch",
                "assigned_dept": "Road & Infrastructure",
                "latitude": 31.5204,
                "longitude": 74.3587,
                "location_name": "Main Boulevard Gulberg",
                "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
            }
        ]
        st.session_state["incident_ledger"] = pd.DataFrame(mock_data)
