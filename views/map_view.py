import streamlit as st
from database.supabase_client import supabase
import pandas as pd

def render_map_page():
    st.title("🗺️ Interactive Map & Geo-Tagging")
    st.markdown("Yeh map shehar ke mukhtalif ilaajon mein report hone wale infrastructural issues (jaise potholes, garbage, aur fallen trees) ki live locations dikhata hai.")

    with st.spinner("Loading map data from database..."):
        try:
            # Supabase se reports ka data fetch karna (table name 'reports' ya 'detections' ho sakta hai)
            response = supabase.table("reports").select("*").execute()
            data = response.data

            if data:
                df = pd.DataFrame(data)
                
                # Check karna ke table mein latitude aur longitude columns mojood hain ya nahi
                if "latitude" in df.columns and "longitude" in df.columns:
                    # Missing coordinates walay rows ko drop karna
                    map_df = df.dropna(subset=["latitude", "longitude"])
                    
                    if not map_df.empty:
                        # Streamlit Native Map Display
                        st.map(map_df, latitude="latitude", longitude="longitude", size=30, color="#FF4B4B")
                        
                        st.markdown("---")
                        st.subheader("📋 Reported Issues Summary")
                        st.dataframe(map_df, use_container_width=True)
                    else:
                        st.info("ℹ️ Filhal kisi bhi report mein GPS coordinates (latitude/longitude) save nahi hain.")
                else:
                    st.warning("⚠️ Database table mein 'latitude' aur 'longitude' columns nahi milay. Baraye meharbani apni database schema check karein.")
            else:
                st.info("📭 Database mein abhi tak koi reports mojood nahi hain.")

        except Exception as e:
            st.error(f"❌ Map data load karne mein masla pesh aaya: {e}")
