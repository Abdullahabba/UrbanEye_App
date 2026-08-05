import streamlit as st
import pandas as pd

def normalize_records(raw_data, user_email):
    normalized = []
    inactive_statuses = ['resolved', 'closed', 'completed', 'archived', 'cancelled', 'done']

    for row in raw_data:
        if isinstance(row, dict):
            # 1. Check email match
            row_email = (
                row.get('email') or 
                row.get('sender_email') or 
                row.get('officer_email') or 
                row.get('user_email')
            )
            
            if row_email and user_email and str(row_email).strip().lower() != str(user_email).strip().lower():
                continue

            # 2. Check Status (Only Active)
            stat = (
                row.get('status') or 
                row.get('Status') or 
                'Dispatched'
            )
            
            # Agar report resolve ya close ho chuki hai, toh skip kar dein
            if str(stat).strip().lower() in inactive_statuses:
                continue

            t_id = (
                row.get('tracking_id') or 
                row.get('Tracking ID') or 
                row.get('id') or 
                row.get('report_id')
            )
            if not t_id:
                continue
            
            t_id_str = str(t_id)[:12] if len(str(t_id)) > 12 else str(t_id)

            hz = (
                row.get('hazard') or 
                row.get('Hazard') or 
                row.get('hazard_type') or 
                row.get('issue_type') or 
                'General Hazard'
            )
            
            sev = (
                row.get('severity') or 
                row.get('Severity') or 
                'Medium'
            )
            
            loc = (
                row.get('location_name') or 
                row.get('Location Name') or 
                row.get('location') or 
                row.get('address') or 
                'City Location'
            )
            
            ts = (
                row.get('timestamp') or 
                row.get('Timestamp') or 
                row.get('created_at') or 
                row.get('date') or 
                pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
            )
            
            normalized.append({
                "Tracking ID": t_id_str,
                "Hazard": str(hz),
                "Severity": str(sev),
                "Status": str(stat),
                "Location Name": str(loc),
                "Timestamp": str(ts)
            })
    return normalized

def fetch_user_reports(user_email):
    raw_reports = []
    
    # 1. Fetch from Supabase Cloud Database
    try:
        from database.supabase_client import supabase
        if supabase:
            response = supabase.table("reports").select("*").execute()
            if response.data:
                raw_reports.extend(response.data)
    except Exception:
        try:
            from supabase import create_client
            s_url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
            s_key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")
            if s_url and s_key:
                sb = create_client(s_url, s_key)
                res = sb.table("reports").select("*").execute()
                if res and res.data:
                    raw_reports.extend(res.data)
        except Exception:
            pass

    # 2. Merge with local session state if available
    if "hazard_history" in st.session_state and st.session_state["hazard_history"]:
        raw_reports.extend(st.session_state["hazard_history"])
        
    if "incident_ledger" in st.session_state:
        ledger = st.session_state["incident_ledger"]
        if isinstance(ledger, pd.DataFrame) and not ledger.empty:
            raw_reports.extend(ledger.to_dict(orient="records"))
        elif isinstance(ledger, list) and ledger:
            raw_reports.extend(ledger)

    return normalize_records(raw_reports, user_email)

def render_profile_page(user_details: dict):
    st.title("👤 Officer Profile & Activity History")
    st.caption("Manage your professional credentials, contact info, and review your active hazard inspection reports.")

    # Top Section: Officer Credentials
    user_email = user_details.get('email', 'officer@urbaneye.ai') if isinstance(user_details, dict) else 'officer@urbaneye.ai'
    user_name = user_details.get('username', 'Abdullah Abbasi') if isinstance(user_details, dict) else 'Abdullah Abbasi'
    user_phone = user_details.get('phone', '+92 300 1234567') if isinstance(user_details, dict) else '+92 300 1234567'
    user_address = user_details.get('address', 'Iqbal Sector, Block AA, Lahore') if isinstance(user_details, dict) else 'Iqbal Sector, Block AA, Lahore'

    st.markdown("### 📋 Profile Credentials")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**👤 Full Name:** {user_name}")
        st.markdown(f"**📧 Official Email:** {user_email}")
    with col2:
        st.markdown(f"**📞 Phone Number:** {user_phone}")
        st.markdown(f"**📍 Assigned Sector / Address:** {user_address}")

    st.divider()

    # Bottom Section: Active Submitted Reports Only
    st.markdown("### 📂 My Active Inspection Reports")
    
    user_reports = fetch_user_reports(user_email)
    
    # Deduplicate by Tracking ID
    unique_reports = {r["Tracking ID"]: r for r in user_reports}.values()

    if not unique_reports:
        st.info("📭 No active inspection reports found.")
    else:
        for item in unique_reports:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**Tracking ID:** `{item['Tracking ID']}`")
                    st.markdown(f"**Hazard Type:** {item['Hazard']}")
                    st.markdown(f"**Location:** {item['Location Name']}")
                with c2:
                    st.markdown(f"**Date:** {str(item['Timestamp'])[:16]}")
                    st.markdown(f"**Severity:** {item['Severity']}")
                    st.markdown(f"**Status:** :blue[{item['Status']}]")
