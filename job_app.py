import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import json
import os
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder")
st.success("✅ Multi-Source • Improved Scrapers • Last 24 Hours")

# ===================== SESSION STATE =====================
if "keywords" not in st.session_state:
    st.session_state.keywords = ["fundraising", "manager", "officer", "coordinator", "safeguarding", "trustee"]

if "location" not in st.session_state:
    st.session_state.location = "West Yorkshire"

if "custom_sources" not in st.session_state:
    st.session_state.custom_sources = [
        {"name": "CharityJob", "active": True},
        {"name": "Indeed", "active": True},
        {"name": "Third Sector", "active": True},
    ]

if "smtp_settings" not in st.session_state:
    st.session_state.smtp_settings = {
        "sender_email": "", "app_password": "", "recipient_email": "", "enabled": False
    }

SEEN_FILE = "seen_jobs.json"
seen_jobs: set = set()
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
    t = text.lower()
    recent = ["today", "just posted", "1 day ago", "24 hour", "hours ago", "posted today", "new today"]
    return any(k in t for k in recent)

# ===================== IMPROVED SCRAPERS =====================
def scrape_charityjob(keyword: str, location: str) -> List[Dict]:
    jobs = []
    try:
        url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(keyword)}&Sort=Date"
        if location and location.lower() not in ["any", "anywhere", ""]:
            url += f"&Location={quote_plus(location)}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Stronger,
