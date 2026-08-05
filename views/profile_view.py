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
    
    # Session state ya mock history fetch karna
    history = st.session_state.get("hazard_history", [])
    
    if not history:
        # Fallback sample records agar session mein history na ho
        history = [
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

    if history:
        for item in history:
            st.markdown(f"""
            <div style="padding: 15px; border-radius: 8px; border: 1px solid #d0d7de; margin-bottom: 12px; background-color: #f8f9fa;">
                <b>Tracking ID:</b> {item.get('id', 'N/A')} &nbsp;|&nbsp; 
                <b>Date:</b> {item.get('date', 'N/A')}<br>
                <b>Hazard Type:</b> {item.get('hazard', 'General Hazard')} &nbsp;|&nbsp; 
                <b>Severity Score:</b> {item.get('severity', 'Medium')}<br>
                <b>Location:</b> {item.get('location', 'N/A')}<br>
                <b>Status:</b> <span style="color: #0077b6; font-weight: bold;">{item.get('status', 'Submitted')}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No reports submitted yet during this session.")
