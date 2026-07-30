import streamlit as st
from database.supabase_client import supabase, supabase_admin

from pathlib import Path

def load_css():
    css_path = Path(__file__).parent / "style.css"
    css = css_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_css()

def render_login_page():
    st.title("👁️ Urban Eye AI - Security Portal")

    # 1. Password Reset State Initialization
    if "reset_verified" not in st.session_state:
        st.session_state["reset_verified"] = False
    if "reset_target_user_id" not in st.session_state:
        st.session_state["reset_target_user_id"] = None
    if "reset_matched_email" not in st.session_state:
        st.session_state["reset_matched_email"] = ""

    # 2. Auto-login recovery on page refresh (Keep me logged in)
    if "user" not in st.session_state or st.session_state["user"] is None:
        if "logged_in_email" in st.query_params and supabase_admin:
            try:
                saved_email = st.query_params["logged_in_email"]
                res = supabase_admin.table("profiles").select("*").eq("email", saved_email.strip().lower()).execute()
                if res.data and len(res.data) > 0:
                    profile = res.data[0]
                    st.session_state["user_profile"] = {
                        "email": profile.get("email", saved_email),
                        "username": profile.get("username", "Inspector Ahmed"),
                        "phone": profile.get("phone", "+92 300 1234567"),
                        "address": profile.get("address", "Lahore Urban Sector 4"),
                    }
            except Exception:
                pass

    tab_login, tab_signup, tab_forgot = st.tabs(
        ["🔑 Login", "📝 Sign Up", "❓ Forgot Password"]
    )

    # =========================================================================
    # --- LOGIN TAB ---
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
                    response = supabase.auth.sign_in_with_password(
                        {"email": email, "password": password}
                    )
                    st.session_state["user"] = response.user
                    
                    if remember_me:
                        st.query_params["logged_in_email"] = email
                    else:
                        if "logged_in_email" in st.query_params:
                            del st.query_params["logged_in_email"]

                    # Database se profile fetch karke session cache mein save karein
                    res = supabase.table("profiles").select("*").eq("email", email.strip().lower()).execute()
                    if res.data and len(res.data) > 0:
                        profile = res.data[0]
                        st.session_state["user_profile"] = {
                            "email": profile.get("email", email),
                            "username": profile.get("username", "Inspector Ahmed"),
                            "phone": profile.get("phone", "+92 300 1234567"),
                            "address": profile.get("address", "Lahore Urban Sector 4"),
                        }

                    st.success("✅ Login successful!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Login failed: {e}")

    # =========================================================================
    # --- SIGN UP TAB ---
    # =========================================================================
    with tab_signup:
        st.subheader("Create a new account")
        username = st.text_input("Full Name / Username", key="signup_username")
        new_email = st.text_input("Email Address", key="signup_email")
        phone = st.text_input("Phone Number", key="signup_phone", placeholder="+923001234567")
        address = st.text_input("Address", key="signup_address", placeholder="City, Country")
        new_password = st.text_input("Password", type="password", key="signup_pass")

        if st.button("Register", key="btn_signup", use_container_width=True):
            if not username or not new_email or not phone or not address or not new_password:
                st.warning("Please fill in all required fields!")
            elif len(new_password) < 6:
                st.warning("Password must be at least 6 characters long!")
            else:
                try:
                    auth_response = supabase.auth.sign_up(
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
                    
                    user_obj = auth_response.user
                    if user_obj and supabase_admin:
                        profile_data = {
                            "id": user_obj.id,
                            "email": new_email.strip().lower(),
                            "username": username.strip(),
                            "phone": phone.strip(),
                            "address": address.strip()
                        }
                        # Admin client ke zariye profiles table mein save karein
                        supabase_admin.table("profiles").upsert(profile_data).execute()
                        
                        # Foran session cache mein bhi save karein
                        st.session_state["user_profile"] = profile_data

                    st.success("✅ Account created successfully! Please switch to the Login tab to sign in.")
                except Exception as e:
                    st.error(f"❌ Registration failed: {e}")

    # =========================================================================
    # --- FORGOT PASSWORD TAB ---
    # =========================================================================
    with tab_forgot:
        st.subheader("🔑 Reset Password")

        # Agar account abhi tak verify nahi hua, toh email aur phone mangay ga
        if not st.session_state["reset_verified"]:
            st.info("💡 Enter your registered **Email Address** and **Phone Number** to verify your account.")

            reset_email = st.text_input("Registered Email Address", key="reset_email_input")
            reset_phone = st.text_input("Registered Phone Number", key="reset_phone_input", placeholder="+923001234567")

            if st.button("🔍 Verify Account Details", key="btn_verify_account", use_container_width=True):
                if not reset_email.strip() or not reset_phone.strip():
                    st.warning("Please enter both Email Address and Phone Number!")
                else:
                    with st.spinner("Checking database for matching account..."):
                        try:
                            # Direct check from profiles table (Extremely fast & accurate)
                            res = supabase_admin.table("profiles").select("id, email, phone").eq("email", reset_email.strip().lower()).eq("phone", reset_phone.strip()).execute()

                            if res.data and len(res.data) > 0:
                                target_user = res.data[0]
                                st.session_state["reset_verified"] = True
                                st.session_state["reset_target_user_id"] = target_user["id"]
                                st.session_state["reset_matched_email"] = target_user["email"]
                                st.success("✅ Account verified successfully!")
                                st.rerun()
                            else:
                                st.error("❌ Invalid credentials! No matching account found with this email and phone number.")
                        except Exception as e:
                            st.error(f"❌ Verification failed: {e}")
        else:
            # Jab account verify ho jaye, tab naya password set karne ka form aaye ga
            st.success(f"✅ Verified Account: **{st.session_state['reset_matched_email']}**")
            
            st.subheader("Set Your New Password")

            pass_1 = st.text_input("New Password", type="password", key="reset_new_pass")
            pass_2 = st.text_input("Confirm New Password", type="password", key="reset_conf_pass")

            col1, col2 = st.columns([3, 1])

            with col1:
                if st.button("💾 Update Password", key="btn_save_pass", use_container_width=True):
                    if not pass_1 or not pass_2:
                        st.warning("Please fill in both password fields!")
                    elif pass_1 != pass_2:
                        st.error("❌ Passwords do not match!")
                    elif len(pass_1) < 6:
                        st.warning("⚠️ Password must be at least 6 characters long.")
                    else:
                        try:
                            with st.spinner("Updating password securely..."):
                                supabase_admin.auth.admin.update_user_by_id(
                                    st.session_state["reset_target_user_id"],
                                    {"password": pass_1},
                                )

                                # Reset states
                                st.session_state["reset_verified"] = False
                                st.session_state["reset_target_user_id"] = None
                                st.session_state["reset_matched_email"] = ""

                                st.success("🎉 Password updated successfully! Please switch to Login tab.")
                        except Exception as e:
                            st.error(f"❌ Failed to update password: {e}")

            with col2:
                if st.button("🔙 Go Back", key="btn_back_reset", use_container_width=True):
                    st.session_state["reset_verified"] = False
                    st.session_state["reset_target_user_id"] = None
                    st.session_state["reset_matched_email"] = ""
                    st.rerun()
