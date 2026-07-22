import os
import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def get_supabase_client() -> Client:
    url = ""
    key = ""
    
    # Try fetching from Streamlit secrets safely
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        # Fallback to Environment variables if secrets file is missing
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
        
    if not url or not key:
        st.error("⚠️ Supabase Credentials missing! Please add SUPABASE_URL and SUPABASE_KEY in .streamlit/secrets.toml")
        st.stop()
        
    return create_client(url, key)