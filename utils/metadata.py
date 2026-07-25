import streamlit as st

try:
    from database.supabase_client import supabase_admin
except ImportError:
    supabase_admin = None

def get_user_metadata():
    default_details = {
        "email": "officer@urbaneye.ai",
        "username": "Inspector Ahmed",
        "phone": "+92 300 1234567",
        "address": "Lahore Urban Sector 4",
    }

    # 1. Agar session mein pehle se profile cached hai
    if "user_profile" in st.session_state and st.session_state["user_profile"]:
        return st.session_state["user_profile"]

    user_id = None
    email = None
    auth_user_metadata = {}

    # 2. Session state se user details nikalein
    if "user" in st.session_state and st.session_state["user"] is not None:
        user = st.session_state["user"]
        user_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)
        email = getattr(user, "email", None) or (user.get("email") if isinstance(user, dict) else None)
        
        # Supabase auth built-in metadata
        auth_metadata = getattr(user, "user_metadata", None) or (user.get("user_metadata") if isinstance(user, dict) else {})
        if auth_metadata:
            auth_user_metadata = auth_metadata

    # 3. Query params se email recovery (Keep me logged in)
    if not email and "logged_in_email" in st.query_params:
        email = st.query_params["logged_in_email"]

    # 4. Database ('profiles' table) se supabase_admin ke zariye fetch karein
    if supabase_admin:
        try:
            res = None
            if user_id:
                res = supabase_admin.table("profiles").select("*").eq("id", user_id).execute()
            
            if (not res or not res.data) and email:
                res = supabase_admin.table("profiles").select("*").eq("email", email.strip().lower()).execute()

            if res and res.data and len(res.data) > 0:
                profile = res.data[0]
                user_details = {
                    "email": profile.get("email") or email or "officer@urbaneye.ai",
                    "username": profile.get("username") or auth_user_metadata.get("username", "Inspector Ahmed"),
                    "phone": profile.get("phone") or auth_user_metadata.get("phone", "+92 300 1234567"),
                    "address": profile.get("address") or auth_user_metadata.get("address", "Lahore Urban Sector 4"),
                }
                st.session_state["user_profile"] = user_details
                return user_details
        except Exception:
            pass

    # 5. Fallback: Agar profiles table mein row na mile lekin Auth mein mojood ho
    if auth_user_metadata or email:
        fallback_details = {
            "email": email or auth_user_metadata.get("email", "officer@urbaneye.ai"),
            "username": auth_user_metadata.get("username", "Inspector Ahmed"),
            "phone": auth_user_metadata.get("phone", "+92 300 1234567"),
            "address": auth_user_metadata.get("address", "Lahore Urban Sector 4"),
        }
        st.session_state["user_profile"] = fallback_details
        return fallback_details

    return default_details
