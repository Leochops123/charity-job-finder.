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
st.success("✅ Multi-Source • Last 24 Hours • Smart Filters")

# ===================== SESSION STATE =====================
if "keywords" not in st.session_state:
    st.session_state.keywords = ["fundraising", "manager", "officer", "coordinator", "safeguarding", "trustee"]

if "location" not in st.session_state:
    st.session_state.location = "West Yorkshire"

if "custom_sources" not in st.session_state:
    st.session_state.custom_sources = [
        {"name": "CharityJob", "base": "https://www.charityjob.co.uk", "active": True},
        {"name": "Indeed", "base": "https://uk.indeed.com", "active": True},
        {"name": "Third Sector", "base": "https://jobs.thirdsector.co.uk", "active": True},
    ]

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

# ===================== SCRAPERS =====================
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

            card_text = card.get_text()
            if not is_within_24h(card_text):
                continue

            # Extract salary & location if available
            salary = next((t.strip() for t in card_text.split() if "£" in t), "Not listed")
            loc = location or "UK"

            job_hash = get_job_hash(title, full_link)
            if job_hash not in seen_jobs:
                jobs.append({
                    "title": title, "link": full_link, "source": "CharityJob",
                    "salary": salary, "location": loc
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
            if not title_tag: continue
            title = title_tag.get_text(strip=True)
            link = "https://uk.indeed.com" + title_tag.get("href", "")

            if not is_within_24h(card.get_text()[:400]):
                continue

            salary = card.select_one("div[class*='salary']")
            salary_text = salary.get_text(strip=True) if salary else "Not listed"

            job_hash = get_job_hash(title, link)
            if job_hash not in seen_jobs:
                jobs.append({
                    "title": title, "link": link, "source": "Indeed",
                    "salary": salary_text, "location": location
                })
        return jobs[:20]
    except:
        return []

def scrape_thirdsector(keyword: str) -> List[Dict]:
    try:
        url = f"https://jobs.thirdsector.co.uk/jobs?keywords={quote_plus(keyword)}"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        for card in soup.select("article, div.job"):
            title_tag = card.select_one("a[href*='/job']")
            if not title_tag or len(title_tag.get_text(strip=True)) < 15:
                continue
            title = title_tag.get_text(strip=True)
            link = "https://jobs.thirdsector.co.uk" + title_tag["href"] if title_tag["href"].startswith("/") else title_tag["href"]

            if not is_within_24h(card.get_text()):
                continue

            job_hash = get_job_hash(title, link)
            if job_hash not in seen_jobs:
                jobs.append({
                    "title": title, "link": link, "source": "Third Sector",
                    "salary": "Not listed", "location": "UK"
                })
        return jobs[:20]
    except:
        return []

# ===================== EMAIL ALERTS =====================
def send_email_alert(jobs: List[Dict], email: str):
    if not jobs or not email:
        return
    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"New Charity Jobs Found - {len(jobs)} opportunities"
        msg['From'] = "yourapp@example.com"
        msg['To'] = email

        body = "Here are the newest jobs:\n\n"
        for job in jobs[:10]:
            body += f"• {job['title']}\n  {job['link']}\n\n"

        msg.attach(MIMEText(body, 'plain'))

        # Configure your SMTP settings here (Gmail example)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login("your-email@gmail.com", "your-app-password")
            server.send_message(msg)
        st.success("Email alert sent!")
    except Exception as e:
        st.warning(f"Could not send email: {e}")

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("🛠️ Filters & Settings")
    
    # Location
    st.subheader("📍 Location")
    new_loc = st.text_input("Preferred Location", value=st.session_state.location, key="loc_input")
    if new_loc != st.session_state.location:
        st.session_state.location = new_loc

    st.subheader("🔑 Keywords")
    new_kw = st.text_input("Add Keyword", placeholder="e.g. grant manager")
    if st.button("➕ Add Keyword") and new_kw.strip():
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

    st.subheader("📌 Active Sources")
    for idx, source in enumerate(st.session_state.custom_sources):
        col1, col2 = st.columns([5,1])
        source["active"] = col1.checkbox(source["name"], value=source.get("active", True), key=f"src_{idx}")
        if col2.button("🗑️", key=f"delsrc_{idx}"):
            st.session_state.custom_sources.pop(idx)
            st.rerun()

    st.subheader("📧 Email Alerts")
    alert_email = st.text_input("Your Email", placeholder="you@example.com", key="alert_email")
    enable_alerts = st.toggle("Send Email Alert on New Jobs", value=True)

# ===================== MAIN APP =====================
st.subheader(f"🔍 Recent Jobs in **{st.session_state.location}**")

if st.button("🔍 Search Last 24 Hours", type="primary", use_container_width=True):
    with st.spinner("Searching across sources..."):
        all_jobs = []
        active_sources = [s for s in st.session_state.custom_sources if s.get("active")]
        
        progress_bar = st.progress(0)
        total = len(active_sources) * len(st.session_state.keywords)

        for i, source in enumerate(active_sources):
            for kw in st.session_state.keywords:
                if source["name"] == "CharityJob":
                    jobs = scrape_charityjob(kw, st.session_state.location)
                elif source["name"] == "Indeed":
                    jobs = scrape_indeed(kw, st.session_state.location)
                elif source["name"] == "Third Sector":
                    jobs = scrape_thirdsector(kw)
                else:
                    jobs = []
                
                all_jobs.extend(jobs)
                time.sleep(0.9)

            progress_bar.progress((i+1) / len(active_sources))

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
            
            for job in unique_jobs[:50]:
                with st.expander(f"**{job['title']}** — {job['source']}"):
                    st.markdown(f"[🔗 View Job]({job['link']})")
                    st.caption(f"Salary: {job.get('salary', 'N/A')} | Location: {job.get('location', 'N/A')}")

            if enable_alerts and alert_email:
                send_email_alert(unique_jobs, alert_email)
        else:
            st.info("No new jobs found in the last 24 hours.")

st.caption("Jobs are automatically marked as seen • Respectful scraping with delays")
