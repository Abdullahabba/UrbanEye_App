import streamlit as st
from database.supabase_client import SUPABASE_KEY, SUPABASE_URL, supabase
# Admin Client for password override without email
from supabase import create_client

# Admin client with Service Role Key (Ya direct client if configured)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_KEY)


def render_login_page():
    st.title("👁️ Urban Eye AI - Security Portal")

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

        if st.button("Sign In", key="btn_login", use_container_width=True):
            if not email or not password:
                st.warning("Pehle Email aur Password dono enter karein!")
            else:
                try:
                    response = supabase.auth.sign_in_with_password(
                        {"email": email, "password": password}
                    )
                    st.session_state["user"] = response.user
                    st.success("✅ Login successful!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Login failed: {e}")

    # =========================================================================
    # TAB 2: SIGN UP (With 4-Digit Security PIN)
    # =========================================================================
    with tab_signup:
        st.subheader("Create a new account")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input(
            "Password", type="password", key="signup_pass"
        )

        # Security PIN field added
        security_pin = st.text_input(
            "Set 4-Digit Security PIN (Password Reset ke liye)",
            type="password",
            max_chars=4,
            key="signup_pin",
            placeholder="e.g. 1234",
        )

        if st.button("Register", key="btn_signup", use_container_width=True):
            if not new_email or not new_password or not security_pin:
                st.warning(
                    "Khabardar: Email, Password aur 4-digit PIN teeno fill karein!"
                )
            elif len(security_pin) < 4 or not security_pin.isdigit():
                st.warning("Security PIN me sirf 4 numbers hone chahiye!")
            else:
                try:
                    # Save PIN inside user metadata
                    supabase.auth.sign_up(
                        {
                            "email": new_email,
                            "password": new_password,
                            "options": {"data": {"security_pin": security_pin}},
                        }
                    )
                    st.success("✅ Account created successfully! Ab login karein.")
                except Exception as e:
                    st.error(f"❌ Registration failed: {e}")

    # =========================================================================
    # TAB 3: FORGOT PASSWORD (Instant Reset via Security PIN)
    # =========================================================================
    with tab_forgot:
        st.subheader("🔑 Instant Password Reset")
        st.info(
            "💡 Registration ke waqt set kiya gaya **4-Digit Security PIN** enter karein."
        )

        reset_email = st.text_input(
            "Registered Email", key="reset_pin_email"
        )
        entered_pin = st.text_input(
            "Your 4-Digit Security PIN",
            type="password",
            max_chars=4,
            key="reset_pin_input",
        )

        st.divider()

        new_password = st.text_input(
            "Naya Password (New Password)", type="password", key="reset_new_pass"
        )
        confirm_password = st.text_input(
            "Confirm Naya Password", type="password", key="reset_conf_pass"
        )

        if st.button(
            "⚡ Reset Password Instantly",
            key="btn_reset_by_pin",
            use_container_width=True,
        ):
            if (
                not reset_email
                or not entered_pin
                or not new_password
                or not confirm_password
            ):
                st.warning("Tamam fields fill karein!")
            elif new_password != confirm_password:
                st.error("❌ Passwords match nahi kar rahe!")
            elif len(new_password) < 6:
                st.warning("⚠️ Password kam az kam 6 characters ka hona chahiye.")
            else:
                try:
                    with st.spinner("Verifying PIN & Updating Password..."):
                        # 1. Sign in temporarily with old credentials OR check PIN metadata via Admin API
                        # Fetch user list to verify PIN
                        users = (
                            supabase_admin.auth.admin.list_users()
                        )  # Fetches user profiles
                        target_user = None

                        for u in users:
                            if u.email.lower() == reset_email.lower().strip():
                                target_user = u
                                break

                        if not target_user:
                            st.error("❌ Yeh Email registered nahi hai!")
                        else:
                            # Verify PIN from metadata
                            saved_pin = target_user.user_metadata.get(
                                "security_pin"
                            )

                            if saved_pin and str(saved_pin) == str(entered_pin):
                                # Update user password directly using Admin API
                                supabase_admin.auth.admin.update_user_by_id(
                                    target_user.id, {"password": new_password}
                                )
                                st.success(
                                    "🎉 Password instantly update ho gaya! Ab Login tab se Sign In karein."
                                )
                            else:
                                st.error("❌ Invalid Security PIN! Sahi PIN enter karein.")
                except Exception as e:
                    st.error(f"❌ Reset failed: {e}")
