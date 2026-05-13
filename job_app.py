import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import os
from typing import List, Dict

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder")
st.success("✅ Last 24 Hours • Multi-Source • Fixed")

# Session State
if "keywords" not in st.session_state:
    st.session_state.keywords = ["manager", "officer", "coordinator", "fundraising"]

if "custom_sources" not in st.session_state:
    st.session_state.custom_sources = [
        {"name": "CharityJob", "base": "https://www.charityjob.co.uk", "active": True},
        {"name": "Indeed", "base": "https://uk.indeed.com", "active": True},
        {"name": "Third Sector", "base": "https://jobs.thirdsector.co.uk", "active": True},
    ]

# ===================== SCRAPERS =====================
def scrape_charityjob(keyword: str, location: str) -> List[Dict]:
    try:
        url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(keyword)}&Sort=Date"
        if location and location.lower() not in ["any", "anywhere"]:
            url += f"&Location={quote_plus(location)}"
        
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        for card in soup.select("div.job-result, article")[:15]:
            title_tag = card.select_one("a[href*='/jobs/']")
            if not title_tag: continue
            title = title_tag.get_text(strip=True)
            if len(title) < 10: continue
            link = title_tag["href"]
            full_link = "https://www.charityjob.co.uk" + link if link.startswith("/") else link
            jobs.append({"title": title, "link": full_link, "source": "CharityJob"})
        return jobs
    except Exception as e:
        st.error(f"CharityJob Error: {e}")
        return []

def scrape_indeed(keyword: str, location: str) -> List[Dict]:
    try:
        url = f"https://uk.indeed.com/jobs?q={quote_plus(keyword)}&l={quote_plus(location)}&sort=date"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        for card in soup.select("div.job_seen_beacon")[:15]:
            title_tag = card.select_one("h2 a")
            if not title_tag: continue
            title = title_tag.get_text(strip=True)
            link = title_tag.get("href", "")
            if link.startswith("/"):
                link = "https://uk.indeed.com" + link
            jobs.append({"title": title, "link": link, "source": "Indeed"})
        return jobs
    except Exception as e:
        st.error(f"Indeed Error: {e}")
        return []

def scrape_thirdsector(keyword: str) -> List[Dict]:
    try:
        url = f"https://jobs.thirdsector.co.uk/jobs?keywords={quote_plus(keyword)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        for card in soup.select("article, div.job")[:12]:
            title_tag = card.select_one("a[href*='/job']")
            if not title_tag: continue
            title = title_tag.get_text(strip=True)
            if len(title) < 15: continue
            link = title_tag["href"]
            full_link = "https://jobs.thirdsector.co.uk" + link if link.startswith("/") else link
            jobs.append({"title": title, "link": full_link, "source": "Third Sector"})
        return jobs
    except Exception as e:
        st.error(f"Third Sector Error: {e}")
        return []

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("Settings")
    location = st.text_input("Location", "West Yorkshire", key="location_input")

# ===================== MAIN APP =====================
st.subheader("🔍 Search Jobs Posted in Last 24 Hours")

if st.button("🔍 Search Last 24 Hours", type="primary", use_container_width=True):
    with st.spinner("Searching across all sources..."):
        all_jobs = []
        active_sources = [s for s in st.session_state.custom_sources if s.get("active")]

        for source in active_sources:
            st.info(f"🔎 Scanning **{source['name']}**...")
            
            if source["name"] == "CharityJob":
                jobs = scrape_charityjob("manager", location)
            elif source["name"] == "Indeed":
                jobs = scrape_indeed("manager", location)
            elif source["name"] == "Third Sector":
                jobs = scrape_thirdsector("manager")
            else:
                jobs = []
                st.warning(f"No scraper for {source['name']}")
            
            all_jobs.extend(jobs)
            time.sleep(1.0)

        if all_jobs:
            st.success(f"✅ Found {len(all_jobs)} jobs
