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
st.success("✅ Last 24 Hours • Sources Fixed & Restored")

# ===================== SESSION STATE INITIALIZATION =====================
if "keywords" not in st.session_state:
    st.session_state.keywords = ["fundraising", "manager", "officer", "coordinator", "trustee", "safeguarding"]

if "custom_sources" not in st.session_state:
    st.session_state.custom_sources = [
        {"name": "CharityJob", "base": "https://www.charityjob.co.uk", "active": True},
        {"name": "Indeed", "base": "https://uk.indeed.com", "active": True},
        {"name": "Third Sector", "base": "https://jobs.thirdsector.co.uk", "active": True},
        {"name": "Guardian", "base": "https://jobs.theguardian.com", "active": False},
    ]

# Force reset if sources disappeared
if len(st.session_state.custom_sources) == 0:
    st.session_state.custom_sources = [
        {"name": "CharityJob", "base": "https://www.charityjob.co.uk", "active": True},
        {"name": "Indeed", "base": "https://uk.indeed.com", "active": True},
        {"name": "Third Sector", "base": "https://jobs.thirdsector.co.uk", "active": True},
    ]
    st.rerun()

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

def is_within_24h(date_text: str) -> bool:
    if not date_text:
        return True
    text = date_text.lower()
    return any(x in text for x in ["today", "just posted",
