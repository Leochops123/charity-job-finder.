import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder")
st.success("✅ Last 24 Hours • Simplified & Fixed")

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("Settings")
    location = st.text_input("📍 Location", "West Yorkshire", key="location")

# ===================== SCRAPERS =====================
def scrape_charityjob(location):
    try:
        url = "https://www.charityjob.co.uk/jobs?Sort=Date"
        if location and location.lower() not in ["any", "anywhere"]:
            url += f"&Location={quote_plus(location)}"
        
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []
        for card in soup.select("div.job-result, article")[:15]:
            a = card.select_one("a[href*='/jobs/']")
            if a:
                title = a.get_text(strip=True)
                if len(title) > 15:
                    link = a["href"]
                    full_link = "https://www.charityjob.co.uk" + link if link.startswith("/") else link
                    jobs.append({"title": title, "link": full_link, "source": "CharityJob"})
        return jobs
    except Exception as e:
        st.error(f"CharityJob Error: {e}")
        return []

def scrape_indeed(location):
    try:
        url = f"https://uk.indeed.com/jobs?q=charity&l={quote_plus(location)}&sort=date"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0
