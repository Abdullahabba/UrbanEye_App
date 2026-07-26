import streamlit as st
import pandas as pd

def render_report_tracker():
    st.subheader("🔎 Public Hazard Incident Tracker")
    st.caption("Live incident reports synchronized from Supabase Cloud Database.")
    st.divider()

    reports_data = []

    # 1. Supabase Cloud Database se data fetch karein
    try:
        from database.supabase_client import supabase
        if supabase:
            response = supabase.table("reports").select("*").execute()
            if response.data:
                reports_data = response.data
    except Exception as e:
        st.warning(f"Could not connect to Supabase: {e}")

    # 2. Fallback to session state if empty
    if not reports_data and "incident_ledger" in st.session_state and not st.session_state["incident_ledger"].empty:
        reports_data = st.session_state["incident_ledger"].to_dict(orient="records")

    # 3. Data Render Karein
    if reports_data:
        df = pd.DataFrame(reports_data)
        
        search_id = st.text_input("🔍 Search by Tracking ID", key="search_tracker_id")
        if search_id:
            id_col = "Tracking ID" if "Tracking ID" in df.columns else "tracking_id"
            if id_col in df.columns:
                df = df[df[id_col].astype(str).str.contains(search_id, case=False, na=False)]
            
        st.dataframe(df, use_container_width=True)
    else:
        st.info("📭 No reports found in the database yet. Submit a report from the detection engine to see it here!")
