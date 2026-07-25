import streamlit as st
from streamlit_cookies_controller import CookieController
from auth.login import render_login_page
from views.dashboard import render_dashboard_page

# Page Configuration
st.set_page_config(
    page_title="UrbanEye AI",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Cookie Controller
controller = CookieController()

# Session State Check & Cookie Restoration
if "user" not in st.session_state or st.session_state["user"] is None:
    saved_user = controller.get("urbaneye_logged_in_user")
    if saved_user:
        st.session_state["user"] = saved_user
    else:
        st.session_state["user"] = None

# Automatically save to cookie if user logs in successfully
if st.session_state["user"] is not None:
    current_cookie = controller.get("urbaneye_logged_in_user")
    if not current_cookie:
        user_val = st.session_state["user"]
        if hasattr(user_val, "email"):
            controller.set("urbaneye_logged_in_user", {"email": user_val.email}, max_age=60*60*24*7)
        else:
            controller.set("urbaneye_logged_in_user", user_val, max_age=60*60*24*7)

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
            controller.remove("urbaneye_logged_in_user")
            st.rerun()

        st.markdown("---")

    # Render Main Dashboard
    render_dashboard_page()
