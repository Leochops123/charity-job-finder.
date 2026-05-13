import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import hashlib
import os

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder")
st.success("✅ Debug Version Active")

# Session State
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

def get_job_hash(title, link):
    return hashlib.md5((title.lower().strip() + link).encode()).hexdigest()

# ===================== IMPROVED SCRAPER WITH DEBUG =====================
def scrape_charityjob(keyword, location):
    st.info(f"Searching for: **{keyword}** in **{location}**")
    try:
        url = "https://www.charityjob.co.uk/jobs?Keywords=" + quote_plus(keyword) + "&Sort=Date"
        if location and location.lower() not in ["any", "anywhere", ""]:
            url += "&Location=" + quote_plus(location)
        
        st.write("URL:", url)
        
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        st.write("Status Code:", resp.status_code)
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        selectors = ["article", "div.job-result", "div[class*='job']", "div[data-testid]"]
        
        for selector in selectors:
            cards = soup.select(selector)
            st.write(f"Found {len(cards)} cards with selector: {selector}")
            
            for card in cards[:10]:   # limit for debug
                title_tag = card.select_one("a[href*='/jobs/']")
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    if len(title) > 15
