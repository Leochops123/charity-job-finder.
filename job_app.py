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
st.success("✅ Last 24 Hours • Multi-Source • Fixed")

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

def is_within_24h(text: str) -> bool:
    if not text:
        return True
    text = text.lower()
    recent = ["today", "just posted", "1 day ago", "24 hour", "hours ago", 
              "posted 1 day", "1 hour", "2 hour", "minutes ago"]
    return any(x in text for x in recent)

# ===================== SCRAPERS =====================
def scrape_charityjob(keyword: str, location: str) -> List[Dict]:
    try:
        url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(keyword)}&Sort=Date"
        if location and location.lower() not in ["any", "anywhere"]:
            url += f"&Location={quote_plus(location)}"
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url,
