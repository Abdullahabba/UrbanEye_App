import streamlit as st
import pandas as pd

def render_map_page():
    st.title("🗺️ Interactive Map & Geo-Tagging")
    st.caption("Live locations of reported municipal infrastructure issues across the city.")
    st.divider()

    reports_data = []

    # 1. Pehle Local Session Ledger se data check karein
    if "incident_ledger" in st.session_state and not st.session_state["incident_ledger"].empty:
        df_local = st.session_state["incident_ledger"]
        reports_data.extend(df_local.to_dict(orient="records"))

    # 2. Phir Supabase Database se fetch karne ki koshish karein (Agar connected ho)
    try:
        from utils.supabase_client import init_supabase
        supabase = init_supabase()
        if supabase:
            response = supabase.table("reports").select("*").execute()
            if response.data:
                # Merge or append supabase data
                db_reports = response.data
                # Avoid duplicates based on tracking_id if needed
                existing_ids = {r.get("Tracking ID") or r.get("tracking_id") for r in reports_data}
                for r in db_reports:
                    t_id = r.get("Tracking ID") or r.get("tracking_id")
                    if t_id not in existing_ids:
                        reports_data.append(r)
    except Exception:
        pass # Supabase offline ho toh local session chalta rahega

    # 3. Render Map agar data mojood hai
    if reports_data:
        df = pd.DataFrame(reports_data)
        
        # Ensure column names match expected case
        if "latitude" in df.columns and "longitude" in df.columns:
            map_df = df.rename(columns={"latitude": "lat", "longitude": "lon"})
        elif "Latitude" in df.columns and "Longitude" in df.columns:
            map_df = df.rename(columns={"Latitude": "lat", "Longitude": "lon"})
        else:
            map_df = pd.DataFrame()

        if not map_df.empty and "lat" in map_df.columns and "lon" in map_df.columns:
            # Drop rows with null coords
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
