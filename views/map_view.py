import streamlit as st
import pandas as pd

def render_map_page():
    st.title("🗺️ Interactive Map & Geo-Tagging")
    st.caption("Live locations of reported municipal infrastructure issues across the city.")
    st.divider()

    reports_data = []

    # 1. Fetch data directly from Supabase Cloud Database using correct client import
    try:
        from database.supabase_client import supabase
        if supabase:
            response = supabase.table("reports").select("*").execute()
            if response.data:
                reports_data = response.data
    except Exception as e:
        st.error(f"❌ Supabase Fetch Error: {e}")

    # 2. Fallback or merge with local session state if ledger has records
    if "incident_ledger" in st.session_state and not st.session_state["incident_ledger"].empty:
        df_local = st.session_state["incident_ledger"]
        local_records = df_local.to_dict(orient="records")
        existing_ids = {r.get("Tracking ID") or r.get("tracking_id") for r in reports_data}
        for r in local_records:
            t_id = r.get("Tracking ID") or r.get("tracking_id")
            if t_id not in existing_ids:
                reports_data.append(r)

    # 3. Render Map if data exists
    if reports_data:
        df = pd.DataFrame(reports_data)
        
        # Clean up duplicate columns if any
        df = df.loc[:, ~df.columns.duplicated()]

        # Ensure column names match expected case for mapping
        map_df = pd.DataFrame()
        if "latitude" in df.columns and "longitude" in df.columns:
            map_df = df.rename(columns={"latitude": "lat", "longitude": "lon"})
        elif "Latitude" in df.columns and "Longitude" in df.columns:
            map_df = df.rename(columns={"Latitude": "lat", "Longitude": "lon"})

        if not map_df.empty and "lat" in map_df.columns and "lon" in map_df.columns:
            # Ensure numeric conversion for coordinates
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

    # Agar koi report na ho
    st.info("📭 No reports found in the database yet. Run a detection and submit an incident from the dashboard to view pins on the map!")
