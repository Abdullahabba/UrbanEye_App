import streamlit as st
import pandas as pd

def normalize_records(raw_data):
    normalized = []
    for row in raw_data:
        if isinstance(row, dict):
            t_id = row.get('tracking_id') or row.get('Tracking ID') or (str(row.get('id'))[:12] if row.get('id') else None)
            if not t_id:
                continue
            hz = row.get('hazard') or row.get('Hazard') or row.get('issue_type') or 'General Hazard'
            sev = row.get('severity') or row.get('Severity') or 'Medium'
            sla = row.get('sla_target') or row.get('SLA Target') or '12 Hours'
            stat = row.get('status') or row.get('Status') or 'Pending'
            dept = row.get('assigned_dept') or row.get('Assigned Dept') or 'Road Maintenance'
            lat = row.get('latitude') or row.get('Latitude') or 31.5204
            lon = row.get('longitude') or row.get('Longitude') or 74.3587
            loc = row.get('location_name') or row.get('Location Name') or row.get('location') or 'City Location'
            ts = row.get('timestamp') or row.get('Timestamp') or row.get('created_at') or pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
            
            normalized.append({
                "Tracking ID": str(t_id),
                "Hazard": str(hz),
                "Severity": str(sev),
                "SLA Target": str(sla),
                "Status": str(stat),
                "Assigned Dept": str(dept),
                "Latitude": float(lat) if lat is not None else 31.5204,
                "Longitude": float(lon) if lon is not None else 74.3587,
                "Location Name": str(loc),
                "Timestamp": str(ts)
            })
    return normalized

def render_report_tracker():
    st.subheader("🔎 Public Hazard Incident Tracker")
    st.caption("Live incident reports synchronized from Supabase & Custom Data.")
    st.divider()

    # Optional CSV File Uploader to enforce exact user data
    uploaded_file = st.file_uploader("📂 Upload Exported CSV Data (Optional)", type=["csv"], key="tracker_csv_upload")
    
    raw_reports = []

    if uploaded_file is not None:
        try:
            df_uploaded = pd.read_csv(uploaded_file)
            raw_reports = df_uploaded.to_dict(orient="records")
            st.success("✅ Loaded data successfully from your uploaded CSV file!")
        except Exception as e:
            st.error(f"❌ Error reading uploaded CSV: {e}")
    else:
        # 1. Fetch from Supabase Cloud Database
        try:
            from database.supabase_client import supabase
            if supabase:
                response = supabase.table("reports").select("*").execute()
                if response.data:
                    raw_reports.extend(response.data)
        except Exception as e:
            pass

        # 2. Fallback or merge with local session state
        if "incident_ledger" in st.session_state and not st.session_state["incident_ledger"].empty:
            raw_reports.extend(st.session_state["incident_ledger"].to_dict(orient="records"))

    # Normalize and deduplicate by Tracking ID
    clean_records = normalize_records(raw_reports)
    unique_records = {r["Tracking ID"]: r for r in clean_records}.values()

    if unique_records:
        df = pd.DataFrame(list(unique_records))
        df = df.loc[:, ~df.columns.duplicated()]

        # Search filter by Tracking ID
        search_id = st.text_input("🔍 Search by Tracking ID", key="search_tracker_id")
        if search_id and "Tracking ID" in df.columns:
            df = df[df["Tracking ID"].astype(str).str.contains(str(search_id), case=False, na=False)]
            
        st.dataframe(df, use_container_width=True)
    else:
        st.info("📭 No reports found. Upload your exported CSV above or submit an incident from the dashboard!")
