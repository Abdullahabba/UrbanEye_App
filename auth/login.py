import streamlit as st
from database.supabase_client import supabase
from supabase import create_client

# Direct Admin Client setup with Service Role Key to bypass module cache
SUPABASE_URL = "https://clriyqbkdxpjscpufqns.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNscml5cWJrZHhwanNjcHVmcW5zIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NDc0MTAyNywiZXhwIjoyMTAwMzE3MDI3fQ.PpNmjWt6babeIB5b5ACghI7e633Cl0O1dtTsNWXPC_4"

# Admin Client (Has full database access for password resets)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def render_login_page():
    st.title("👁️ Urban Eye AI - Security Portal")

    # Session State Variables for 2-Step Password Reset Flow & Persistent Login
    if "reset_verified" not in st.session_state:
        st.session_state["reset_verified"] = False
    if "reset_target_user_id" not in st.session_state:
        st.session_state["reset_target_user_id"] = None
    if "reset_matched_email" not in st.session_state:
        st.session_state["reset_matched_email"] = ""

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
        remember_me = st.checkbox("Keep me logged in", key="login_remember_me")

        if st.button("Sign In", key="btn_login", use_container_width=True):
            if not email or not password:
                st.warning("Please enter both Email and Password!")
            else:
                try:
                    # 1. Supabase Authentication
                    response = supabase.auth.sign_in_with_password(
                        {"email": email, "password": password}
                    )
                    st.session_state["user"] = response.user
                    st.session_state["remember_me"] = remember_me
                    
                    # 2. Persistent Login via Query Parameters
                    if remember_me:
                        st.query_params["logged_in_email"] = email
                        st.success("✅ Login successful! (Session remembered)")
                    else:
                        if "logged_in_email" in st.query_params:
                            del st.query_params["logged_in_email"]
                        st.success("✅ Login successful!")
                        
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Login failed: {e}")

    # =========================================================================
    # TAB 2: SIGN UP
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

        if st.button("Register", key="btn_signup", use_container_width=True):
            if (
                not username
                or not new_email
                or not phone
                or not address
                or not new_password
            ):
                st.warning("Please fill in all required fields!")
            elif len(new_password) < 6:
                st.warning("Password must be at least 6 characters long!")
            else:
                try:
                    supabase.auth.sign_up(
                        {
                            "email": new_email,
                            "password": new_password,
                            "options": {
                                "data": {
                                    "username": username,
                                    "phone": phone.strip(),
                                    "address": address,
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
    # TAB 3: FORGOT PASSWORD (REQUIRES BOTH EMAIL & PHONE NUMBER)
    # =========================================================================
    with tab_forgot:
        st.subheader("🔑 Reset Password")

        # ---------------------------------------------------------------------
        # STEP 1: EMAIL & PHONE NUMBER VERIFICATION
        # ---------------------------------------------------------------------
        if not st.session_state["reset_verified"]:
            st.info(
                "💡 Enter both your registered **Email Address** and **Phone Number** to proceed."
            )

            reset_email = st.text_input(
                "Registered Email Address", key="reset_email_input"
            )
            reset_phone = st.text_input(
                "Registered Phone Number",
                key="reset_phone_input",
                placeholder="+923001234567",
            )

            if st.button(
                "🔍 Verify Account Details",
                key="btn_verify_account",
                use_container_width=True,
            ):
                if not reset_email.strip() or not reset_phone.strip():
                    st.warning("Please enter both Email Address and Phone Number!")
                else:
                    with st.spinner("Checking database for matching account..."):
                        try:
                            users = supabase_admin.auth.admin.list_users()
                            target_user = None

                            cleaned_email = reset_email.strip().lower()
                            cleaned_phone = reset_phone.strip()

                            for u in users:
                                u_email = (u.email or "").strip().lower()
                                user_metadata = (
                                    getattr(u, "user_metadata", {}) or {}
                                )
                                u_phone = str(
                                    user_metadata.get("phone", "")
                                ).strip()

                                if (
                                    u_email == cleaned_email
                                    and u_phone == cleaned_phone
                                ):
                                    target_user = u
                                    break

                            if target_user:
                                st.session_state["reset_verified"] = True
                                st.session_state["reset_target_user_id"] = (
                                    target_user.id
                                )
                                st.session_state["reset_matched_email"] = (
                                    cleaned_email
                                )
                                st.success(
                                    "✅ Account verified successfully!"
                                )
                                st.rerun()
                            else:
                                st.error(
                                    "❌ Invalid credentials! No matching account found with this Email and Phone Number combination."
                                )
                        except Exception as e:
                            st.error(f"❌ Verification failed: {e}")

        # ---------------------------------------------------------------------
        # STEP 2: NEW PASSWORD SETTING SCREEN
        # ---------------------------------------------------------------------
        else:
            st.success(
                f"✅ Verified Account: **{st.session_state['reset_matched_email']}**"
            )
            st.subheader("Set Your New Password")

            new_password = st.text_input(
                "New Password", type="password", key="reset_new_pass"
            )
            confirm_password = st.text_input(
                "Confirm New Password", type="password", key="reset_conf_pass"
            )

            col1, col2 = st.columns([3, 1])

            with col1:
                if st.button(
                    "💾 Update Password",
                    key="btn_save_pass",
                    use_container_width=True,
                ):
                    if not new_password or not confirm_password:
                        st.warning("Please fill in both password fields!")
                    elif new_password != confirm_password:
                        st.error("❌ Passwords do not match!")
                    elif len(new_password) < 6:
                        st.warning("⚠️ Password must be at least 6 characters long.")
                    else:
                        try:
                            with st.spinner("Updating password..."):
                                supabase_admin.auth.admin.update_user_by_id(
                                    st.session_state["reset_target_user_id"],
                                    {"password": new_password},
                                )

                                st.session_state["reset_verified"] = False
                                st.session_state["reset_target_user_id"] = None
                                st.session_state["reset_matched_email"] = ""

                                st.success(
                                    "🎉 Password updated successfully! Switch to the Login tab to sign in with your new password."
                                )
                        except Exception as e:
                            st.error(f"❌ Failed to update password: {e}")

            with col2:
                if st.button(
                    "🔙 Go Back", key="btn_back_reset", use_container_width=True
                ):
                    st.session_state["reset_verified"] = False
                    st.session_state["reset_target_user_id"] = None
                    st.session_state["reset_matched_email"] = ""
                    st.rerun()
