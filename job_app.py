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
st.success("✅ Multi-Source • Robust Scrapers • Last 24 Hours")

# ===================== SESSION STATE =====================
if "keywords" not in st.session_state:
    st.session_state.keywords = ["fundraising", "manager", "officer", "coordinator", "trustee"]

if "location" not in st.session_state:
    st.session_state.location = "West Yorkshire"

if "custom_sources" not in st.session_state:
    st.session_state.custom_sources = [
        {"name": "CharityJob", "active": True},
        {"name": "Indeed", "active": True},
        {"name": "Third Sector", "active": True},
    ]

if "smtp_settings" not in st.session_state:
    st.session_state.smtp_settings = {"enabled": False, "sender_email": "", "app_password": "", "recipient_email": ""}

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
    t = text.lower()
    return any(word in t for word in ["today", "just posted", "1 day ago", "hours ago", "24 hour", "posted today"])

# ===================== SCRAPERS =====================
def scrape_charityjob(keyword: str, location: str) -> List[Dict]:
    try:
        url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(keyword)}&Sort=Date"
        if location and location.lower() not in ["any", "anywhere", ""]:
            url += f"&Location={quote_plus(location)}"

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")

        jobs = []
        # Multiple possible selectors
        for selector in ["article", "div.job-result", "div[class*='job']", "div[data-job]"]:
            cards = soup.select(selector)
            for card in cards:
                title_tag = card.select_one("a[href*='/jobs/']")
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    if len(title) < 15:
                        continue
                    link = title_tag["href"]
                    full_link = "https://www.charityjob.co.uk" + link if link.startswith("/") else link

                    if is_within_24h(card.get_text()):
                        jobs.append({
                            "title": title,
                            "link": full_link,
                            "source": "CharityJob",
                            "salary": "See posting",
                            "location": location
                        })
        return jobs[:25]
    except Exception as e:
        st.error(f"CharityJob failed: {e}")
        return []

def scrape_indeed(keyword: str, location: str) -> List[Dict]:
    try:
        url = f"https://uk.indeed.com/jobs?q={quote_plus(keyword)}+charity&l={quote_plus(location)}&sort=date"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        jobs = []
        for card in soup.select("div.job_seen_beacon, div[class*='jobcard'], div[data-jk]"):
            title_tag = card.select_one("h2 a, a.jcs-JobTitle")
            if title_tag:
                title = title_tag.get_text(strip=True)
                link = title_tag.get("href", "")
                full_link = "https://uk.indeed.com" + link if link.startswith("/") else link

                if is_within_24h(card.get_text()):
                    jobs.append({
                        "title": title,
                        "link": full_link,
                        "source": "Indeed",
                        "salary": "See posting",
                        "location": location
                    })
        return jobs[:20]
    except Exception as e:
        st.error(f"Indeed failed: {e}")
        return []

def scrape_thirdsector(keyword: str) -> List[Dict]:
    try:
        url = f"https://jobs.thirdsector.co.uk/jobs?keywords={quote_plus(keyword)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        jobs = []
        for card in soup.select("article, div.job, div[class*='job']"):
            title_tag = card.select_one("a[href*='/job']")
            if title
