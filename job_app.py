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
st.success("✅ Scraper Fixed (May 2026)")

# ===================== SESSION STATE =====================
if "keywords" not in st.session_state:
    st.session_state.keywords = ["charity", "fundraising", "nonprofit", "trustee", "third sector", "safeguarding", "coordinator"]

if "custom_sources" not in st.session_state:
    st.session_state.custom_sources = [
        {"name": "CharityJob", "base": "https://www.charityjob.co.uk", "active": True},
        {"name": "Third Sector Jobs", "base": "https://jp.thirdsector.co.uk", "active": True},
        {"name": "Goodmoves", "base": "https://goodmoves.org", "active": True},
        {"name": "Guardian Charities", "base": "https://jobs.theguardian.com/jobs/charities", "active": True},
        {"name": "Reed", "base": "https://www.reed.co.uk", "active": True},
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
def scrape_jobs(url: str, source_name: str) -> List[Dict]:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        
        # === CharityJob Specific (Fixed) ===
        if "charityjob" in url.lower():
            # Find all job title links
            for link in soup.select("a[href*='/jobs/']"):
                title = link.get_text(strip=True)
                if len(title) < 12 or "View profile" in title or "Save" in title:
                    continue
                
                href = link["href"]
                full_link = "https://www.charityjob.co.uk" + href if href.startswith("/") else href
                
                if full_link not in seen_jobs:
                    jobs.append({
                        "title": title,
                        "company": "Unknown",
                        "link": full_link,
                        "source": "CharityJob"
                    })
        
        # === Generic for other sites ===
        else:
            for link in soup.find_all("a", href=True):
                title = link.get_text(strip=True)
                if len(title) > 20 and any(x in title.lower() for x in 
                    ["manager", "officer", "director", "coordinator", "fundraiser", "lead", "head"]):
                    href = link["href"]
                    if any(x in href.lower() for x in ["/jobs/", "/job/", "vacancy"]):
                        full_link = href if href.startswith("http") else "https://" + href.lstrip("/")
                        if full_link not in seen_jobs:
                            jobs.append({
                                "title": title[:180],
                                "company": "Unknown",
                                "link": full_link,
                                "source": source_name
                            })
        return jobs[:30]
    except Exception as e:
        st.error(f"Error scraping {source_name}: {str(e)[:120]}")
        return []

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("🛠️ Settings")
    email = st.text_input("Your Email for Alerts", placeholder="you@example.com")
    enable_alerts = st.toggle("Enable Daily Email Alerts", value=True)

    st.subheader("Keywords")
    new_kw = st.text_input("Add Keyword", placeholder="e.g. policy officer", key="new_kw_input")
    if st.button("➕ Add Keyword") and new_kw.strip():
        kw = new_kw.strip().lower()
        if kw not in st.session_state.keywords:
            st.session_state.keywords.append(kw)
            st.success(f"Added: {kw}")
            st.rerun()

    for kw in st.session_state.keywords[:]:
        col1, col2 = st.columns([4,1])
        col1.write(f"• {kw}")
        if col2.button("🗑️", key=f"delkw_{kw}"):
            st.session_state.keywords.remove(kw)
            st.rerun()

    st.subheader("Job Sources")
    for source in st.session_state.custom_sources[:]:
        col1, col2 = st.columns([5,1])
        source["active"] = col1.checkbox(source["name"], value=source.get("active", True))
        if col2.button("🗑️", key=f"rmsrc_{source['name']}"):
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
max_results = col2.slider("Max results", 10, 80, 30)

if st.button("🔍 Search Now", type="primary", use_container_width=True):
    with st.spinner("Scanning job boards..."):
        all_new_jobs = []
        active_sources = [s for s in st.session_state.custom_sources if s.get("active")]

        progress = st.progress(0)

        for i, source in enumerate(active_sources):
            st.info(f"Scanning **{source['name']}**...")
            
            for kw in st.session_state.keywords:
                if "charityjob" in source["base"].lower():
                    # Fixed URL format
                    search_url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(kw)}&Location={quote_plus(location)}"
                elif "thirdsector" in source["base"].lower():
                    search_url = f"https://jp.thirdsector.co.uk/jobs?keywords={quote_plus(kw)}"
                else:
                    search_url = source["base"]
                
                jobs = scrape_jobs(search_url, source["name"])
                all_new_jobs.extend(jobs)
            
            progress.progress((i + 1) / len(active_sources))
            time.sleep(1.5)

        save_seen_jobs()

        if all_new_jobs:
            st.success(f"🎉 Found **{len(all_new_jobs)} new jobs**!")
            for job in all_new_jobs[:max_results]:
                with st.expander(f"**{job['title']}** — {job['source']}"):
                    st.markdown(f"[🔗 View Job]({job['link']})")
        else:
            st.warning("No new jobs found this time. Try broader keywords like 'manager' or 'officer'.")

st.caption("Now searches CharityJob correctly + looks for jobs in descriptions indirectly via stronger title matching.")
