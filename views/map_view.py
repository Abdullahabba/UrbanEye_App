import streamlit as st
from database.supabase_client import supabase
import pandas as pd

def render_map_page():
    st.title("🗺️ Interactive Map & Geo-Tagging")
    st.markdown("This map displays the live locations of reported infrastructure issues (such as potholes, garbage dumps, and fallen trees) across the city.")

    with st.spinner("Loading map data from database..."):
        try:
            # Fetching reports data from Supabase
            response = supabase.table("reports").select("*").execute()
            data = response.data

            if data:
                df = pd.DataFrame(data)
                
                # Check if latitude and longitude columns exist in the table
                if "latitude" in df.columns and "longitude" in df.columns:
                    # Drop rows with missing coordinates
                    map_df = df.dropna(subset=["latitude", "longitude"])
                    
                    if not map_df.empty:
                        # Streamlit Native Map Display
                        st.map(map_df, latitude="latitude", longitude="longitude", size=30, color="#FF4B4B")
                        
                        st.markdown("---")
                        st.subheader("📋 Reported Issues Summary")
                        st.dataframe(map_df, use_container_width=True)
                    else:
                        st.info("ℹ️ No reports currently contain saved GPS coordinates (latitude/longitude).")
                else:
                    st.warning("⚠️ 'latitude' and 'longitude' columns were not found in the database table. Please verify your database schema.")
            else:
                st.info("📭 No reports found in the database yet.")

        except Exception as e:
            st.error(f"❌ Error loading map data: {e}")
