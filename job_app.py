import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder")
st.success("✅ Last 24 Hours • Fixed Version")

# Sidebar
with st.sidebar:
    st.header("Settings")
    location = st.text_input("Location", "West Yorkshire", key="loc")

# Scrapers
def scrape_charityjob(loc):
    try:
        url = "https://www.charityjob.co.uk/jobs?Sort=Date"
        if loc and loc.lower() not in ["any", "anywhere"]:
            url += "&Location=" + quote_plus(loc)
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        jobs = []
        for card in soup.select("div.job-result, article")[:15]:
            a = card.select_one("a[href*='/jobs/']")
            if a:
                title = a.get_text(strip=True)
                if len(title) > 15:
                    link = a["href"]
                    full = "https://www.charityjob.co.uk" + link if link.startswith("/") else link
                    jobs.append({"title": title, "link": full, "source": "CharityJob"})
        return jobs
    except:
        return []

def scrape_indeed(loc):
    try:
        url =
