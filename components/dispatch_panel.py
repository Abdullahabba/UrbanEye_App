if st.button("💾 Submit & Log to Tracker", use_container_width=True, key="btn_save_ledger"):
            primary_hazard = list(st.session_state["counts"].keys())[0].title() if st.session_state["counts"] else "General Hazard"
            
            new_record = {
                "tracking_id": tracking_id,
                "hazard": primary_hazard,
                "issue_type": primary_hazard,  # Added to satisfy database NOT NULL constraint
                "severity": severity_label,
                "sla_target": sla_target,
                "status": "Pending",
                "assigned_dept": dept_email.split("@")[0].replace("_", " ").title(),
                "latitude": 31.5204,
                "longitude": 74.3587,
                "location_name": manual_loc_name,
                "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
            }

            # 1. Update Session State Ledger
            if "incident_ledger" in st.session_state:
                new_row_df = pd.DataFrame([new_record])
                st.session_state["incident_ledger"] = pd.concat([st.session_state["incident_ledger"], new_row_df], ignore_index=True)

            # 2. Save directly to Supabase Database
            try:
                from database.supabase_client import supabase
                if supabase:
                    res = supabase.table("reports").insert(new_record).execute()
                    st.success(f"✅ Incident submitted & synced to Supabase successfully! Tracking ID: **{tracking_id}**")
                else:
                    st.error("❌ Supabase client is None. Check configuration.")
            except Exception as e:
                st.error(f"❌ Supabase Insert Error: {e}")
