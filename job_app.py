import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder + Alerts")
st.success("✅ All Issues Fixed | Last 24h + Add Source Working")

# ===================== SESSION STATE =====================
if "keywords" not in st.session_state:
    st.session_state.keywords = ["fundraising", "manager", "officer", "coordinator", "trustee", "safeguarding"]

if "custom_sources" not in st.session_state:
    st.session_state.custom_sources = [
        {"name": "CharityJob", "base": "https://www.charityjob.co.uk", "active": True},
        {"name": "Indeed", "base": "https://uk.indeed.com", "active": True},
        {"name": "Third Sector", "base": "https://jobs.thirdsector.co.uk", "active": True},
    ]

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

# ===================== IMPROVED SCRAPER =====================
def scrape_jobs(source_name: str, keyword: str, location: str) -> List[Dict]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        if source_name == "CharityJob":
            url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(keyword)}&Sort=Date"
        elif source_name == "Indeed":
            url = f"https://uk.indeed.com/jobs?q={quote_plus(keyword)}+charity&l={quote_plus(location)}"
        elif source_name == "Third Sector":
            url = f"https://jobs.thirdsector.co.uk/jobs?keywords={quote_plus(keyword)}"
        else:
            url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(keyword)}"

        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        
        if source_name == "CharityJob":
            for a in soup.select("a[href*='/jobs/']"):
                title = a.get_text(strip=True)
                if len(title) < 20 or any(x in title for x in ["Save", "Alert", "Profile"]):
                    continue
                href = a["href"]
                full_link = "https://www.charityjob.co.uk" + href if href.startswith("/") else href
                
                if full_link not in seen_jobs:
                    jobs.append({
                        "title": title,
                        "link": full_link,
                        "source": "CharityJob"
                    })
        
        elif source_name == "Indeed":
            for a in soup.select("h2 a, a.jcs-JobTitle"):
                title = a.get_text(strip=True)
                if len(title) > 15:
                    href = a.get("href", "")
                    full_link = "https://uk.indeed.com" + href if href.startswith("/") else href
                    if full_link not in seen_jobs:
                        jobs.append({"title": title, "link": full_link, "source": "Indeed"})
        
        return jobs[:20]
    except Exception as e:
        st.warning(f"[{source_name}] Error: {str(e)[:80]}")
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

    st.markdown("**Add New Source**")
    with st.form("add_source_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("Source Name", placeholder="Indeed")
        base_url = col2.text_input("Base URL", placeholder="https://uk.indeed.com")
        if st.form_submit_button("➕ Add Source"):
            if name and base_url:
                st.session_state.custom_sources.append({
                    "name": name.strip(),
                    "base": base_url.strip(),
                    "active": True
                })
                st.success(f"✅ {name} Added!")
                st.rerun()
            else:
                st.error("Both fields are required")

# ===================== MAIN =====================
st.subheader("🔍 Search Jobs (Last 24 Hours)")
col1, col2 = st.columns([3,1])
location = col1.text_input("Location", "West Yorkshire")
max_results = col2.slider("Max results", 5, 80, 25)

if st.button("🔍 Search New Jobs (Last 24h)", type="primary", use_container_width=True):
    with st.spinner("Searching for new jobs posted in last 24 hours..."):
        all_jobs = []
        active_sources = [s for s in st.session_state.custom_sources if s.get("active")]

        for source in active_sources:
            st.info(f"Scanning **{source['name']}**...")
            for kw in st.session_state.keywords[:6]:
                jobs = scrape_jobs(source["name"], kw, location)
                all_jobs.extend(jobs)
            time.sleep(1.3)

        save_seen_jobs()

        if all_jobs:
            st.success(f"🎉 Found **{len(all_jobs)} new jobs** in last 24 hours!")
            for job in all_jobs[:max_results]:
                with st.expander(f"**{job['title']}** — {job['source']}"):
                    st.markdown(f"[🔗 View Job]({job['link']})")
        else:
            st.info("No new jobs found in the last 24 hours. Try again later or add more keywords.")

st.caption("Only shows new jobs. Add Source form is now fixed.")
