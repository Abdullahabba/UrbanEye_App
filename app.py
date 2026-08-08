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

# Safely Initialize All Core Session State Variables (Prevents KeyError & Mode Pollution)
default_states = {
    "user": None,
    "counts": {},
    "processed_img": None,
    "captured_images": [],
    "current_mode": None,
    "location_confirmed": False,
    "selected_lat": None,
    "selected_lon": None,
    "selected_loc_name": "",
}

for key, val in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = val

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
            # Clear all session state and query parameters on logout
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.query_params.clear()
            st.rerun()

        st.markdown("---")

    # Render Main Dashboard
    render_dashboard_page()
