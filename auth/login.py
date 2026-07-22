import streamlit as st
from database.supabase_client import supabase


def render_login_page():
    st.title("👁️ UrbanEye AI - Login")

    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input(
            "Password", type="password", key="login_password"
        )

        if st.button("Login", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password(
                    {"email": email, "password": password}
                )
                st.session_state["user"] = res.user
                st.success("Successfully Logged In!")
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")

    with tab2:
        signup_email = st.text_input("Email", key="signup_email")
        signup_password = st.text_input(
            "Password", type="password", key="signup_password"
        )

        if st.button("Create Account", use_container_width=True):
            try:
                res = supabase.auth.sign_up(
                    {"email": signup_email, "password": signup_password}
                )
                st.success("Account created! Check your email for verification.")
            except Exception as e:
                st.error(f"Signup failed: {e}")
