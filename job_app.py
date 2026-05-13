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
st.success("✅ CharityJob + Indeed + Third Sector • Last 24 Hours")

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

# Email Settings
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
    recent = ["today", "just posted", "1 day ago", "24 hour", "hours ago", "1 hour", 
              "2 hour", "posted 1 day", "new today"]
    return any(k in t for k in recent)

# ===================== FULL SCRAPERS =====================
def scrape_charityjob(keyword: str, location: str) -> List[Dict]:
    try:
        url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(keyword)}&Sort=Date"
        if location and location.lower() not in ["any", "anywhere", ""]:
            url += f"&Location={quote_plus(location)}"

        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        for card in soup.select("div.job-result, article"):
            title_tag = card.select_one("a[href*='/jobs/']")
            if not title_tag or len(title_tag.get_text(strip=True)) < 15:
                continue
            title = title_tag.get_text(strip=True)
            link = title_tag["href"]
            full_link = "https://www.charityjob.co.uk" + link if link.startswith("/") else link

            if not is_within_24h(card.get_text()):
                continue

            jobs.append({
                "title": title, 
                "link": full_link, 
                "source": "CharityJob",
                "salary": "Not listed", 
                "location": location
            })
        return jobs[:25]
    except:
        return []

def scrape_indeed(keyword: str, location: str) -> List[Dict]:
    try:
        url = f"https://uk.indeed.com/jobs?q={quote_plus(keyword)}+charity&l={quote_plus(location)}&sort=date"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        for card in soup.select("div.job_seen_beacon"):
            title_tag = card.select_one("h2 a")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link = title_tag.get("href", "")
            full_link = "https://uk.indeed.com" + link if link.startswith("/") else link

            if not is_within_24h(card.get_text()[:400]):
                continue

            salary_tag = card.select_one("div[class*='salary'], span[class*='salary']")
            salary = salary_tag.get_text(strip=True) if salary_tag else "Not listed"

            jobs.append({
                "title": title, 
                "link": full_link, 
                "source": "Indeed",
                "salary": salary, 
                "location": location
            })
        return jobs[:20]
    except:
        return []

def scrape_thirdsector(keyword: str) -> List[Dict]:
    try:
        url = f"https://jobs.thirdsector.co.uk/jobs?keywords={quote_plus(keyword)}"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        for card in soup.select("article, div.job-card, div.job"):
            title_tag = card.select_one("a[href*='/job']")
            if not title_tag or len(title_tag.get_text(strip=True)) < 15:
                continue
            title = title_tag.get_text(strip=True)
            link = title_tag["href"]
            full_link = "https://jobs.thirdsector.co.uk" + link if link.startswith("/") else link

            if not is_within_24h(card.get_text()):
                continue

            jobs.append({
                "title": title, 
                "link": full_link, 
                "source": "Third Sector",
                "salary": "Not listed", 
                "location": "UK"
            })
        return jobs[:20]
    except:
        return []

# ===================== EMAIL FUNCTION =====================
def send_email_alert(jobs: List[Dict]):
    settings = st.session_state.smtp_settings
    if not settings["enabled"] or not settings["sender_email"] or not settings["app_password"] or not jobs:
        return

    recipient = settings.get("recipient_email") or settings["sender_email"]
    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"New Charity Jobs Found - {len(jobs)}"
        msg['From'] = settings["sender_email"]
        msg['To'] = recipient

        body = f"<h3>Found {len(jobs)} new jobs in last 24 hours</h3><ul>"
        for job in jobs[:15]:
            body += f"<li><b>{job['title']}</b><br>{job.get('salary','')} | {job.get('location','')}<br>"
            body += f"<a href='{job['link']}'>View Job →</a></li><br>"
        body += "</ul>"

        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(settings["sender_email"], settings["app_password"])
            server.send_message(msg)
        st.success(f"📧 Email sent to {recipient}")
    except Exception as e:
        st.error(f"Email error: {e}")

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("🛠️ Filters & Settings")

    st.subheader("📍 Location")
    new_loc = st.text_input("Preferred Location", value=st.session_state.location, key="loc_input")
    if new_loc != st.session_state.location:
        st.session_state.location = new_loc

    st.subheader("🔑 Keywords")
    new_kw = st.text_input("Add Keyword", placeholder="e.g. grant manager", key="new_kw")
    if st.button("➕ Add") and new_kw.strip():
        kw = new_kw.strip().lower()
        if kw not in st.session_state.keywords:
            st.session_state.keywords.append(kw)
            st.rerun()

    for kw in list(st.session_state.keywords):
        col1, col2 = st.columns([4,1])
        col1.write(f"• {kw}")
        if col2.button("🗑️", key=f"del_{kw}"):
            st.session_state.keywords.remove(kw)
            st.rerun()

    st.subheader("📌 Job Sources")
    for idx, source in enumerate(st.session_state.custom_sources):
        col1, col2 = st.columns([5,1])
        source["active"] = col1.checkbox(source["name"], value=source.get("active", True), key=f"src_{idx}")
        if col2.button("🗑️", key=f"delsrc_{idx}"):
            st.session_state.custom_sources.pop(idx)
            st.rerun()

    st.subheader("📧 Email Alerts")
    st.session_state.smtp_settings["enabled"] = st.toggle("Enable Email Alerts", value=st.session_state.smtp_settings["enabled"])
    st.text_input("Sender Gmail", key="sender_email", value=st.session_state.smtp_settings["sender_email"])
    st.text_input("Gmail App Password", key="app_password", value=st.session_state.smtp_settings["app_password"], type="password")
    st.text_input("Recipient Email (optional)", key="recipient_email", value=st.session_state.smtp_settings["recipient_email"])

# ===================== MAIN =====================
st.subheader(f"🔍 Search Recent Jobs in **{st.session_state.location}**")

if st.button("🔍 Search Last 24 Hours", type="primary", use_container_width=True):
    with st.spinner("Searching CharityJob, Indeed & Third Sector..."):
        all_jobs = []
        active_sources = [s for s in st.session_state.custom_sources if s.get("active")]

        progress_bar = st.progress(0)

        for i, source in enumerate(active_sources):
            st.info(f"🔎 Scanning **{source['name']}**...")
            for kw in st.session_state.keywords[:8]:
                if source["name"] == "CharityJob":
                    jobs = scrape_charityjob(kw, st.session_state.location)
                elif source["name"] == "Indeed":
                    jobs = scrape_indeed(kw, st.session_state.location)
                elif source["name"] == "Third Sector":
                    jobs = scrape_thirdsector(kw)
                else:
                    jobs = []
                
                all_jobs.extend(jobs)
                time.sleep(1.0)
            
            progress_bar.progress((i + 1) / len(active_sources) if active_sources else 1)

        # Deduplicate
        unique_jobs = []
        for job in all_jobs:
            jhash = get_job_hash(job["title"], job["link"])
            if jhash not in seen_jobs:
                seen_jobs.add(jhash)
                unique_jobs.append(job)

        save_seen_jobs()

        if unique_jobs:
            st.success(f"🎉 Found **{len(unique_jobs)}** new jobs!")
            for job in unique_jobs[:60]:
                with st.expander(f"**{job['title']}** — {job['source']}"):
                    st.markdown(f"[🔗 View Job]({job['link']})")
                    st.caption(f"Salary: {job.get('salary', 'N/A')} | Location: {job.get('location', 'N/A')}")
            
            if st.session_state.smtp_settings["enabled"]:
                send_email_alert(unique_jobs)
        else:
            st.info("No new jobs found in the last 24 hours.")

st.caption("All sources are now active • Use Gmail App Password for emails")
