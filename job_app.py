if st.button("🔍 Search Last 24 Hours", type="primary", use_container_width=True):
    with st.spinner("Searching recent jobs across all sources..."):
        all_jobs = []
        active_sources = [s for s in st.session_state.custom_sources if s.get("active")]
        
        if not active_sources:
            st.error("Please enable at least one job source in the sidebar.")
        else:
            progress_bar = st.progress(0)
            total_steps = len(active_sources) * len(st.session_state.keywords[:8])
            step = 0

            for source in active_sources:
                st.info(f"🔎 Scanning **{source['name']}**...")
                source_jobs = []

                for kw in st.session_state.keywords[:8]:
                    try:
                        if source["name"] == "CharityJob":
                            jobs = scrape_charityjob(kw, location)
                        elif source["name"] == "Indeed":
                            jobs = scrape_indeed(kw, location)
                        elif source["name"] == "Third Sector":
                            jobs = scrape_thirdsector(kw)
                        else:
                            # For all custom sources - show that it's not supported yet
                            st.warning(f"⚠️ Scraping not implemented for **{source['name']}** yet.")
                            jobs = []
                        
                        source_jobs.extend(jobs)
                    except Exception as e:
                        st.error(f"Error with {source['name']}: {str(e)}")
                    
                    step += 1
                    progress_bar.progress(min(step / total_steps, 1.0))
                    time.sleep(0.9)

                all_jobs.extend(source_jobs)

            # Remove duplicates
            unique_jobs = []
            seen_this_run = set()
            for job in all_jobs:
                jhash = get_job_hash(job["title"], job["link"])
                if jhash not in seen_jobs and jhash not in seen_this_run:
                    seen_jobs.add(jhash)
                    seen_this_run.add(jhash)
                    unique_jobs.append(job)

            save_seen_jobs()

            if unique_jobs:
                st.success(f"🎉 Found **{len(unique_jobs)}** new jobs in last 24 hours!")
                # Group by source for easier reading
                for source_name in sorted(set(j["source"] for j in unique_jobs)):
                    source_jobs = [j for j in unique_jobs if j["source"] == source_name]
                    st.subheader(f"{source_name} ({len(source_jobs)})")
                    for job in source_jobs[:15]:
                        with st.expander(f"**{job['title']}**"):
                            st.markdown(f"[🔗 Open Job]({job['link']})")
            else:
                st.info("No new jobs found in the last 24 hours. Try broader keywords or more sources.")
