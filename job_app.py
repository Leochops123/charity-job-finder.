import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import json
import os
import hashlib
from typing import List, Dict

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder")
st.success("✅ Last 24 Hours • Multi-Source • Fully Fixed")

# ===================== SESSION STATE =====================
if "keywords" not in st.session_state:
    st.session_state.keywords = ["manager", "officer", "coordinator", "fundraising"]

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
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            if len(title) < 10:
                continue
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
            if not title_tag:
                continue
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
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            if len(title) < 15:
                continue
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
st.subheader("
