import streamlit as st
from supabase import Client, create_client


@st.cache_resource
def init_supabase() -> Client:
    """Supabase client ko initialize karta hai using Streamlit secrets."""
    supabase_url = st.secrets.get(
        "SUPABASE_URL", "https://your-project.supabase.co"
    )
    supabase_key = st.secrets.get("SUPABASE_KEY", "your-anon-key")
    return create_client(supabase_url, supabase_key)


supabase = init_supabase()
