import streamlit as st

try:
    from database.supabase_client import supabase_admin, supabase
except ImportError:
    supabase_admin = None
    supabase = None

def get_user_metadata():
    default_details = {
        "email": "officer@urbaneye.ai",
        "username": "Inspector Ahmed",
        "phone": "+92 300 1234567",
        "address": "Lahore Urban Sector 4",
    }

    # 1. Check session state cache first (Fastest)
    if "user_profile" in st.session_state and st.session_state["user_profile"]:
        return st.session_state["user_profile"]

    user_id = None
    email = None

    # 2. Extract user_id and email from session
    if "user" in st.session_state and st.session_state["user"] is not None:
        user = st.session_state["user"]
        user_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)
        email = getattr(user, "email", None) or (user.get("email") if isinstance(user, dict) else None)

    # 3. Recover email from query params if page refreshed
    if not email and "logged_in_email" in st.query_params:
        email = st.query_params["logged_in_email"]

    # 4. Fetch directly using supabase_admin (Bypasses RLS restrictions completely)
    client = supabase_admin if supabase_admin else supabase
    if client:
        try:
            res = None
            if user_id:
                res = client.table("profiles").select("*").eq("id", user_id).execute()
            
            if (not res or not res.data) and email:
                res = client.table("profiles").select("*").eq("email", email.strip().lower()).execute()

            if res and res.data and len(res.data) > 0:
                profile = res.data[0]
                user_details = {
                    "email": profile.get("email") or email or "officer@urbaneye.ai",
                    "username": profile.get("username") or "Inspector Ahmed",
                    "phone": profile.get("phone") or "+92 300 1234567",
                    "address": profile.get("address") or "Lahore Urban Sector 4",
                }
                # Permanent cache in session state
                st.session_state["user_profile"] = user_details
                return user_details
        except Exception:
            pass

    return default_details
