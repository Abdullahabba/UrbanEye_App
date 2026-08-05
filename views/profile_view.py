import streamlit as st

def fetch_reports_from_supabase():
    try:
        from supabase import create_client
        
        # Supabase credentials from Streamlit secrets or environment
        supabase_url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
        supabase_key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")
        
        if not supabase_url or not supabase_key:
            return []
            
        supabase = create_client(supabase_url, supabase_key)
        
        # Querying the reports table (change 'reports' to your exact table name if different)
        response = supabase.table("reports").select("*").execute()
        return response.data if response and response.data else []
    except Exception as e:
        return []

def render_profile_page(user_details: dict):
    st.title("👤 Officer Profile & Activity History")
    st.caption("Manage your professional credentials, contact info, and review your submitted hazard inspection reports.")

    # Top Section: Officer Credentials
    st.markdown("### 📋 Profile Credentials")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**👤 Full Name:** {user_details.get('username', 'Officer Ahmed')}")
        st.markdown(f"**📧 Official Email:** {user_details.get('email', 'officer@urbaneye.ai')}")
    with col2:
        st.markdown(f"**📞 Phone Number:** {user_details.get('phone', '+92 300 1234567')}")
        st.markdown(f"**📍 Assigned Sector / Address:** {user_details.get('address', 'Iqbal Sector, Block AA, Lahore')}")

    st.divider()

    # Bottom Section: Submitted Reports History from Supabase
    st.markdown("### 📂 My Submitted Inspection Reports (Supabase)")
    
    # Fetching live data from Supabase
    db_history = fetch_reports_from_supabase()
    
    # Fallback to session state if Supabase returns nothing or credentials aren't set
    fallback_history = st.session_state.get("hazard_history", [])
    display_list = db_history if db_history else fallback_history

    if not display_list:
        st.info("No reports found in Supabase database or session history.")
    else:
        for item in display_list:
            rep_id = item.get('id') or item.get('tracking_id') or item.get('report_id') or "N/A"
            rep_date = item.get('created_at') or item.get('date') or item.get('timestamp') or "2026-08-06"
            rep_hazard = item.get('hazard') or item.get('hazard_type') or item.get('title') or "Municipal Hazard"
            rep_loc = item.get('location') or item.get('address') or "Lahore"
            rep_sev = item.get('severity') or item.get('score') or "Medium"
            rep_status = item.get('status', 'Dispatched')

            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**Tracking ID:** `{rep_id}`")
                    st.markdown(f"**Hazard Type:** {rep_hazard}")
                    st.markdown(f"**Location:** {rep_loc}")
                with c2:
                    st.markdown(f"**Date:** {str(rep_date)[:16]}")
                    st.markdown(f"**Severity:** {rep_sev}")
                    st.markdown(f"**Status:** :blue[{rep_status}]")
