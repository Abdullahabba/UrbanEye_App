from pathlib import Path
import streamlit as st

def load_css():
    """Loads style.css securely from the project root directory."""
    css_path = Path(__file__).parent.parent / "style.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def render_login_page():
    load_css()
    
    # Centered Login UI Container
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>👁️ UrbanEye AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Smart City Visual Inspection & Hazard Tracking System</p>", unsafe_allow_html=True)
        st.divider()
        
        with st.form("login_form"):
            st.subheader("🔐 Officer Login")
            username = st.text_input("Username / Badge ID", value="inspector_01")
            password = st.text_input("Password", type="password", value="urbaneye123")
            
            submitted = st.form_submit_button("Login to Dashboard", use_container_width=True)
            
            if submitted:
                if username and password:
                    st.session_state["authenticated"] = True
                    st.session_state["user_details"] = {
                        "username": username,
                        "email": "abdullahabbasi555a@gmail.com",
                        "phone": "+92 300 1234567",
                        "address": "Iqbal Sector, Block AA, Lahore"
                    }
                    st.success("✅ Login successful! Loading dashboard...")
                    st.rerun()
                else:
                    st.error("❌ Please enter valid credentials.")
