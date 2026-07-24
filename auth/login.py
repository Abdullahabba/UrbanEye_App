import streamlit as st
from database.supabase_client import supabase


def render_login_page():
    st.title("👁️ Urban Eye AI - Security Portal")

    # Session State Variables for OTP Flow Control
    if "otp_sent" not in st.session_state:
        st.session_state["otp_sent"] = False
    if "otp_verified" not in st.session_state:
        st.session_state["otp_verified"] = False
    if "reset_email" not in st.session_state:
        st.session_state["reset_email"] = ""

    # Tabs for Login, Sign Up, and Forgot Password
    tab_login, tab_signup, tab_forgot = st.tabs(
        ["🔑 Login", "📝 Sign Up", "❓ Forgot Password"]
    )

    # =========================================================================
    # TAB 1: LOGIN
    # =========================================================================
    with tab_login:
        st.subheader("Login to your account")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")

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
                    st.session_state["user"] = response.user
                    st.session_state["remember_me"] = remember_me
                    st.success("✅ Login successful!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Login failed: {e}")

    # =========================================================================
    # TAB 2: SIGN UP
    # =========================================================================
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

    # =========================================================================
    # TAB 3: FORGOT PASSWORD (6-DIGIT OTP FLOW)
    # =========================================================================
    with tab_forgot:
        st.subheader("🔑 Password Recovery via OTP")

        # ---------------------------------------------------------------------
        # STEP 1: REQUEST OTP (Email Enter Karein)
        # ---------------------------------------------------------------------
        if (
            not st.session_state["otp_sent"]
            and not st.session_state["otp_verified"]
        ):
            st.info(
                "📧 Apna registered email enter karein. Aap ko 6-digit OTP code bhej diya jayega."
            )
            reset_email_input = st.text_input(
                "Registered Email", key="input_reset_email"
            )

            if st.button(
                "📩 Send OTP Code",
                key="btn_send_otp",
                use_container_width=True,
            ):
                if not reset_email_input:
                    st.warning("Pehle Email enter karein!")
                else:
                    try:
                        # Supabase triggers OTP for password recovery
                        supabase.auth.reset_password_for_email(
                            reset_email_input
                        )
                        st.session_state["otp_sent"] = True
                        st.session_state["reset_email"] = reset_email_input
                        st.success(
                            f"✅ OTP Code **{reset_email_input}** par bhej diya gaya hai! Inbox check karein."
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ OTP bhejne me masla aaya: {e}")

        # ---------------------------------------------------------------------
        # STEP 2: ENTER & VERIFY OTP CODE
        # ---------------------------------------------------------------------
        elif (
            st.session_state["otp_sent"]
            and not st.session_state["otp_verified"]
        ):
            st.info(
                f"📩 Email **{st.session_state['reset_email']}** par bheja gaya 6-digit OTP code yahan enter karein:"
            )

            otp_code = st.text_input(
                "Enter 6-Digit OTP Code",
                max_chars=6,
                key="input_otp_code",
                placeholder="123456",
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "✅ Verify OTP",
                    key="btn_verify_otp",
                    use_container_width=True,
                ):
                    if not otp_code or len(otp_code) < 6:
                        st.warning("Mukammal 6-digit OTP enter karein!")
                    else:
                        try:
                            # Verify recovery OTP with Supabase
                            res = supabase.auth.verify_otp(
                                {
                                    "email": st.session_state["reset_email"],
                                    "token": otp_code,
                                    "type": "recovery",
                                }
                            )
                            st.session_state["otp_verified"] = True
                            st.success(
                                "🎉 OTP verified successfully! Ab naya password set karein."
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(
                                f"❌ Invalid or Expired OTP: {e}. Sahi code enter karein."
                            )

            with col2:
                if st.button(
                    "🔄 Wrong Email? Retry",
                    key="btn_reset_otp_state",
                    use_container_width=True,
                ):
                    st.session_state["otp_sent"] = False
                    st.session_state["reset_email"] = ""
                    st.rerun()

        # ---------------------------------------------------------------------
        # STEP 3: SET NEW PASSWORD (2 DAFA ENTER KAREIN)
        # ---------------------------------------------------------------------
        elif st.session_state["otp_verified"]:
            st.success("🔒 Identity Verified! Naya password set karein.")

            new_pwd = st.text_input(
                "Naya Password (New Password)",
                type="password",
                key="new_pwd_1",
            )
            confirm_pwd = st.text_input(
                "Confirm Naya Password", type="password", key="new_pwd_2"
            )

            if st.button(
                "💾 Save New Password & Finish",
                key="btn_save_new_pwd",
                use_container_width=True,
            ):
                if not new_pwd or not confirm_pwd:
                    st.warning("Dono password fields fill karein!")
                elif new_pwd != confirm_pwd:
                    st.error("❌ Mismatch! Dono passwords aik jaisay hone chahiye.")
                elif len(new_pwd) < 6:
                    st.warning("⚠️ Password kam az kam 6 characters ka hona chahiye.")
                else:
                    try:
                        # Update password in Supabase for verified user session
                        supabase.auth.update_user({"password": new_pwd})

                        # Sign out session so they can clean log in with new password
                        supabase.auth.sign_out()

                        # Reset states
                        st.session_state["otp_sent"] = False
                        st.session_state["otp_verified"] = False
                        st.session_state["reset_email"] = ""

                        st.success(
                            "🎉 Password kamyabi se update ho gaya! Ab Login tab se naye password ke sath sign in karein."
                        )
                    except Exception as e:
                        st.error(f"❌ Password update failed: {e}")
