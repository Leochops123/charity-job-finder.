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
st.success("✅ Working Version - All Sources")

# ===================== SESSION STATE =====================
if "keywords" not in st.session_state:
    st.session_state.keywords = ["fundraising", "manager", "officer", "coordinator"]

if "location" not in st.session_state:
    st.session_state.location = "West Yorkshire"

if "custom_sources" not in st.session_state:
    st.session_state.custom_sources = [
        {"name": "CharityJob", "active": True},
        {"name": "Indeed", "active": True},
        {"name": "Third Sector", "active": True},
        {"name": "Guardian", "active": True},
        {"name": "Totaljobs", "active": True}
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

def get_job_hash(title, link):
    return hashlib.md5(f"{title.lower().strip()}{link}".encode()).hexdigest()

def is_within_24h(text):
    if not text:
        return True
    t = text.lower()
    return any(word in t for word in ["today", "1 day ago", "hours ago", "just posted"])

# ===================== CHARITYJOB SCRAPER =====================
def scrape_charityjob(keyword, location):
    try:
        url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(keyword)}&Sort=Date"
        if location and location.lower() not in ["any", "anywhere", ""]:
            url += f"&Location
