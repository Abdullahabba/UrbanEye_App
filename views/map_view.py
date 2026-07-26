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

def render_map_page():
    st.title("🗺️ Interactive Map & Geo-Tagging")
    st.caption("Live locations of reported municipal infrastructure issues across the city.")
    st.divider()

    # Optional CSV File Uploader to enforce exact user data on map
    uploaded_file = st.file_uploader("📂 Upload Exported CSV Data (Optional)", type=["csv"], key="map_csv_upload")

    raw_reports = []

    if uploaded_file is not None:
        try:
            df_uploaded = pd.read_csv(uploaded_file)
            raw_reports = df_uploaded.to_dict(orient="records")
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

        # Prepare map coordinates
        map_df = df[["Latitude", "Longitude", "Hazard", "Tracking ID"]].copy()
        map_df = map_df.rename(columns={"Latitude": "lat", "Longitude": "lon"})
        
        map_df["lat"] = pd.to_numeric(map_df["lat"], errors="coerce")
        map_df["lon"] = pd.to_numeric(map_df["lon"], errors="coerce")
        map_df = map_df.dropna(subset=["lat", "lon"])

        if not map_df.empty:
            st.subheader("📍 Live Incident Coordinates Map")
            st.map(map_df, latitude="lat", longitude="lon", size=20, color="#FF4B4B")
            
            st.divider()
            st.subheader("📋 Detailed Reports Registry")
            st.dataframe(df, use_container_width=True)
            return

    st.info("📭 No location reports found. Upload your exported CSV above or submit an incident from the dashboard!")
