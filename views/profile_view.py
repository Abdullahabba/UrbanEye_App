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

    # Combine live session history with defaults if session history is empty
    if not history:
        display_list = default_reports
    else:
        display_list = history

    # Render each report card cleanly
    for item in display_list:
        rep_id = item.get('id') or item.get('tracking_id') or "URB-2026-XXX"
        rep_date = item.get('date') or item.get('timestamp') or "2026-08-06"
        rep_hazard = item.get('hazard') or item.get('title') or item.get('hazard_type') or "Municipal Hazard"
        rep_loc = item.get('location') or item.get('address') or user_details.get('address', 'Lahore')
        rep_sev = item.get('severity') or item.get('score') or "Medium"
        rep_status = item.get('status', 'Dispatched / Pending')

        st.markdown(f"""
        <div style="padding: 15px; border-radius: 8px; border: 1px solid #d0d7de; margin-bottom: 12px; background-color: #f8f9fa;">
            <b>Tracking ID:</b> {rep_id} &nbsp;|&nbsp; 
            <b>Date:</b> {rep_date}<br>
            <b>Hazard Type:</b> {rep_hazard} &nbsp;|&nbsp; 
            <b>Severity Score:</b> {rep_sev}<br>
            <b>Location:</b> {rep_loc}<br>
            <b>Status:</b> <span style="color: #0077b6; font-weight: bold;">{rep_status}</span>
        </div>
        """, unsafe_allow_html=True)
