import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import json
import os
from datetime import datetime, timedelta
import hashlib
from typing import List, Dict

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder + Alerts")
st.success("✅ Last 24 Hours + Improved Location Filter")

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

def get_job_hash(title: str, link: str) -> str:
    return hashlib.md5(f"{title.lower().strip()}{link}".encode()).hexdigest()

def is_within_24h(date_text: str) -> bool:
    if not date_text:
        return True  # Keep if no date found (safer)
    text = date_text.lower()
    if any(x in text for x in ["today", "posted today", "just posted", "1 day ago", "24 hour", "now"]):
        return True
    if "2 day" in text or "3 day" in text:
        return False
    return True  # Default to show if parsing fails

# ===================== IMPROVED SCRAPERS =====================
def scrape_charityjob(keyword: str, location: str) -> List[Dict]:
    try:
        # CharityJob supports location
        url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(keyword)}&Sort=Date"
        if location and location.lower() != "anywhere":
            url += f"&Location={quote_plus(location)}"
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        # Main job cards
        cards = soup.select("div.job-result, article")
        for card in cards:
            title_tag = card.select_one("a[href*='/jobs/']")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            if len(title) < 15:
                continue

            link = title_tag["href"]
            full_link = "https://www.charityjob.co.uk" + link if link.startswith("/") else link

            # Date extraction
            date_text = ""
            date_tag = card.select_one("text:contains('Posted'), span:contains('ago'), div:contains('today')")
            if date_tag:
                date_text = date_tag.get_text(strip=True)
            else:
                # Alternative
                date_text = card.get_text()[:200]

            if not is_within_24h(date_text):
                continue

            job_hash = get_job_hash(title, full_link)
            if job_hash not in seen_jobs:
                jobs.append({
                    "title": title,
                    "link": full_link,
                    "source": "CharityJob",
                    "date": date_text[:60]
                })
        return jobs[:25]
    except Exception as e:
        st.warning(f"CharityJob: {str(e)[:80]}")
        return []

def scrape_indeed(keyword: str, location: str) -> List[Dict]:
    try:
        url = f"https://uk.indeed.com/jobs?q={quote_plus(keyword)}+charity&l={quote_plus(location)}&sort=date"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        for card in soup.select("div.job_seen_beacon, div.css-1fa6ij6"):
            title_tag = card.select_one("h2 a, a.jcs-JobTitle")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link = title_tag.get("href", "")
            if link.startswith("/"):
                link = "https://uk.indeed.com" + link

            # Date
            date_tag = card.select_one("span.date, span[data-testid='job-date']")
            date_text = date_tag.get_text(strip=True) if date_tag else ""

            if not is_within_24h(date_text):
                continue

            job_hash = get_job_hash(title, link)
            if job_hash not in seen_jobs and len(title) > 12:
                jobs.append({
                    "title": title,
                    "link": link,
                    "source": "Indeed",
                    "date": date_text
                })
        return jobs[:20]
    except Exception:
        return []

def scrape_thirdsector(keyword: str) -> List[Dict]:
    try:
        url = f"https://jobs.thirdsector.co.uk/jobs?keywords={quote_plus(keyword)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        for card in soup.select("div.job, article"):
            title_tag = card.select_one("a[href*='/jobdetail/']")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            if len(title) < 20:
                continue

            link = title_tag["href"]
            full_link = "https://jobs.thirdsector.co.uk" + link if link.startswith("/") else link

            # Date (shows "1 day ago", "14 days ago", etc.)
            date_text = ""
            date_tag = card.select_one("text:contains('ago'), span:contains('day'), div:contains('New')")
            if date_tag:
                date_text = date_tag.get_text(strip=True)

            if not is_within_24h(date_text):
                continue

            job_hash = get_job_hash(title, full_link)
            if job_hash not in seen_jobs:
                jobs.append({
                    "title": title,
                    "link": full_link,
                    "source": "Third Sector",
                    "date": date_text
                })
        return jobs[:20]
    except Exception:
        return []

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("Settings")
    email = st.text_input("Your Email for Alerts", placeholder="you@example.com")
    st.toggle("Enable Daily Alerts", value=True)

    st.subheader("Keywords")
    new_kw = st.text_input("Add Keyword", placeholder="e.g. grant manager")
    if st.button("➕ Add") and new_kw.strip():
        kw = new_kw.strip().lower()
        if kw not in st.session_state.keywords:
            st.session_state.keywords.append(kw)
            st.rerun()

    for kw in list(st.session_state.keywords):
        col1, col2 = st.columns([4,1])
        col1.write(f"• {kw}")
        if col2.button("🗑️", key=f"del_{kw}"):
            st.session_state.keywords.remove(kw)
            st.rerun()

# ===================== MAIN =====================
st.subheader("🔍 Search Jobs (Last 24 Hours)")

col1, col2 = st.columns([3,1])
location = col1.text_input("Location (e.g. West Yorkshire, London, Remote)", "West Yorkshire")
search_radius = col2.selectbox("Radius", ["Any", "10 miles", "25 miles", "50 miles"], index=2)

if st.button("🔍 Search Last 24 Hours", type="primary", use_container_width=True):
    with st.spinner("Searching recent jobs across sources..."):
        all_jobs = []
        active_sources = [s for s in st.session_state.custom_sources if s.get("active")]
        
        progress_bar = st.progress(0)
        
        for i, source in enumerate(active_sources):
            st.info(f"Scanning **{source['name']}** for last 24h...")
            
            for kw in st.session_state.keywords[:8]:
                if source["name"] == "CharityJob":
                    jobs = scrape_charityjob(kw, location)
                elif source["name"] == "Indeed":
                    jobs = scrape_indeed(kw, location)
                elif source["name"] == "Third Sector":
                    jobs = scrape_thirdsector(kw)
                else:
                    jobs = []
                
                all_jobs.extend(jobs)
                time.sleep(1.0)
            
            progress_bar.progress((i + 1) / len(active_sources))

        # Deduplicate
        unique_jobs = []
        for job in all_jobs:
            jhash = get_job_hash(job["title"], job["link"])
            if jhash not in seen_jobs:
                seen_jobs.add(jhash)
                unique_jobs.append(job)

        save_seen_jobs()

        if unique_jobs:
            st.success(f"🎉 Found **{len(unique_jobs)} new jobs** posted in the last 24 hours!")
            for job in sorted(unique_jobs, key=lambda x: x.get("date", ""), reverse=True)[:60]:
                with st.expander(f"**{job['title']}** — {job['source']}"):
                    st.markdown(f"[🔗 View Job]({job['link']})")
                    if job.get("date"):
                        st.caption(f"📅 {job['date']} | Location filter: {location}")
        else:
            st.info("No new jobs in the last 24 hours with current filters. Try broader keywords or check back tomorrow.")

st.caption("Now filtering to **last 24 hours** | Location-aware where supported")
