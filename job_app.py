import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
from datetime import date, datetime
from typing import List, Dict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder + Alerts")
st.success("✅ Scanner + Email Alerts Active")

# ===================== SESSION + PERSISTENCE =====================
if "keywords" not in st.session_state:
    st.session_state.keywords = ["charity", "fundraising", "nonprofit", "trustee", "third sector"]

if "custom_sources" not in st.session_state:
    st.session_state.custom_sources = [
        {"name": "CharityJob", "base": "https://www.charityjob.co.uk", "active": True},
        {"name": "Third Sector Jobs", "base": "https://jp.thirdsector.co.uk", "active": True},
        {"name": "Goodmoves", "base": "https://goodmoves.org", "active": True},
        {"name": "Guardian Charities", "base": "https://jobs.theguardian.com/jobs/charities", "active": True},
        {"name": "Reed", "base": "https://www.reed.co.uk", "active": True},
        {"name": "Prospectus", "base": "https://www.prospect-us.co.uk", "active": False},
    ]

# Load previously seen jobs (simple persistence)
SEEN_FILE = "seen_jobs.json"
if os.path.exists(SEEN_FILE):
    try:
        with open(SEEN_FILE, "r") as f:
            seen_jobs = set(json.load(f))
    except:
        seen_jobs = set()
else:
    seen_jobs = set()

def save_seen_jobs():
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_jobs), f)

# ===================== EMAIL SENDING =====================
def send_email_alert(new_jobs: List[Dict], recipient: str):
    if not recipient or not new_jobs:
        return False
    
    try:
        sender_email = st.secrets.get("EMAIL_ADDRESS") or "your_email@gmail.com"  # Use Streamlit secrets in production
        password = st.secrets.get("EMAIL_PASSWORD") or None

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = f"New Third Sector Jobs Found - {date.today()}"

        body = f"<h2>{len(new_jobs)} New Jobs Found</h2><br>"
        for job in new_jobs[:15]:
            body += f"<strong>{job['title']}</strong> — {job['source']}<br>"
            body += f"<a href='{job['link']}'>View Job</a><br><br>"

        msg.attach(MIMEText(body, 'html'))

        # Gmail example (use your own SMTP)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email failed: {e}")
        return False

# ===================== SCRAPERS (same as before) =====================
def scrape_generic(url: str, source_name: str) -> List[Dict]:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        for card in soup.select("article, div[class*='job'], li[class*='job'], div[class*='result']"):
            link = card.find("a", href=True)
            if not link: 
                continue
            title = link.get_text(strip=True)
            if len(title) < 8: 
                continue
                
            full_link = link["href"]
            if not full_link.startswith("http"):
                domain = "/".join(url.split("/")[:3])
                full_link = domain + full_link if full_link.startswith("/") else domain + "/" + full_link
            
            jobs.append({
                "title": title,
                "company": "Unknown",
                "location": "",
                "salary": "",
                "link": full_link,
                "source": source_name,
                "found_date": str(date.today())
            })
        return jobs[:25]
    except:
        return []

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("⚙️ Alert Settings")
    
    email = st.text_input("Your Email Address", placeholder="you@example.com")
    enable_alerts = st.toggle("Enable Daily Email Alerts", value=False)
    
    if enable_alerts and email:
        st.success("✅ Alerts Enabled - Will scan and notify you")
    elif enable_alerts and not email:
        st.warning("Please enter your email")

    st.subheader("Keywords")
    # ... (keyword management same as before)

    st.subheader("Job Sources")
    # ... (source management same as before)

# ===================== MAIN =====================
st.subheader("🔍 Search & Alert System")
col1, col2 = st.columns([3,1])
with col1:
    location = st.text_input("Location", "West Yorkshire")
with col2:
    max_results = st.slider("Max results", 10, 100, 30)

# Two action buttons
col_a, col_b = st.columns(2)
search_clicked = col_a.button("🔍 Search Now", type="primary", use_container_width=True)
alert_clicked = col_b.button("📧 Check New Jobs & Send Alert", use_container_width=True)

if search_clicked or alert_clicked:
    with st.spinner("Scanning all active third sector job boards..."):
        new_jobs = []
        active_sources = [s for s in st.session_state.custom_sources if s.get("active")]

        progress_bar = st.progress(0)

        for idx, source in enumerate(active_sources):
            st.info(f"Scanning **{source['name']}**...")
            
            for kw in st.session_state.keywords:
                search_url = source["base"]
                
                # Site-specific URL building
                if "charityjob" in search_url.lower():
                    search_url = f"https://www.charityjob.co.uk/jobs/{quote_plus(kw)}/{quote_plus(location)}?sort=Date"
                elif "thirdsector" in search_url.lower():
                    search_url = f"https://jp.thirdsector.co.uk/jobs?keywords={quote_plus(kw)}"
                elif "goodmoves" in search_url.lower():
                    search_url = f"https://goodmoves.org/search?keywords={quote_plus(kw)}"
                elif "guardian" in search_url.lower():
                    search_url = f"https://jobs.theguardian.com/jobs/charities/?keywords={quote_plus(kw)}"
                
                jobs = scrape_generic(search_url, source["name"])
                
                for job in jobs:
                    if job["link"] not in seen_jobs:
                        seen_jobs.add(job["link"])
                        new_jobs.append(job)
            
            progress_bar.progress((idx + 1) / len(active_sources))
            time.sleep(1.2)

        save_seen_jobs()

        if new_jobs:
            st.success(f"🎉 Found **{len(new_jobs)} NEW jobs**!")
            for job in new_jobs[:max_results]:
                with st.expander(f"**{job['title']}** — {job['source']}"):
                    st.markdown(f"[🔗 View Job]({job['link']})")

            # Send Email Alert
            if alert_clicked and enable_alerts and email:
                with st.spinner("Sending email alert..."):
                    if send_email_alert(new_jobs, email):
                        st.success(f"📧 Alert sent to {email}!")
        else:
            st.info("No new jobs found since last scan.")

st.caption("The app remembers previously seen jobs. Click 'Check New Jobs & Send Alert' regularly or deploy with scheduler for true automation.")
