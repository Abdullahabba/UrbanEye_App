import streamlit as st
from database.supabase_client import supabase
from supabase import create_client

SUPABASE_URL = "https://clriyqbkdxpjscpufqns.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNscml5cWJrZHhwanNjcHVmcW5zIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NDc0MTAyNywiZXhwIjoyMTAwMzE3MDI3fQ.PpNmjWt6babeIB5b5ACghI7e633Cl0O1dtTsNWXPC_4"

supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def render_login_page():
    st.title("👁️ Urban Eye AI - Security Portal")

    tab_login, tab_signup = st.tabs(["🔑 Login", "📝 Sign Up"])

    # --- LOGIN TAB ---
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

    # --- SIGN UP TAB ---
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
                    if user_obj:
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
