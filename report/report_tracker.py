import streamlit as st

def render_report_tracker():
    st.subheader("🔎 Public Hazard Incident Tracker")
    
    # Check if ledger exists in session state
    if "incident_ledger" in st.session_state and not st.session_state["incident_ledger"].empty:
        df = st.session_state["incident_ledger"]
        
        # Search filter
        search_id = st.text_input("Search by Tracking ID", key="search_tracker_id")
        if search_id:
            df = df[df["Tracking ID"].str.contains(search_id, case=False, na=False)]
            
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No incidents logged yet.")
