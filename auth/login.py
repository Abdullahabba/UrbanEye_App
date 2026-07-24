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

        # 🔹 Remember Me Feature Added
        remember_me = st.checkbox(
            " Remember Me (Mujhe logged in rakhein)", key="chk_remember_me"
        )

        if st.button("Sign In", key="btn_login", use_container_width=True):
            if not email or not password:
                st.warning("Pehle Email aur Password dono enter karein!")
            else:
                try:
                    response = supabase.auth.sign_in_with_password(
                        {"email": email, "password": password}
                    )
                    st.session_state["user"] = response.user

                    # Save 'Remember Me' status in Session
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
    # TAB 3: SIMPLIFIED FORGOT PASSWORD
    # -------------------------------------------------------------------------
    with tab_forgot:
        st.subheader("🔑 Password Recovery & Magic Link")

        reset_mode = st.radio(
            "Recovery Method Select Karein:",
            [
                "✨ Option 1: Direct Magic Link (Bina Password Direct Login)",
                "📧 Option 2: Password Reset Link Email Karein",
            ],
            key="reset_mode_choice",
        )

        st.divider()

        # EASY METHOD 1: MAGIC LINK
        if "Magic Link" in reset_mode:
            st.info(
                "💡 **Asaan Tareeqah:** Apna email likhein, hum aap ko login link bhej dein ge. Aap ko password ki zarurat nahi pare gi!"
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
                            f"✅ Login Link **{magic_email}** par bhej diya gaya hai! Email khol kar link par click karein."
                        )
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

        # EASY METHOD 2: STANDARD RESET LINK
        else:
            st.info(
                "📧 Apna email enter karein. Reset link par click kar ke aap naya password set kar sakte hain."
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
                            f"✅ Reset link **{reset_email}** par bhej diya gaya hai! Inbox / Spam folder check karein."
                        )
                    except Exception as e:
                        st.error(f"❌ Error sending reset link: {e}")

        # RECOVERY URL HANDLER (Jab user Email Link par click karke wapas aaye)
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
                            "🎉 Password update ho gaya! Ab Login tab se sign-in karein."
                        )
                    except Exception as e:
                        st.error(f"❌ Password update failed: {e}")
