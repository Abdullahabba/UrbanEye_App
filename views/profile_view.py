import streamlit as st

def render_profile_page(user_details: dict):
    st.title("👤 Officer Profile")
    st.caption("Manage your professional credentials and contact information.")

    # Officer Credentials from user_details
    user_email = user_details.get('email', 'officer@urbaneye.ai') if isinstance(user_details, dict) else 'officer@urbaneye.ai'
    user_name = user_details.get('username', 'Abdullah Abbasi') if isinstance(user_details, dict) else 'Abdullah Abbasi'
    user_phone = user_details.get('phone', '+92 300 1234567') if isinstance(user_details, dict) else '+92 300 1234567'
    user_address = user_details.get('address', 'Iqbal Sector, Block AA, Lahore') if isinstance(user_details, dict) else 'Iqbal Sector, Block AA, Lahore'

    st.markdown("### 📋 Profile Credentials")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**👤 Full Name:** {user_name}")
            st.markdown(f"**📧 Official Email:** {user_email}")
        with col2:
            st.markdown(f"**📞 Phone Number:** {user_phone}")
            st.markdown(f"**📍 Assigned Sector / Address:** {user_address}")

    st.divider()

    # Profile Edit Section
    with st.expander("✏️ Update Profile Details"):
        with st.form(key="edit_profile_form"):
            new_name = st.text_input("Full Name", value=user_name)
            new_phone = st.text_input("Phone Number", value=user_phone)
            new_address = st.text_input("Assigned Sector / Address", value=user_address)

            submitted = st.form_submit_button("💾 Save Profile Changes")
            if submitted:
                # 1. Update local session dictionary
                if isinstance(user_details, dict):
                    user_details['username'] = new_name
                    user_details['phone'] = new_phone
                    user_details['address'] = new_address

                # 2. Push/Upsert changes to Supabase Database with full error tracking
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
                    
                    if supabase_url and supabase_key:
                        supabase = create_client(supabase_url, supabase_key)
                        # Agar table ka naam 'profiles' nahi hai, toh yahan error aayega
                        response = supabase.table("profiles").upsert(payload, on_conflict="email").execute()
                        st.success("✅ Profile successfully updated and synced with Supabase database!")
                        st.rerun()
                    else:
                        st.error("❌ Supabase URL or Key missing in Streamlit secrets.")
                except Exception as e:
                    st.error(f"❌ Supabase Sync Failed. Exact Error: {str(e)}")
