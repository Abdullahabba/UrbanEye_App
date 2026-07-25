import streamlit as st

try:
    from database.supabase_client import supabase, supabase_admin
except ImportError:
    supabase = None
    supabase_admin = None

def get_user_metadata():
    details = {
        "email": "officer@urbaneye.ai",
        "username": "Inspector Ahmed",
        "phone": "+92 300 1234567",
        "address": "Lahore Urban Sector 4",
    }
    
    user_id = None
    email = None

    # 1. Check existing session in st.session_state
    if "user" in st.session_state and st.session_state["user"] is not None:
        user = st.session_state["user"]
        user_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)
        email = getattr(user, "email", None) or (user.get("email") if isinstance(user, dict) else None)
    
    # 2. If session lost on refresh, recover using query parameters (Persistent Login)
    if not user_id and "logged_in_email" in st.query_params and supabase_admin:
        try:
            logged_email = st.query_params["logged_in_email"]
            users = supabase_admin.auth.admin.list_users()
            for u in users:
                if (u.email or "").strip().lower() == logged_email.strip().lower():
                    user_id = u.id
                    email = u.email
                    st.session_state["user"] = u
                    break
        except Exception:
            pass

    if email:
        details["email"] = email

    # 3. Fetch fresh data directly from the 'profiles' table
    if user_id and supabase:
        try:
            res = supabase.table("profiles").select("*").eq("id", user_id).execute()
            if res.data and len(res.data) > 0:
                profile = res.data[0]
                if profile.get("username"):
                    details["username"] = profile.get("username")
                if profile.get("phone") and str(profile.get("phone")).strip() != "":
                    details["phone"] = profile.get("phone")
                if profile.get("address") and str(profile.get("address")).strip() != "":
                    details["address"] = profile.get("address")
        except Exception:
            pass
            
    return details
