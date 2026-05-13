import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder")
st.success("✅ Ultra Clean Version")

if "keywords" not in st.session_state:
    st.session_state.keywords = ["fundraising", "manager", "officer"]

if "location" not in st.session_state:
    st.session_state.location = "West Yorkshire"

def scrape_charityjob(keyword, location):
    try:
        url = "https://www.charityjob.co.uk/jobs?Keywords=" + quote_plus(keyword) + "&Sort=Date"
        if location and location.lower() not in ["any", "anywhere", ""]:
            url = url + "&Location=" + quote_plus(location)
        
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        for card in soup.select("article, div.job-result"):
            title_tag = card.select_one("a[href*='/jobs/']")
            if title_tag:
                title = title_tag.get_text(strip=True)
                if len(title) >= 15:
                    link = title_tag["href"]
                    full_link = "https://www.charityjob.co.uk" + link if link.startswith("/") else link
                    jobs.append({"title": title, "link": full_link, "source": "CharityJob"})
        return jobs[:
