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
            title = link_el.get_text(strip=True)
            link = link_el["href"]
            if not link.startswith("http"): link = base + link
            jobs.append({"title": title, "company": "Unknown", "link": link, "source": "CharityJob"})
        return jobs
    except Exception:
        return []


def get_reed_jobs(keyword: str, location: str) -> List[Dict]:
    try:
        base = "https://www.reed.co.uk"
        url = f"{base}/jobs/{quote_plus(keyword)}-jobs-in-{quote_plus(location)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        for card in soup.select("article.job-result"):
            link_el = card.select_one("a.title, a.job-block-link")
            if not link_el: continue
            title = link_el.get_text(strip=True)
            link = link_el["href"]
            if not link.startswith("http"): link = base + link
            jobs.append({"title": title, "company": "Unknown", "link": link, "source": "Reed"})
        return jobs
    except Exception:
        return []


# ====================== SIDEBAR ======================
with st.sidebar:
    st.header("⚙️ Search Settings")
    
    # === Keywords Section ===
    st.subheader("Keywords")
    new_keyword = st.text_input
