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

# Safely Initialize Session State
if "user" not in st.session_state:
    st.session_state["user"] = None

# Attempt Cookie Restoration if User is not in Session
if st.session_state["user"] is None:
    try:
        cookies = controller.getAll()
        if cookies and isinstance(cookies, dict):
            saved_user = cookies.get("urbaneye_logged_in_user")
            if saved_user:
                st.session_state["user"] = saved_user
    except Exception as e:
        print(f"Cookie fetch warning: {e}")

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
            try:
                controller.remove("urbaneye_logged_in_user")
            except Exception:
                pass
            st.rerun()

        st.markdown("---")

    # Render Main Dashboard
    render_dashboard_page()
