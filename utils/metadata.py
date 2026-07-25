import streamlit as st

try:
    from database.supabase_client import supabase
except ImportError:
    supabase = None

def get_user_metadata():
    # Session restore karne ke liye Supabase session check karein
    if "user" not in st.session_state or st.session_state["user"] is None:
        if supabase:
            try:
                session_response = supabase.auth.get_session()
                if session_response and session_response.session:
                    st.session_state["user"] = session_response.session.user
            except Exception:
                pass

    user = st.session_state.get("user", None)
    
    details = {
        "email": "officer@urbaneye.ai",
        "username": "Inspector Ahmed",
        "phone": "+92 300 1234567",
        "address": "Lahore Urban Sector 4",
    }
    
    if user:
        user_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)
        email = getattr(user, "email", None) or (user.get("email") if isinstance(user, dict) else None)
        
        if email:
            details["email"] = email

        # 1. Database ki 'profiles' table se fresh data fetch karein
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
                    return details
            except Exception:
                pass

        # 2. Fallback to Auth metadata agar profiles table query fail ho jaye
        meta = {}
        if isinstance(user, dict):
            meta = user.get("user_metadata") or user.get("raw_user_meta_data") or {}
        else:
            meta = getattr(user, "user_metadata", None) or getattr(user, "raw_user_meta_data", None) or {}

        if meta.get("username"):
            details["username"] = meta.get("username")
        elif email:
            details["username"] = email.split("@")[0].replace(".", " ").replace("_", " ").title()

        if meta.get("phone") and str(meta.get("phone")).strip() != "":
            details["phone"] = meta.get("phone")
            
        if meta.get("address") and str(meta.get("address")).strip() != "":
            details["address"] = meta.get("address")
            
    return details
