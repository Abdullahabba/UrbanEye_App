import streamlit as st

try:
    from database.supabase_client import supabase, supabase_admin
except ImportError:
    supabase = None
    supabase_admin = None

def get_user_metadata():
    default_details = {
        "email": "officer@urbaneye.ai",
        "username": "Inspector Ahmed",
        "phone": "+92 300 1234567",
        "address": "Lahore Urban Sector 4",
    }

    # 1. Agar session mein pehle se cached profile mojood hai
    if "user_profile" in st.session_state and st.session_state["user_profile"]:
        return st.session_state["user_profile"]

    user_id = None
    email = None

    # 2. Session state se user_id aur email nikalein
    if "user" in st.session_state and st.session_state["user"] is not None:
        user = st.session_state["user"]
        user_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)
        email = getattr(user, "email", None) or (user.get("email") if isinstance(user, dict) else None)

    # 3. Agar refresh ki wajah se session lose ho jaye, toh query params se recover karein
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

    # 4. Seedha 'profiles' table se user_id (UUID) ke zariye data fetch karein (No Failures)
    client = supabase_admin if supabase_admin else supabase
    if user_id and client:
        try:
            res = client.table("profiles").select("*").eq("id", user_id).execute()
            if res.data and len(res.data) > 0:
                profile = res.data[0]
                user_details = {
                    "email": profile.get("email") or email or "officer@urbaneye.ai",
                    "username": profile.get("username") or "Inspector Ahmed",
                    "phone": profile.get("phone") or "+92 300 1234567",
                    "address": profile.get("address") or "Lahore Urban Sector 4",
                }
                # Session mein permanent cache kar lein
                st.session_state["user_profile"] = user_details
                return user_details
        except Exception:
            pass

    return default_details
