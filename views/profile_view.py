import streamlit as st
import pandas as pd

def normalize_records(raw_data):
    normalized = []
    for row in raw_data:
        if isinstance(row, dict):
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
            
            stat = (
                row.get('status') or 
                row.get('Status') or 
                'Dispatched'
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

def fetch_all_reports():
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

    # 2. Fallback / merge with local session state
    if "hazard_history" in st.session_state and st.session_state["hazard_history"]:
        raw_reports.extend(st.session_state["hazard_history"])
        
    if "incident_ledger" in st.session_state:
        ledger = st.session_state["incident_ledger"]
        if isinstance(ledger, pd.DataFrame) and not ledger.empty:
            raw_reports.extend(ledger.to_dict(orient="records"))
        elif isinstance(ledger, list) and ledger:
            raw_reports.extend(ledger)

    return normalize_records(raw_reports)

def render_profile_page(user_details: dict):
    st.title("👤 Officer Profile & Activity History")
    st.caption("Manage your professional credentials, contact info, and review your submitted hazard inspection reports.")

    # Top Section: Officer Credentials
    st.markdown("### 📋 Profile Credentials")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**👤 Full Name:** {user_details.get('username', 'Abdullah Abbasi')}")
        st.markdown(f"**📧 Official Email:** {user_details.get('email', 'officer@urbaneye.ai')}")
    with col2:
        st.markdown(f"**📞 Phone Number:** {user_details.get('phone', '+92 300 1234567')}")
        st.markdown(f"**📍 Assigned Sector / Address:** {user_details.get('address', 'Iqbal Sector, Block AA, Lahore')}")

    st.divider()

    # Bottom Section: Submitted Reports History (Synced with Tracker Source)
    st.markdown("### 📂 My Submitted Inspection Reports")
    
    all_reports = fetch_all_reports()
    
    # Deduplicate by Tracking ID
    unique_reports = {r["Tracking ID"]: r for r in all_reports}.values()

    if not unique_reports:
        st.info("📭 No inspection reports found in Supabase database or local session history yet.")
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
