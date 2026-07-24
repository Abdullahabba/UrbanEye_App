import streamlit as st
from database.supabase_client import SUPABASE_KEY, SUPABASE_URL, supabase
from supabase import create_client

# Admin Client for password override without email verification
try:
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    supabase_admin = supabase


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
        email = st.text_input("Email Address", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Sign In", key="btn_login", use_container_width=True):
            if not email or not password:
                st.warning("Please enter both Email and Password!")
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
    # TAB 2: SIGN UP (With Username, Phone, Address & 4-Digit Security PIN)
    # =========================================================================
    with tab_signup:
        st.subheader("Create a new account")
        username = st.text_input("Full Name / Username", key="signup_username")
        new_email = st.text_input("Email Address", key="signup_email")
        phone = st.text_input(
            "Phone Number", key="signup_phone", placeholder="+923001234567"
        )
        address = st.text_input(
            "Address", key="signup_address", placeholder="City, Country"
        )
        new_password = st.text_input(
            "Password", type="password", key="signup_pass"
        )

        security_pin = st.text_input(
            "4-Digit Security PIN (For Password Recovery)",
            type="password",
            max_chars=4,
            key="signup_pin",
            placeholder="e.g. 1234",
        )

        if st.button("Register", key="btn_signup", use_container_width=True):
            if (
                not username
                or not new_email
                or not phone
                or not address
                or not new_password
                or not security_pin
            ):
                st.warning("Please fill in all required fields!")
            elif len(security_pin) < 4 or not security_pin.isdigit():
                st.warning("Security PIN must be exactly 4 digits!")
            elif len(new_password) < 6:
                st.warning("Password must be at least 6 characters long!")
            else:
                try:
                    # Storing all extra metadata attributes in Supabase user profile
                    supabase.auth.sign_up(
                        {
                            "email": new_email,
                            "password": new_password,
                            "options": {
                                "data": {
                                    "username": username,
                                    "phone": phone,
                                    "address": address,
                                    "security_pin": security_pin,
                                }
                            },
                        }
                    )
                    st.success(
                        "✅ Account created successfully! Please switch to the Login tab to sign in."
                    )
                except Exception as e:
                    st.error(f"❌ Registration failed: {e}")

    # =========================================================================
    # TAB 3: FORGOT PASSWORD (Instant Reset via Security PIN)
    # =========================================================================
    with tab_forgot:
        st.subheader("🔑 Instant Password Reset")
        st.info(
            "💡 Enter your registered email and the **4-Digit Security PIN** you set during registration."
        )

        reset_email = st.text_input("Registered Email", key="reset_pin_email")
        entered_pin = st.text_input(
            "Your 4-Digit Security PIN",
            type="password",
            max_chars=4,
            key="reset_pin_input",
        )

        st.divider()

        new_password = st.text_input(
            "New Password", type="password", key="reset_new_pass"
        )
        confirm_password = st.text_input(
            "Confirm New Password", type="password", key="reset_conf_pass"
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
                st.warning("Please fill in all required fields!")
            elif new_password != confirm_password:
                st.error("❌ Passwords do not match!")
            elif len(new_password) < 6:
                st.warning("⚠️ Password must be at least 6 characters long.")
            else:
                try:
                    with st.spinner("Verifying PIN & updating password..."):
                        users = supabase_admin.auth.admin.list_users()
                        target_user = None

                        for u in users:
                            if u.email.lower() == reset_email.lower().strip():
                                target_user = u
                                break

                        if not target_user:
                            st.error("❌ This email is not registered!")
                        else:
                            saved_pin = target_user.user_metadata.get(
                                "security_pin"
                            )

                            if saved_pin and str(saved_pin) == str(entered_pin):
                                supabase_admin.auth.admin.update_user_by_id(
                                    target_user.id, {"password": new_password}
                                )
                                st.success(
                                    "🎉 Password updated successfully! Please switch to the Login tab to sign in."
                                )
                            else:
                                st.error(
                                    "❌ Invalid Security PIN! Please enter the correct PIN."
                                )
                except Exception as e:
                    st.error(f"❌ Reset failed: {e}")
