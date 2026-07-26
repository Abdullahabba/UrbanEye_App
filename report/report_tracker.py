import streamlit as st
import pandas as pd

def render_report_tracker():
    st.subheader("🔎 Public Hazard Incident Tracker")
    st.caption("Live incident reports synchronized from Supabase Cloud Database.")
    st.divider()

    reports_data = []

    # 1. Fetch data from Supabase Cloud Database
    try:
        from database.supabase_client import supabase
        if supabase:
            response = supabase.table("reports").select("*").execute()
            if response.data:
                reports_data = response.data
    except Exception as e:
        st.error(f"❌ Supabase Fetch Error: {e}")

    # 2. Fallback to session state if Supabase data is empty
    if not reports_data and "incident_ledger" in st.session_state and not st.session_state["incident_ledger"].empty:
        reports_data = st.session_state["incident_ledger"].to_dict(orient="records")

    # 3. Render Data in DataFrame
    if reports_data:
        df = pd.DataFrame(reports_data)
        
        # Clean up internal columns if present
        if "id" in df.columns:
            df = df.drop(columns=["id"])
        if "created_at" in df.columns:
            df = df.drop(columns=["created_at"])

        # Rename columns to user-friendly titles for display if they exist
        rename_map = {
            "tracking_id": "Tracking ID",
            "hazard": "Hazard",
            "issue_type": "Issue Type",
            "severity": "Severity",
            "sla_target": "SLA Target",
            "status": "Status",
            "assigned_dept": "Assigned Dept",
            "latitude": "Latitude",
            "longitude": "Longitude",
            "location_name": "Location Name",
            "timestamp": "Timestamp"
        }
        df = df.rename(columns=rename_map)

        # Drop any duplicate columns to prevent PyArrow / Streamlit crash
        df = df.loc[:, ~df.columns.duplicated()]

        # Search filter by Tracking ID (Bulletproof check)
        search_id = st.text_input("🔍 Search by Tracking ID", key="search_tracker_id")
        if search_id:
            possible_cols = ["Tracking ID", "tracking_id"]
            found_col = next((col for col in possible_cols if col in df.columns), None)
            if found_col:
                df = df[df[found_col].astype(str).str.contains(str(search_id), case=False, na=False)]

        st.dataframe(df, use_container_width=True)
    else:
        st.info("📭 No reports found in the database yet. Submit a report from the detection engine to see it here!")
