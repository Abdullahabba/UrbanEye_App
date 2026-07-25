import streamlit as st

try:
    from database.supabase_client import supabase
except ImportError:
    supabase = None

def get_user_metadata():
    default_details = {
        "email": "officer@urbaneye.ai",
        "username": "Inspector Ahmed",
        "phone": "+92 300 1234567",
        "address": "Lahore Urban Sector 4",
    }
    
    # 1. Agar session mein pehle se profile saved hai, toh wahi return karein (Fastest)
    if "user_profile" in st.session_state and st.session_state["user_profile"]:
        return st.session_state["user_profile"]

    email = None
    
    # 2. Session state se email nikalein
    if "user" in st.session_state and st.session_state["user"] is not None:
        user = st.session_state["user"]
        email = getattr(user, "email", None) or (user.get("email") if isinstance(user, dict) else None)
    
    # 3. Agar session loss ho jaye toh query params (Keep me logged in) se email nikalein
    if not email and "logged_in_email" in st.query_params:
        email = st.query_params["logged_in_email"]

    # 4. Database ki 'profiles' table se email ke zariye data fetch karein
    if email and supabase:
        try:
            res = supabase.table("profiles").select("*").eq("email", email.strip().lower()).execute()
            if res.data and len(res.data) > 0:
                profile = res.data[0]
                user_details = {
                    "email": profile.get("email", email),
                    "username": profile.get("username", "Inspector Ahmed"),
                    "phone": profile.get("phone", "+92 300 1234567"),
                    "address": profile.get("address", "Lahore Urban Sector 4"),
                }
                # Session mein permanent cache kar lein
                st.session_state["user_profile"] = user_details
                return user_details
        except Exception:
            pass

    return default_details
