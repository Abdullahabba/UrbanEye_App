import streamlit as st

def render_profile_page(user_details: dict):
    st.title("👤 Officer Profile & Activity History")
    st.caption("Manage your professional credentials, contact info, and review your submitted hazard inspection reports.")

    # Top Section: Officer Credentials
    st.markdown("### 📋 Profile Credentials")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**👤 Full Name:** {user_details.get('username', 'Officer Ahmed')}")
        st.markdown(f"**📧 Official Email:** {user_details.get('email', 'officer@urbaneye.ai')}")
    with col2:
        st.markdown(f"**📞 Phone Number:** {user_details.get('phone', '+92 300 1234567')}")
        st.markdown(f"**📍 Assigned Sector / Address:** {user_details.get('address', 'Iqbal Sector, Block AA, Lahore')}")

    st.divider()

    # Bottom Section: Submitted Reports History
    st.markdown("### 📂 My Submitted Inspection Reports")
    
    # Fetching history from session state safely
    history = st.session_state.get("hazard_history", [])
    
    # Default sample reports if history is empty
    default_reports = [
        {
            "id": "URB-2026-001",
            "date": "2026-08-05 14:30",
            "hazard": "Pothole / Road Damage",
            "location": "Iqbal Sector, Block AA, Lahore",
            "severity": "High (85/100)",
            "status": "Dispatched / Pending"
        },
        {
            "id": "URB-2026-002",
            "date": "2026-08-04 11:15",
            "hazard": "Garbage Dump Overflow",
            "location": "Gulberg Zone, Main Market",
            "severity": "Medium (60/100)",
            "status": "Resolved"
        }
    ]

    display_list = history if history else default_reports

    # Render each report card cleanly using native Streamlit containers
    for item in display_list:
        rep_id = item.get('id') or item.get('tracking_id') or "URB-2026-XXX"
        rep_date = item.get('date') or item.get('timestamp') or "2026-08-06"
        rep_hazard = item.get('hazard') or item.get('title') or item.get('hazard_type') or "Municipal Hazard"
        rep_loc = item.get('location') or item.get('address') or user_details.get('address', 'Lahore')
        rep_sev = item.get('severity') or item.get('score') or "Medium"
        rep_status = item.get('status', 'Dispatched / Pending')

        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**Tracking ID:** `{rep_id}`")
                st.markdown(f"**Hazard Type:** {rep_hazard}")
                st.markdown(f"**Location:** {rep_loc}")
            with c2:
                st.markdown(f"**Date:** {rep_date}")
                st.markdown(f"**Severity:** {rep_sev}")
                st.markdown(f"**Status:** :blue[{rep_status}]")
