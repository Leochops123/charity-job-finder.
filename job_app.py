import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
from datetime import date
import json
import os
from typing import List, Dict

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder + Alerts")
st.success("✅ Scraper Improved - May 2026 Version")

# ===================== SESSION STATE =====================
if "keywords" not in st.session_state:
    st.session_state.keywords = ["charity", "fundraising", "nonprofit", "trustee", "third sector", "safeguarding"]

if "custom_sources" not in st.session_state:
    st.session_state.custom_sources = [
        {"name": "CharityJob", "base": "https://www.charityjob.co.uk", "active": True},
        {"name": "Third Sector Jobs", "base": "https://jp.thirdsector.co.uk", "active": True},
        {"name": "Goodmoves", "base": "https://goodmoves.org", "active": True},
        {"name": "Guardian Charities", "base": "https://jobs.theguardian.com/jobs/charities", "active": True},
        {"name": "Reed", "base": "https://www.reed.co.uk", "active": True},
    ]

# Seen jobs persistence
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
def scrape_jobs(url: str, source_name: str) -> List[Dict]:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        
        # Stronger selectors for CharityJob
        if "charityjob" in url.lower():
            # Main job links
            for link in soup.select("a[href*='/jobs/']"):
                title = link.get_text(strip=True)
                if len(title) < 10 or "View profile" in title:
                    continue
                
                full_link = link["href"]
                if not full_link.startswith("http"):
                    full_link = "https://www.charityjob.co.uk" + full_link if full_link.startswith("/") else full_link
                
                if full_link not in seen_jobs:
                    jobs.append({
                        "title": title,
                        "company": "Unknown",
                        "link": full_link,
                        "source": source_name
                    })
        
        else:
            # Generic fallback for other sites
            for link in soup.select("a"):
                title = link.get_text(strip=True)
                if len(title) > 15 and any(word in title.lower() for word in 
                    ["manager", "officer", "director", "coordinator", "fundraiser", "lead", "head"]):
                    href = link.get("href", "")
                    if href and ("job" in href.lower() or "/jobs/" in href or "/jobdetail" in href):
                        full_link = href
                        if not full_link.startswith("http"):
                            domain = "/".join(url.split("/")[:3])
                            full_link = domain + full_link if full_link.startswith("/") else domain + "/" + full_link
                        
                        if full_link not in seen_jobs:
                            jobs.append({
                                "title": title[:150],
                                "company": "Unknown",
                                "link": full_link,
                                "source": source_name
                            })
        return jobs[:30]
    except Exception as e:
        st.warning(f"Error scraping {source_name}: {str(e)[:80]}")
        return []

# ===================== SIDEBAR (same as before) =====================
with st.sidebar:
    st.header("🛠️ Settings")
    email = st.text_input("Your Email for Alerts", placeholder="you@example.com")
    enable_alerts = st.toggle("Enable Daily Email Alerts", value=True)

    st.subheader("Keywords")
    new_kw = st.text_input("Add Keyword", placeholder="e.g. policy officer", key="new_kw")
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

    with st.form("add_source"):
        name = st.text_input("Source Name")
        url = st.text_input("Base/Search URL")
        if st.form_submit_button("Add Source") and name and url:
            st.session_state.custom_sources.append({"name": name, "base": url, "active": True})
            st.rerun()

# ===================== MAIN =====================
st.subheader("🔍 Search Jobs")
col1, col2 = st.columns([3,1])
location = col1.text_input("Location", "West Yorkshire")
max_results = col2.slider("Max results", 10, 80, 25)

if st.button("🔍 Search Now", type="primary", use_container_width=True):
    with st.spinner("Scanning major charity job boards..."):
        all_new_jobs = []
        active_sources = [s for s in st.session_state.custom_sources if s.get("active")]

        progress = st.progress(0)

        for i, source in enumerate(active_sources):
            st.info(f"Scanning **{source['name']}**...")
            
            for kw in st.session_state.keywords[:5]:   # limit keywords per run
                if "charityjob" in source["base"].lower():
                    search_url = f"https://www.charityjob.co.uk/jobs/{quote_plus(kw)}/{quote_plus(location)}?sort=Date"
                elif "thirdsector" in source["base"].lower():
                    search_url = f"https://jp.thirdsector.co.uk/jobs?keywords={quote_plus(kw)}"
                else:
                    search_url = source["base"]
                
                jobs = scrape_jobs(search_url, source["name"])
                all_new_jobs.extend(jobs)
            
            progress.progress((i + 1) / len(active_sources))
            time.sleep(1.2)

        save_seen_jobs()

        if all_new_jobs:
            st.success(f"🎉 Found **{len(all_new_jobs)} new jobs**!")
            for job in all_new_jobs[:max_results]:
                with st.expander(f"**{job['title']}** — {job['source']}"):
                    st.markdown(f"[🔗 View Job]({job['link']})")
        else:
            st.warning("Still no jobs found. Try different keywords or check internet connection.")

st.caption("Improved scraper for CharityJob (May 2026). Daily automation still uses scanner.py")
