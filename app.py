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

# Session State Check
if "user" not in st.session_state:
    st.session_state["user"] = None

# Navigation Guard: User Login Required
if st.session_state["user"] is None:
    render_login_page()
else:
    # Sidebar User Info & Logout
    with st.sidebar:
        st.title("👁️ UrbanEye AI")
        user_email = getattr(
            st.session_state["user"], "email", "Logged in User"
        )
        st.success(f"👤 {user_email}")

        if st.button("🚪 Logout", key="btn_logout", use_container_width=True):
            st.session_state["user"] = None
            st.rerun()

        st.markdown("---")

    # Render Main Dashboard
    render_dashboard_page()
