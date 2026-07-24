import streamlit as st
from database.supabase_client import supabase


def render_login_page():
    st.title("👁️ Urban Eye AI - Security Portal")

    # Tabs for Login, Sign Up, and Forgot Password
    tab_login, tab_signup, tab_forgot = st.tabs(
        ["🔑 Login", "📝 Sign Up", "❓ Forgot Password"]
    )

    # -------------------------------------------------------------------------
    # TAB 1: LOGIN
    # -------------------------------------------------------------------------
    with tab_login:
        st.subheader("Login to your account")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Sign In", key="btn_login"):
            try:
                response = supabase.auth.sign_in_with_password(
                    {"email": email, "password": password}
                )
                st.session_state["user"] = response.user
                st.success("✅ Login successful!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Login failed: {e}")

    # -------------------------------------------------------------------------
    # TAB 2: SIGN UP
    # -------------------------------------------------------------------------
    with tab_signup:
        st.subheader("Create a new account")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_pass")

        if st.button("Register", key="btn_signup"):
            try:
                supabase.auth.sign_up({"email": new_email, "password": new_password})
                st.success("✅ Account created! Please check your email to verify.")
            except Exception as e:
                st.error(f"❌ Registration failed: {e}")

    # -------------------------------------------------------------------------
    # TAB 3: FORGOT PASSWORD (Naya Option)
    # -------------------------------------------------------------------------
    with tab_forgot:
        st.subheader("🔑 Reset Your Password")
        st.caption(
            "Apna registered email enter karein. Hum aap ko password reset karne ka link bhejen ge."
        )

        reset_email = st.text_input("Registered Email", key="reset_email_input")

        if st.button("📩 Send Reset Link", key="btn_forgot_password"):
            if not reset_email:
                st.warning("Khabardar: Pehle email enter karein!")
            else:
                try:
                    # Supabase API call for Password Reset Link
                    supabase.auth.reset_password_for_email(
                        reset_email,
                        # Live app URL ya Localhost link jahan user click karke wapas aaye
                        redirect_to="http://localhost:8501",
                    )
                    st.success(
                        f"✅ Reset link **{reset_email}** par bhej diya gaya hai! Apna Inbox / Spam folder check karein."
                    )
                except Exception as e:
                    st.error(f"❌ Error sending reset link: {e}")

        st.divider()

        # STEP 2: Jab user email link se wapas aaye toh Naya Password Set karne ka Form
        # Streamlit URL se check karein ke kya recovery token aaya hai
        query_params = st.query_params
        if "type" in query_params and query_params["type"] == "recovery":
            st.info("🔐 Set your new password below:")
            new_pwd = st.text_input(
                "Enter New Password", type="password", key="new_pwd_input"
            )
            confirm_pwd = st.text_input(
                "Confirm New Password", type="password", key="confirm_pwd_input"
            )

            if st.button("💾 Update Password", key="btn_update_password"):
                if new_pwd != confirm_pwd:
                    st.error("Passwords match nahi kar rahe!")
                elif len(new_pwd) < 6:
                    st.warning("Password kam az kam 6 characters ka hona chahiye.")
                else:
                    try:
                        # Update user password in Supabase
                        supabase.auth.update_user({"password": new_pwd})
                        st.success(
                            "🎉 Password successfully update ho gaya! Ab Login tab se sign-in karein."
                        )
                    except Exception as e:
                        st.error(f"❌ Password update fail hua: {e}")
