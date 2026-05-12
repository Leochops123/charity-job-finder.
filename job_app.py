import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import json
import os
from typing import List, Dict

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder + Alerts")
st.success("✅ Working | Multi-Source Improved")

# ===================== SESSION STATE =====================
if "keywords" not in st.session_state:
    st.session_state.keywords = ["fundraising", "manager", "officer", "coordinator", "trustee", "safeguarding"]

if "custom_sources" not in st.session_state:
    st.session_state.custom_sources = [
        {"name": "CharityJob", "base": "https://www.charityjob.co.uk", "active": True},
        {"name": "Indeed", "base": "https://uk.indeed.com", "active": True},
        {"name": "Third Sector", "base": "https://jobs.thirdsector.co.uk", "active": True},
        {"name": "Guardian", "base": "https://jobs.theguardian.com", "active": False},
    ]

# Seen jobs (to avoid duplicates)
SEEN_FILE = "seen_jobs.json"
seen_jobs = set()
if os.path.exists(SEEN_FILE):
    try:
        with open(SEEN_FILE, "r") as f:
            seen_jobs = set(json.load(f))
    except:
        pass

def save_seen_jobs():
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_jobs), f)

# ===================== MULTI-SOURCE SCRAPER =====================
def scrape_jobs(source_name: str, keyword: str, location: str) -> List[Dict]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        if source_name == "CharityJob":
            url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(keyword)}&Sort=Date"
        elif source_name == "Indeed":
            url = f"https://uk.indeed.com/jobs?q={quote_plus(keyword)}+charity&l={quote_plus(location)}"
        elif source_name == "Third Sector":
            url = f"https://jobs.thirdsector.co.uk/jobs?keywords={quote_plus(keyword)}"
        elif source_name == "Guardian":
            url = f"https://jobs.theguardian.com/jobs/charities?keywords={quote_plus(keyword)}"
        else:
            url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(keyword)}"

        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        
        # === CharityJob ===
        if source_name == "CharityJob":
            for a in soup.select("a[href*='/jobs/']"):
                title = a.get_text(strip=True)
                if len(title) < 20 or any(x in title for x in ["Save", "Alert"]):
                    continue
                href = a["href"]
                full_link = "https://www.charityjob.co.uk" + href if href.startswith("/") else href
                if full_link not in seen_jobs:
                    jobs.append({"title": title, "link": full_link, "source": "CharityJob"})
        
        # === Indeed ===
        elif source_name == "Indeed":
            for a in soup.select("h2 a, a.jcs-JobTitle"):
                title = a.get_text(strip=True)
                if len(title) > 15:
                    href = a.get("href", "")
                    full_link = "https://uk.indeed.com" + href if href.startswith("/") else href
                    if full_link not in seen_jobs and "indeed.com" in full_link:
                        jobs.append({"title": title, "link": full_link, "source": "Indeed"})
        
        # === Third Sector ===
        elif source_name == "Third Sector":
            for a in soup.select("a[href*='/jobdetail/'], a[href*='/jobs/']"):
                title = a.get_text(strip=True)
                if len(title) > 20:
                    href = a["href"]
                    full_link = "https://jobs.thirdsector.co.uk" + href if href.startswith("/") else href
                    if full_link not in seen_jobs:
                        jobs.append({"title": title, "link": full_link, "source": "Third Sector"})
        
        return jobs[:25]
    except Exception as e:
        st.warning(f"[{source_name}] {str(e)[:80]}")
        return []

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("Settings")
    email = st.text_input("Your Email for Alerts", placeholder="you@example.com")
    enable_alerts = st.toggle("Enable Email Alerts", value=True)

    st.subheader("Keywords")
    new_kw = st.text_input("Add Keyword", placeholder="e.g. fundraiser", key="new_kw")
    if st.button("➕ Add Keyword") and new_kw.strip():
        kw = new_kw.strip().lower()
        if kw not in st.session_state.keywords:
            st.session_state.keywords.append(kw)
            st.success(f"Added: {kw}")
            st.rerun()

    for kw in st.session_state.keywords[:]:
        col1, col2 = st.columns([4,1])
        col1.write(f"• {kw}")
        if col2.button("🗑️", key=f"del_{kw}"):
            st.session_state.keywords.remove(kw)
            st.rerun()

    st.subheader("Job Sources")
    for source in st.session_state.custom_sources[:]:
        col1, col2 = st.columns([5,1])
        source["active"] = col1.checkbox(source["name"], value=source.get("active", True))
        if col2.button("🗑️", key=f"rm_{source['name']}"):
            st.session_state.custom_sources.remove(source)
            st.rerun()

    with st.form("add_source_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("Source Name", placeholder="Totaljobs")
        base_url = col2.text_input("Base URL", placeholder="https://www.totaljobs.com")
        if st.form_submit_button("➕ Add Source"):
            if name and base_url:
                st.session_state.custom_sources.append({"name": name.strip(), "base": base_url.strip(), "active": True})
                st.success(f"✅ {name} Added!")
                st.rerun()

# ===================== MAIN =====================
st.subheader("🔍 Search New Jobs")
col1, col2 = st.columns([3,1])
location = col1.text_input("Location", "West Yorkshire")

if st.button("🔍 Search All Sources Now", type="primary", use_container_width=True):
    with st.spinner("Searching CharityJob, Indeed, Third Sector..."):
        all_jobs = []
        active_sources = [s for s in st.session_state.custom_sources if s.get("active")]

        progress = st.progress(0)

        for i, source in enumerate(active_sources):
            st.info(f"Scanning **{source['name']}**...")
            for kw in st.session_state.keywords[:6]:
                jobs = scrape_jobs(source["name"], kw, location)
                all_jobs.extend(jobs)
            
            progress.progress((i + 1) / len(active_sources))
            time.sleep(1.3)

        save_seen_jobs()

        if all_jobs:
            st.success(f"🎉 Found **{len(all_jobs)}** new jobs across all sources!")
            for job in all_jobs[:50]:   # Increased limit
                with st.expander(f"**{job['title']}** — {job['source']}"):
                    st.markdown(f"[🔗 View Job]({job['link']})")
        else:
            st.warning("No new jobs found. Try different keywords or check back later.")

st.caption("Now searching multiple sources | Shows up to 50 jobs")
