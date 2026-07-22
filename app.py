import sys
import os

# Project root path setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from auth.login import handle_google_callback, render_login_ui
from views.dashboard import render_dashboard_ui

# Page Config
st.set_page_config(
    page_title="Urban Eye AI Portal",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global Session State Initializations
if "user" not in st.session_state:
    st.session_state.user = None
if "processed_image" not in st.session_state:
    st.session_state.processed_image = None
if "detection_stats" not in st.session_state:
    st.session_state.detection_stats = None

def main():
    handle_google_callback()

    # Router logic
    if st.session_state.user is None:
        render_login_ui()
    else:
        render_dashboard_ui()

if __name__ == "__main__":
    main()