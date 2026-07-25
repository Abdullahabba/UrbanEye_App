if st.button("💾 Submit & Log to Tracker", use_container_width=True, key="btn_save_ledger"):
            primary_hazard = list(st.session_state["counts"].keys())[0].title() if st.session_state["counts"] else "General Hazard"
            
            # Key names ab mock ledger (`helpers.py`) ke sath 100% match kar rahe hain
            new_record = {
                "Tracking ID": tracking_id,
                "Hazard": primary_hazard,
                "Severity": severity_label,
                "SLA Target": sla_target,
                "Status": "Pending",
                "Assigned Dept": dept_email.split("@")[0].replace("_", " ").title(),
                "Latitude": 31.5204,
                "Longitude": 74.3587,
                "Location Name": manual_loc_name,
                "Timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
            }

            # 1. Save to Session State Ledger
            new_row_df = pd.DataFrame([new_record])
            st.session_state["incident_ledger"] = pd.concat([st.session_state["incident_ledger"], new_row_df], ignore_index=True)

            # 2. Save to Supabase (Optional backup)
            try:
                from utils.supabase_client import init_supabase
                supabase = init_supabase()
                if supabase:
                    supabase.table("reports").insert(new_record).execute()
            except Exception:
                pass

            st.success(f"✅ Incident submitted successfully! Tracking ID: **{tracking_id}**")
