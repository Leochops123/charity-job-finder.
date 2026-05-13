# ===================== MAIN APP =====================
st.subheader("🔍 Search Jobs Posted in Last 24 Hours")

col1, col2 = st.columns([3, 1])
location = col1.text_input("Location", "West Yorkshire", key="location_input")

# ==================== SEARCH BUTTON ====================
if st.button("🔍 Search Last 24 Hours", type="primary", use_container_width=True):
    with st.spinner("Searching recent jobs across all sources..."):
        all_jobs = []
        active_sources = [s for s in st.session_state.custom_sources if s.get("active")]
        
        if not active_sources:
            st.error("Please enable at least one job source in the sidebar.")
        else:
            progress_bar = st.progress(0)
            total_steps = len(active_sources) * min(len(st.session_state.keywords), 8)
            step = 0

            for source in active_sources:
                st.info(f"🔎 Scanning **{source['name']}**...")
                source_jobs = []

                for kw in st.session_state.keywords[:8]:
                    try:
                        if source["name"] ==...
