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
st.success("✅ Syntax Fixed | Indeed Improved")

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

# ===================== SCRAPER =====================
def scrape_jobs(source_name: str, keyword: str, location: str) -> List[Dict]:
   
