import streamlit as st
from auth.login import render_login_page
from views.dashboard import render_dashboard_page

# Page Configuration
st.set_page_config(
    page_title="UrbanEye AI",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Safely Initialize Session State
if "user" not in st.session_state:
    st.session_state["user"] = None

# Check Query Parameters for Persistent Login (Instant & Reliable)
if st.session_state["user"] is None:
    saved_email = st.query_params.get("logged_in_email")
    if saved_email:
        st.session_state["user"] = {"email": saved_email}

# Navigation Guard: User Login Required
if st.session_state["user"] is None:
    render_login_page()
else:
    # Sidebar User Info & Logout
    with st.sidebar:
        st.title("👁️ UrbanEye AI")
        user_val = st.session_state["user"]
        if isinstance(user_val, dict):
            user_email = user_val.get("email", "Logged in User")
        else:
            user_email = getattr(user_val, "email", "Logged in User")
            
        st.success(f"👤 {user_email}")

        if st.button("🚪 Logout", key="btn_logout", use_container_width=True):
            st.session_state["user"] = None
            st.query_params.clear() # Clear persistent login parameter
            st.rerun()

        st.markdown("---")

    # Render Main Dashboard
    render_dashboard_page()
