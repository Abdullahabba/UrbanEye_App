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

    # Optional: Profile Edit Section
    with st.expander("✏️ Update Profile Details"):
        with st.form(key="edit_profile_form"):
            new_name = st.text_input("Full Name", value=user_name)
            new_phone = st.text_input("Phone Number", value=user_phone)
            new_address = st.text_input("Assigned Sector / Address", value=user_address)

            submitted = st.form_submit_button("💾 Save Profile Changes")
            if submitted:
                # Update session state or user details dictionary
                if isinstance(user_details, dict):
                    user_details['username'] = new_name
                    user_details['phone'] = new_phone
                    user_details['address'] = new_address
                st.success("✅ Profile credentials updated successfully!")
                st.rerun()
