import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
from datetime import date
from typing import List, Dict

st.set_page_config(page_title="Charity Job Finder", layout="wide")

st.title("💼 Charity & UK Job Finder + Email Alerts")

# ====================== SESSION STATE ======================
if "keywords" not in st.session_state:
    st.session_state.keywords = ["charity", "fundraising", "nonprofit"]
if "websites" not in st.session_state:
    st.session_state.websites = ["CharityJob", "Reed"]

# ====================== SCRAPERS ======================
def get_charityjob_jobs(keyword: str, location: str) -> List[Dict]:
    try:
        base = "https://www.charityjob.co.uk"
        url = f"{base}/jobs/{quote_plus(keyword)}/{quote_plus(location)}?sort=Date"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        for card in soup.select(".job-result"):
            link_el = card.select_one("h2 a")
            if not link_el: continue
