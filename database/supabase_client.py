import os
import streamlit as st
from supabase import Client, create_client

# -----------------------------------------------------------------------------
# 📌 SUPABASE CREDENTIALS (URBAN EYE AI)
# -----------------------------------------------------------------------------
SUPABASE_URL = st.secrets.get(
    "SUPABASE_URL",
    os.getenv("SUPABASE_URL", "https://clriyqbkdxpjscpufqns.supabase.co"),
)

SUPABASE_KEY = st.secrets.get(
    "SUPABASE_KEY",
    os.getenv(
        "SUPABASE_KEY",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNscml5cWJrZHhwanNjcHVmcW5zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ3NDEwMjcsImV4cCI6MjEwMDMxNzAyN30.sgslve6nIZ3h4gSHzHz8Ici9Zd-zbUkx5BPHEldaT2Q",
    ),
)

# Main Supabase Client Instance
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
