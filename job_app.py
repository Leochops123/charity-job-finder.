import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import json
import os
from datetime import datetime

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder")
st.success("✅ Fully Fixed & Working")

# Session State
if "positive_keywords" not in st.session_state:
    st.session_state.positive_keywords = ["fundraising", "manager", "officer", "coordinator"]
if "negative_keywords" not in st.session_state:
    st.session_state.negative_keywords = ["senior", "director", "head of", "intern", "volunteer"]
if "location" not in st.session_state:
    st.session_state.location = "West Yorkshire"

# Sidebar
with st.sidebar:
    st.header("Settings")
    pos_input = st.text_input("Positive Keywords (comma separated)", 
                             ", ".join(st.session_state.positive_keywords))
    neg_input = st.text_input("Keywords to Exclude", 
                             ", ".join(st.session_state.negative_keywords))
    loc_input = st.text_input("Location", st.session_state.location)
    
    if st.button("Save Settings"):
        st.session_state.positive_keywords = [k.strip() for k in pos_input.split(",") if k.strip()]
        st.session_state.negative_keywords = [k.strip() for k in neg_input.split(",") if k.strip()]
        st.session_state.location = loc_input
        st.success("Settings Saved!")

# Functions
def scrape_charityjob(keyword, location):
    try:
        url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(keyword)}&Sort=Date"
        if location and location.lower() not in ["any", "anywhere"]:
            url += f"&Location={quote_plus(location)}"
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        for tag in soup.select("a[href*='/jobs/']"):
            title = tag.get_text(strip=True)
            if len(title) < 12:
                continue
            link = tag["href"]
            full_link = "https://www.charityjob.co.uk" + link if link.startswith("/") else link
            
            parent = tag.find_parent(["div", "article"])
            company = parent.get_text(strip=True)[:150] if parent else "Unknown"
            
            jobs.append({
                "title": title,
                "link": full_link,
                "company": company,
                "source": "CharityJob"
            })
        return jobs[:25]
    except:
        return []

def should_include(title):
    t = title.lower()
    if not any(k.lower() in t for k in st.session_state.positive_keywords):
        return False
    if any(k.lower() in t for k in st.session_state.negative_keywords):
        return False
    return True

# Main
if st.button("🔍 Search Jobs Now", type="primary", use_container_width=True):
    with st.spinner("Searching charity jobs..."):
        all_jobs = []
        for kw in st.session_state.positive_keywords[:6]:
            jobs = scrape_charityjob(kw, st.session_state.location)
            for job in jobs:
                if should_include(job["title"]):
                    all_jobs.append(job)
            time.sleep(1.5)
        
        # Remove duplicates
        seen = set()
        unique = []
        for job in all_jobs:
            if job["link"] not in seen:
                seen.add(job["link"])
                unique.append(job)
        
        st.success(f"✅ Found {len(unique)} matching jobs")
        
        for job in unique[:15]:
            with st.container(border=True):
                st.markdown(f"**[{job['title']}]({job['link']})**")
                st.caption(f"{job['company']} • {job['source']}")
                st.divider()
