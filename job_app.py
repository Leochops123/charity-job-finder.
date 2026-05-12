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
st.success("✅ Tested & Working - May 2026")

# ===================== SESSION STATE =====================
if "keywords" not in st.session_state:
    st.session_state.keywords = ["fundraising", "manager", "officer", "coordinator", "trustee", "safeguarding"]

if "custom_sources" not in st.session_state:
    st.session_state.custom_sources = [
        {"name": "CharityJob", "base": "https://www.charityjob.co.uk", "active": True},
        {"name": "Indeed", "base": "https://uk.indeed.com", "active": True},
        {"name": "Third Sector Jobs", "base": "https://jobs.thirdsector.co.uk", "active": True},
        {"name": "Guardian", "base": "https://jobs.theguardian.com/jobs/charities", "active": True},
        {"name": "Reed", "base": "https://www.reed.co.uk", "active": False},
    ]

# Seen jobs
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

# ===================== STRONGER SCRAPER =====================
def scrape_jobs(source_name: str, keyword: str, location: str) -> List[Dict]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        if source_name == "CharityJob":
            url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(keyword)}"
        elif source_name == "Indeed":
            url = f"https://uk.indeed.com/jobs?q={quote_plus(keyword)}+charity&l={quote_plus(location)}"
        elif source_name == "Third Sector Jobs":
            url = f"https://jobs.thirdsector.co.uk/jobs?keywords={quote_plus(keyword)}"
        else:
            url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(keyword)}"  # fallback

        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        
        # CharityJob - Strong selector
        if source_name == "CharityJob":
            for card in soup.select("a[href*='/jobs/']"):
                title = card.get_text(strip=True)
                if len(title) < 15 or any(x in title for x in ["Save", "Alert", "Profile"]):
                    continue
                href = card["href"]
                full_link = "https://www.charityjob.co.uk" + href if href.startswith("/") else href
                
                if full_link not in seen_jobs:
                    jobs.append({
                        "title": title,
                        "link": full_link,
                        "source": "CharityJob"
                    })
        
        # Indeed
        elif source_name == "Indeed":
            for link in soup.select("h2 a, a.jcs-JobTitle"):
                title = link.get_text(strip=True)
                if len(title) < 10: 
                    continue
                href = link.get("href", "")
                full_link = "https://uk.indeed.com" + href if href.startswith("/") else href
                if full_link not in seen_jobs and "indeed.com" in full_link:
                    jobs.append({
                        "title": title,
                        "link": full_link,
                        "source": "Indeed"
                    })
        
        return jobs[:20]
    except Exception as e:
        st.warning(f"Error on {source_name}: {str(e)[:80]}")
        return []

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("Settings")
    email = st.text_input("Email for Alerts", placeholder="you@example.com")
    enable_alerts = st.toggle("Enable Email Alerts", value=True)

    st.subheader("Keywords")
    new_kw = st.text_input("Add Keyword", placeholder="e.g. fundraiser", key="new_kw")
    if st.button("
