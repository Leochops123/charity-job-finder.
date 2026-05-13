import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import hashlib
import os

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder")
st.success("✅ Working Version - Ready to Test")

# Session State
if "keywords" not in st.session_state:
    st.session_state.keywords = ["fundraising", "manager", "officer"]

if "location" not in st.session_state:
    st.session_state.location = "West Yorkshire"

# Simple Scraper
def scrape_charityjob(keyword, location):
    try:
        url = "https://www.charityjob.co.uk/jobs?Keywords=" + quote_plus(keyword) + "&Sort=Date"
        if location and location.lower() not in ["any", "anywhere", ""]:
            url += "&Location=" + quote_plus(location)
        
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        for card in soup.select("article, div.job-result"):
            title_tag = card.select_one("a[href*='/jobs/']")
            if title_tag and len(title_tag.get_text(strip=True)) >= 15:
                title = title_tag.get_text(strip=True)
                link = title_tag["href"]
                full_link = "https://www.charityjob.co.uk" + link if link.startswith("/") else link
                jobs.append({"title": title, "link": full_link, "source": "CharityJob"})
        return jobs[:25]
    except:
        return []

# Sidebar
with st.sidebar:
    st.header("Filters")
    new_loc = st.text_input("Location", value=st.session_state.location)
    if new_loc != st.session_state.location:
        st.session_state.location = new_loc

    new_kw = st.text_input("Add Keyword", placeholder="e.g. fundraising")
    if st.button("
