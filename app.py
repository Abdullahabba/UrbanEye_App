import streamlit as st
from auth.login import render_login_page
from views.dashboard import render_dashboard_page

st.set_page_config(
    page_title="UrbanEye AI",
    page_icon="👁️",
    layout="wide",
)

# Session State Check
if "user" not in st.session_state:
    st.session_state["user"] = None

# Navigation Logic
if st.session_state["user"] is None:
    render_login_page()
else:
    # Sidebar Logout Button
    with st.sidebar:
        st.write(f"👤 {st.session_state['user'].email}")
        if st.button("Logout"):
            st.session_state["user"] = None
            st.rerun()

    render_dashboard_page()
