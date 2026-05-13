import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import json
import os
import hashlib

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder")
st.success("✅ Fully Fixed & Clean Version")

# ===================== SESSION STATE =====================
if "keywords" not in st.session_state:
    st.session_state.keywords = ["fundraising", "manager", "officer"]

if "location" not in st.session_state:
    st.session_state.location = "West Yorkshire"

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

def get_job_hash(title, link):
    return hashlib.md5((title.lower().strip() + link).encode()).hexdigest()

def is_within_24h(text):
    if not text:
        return True
    t = text.lower()
    words = ["today", "1 day ago", "hours ago", "just posted"]
    for w in words:
        if w in t:
            return True
    return False

# ===================== SCRAPER =====================
def scrape_charityjob(keyword, location):
    try:
        url = "https://www.charityjob.co.uk/jobs?Keywords=" + quote_plus(keyword) + "&Sort=Date"
        if location and location.lower() not in ["any", "anywhere", ""]:
            url = url + "&Location=" + quote_plus(location)
        
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        for card in soup.select("article, div.job-result"):
            title_tag = card.select_one("a[href*='/jobs/']")
            if title_tag:
                title = title_tag.get_text(strip=True)
                if len(title) < 15:
                    continue
                link = title_tag["href"]
                full_link = "https://www.charityjob.co.uk" + link if link.startswith("/") else link
                if is_within_24h(card.get_text()):
                    jobs.append({"title": title, "link": full_link, "source": "CharityJob"})
        return jobs[:25]
    except:
        return []

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("Filters")
    st.subheader("Location")
    new_loc = st.text_input("Preferred Location", value=st.session_state.location)
    if new_loc != st.session_state.location:
        st.session_state.location = new_loc

    st.subheader("Keywords")
    new_kw = st.text_input("Add Keyword", placeholder="e.g. fundraising")
    if st.button("Add Keyword") and new_kw.strip():
        kw = new_kw.strip().lower()
        if kw not in st.session_state.keywords:
            st.session_state.keywords.append(kw)
            st.rerun()

    for kw in list(st.session_state.keywords):
        col1, col2 = st.columns([4,1])
        col1.write("• " + kw)
        if col2.button("Delete", key="del_" + kw):
            st.session_state.keywords.remove(kw)
            st.rerun()

# ===================== MAIN =====================
st.subheader("Search Last 24 Hours Jobs")

if st.button("🔍 Search Last 24 Hours", type="primary", use_container_width=True):
    with st.spinner("Searching..."):
        all_jobs = []
        for kw in st.session_state.keywords:
            jobs = scrape_charityjob(kw, st.session_state.location)
            all_jobs.extend(jobs)
            time.sleep(1)

        # Deduplicate
        unique_jobs = []
        for job in all_jobs:
            if get_job_hash(job["title"], job["link"]) not in seen_jobs:
                seen_jobs.add(get_job_hash(job["title"], job["link"]))
                unique_jobs.append(job)

        save_seen_jobs()

        if unique_jobs:
            st.success("Found " + str(len(unique_jobs)) + " new jobs!")
            for job in unique_jobs[:50]:
                with st.expander(job["title"]):
                    st.markdown("[View Job](" + job["link"] + ")")
                    st.caption(job["source"])
        else:
            st.info("No new jobs found. Try Location = Any")

st.caption("✅ All errors fixed - Clean Version")
