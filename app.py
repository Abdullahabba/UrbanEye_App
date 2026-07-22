import streamlit as st
from supabase import create_client

# Supabase Client Configuration
SUPABASE_URL = "https://clriyqbkdxpjscpufqns.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNscml5cWJrZHhwanNjcHVmcW5zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ3NDEwMjcsImV4cCI6MjEwMDMxNzAyN30.sgslve6nIZ3h4gSHzHz8Ici9Zd-zbUkx5BPHEldaT2Q"  # Yahan apni Anon Public Key daalein

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("👁️ UrbanEye AI Dashboard")

# Google Sign-In Button
if st.button("🌐 Sign in with Google", use_container_width=True):
    response = supabase.auth.sign_in_with_oauth({
        "provider": "google",
        "options": {
            "redirect_to": "https://urbaneye-app.streamlit.app"
        }
    })
    # Google Auth Page par redirect karne ke liye
    st.markdown(f'<meta http-equiv="refresh" content="0;url={response.url}">', unsafe_allow_html=True)
