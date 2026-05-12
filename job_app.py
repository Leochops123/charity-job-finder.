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
st.success("✅ Final Working Version")

# ===================== SESSION STATE =====================
if "keywords" not in st.session_state:
    st.session_state.keywords = ["fundraising", "manager", "officer", "coordinator", "trustee"]

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

# ===================== SCRAPER =====================
def scrape_jobs(source_name: str, keyword: str, location: str) -> List[Dict]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        if source_name == "CharityJob":
            url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(keyword)}"
        elif source_name == "Indeed":
            url = f"https://uk.indeed.com/jobs?q={quote_plus(keyword)}+charity&l={quote_plus(location)}"
        elif source_name == "Third Sector":
            url = f"https://jobs.thirdsector.co.uk/jobs?keywords={quote_plus(keyword)}"
        else:
            url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(keyword)}"

        resp = requests.get(url, headers=headers, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        
        # CharityJob
        if source_name == "CharityJob":
            for a in soup.find_all("a", href=True):
                title = a.get_text(strip=True)
                if len(title) > 20 and "/jobs/" in a["href"]:
                    full_link = "https://www.charityjob.co.uk" + a["href"] if a["href"].startswith("/") else a["href"]
                    if full_link not in seen_jobs:
                        jobs.append({"title": title, "link": full_link, "source": "CharityJob"})
        
        # Indeed
        elif source_name == "Indeed":
            for a in soup.select("h2 a, a.jcs-JobTitle"):
                title = a.get_text(strip=True)
                if len(title) > 15:
                    href = a.get("href", "")
                    full_link = "https://uk.indeed.com" + href if href.startswith("/") else href
                    if full_link not in seen_jobs:
                        jobs.append({"title": title, "link": full_link, "source": "Indeed"})
        
        return jobs[:15]
    except Exception as e:
        st.warning(f"[{source_name}] {str(e)[:100]}")
        return []

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("Settings")
    email = st.text_input("Your Email", placeholder="you@example.com")
    enable_alerts = st.toggle("Enable Email Alerts", value=True)

    st.subheader("Keywords")
    new_kw = st.text_input("Add Keyword", placeholder="e.g. fundraiser", key="kw_input")
    if st.button("➕ Add Keyword") and new_kw.strip():
        kw = new_kw.strip().lower()
        if kw not in st.session_state.keywords:
            st.session_state.keywords.append(kw)
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

    with st.form("add_source"):
        name = st.text_input("Source Name", placeholder="Indeed")
        url = st.text_input("Base URL", placeholder="https://uk.indeed.com")
        if st.form_submit_button("➕ Add Source") and name and url:
            st.session_state.custom_sources.append({"name": name.strip(), "base": url.strip(), "active": True})
            st.rerun()

# ===================== MAIN =====================
st.subheader("🔍 Search Jobs")
col1, col2 = st.columns([3,1])
location = col1.text_input("Location", "West Yorkshire")
max_results = col2.slider("Max results", 5, 80, 20)

if st.button("🔍 Search Now", type="primary", use_container_width=True):
    with st.spinner("Scanning CharityJob, Indeed & others..."):
        all_jobs = []
        active_sources = [s for s in st.session_state.custom_sources if s.get("active")]

        for source in active_sources:
            st.info(f"🔎 Scanning **{source['name']}**...")
            for kw in st.session_state.keywords[:5]:
                jobs = scrape_jobs(source["name"], kw, location)
                all_jobs.extend(jobs)
            time.sleep(1)

        save_seen_jobs()

        if all_jobs:
            st.success(f"🎉 Found **{len(all_jobs)}** jobs!")
            for job in all_jobs[:max_results]:
                with st.expander(f"**{job['title']}** — {job['source']}"):
                    st.markdown(f"[🔗 View Job]({job['link']})")
        else:
            st.error("No jobs found. Please try again or add more keywords.")

st.caption("This is the best generic version possible. Some sites block scraping.")
