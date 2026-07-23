import streamlit as st
from database.supabase_client import supabase


def render_login_page():
    st.title("👁️ UrbanEye AI - Portal Access")

    tab_login, tab_signup = st.tabs(["🔑 Login", "📝 Sign Up"])

    # ---------------------------------------------------------
    # TAB 1: LOGIN (Email + Password + Keep Me Logged In)
    # ---------------------------------------------------------
    with tab_login:
        st.subheader("Welcome Back!")
        email = st.text_input("Email Address", key="login_email")
        password = st.text_input(
            "Password", type="password", key="login_password"
        )

        # 🔘 Keep Me Logged In Option
        keep_logged_in = st.checkbox(
            "Keep me logged in", value=True, key="keep_logged_in"
        )

        if st.button("Sign In", use_container_width=True, type="primary"):
            if not email or not password:
                st.warning("Please fill in both Email and Password.")
            else:
                with st.spinner("Authenticating..."):
                    try:
                        # Supabase Login Call
                        response = supabase.auth.sign_in_with_password(
                            {"email": email, "password": password}
                        )

                        if response.user:
                            # Session State Mein User Save Karna
                            st.session_state["user"] = response.user
                            st.session_state["keep_logged_in"] = keep_logged_in

                            st.success("✅ Login successful!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Login Failed: {str(e)}")

    # ---------------------------------------------------------
    # TAB 2: SIGN UP (Full Registration Form)
    # ---------------------------------------------------------
    with tab_signup:
        st.subheader("Create a New Account")

        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Full Name / Username")
            phone = st.text_input("Phone Number")
        with col2:
            signup_email = st.text_input("Email Address", key="signup_email")
            signup_password = st.text_input(
                "Password", type="password", key="signup_password"
            )

        address = st.text_area("Address / Department Location")

        if st.button(
            "Create Account", use_container_width=True, type="secondary"
        ):
            if (
                not signup_email
                or not signup_password
                or not username
                or not phone
            ):
                st.warning("Please fill in all required fields.")
            else:
                with st.spinner("Creating account..."):
                    try:
                        # Supabase Auth mein Extra Data (User Metadata) save karna
                        response = supabase.auth.sign_up(
                            {
                                "email": signup_email,
                                "password": signup_password,
                                "options": {
                                    "data": {
                                        "username": username,
                                        "phone": phone,
                                        "address": address,
                                    }
                                },
                            }
                        )

                        if response.user:
                            st.success(
                                "🎉 Account created successfully! You can now log in."
                            )
                    except Exception as e:
                        st.error(f"❌ Sign Up Failed: {str(e)}")
