import streamlit as st
from database.supabase_client import get_supabase_client

def handle_google_callback():
    supabase = get_supabase_client()
    code = st.query_params.get("code")
    if code and st.session_state.get("user") is None:
        try:
            res = supabase.auth.exchange_code_for_session({"auth_code": code})
            st.session_state.user = res.user
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Google Auth Error: {e}")
            st.query_params.clear()

def render_login_ui():
    supabase = get_supabase_client()
    
    st.markdown("""
        <div style="background-color: #161b22; padding: 25px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 20px; text-align: center;">
            <h1 style='color: #00e5ff; margin:0;'>👁️ URBAN EYE AI</h1>
            <p style='color: #8b949e; margin-top: 5px;'>AI Inspection & Automated Incident Reporting System</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🌐 CONTINUE WITH GOOGLE ACCOUNT"):
            try:
                redirect_uri = "http://localhost:8501"  # Deploy karne par apna Streamlit Cloud URL dein
                res = supabase.auth.sign_in_with_oauth({
                    "provider": "google",
                    "options": {"redirect_to": redirect_uri}
                })
                st.markdown(f'<meta http-equiv="refresh" content="0;url={res.url}">', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Google Login Failed: {e}")

        st.divider()

        tab_login, tab_signup = st.tabs(["🔑 Password Login", "📝 Register Account"])

        with tab_login:
            email = st.text_input("Email Address", key="l_email")
            password = st.text_input("Password", type="password", key="l_pass")
            if st.button("LOG IN"):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = res.user
                    st.success("Login Successful!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Login Failed: {e}")

        with tab_signup:
            s_email = st.text_input("Email Address", key="s_email")
            s_password = st.text_input("Choose Password", type="password", key="s_pass")
            if st.button("CREATE ACCOUNT"):
                try:
                    supabase.auth.sign_up({"email": s_email, "password": s_password})
                    st.info("Account Created! Switch to Login tab.")
                except Exception as e:
                    st.error(f"Signup Failed: {e}")