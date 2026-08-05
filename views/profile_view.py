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

    st.divider()

    # Profile Edit & Sync Section
    with st.expander("✏️ Update Profile Details"):
        with st.form(key="edit_profile_form"):
            new_name = st.text_input("Full Name", value=user_name)
            new_phone = st.text_input("Phone Number", value=user_phone)
            new_address = st.text_input("Assigned Sector / Address", value=user_address)

            submitted = st.form_submit_button("💾 Save Profile Changes")
            if submitted:
                if not user_email:
                    st.error("❌ Email is required to save profile changes.")
                else:
                    payload = {
                        "email": user_email,
                        "username": new_name,
                        "phone": new_phone,
                        "address": new_address
                    }

                    try:
                        from supabase import create_client
                        supabase_url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
                        supabase_key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")
                        
                        if not supabase_url or not supabase_key:
                            st.error("❌ Supabase credentials are missing from secrets!")
                        else:
                            supabase = create_client(supabase_url, supabase_key)
                            supabase.table("profiles").upsert(payload, on_conflict="email").execute()
                            
                            # Update local session state dictionary
                            if isinstance(user_details, dict):
                                user_details['username'] = new_name
                                user_details['phone'] = new_phone
                                user_details['address'] = new_address
                                
                            st.success("✅ Profile successfully updated and synced with Supabase database!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Supabase Sync Failed. Error: {str(e)}")
