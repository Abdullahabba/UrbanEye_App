import streamlit as st

try:
    from database.supabase_client import supabase
except ImportError:
    supabase = None

def get_user_metadata():
    # Refresh hone par session restore karne ke liye Supabase session check karein
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
        # If user data is stored as a dictionary (Supabase standard response)
        if isinstance(user, dict):
            details["email"] = user.get("email", details["email"])
            meta = user.get("user_metadata") or user.get("raw_user_meta_data") or {}
            if meta:
                details["username"] = meta.get("username", details["username"])
                details["phone"] = meta.get("phone", details["phone"])
                details["address"] = meta.get("address", details["address"])
        
        # If user data is stored as an object
        else:
            if hasattr(user, "email") and user.email:
                details["email"] = user.email
            
            meta = getattr(user, "user_metadata", None) or getattr(user, "raw_user_meta_data", None)
            if meta:
                details["username"] = meta.get("username", details["username"]) if isinstance(meta, dict) else getattr(meta, "username", details["username"])
                details["phone"] = meta.get("phone", details["phone"]) if isinstance(meta, dict) else getattr(meta, "phone", details["phone"])
                details["address"] = meta.get("address", details["address"]) if isinstance(meta, dict) else getattr(meta, "address", details["address"])
                
    return details
