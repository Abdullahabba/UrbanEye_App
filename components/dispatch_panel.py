if st.button("💾 Submit & Log to Tracker", use_container_width=True, key="btn_save_ledger"):
            primary_hazard = list(st.session_state["counts"].keys())[0].title() if st.session_state["counts"] else "General Hazard"
            
            new_record = {
                "tracking_id": tracking_id,
                "hazard": primary_hazard,
                "severity": severity_label,
                "sla_target": sla_target,
                "status": "Pending",
                "assigned_dept": dept_email.split("@")[0].replace("_", " ").title(),
                "latitude": 31.5204,
                "longitude": 74.3587,
                "location_name": manual_loc_name,
                "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
            }

            # 1. Save to Session State Ledger
            new_row_df = pd.DataFrame([new_record])
            st.session_state["incident_ledger"] = pd.concat([st.session_state["incident_ledger"], new_row_df], ignore_index=True)

            # 2. Save to Supabase Database (Taake Map par show ho)
            try:
                from utils.supabase_client import init_supabase # ya jese aapka supabase client import hota hai
                supabase = init_supabase() # ya st.secrets se connection
                if supabase:
                    supabase.table("reports").insert(new_record).execute()
            except Exception as e:
                # Agar Supabase table na bani ho ya offline ho toh local session chalta rahega
                pass

            st.success(f"✅ Incident submitted successfully! Tracking ID: **{tracking_id}**")
