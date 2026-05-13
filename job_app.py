import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import hashlib
import os

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder")
st.success("✅ Clean Working Version")

# ===================== SESSION STATE =====================
if "keywords" not in st.session_state:
    st.session_state.keywords = ["fundraising", "manager", "officer"]

if "location" not in st.session_state:
    st.session_state.location = "West Yorkshire"

# ===================== SCRAPER =====================
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
                jobs.append({"title": title, "link": full_link, "source":
                
