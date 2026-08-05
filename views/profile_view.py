import streamlit as st

def render_profile_page(user_details: dict):
    st.title("👤 Officer Profile")
    st.caption("Manage your professional credentials and contact information.")

    # Get email and fields without hardcoded fake fallbacks
    user_email = user_details.get('email', '') if isinstance(user_details, dict) else ''
    user_name = user_details.get('username', '') if isinstance(user_details, dict) else ''
    user_phone = user_details.get('phone', '') if isinstance(user_details, dict) else ''
    user_address = user_details.get('address', '') if isinstance(user_details, dict) else ''

    # Fetch latest profile data directly from Supabase 'profiles' table on load
    try:
        from supabase import create_client
        supabase_url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
        supabase_key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")
        
        if supabase_url and supabase_key and user_email:
            supabase = create_client(supabase_url, supabase_key)
            response = supabase.table("profiles").select("*").eq("email", user_email).execute()
            
            if response.data and len(response.data) > 0:
                remote_profile = response.data[0]
                user_name = remote_profile.get("username", user_name)
                user_phone = remote_profile.get("phone", user_phone)
                user_address = remote_profile.get("address", user_address)
    except Exception as fetch_err:
        pass

    st.markdown("### 📋 Profile Credentials")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**👤 Full Name:** {user_name if user_name else '*(Not provided)*'}")
            st.markdown(f"**📧 Official Email:** {user_email if user_email else '*(Not provided)*'}")
        with col2:
            st.markdown(f"**📞 Phone Number:** {user_phone if user_phone else '*(Not provided)*'}")
            st.markdown(f"**📍 Assigned Sector / Address:** {user_address if user_address else '*(Not provided)*'}")
