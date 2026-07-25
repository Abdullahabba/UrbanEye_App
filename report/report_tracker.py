import streamlit as st
import pandas as pd

def render_report_tracker():
    st.header("🔍 Citizen & Municipal Report Tracker")
    st.caption("Track real-time resolution progress, SLA timelines, and hazard complaint history.")

    # Check if ledger exists in session state
    if "incident_ledger" not in st.session_state or st.session_state["incident_ledger"].empty:
        st.info("ℹ️ Abhi tak koi report log nahi hui. Main Detection tab se new report log karein.")
        return

    df = st.session_state["incident_ledger"]

    # --- TOP METRIC SUMMARY CARDS ---
    m1, m2, m3, m4 = st.columns(4)
    total_cnt = len(df)
    open_cnt = len(df[df["Status"] == "Open"]) if "Status" in df.columns else 0
    in_prog_cnt = len(df[df["Status"] == "In Progress"]) if "Status" in df.columns else 0
    resolved_cnt = len(df[df["Status"] == "Resolved"]) if "Status" in df.columns else 0

    m1.metric("Total Complaints", total_cnt)
    m2.metric("🔴 Open", open_cnt)
    m3.metric("🟡 In Progress", in_prog_cnt)
    m4.metric("🟢 Resolved", resolved_cnt)

    st.divider()

    # --- SEARCH & FILTER BAR ---
    col1, col2 = st.columns([2, 1])
    with col1:
        search_query = st.text_input("🔎 Search by Report ID or Hazard Type:", placeholder="e.g. INC-101 or Pothole")
    with col2:
        status_options = ["All"] + list(df["Status"].unique()) if "Status" in df.columns else ["All"]
        selected_status = st.selectbox("Filter by Status:", status_options)

    # Filtering Logic
    filtered_df = df.copy()
    if selected_status != "All" and "Status" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Status"] == selected_status]

    if search_query:
        id_match = filtered_df["ID"].astype(str).str.contains(search_query, case=False, na=False) if "ID" in filtered_df.columns else False
        hazard_match = filtered_df["Hazard"].astype(str).str.contains(search_query, case=False, na=False) if "Hazard" in filtered_df.columns else False
        filtered_df = filtered_df[id_match | hazard_match]

    if filtered_df.empty:
        st.warning("Koi matching report nahi mili.")
        return

    # --- INDIVIDUAL TRACKER VIEW ---
    st.subheader("📌 Detailed Incident Progress")
    
    report_ids = filtered_df["ID"].tolist() if "ID" in filtered_df.columns else filtered_df.index.tolist()
    selected_id = st.selectbox("Select Incident ID to track:", report_ids)

    # Get selected row
    report = filtered_df[filtered_df["ID"] == selected_id].iloc[0] if "ID" in filtered_df.columns else filtered_df.loc[selected_id]

    # Progress bar mapping
    status_progress = {
        "Open": (25, "🔴 Report Logged & Dispatched"),
        "In Progress": (65, "🟡 Maintenance Team On-Site"),
        "Resolved": (100, "🟢 Issue Fixed & Verified")
    }
    
    curr_status = report.get("Status", "Open")
    prog_val, prog_text = status_progress.get(curr_status, (10, "Processing"))

    st.markdown(f"### Report ID: `{selected_id}`")
    st.progress(prog_val, text=f"**Current Stage:** {prog_text}")

    # Detailed Info Grid
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"**📍 Location:** {report.get('Location', 'Sector A, LDA City')}")
        st.markdown(f"**⚠️ Hazard Type:** {report.get('Hazard', 'N/A')}")
        st.markdown(f"**📊 Count/Size:** {report.get('Count', 1)}")

    with c2:
        st.markdown(f"**🚨 Severity:** {report.get('Severity', 'MEDIUM')}")
        st.markdown(f"**⏱️ SLA Target:** {report.get('SLA_Hours', 24)} Hours")
        st.markdown(f"**📅 Date Logged:** {report.get('Timestamp', 'N/A')}")

    with c3:
        st.markdown(f"**🏢 Department:** {report.get('Department', 'Municipal Operations')}")
        st.markdown(f"**👤 Reported By:** Citizen AI System")

    # Expandable Master Ledger View
    with st.expander("📋 View Complete Tracked Reports Table"):
        st.dataframe(filtered_df, use_container_width=True)
