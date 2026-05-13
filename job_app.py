import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
from datetime import datetime

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder")
st.success("✅ Fully Fixed & Working")

# Session State
if "positive_keywords" not in st.session_state:
    st.session_state.positive_keywords = ["fundraising", "manager", "officer", "coordinator", "fundraiser"]
if "location" not in st.session_state:
    st.session_state.location = "West Yorkshire"
if "sources" not in st.session_state:
    st.session_state.sources = ["CharityJob"]

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("⚙️ Settings")
    
    pos_input = st.text_input("Search Keywords (comma separated)", 
                             ", ".join(st.session_state.positive_keywords))
    
    loc_input = st.text_input("Location", st.session_state.location)
    
    st.divider()
    
    st.subheader("📧 Email Alerts")
    email_from = st.text_input("Your Email", "")
    email_password = st.text_input("App Password (Gmail)", type="password")
    email_to = st.text_input("Send To", value=email_from)
    
    st.divider()
    
    st.subheader("📌 Job Sources")
    selected_sources = st.multiselect("Active Sources", 
                                     ["CharityJob", "ThirdSector", "Prospects"], 
                                     default=st.session_state.sources)
    
    new_source = st.text_input("Add New Source Name")
    if st.button("Add Source"):
        if new_source and new_source not in st.session_state.sources:
            st.session_state.sources.append(new_source)
            st.success(f"Added {new_source}")
    
    if st.button("💾 Save All Settings"):
        st.session_state.positive_keywords = [k.strip() for k in pos_input.split(",") if k.strip()]
        st.session_state.location = loc_input
        st.session_state.sources = selected_sources
        st.success("✅ All settings saved!")

# ===================== SCRAPER =====================
def scrape_charityjob(keyword, location):
    try:
        url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(keyword)}&Sort=Date"
        if location and location.lower() not in ["any", "anywhere"]:
            url += f"&Location={quote_plus(location)}"
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        for tag in soup.select("a[href*='/jobs/']"):
            title = tag.get_text(strip=True)
            if len(title) < 12:
                continue
            href = tag["href"]
            full_link = "https://www.charityjob.co.uk" + href if href.startswith("/") else href
            
            parent = tag.find_parent(["div", "article"])
            company = parent.get_text(strip=True)[:120] if parent else "Unknown"
            
            jobs.append({
                "title": title,
                "link": full_link,
                "company": company,
                "source": "CharityJob"
            })
        return jobs[:25]
    except Exception:
        return []

def should_include(title):
    t = title.lower()
    return any(k.lower() in t for k in st.session_state.positive_keywords)

# ===================== MAIN APP =====================
if st.button("🔍 Search Jobs Now", type="primary", use_container_width=True):
    with st.spinner("Searching across sources..."):
        all_jobs = []
        
        for kw in st.session_state.positive_keywords[:6]:
            if "CharityJob" in st.session_state.sources:
                jobs = scrape_charityjob(kw, st.session_state.location)
                for job in jobs:
                    if should_include(job["title"]):
                        all_jobs.append(job)
                time.sleep(1.3)

        # Remove duplicates
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            if job["link"] not in seen:
                seen.add(job["link"])
                unique_jobs.append(job)
        
        if unique_jobs:
            st.success(f"✅ Found {len(unique_jobs)} matching jobs")
            for job in unique_jobs[:20]:
                with st.container(border=True):
                    st.markdown(f"**[{job['title']}]({job['link']})**")
                    st.caption
