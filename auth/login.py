import streamlit as st
from database.supabase_client import supabase


def render_login_page():
    st.title("👁️ Urban Eye AI - Security Portal")

    # Tabs for Login, Sign Up, and Password Recovery
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

        # Remember Me Checkbox
        remember_me = st.checkbox(
            "Remember Me (Mujhe logged in rakhein)", key="chk_remember_me"
        )

        if st.button("Sign In", key="btn_login", use_container_width=True):
            if not email or not password:
                st.warning("Pehle Email aur Password dono enter karein!")
            else:
                try:
                    response = supabase.auth.sign_in_with_password(
                        {"email": email, "password": password}
                    )
                    # Store User and Remember Me state
                    st.session_state["user"] = response.user
                    st.session_state["remember_me"] = remember_me

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
        new_password = st.text_input(
            "Password", type="password", key="signup_pass"
        )

        if st.button("Register", key="btn_signup", use_container_width=True):
            if not new_email or not new_password:
                st.warning("Khabardar: Email aur Password dono fill karein!")
            else:
                try:
                    supabase.auth.sign_up(
                        {"email": new_email, "password": new_password}
                    )
                    st.success(
                        "✅ Account created! Check your email inbox to verify your account."
                    )
                except Exception as e:
                    st.error(f"❌ Registration failed: {e}")

    # -------------------------------------------------------------------------
    # TAB 3: FORGOT PASSWORD & MAGIC LINK
    # -------------------------------------------------------------------------
    with tab_forgot:
        st.subheader("🔑 Password Recovery Options")

        reset_mode = st.radio(
            "Select Recovery Option:",
            [
                "✨ Option 1: Direct Magic Link (Bina Password Direct Login)",
                "📧 Option 2: Reset Password Email Link",
            ],
            key="reset_mode_choice",
        )

        st.divider()

        # OPTION 1: MAGIC LINK
        if "Magic Link" in reset_mode:
            st.info(
                "💡 **Asaan Tareeqah:** Email enter karein, aap ko direct login link bhej diya jaye ga."
            )
            magic_email = st.text_input(
                "Registered Email", key="magic_email_input"
            )

            if st.button(
                "✨ Send Magic Login Link",
                key="btn_magic_link",
                use_container_width=True,
            ):
                if not magic_email:
                    st.warning("Pehle apna email enter karein!")
                else:
                    try:
                        supabase.auth.sign_in_with_otp({"email": magic_email})
                        st.success(
                            f"✅ Direct Login Link **{magic_email}** par bhej diya gaya hai! Inbox check karein."
                        )
                    except Exception as e:
                        st.error(f"❌ Magic Link Sending Failed: {e}")

        # OPTION 2: RESET PASSWORD LINK
        else:
            st.info(
                "📧 Email enter karein. Link par click kar ke aap naya password set kar sakte hain."
            )
            reset_email = st.text_input(
                "Registered Email", key="reset_email_input"
            )

            if st.button(
                "📩 Send Reset Link",
                key="btn_forgot_password",
                use_container_width=True,
            ):
                if not reset_email:
                    st.warning("Pehle apna email enter karein!")
                else:
                    try:
                        supabase.auth.reset_password_for_email(
                            reset_email,
                            options={"redirect_to": "http://localhost:8501"},
                        )
                        st.success(
                            f"✅ Reset link **{reset_email}** par bhej diya gaya hai! Inbox / Spam check karein."
                        )
                    except Exception as e:
                        st.error(f"❌ Error sending reset link: {e}")

        # RECOVERY URL HANDLER (Jab user Email Reset Link se wapas aaye)
        query_params = st.query_params
        if "type" in query_params and query_params["type"] == "recovery":
            st.divider()
            st.subheader("🔐 Set Your New Password")
            new_pwd = st.text_input(
                "Enter New Password", type="password", key="new_pwd_input"
            )
            confirm_pwd = st.text_input(
                "Confirm New Password",
                type="password",
                key="confirm_pwd_input",
            )

            if st.button(
                "💾 Update Password",
                key="btn_update_password",
                use_container_width=True,
            ):
                if new_pwd != confirm_pwd:
                    st.error("Passwords match nahi kar rahe!")
                elif len(new_pwd) < 6:
                    st.warning(
                        "Password kam az kam 6 characters ka hona chahiye."
                    )
                else:
                    try:
                        supabase.auth.update_user({"password": new_pwd})
                        st.success(
                            "🎉 Password successfully update ho gaya! Ab Login tab se sign-in karein."
                        )
                    except Exception as e:
                        st.error(f"❌ Password update failed: {e}")
