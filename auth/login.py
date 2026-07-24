import streamlit as st
from database.supabase_client import SUPABASE_KEY, SUPABASE_URL, supabase
from supabase import create_client

# Admin Client for direct password updates
try:
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    supabase_admin = supabase


def render_login_page():
    st.title("👁️ Urban Eye AI - Security Portal")

    # Session State Variables to handle 2-Step Password Reset Flow
    if "reset_phone_verified" not in st.session_state:
        st.session_state["reset_phone_verified"] = False
    if "reset_target_user_id" not in st.session_state:
        st.session_state["reset_target_user_id"] = None
    if "reset_matched_phone" not in st.session_state:
        st.session_state["reset_matched_phone"] = ""

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
    # TAB 3: FORGOT PASSWORD (2-STEP PHONE NUMBER VERIFICATION FLOW)
    # =========================================================================
    with tab_forgot:
        st.subheader("🔑 Reset Password via Phone Number")

        # ---------------------------------------------------------------------
        # STEP 1: PHONE NUMBER CHECK
        # ---------------------------------------------------------------------
        if not st.session_state["reset_phone_verified"]:
            st.info(
                "💡 Enter your registered Phone Number. If verified, you will proceed to the New Password screen."
            )

            reset_phone = st.text_input(
                "Registered Phone Number",
                key="reset_phone_input",
                placeholder="+923001234567",
            )

            if st.button(
                "🔍 Verify Phone Number",
                key="btn_verify_phone",
                use_container_width=True,
            ):
                if not reset_phone.strip():
                    st.warning("Please enter your Phone Number!")
                else:
                    with st.spinner("Checking database for phone number..."):
                        try:
                            users = supabase_admin.auth.admin.list_users()
                            target_user = None
                            cleaned_phone = reset_phone.strip()

                            for u in users:
                                user_metadata = (
                                    getattr(u, "user_metadata", {}) or {}
                                )
                                saved_phone = user_metadata.get("phone", "")

                                if (
                                    saved_phone
                                    and str(saved_phone).strip() == cleaned_phone
                                ):
                                    target_user = u
                                    break

                            if target_user:
                                st.session_state["reset_phone_verified"] = True
                                st.session_state["reset_target_user_id"] = (
                                    target_user.id
                                )
                                st.session_state["reset_matched_phone"] = (
                                    cleaned_phone
                                )
                                st.success("✅ Phone number matched successfully!")
                                st.rerun()
                            else:
                                st.error(
                                    "❌ No account found registered with this Phone Number!"
                                )
                        except Exception as e:
                            st.error(f"❌ Verification failed: {e}")

        # ---------------------------------------------------------------------
        # STEP 2: NEW PASSWORD SETTING SCREEN (Only opens if Phone matches)
        # ---------------------------------------------------------------------
        else:
            st.success(
                f"✅ Verified Account Phone: **{st.session_state['reset_matched_phone']}**"
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
                        st.warning("Please enter both password fields!")
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

                                # Clear reset state
                                st.session_state["reset_phone_verified"] = False
                                st.session_state["reset_target_user_id"] = None
                                st.session_state["reset_matched_phone"] = ""

                                st.success(
                                    "🎉 Password updated successfully! Switch to the Login tab to sign in with your new password."
                                )
                        except Exception as e:
                            st.error(f"❌ Failed to update password: {e}")

            with col2:
                if st.button(
                    "🔙 Change Phone", key="btn_back_phone", use_container_width=True
                ):
                    st.session_state["reset_phone_verified"] = False
                    st.session_state["reset_target_user_id"] = None
                    st.session_state["reset_matched_phone"] = ""
                    st.rerun()
