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
            if not link_el:
                continue
            title = link_el.get_text(strip=True)
            link = link_el["href"]
            if not link.startswith("http"):
                link = base + link
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
            if not link_el:
                continue
            title = link_el.get_text(strip=True)
            link = link_el["href"]
            if not link.startswith("http"):
                link = base + link
            jobs.append({"title": title, "company": "Unknown", "link": link, "source": "Reed"})
        return jobs
    except Exception:
        return []


# ====================== SIDEBAR ======================
with st.sidebar:
    st.header("⚙️ Search Settings")
    
    with st.form("settings_form"):
        st.subheader("Keywords")
        new_keyword = st.text_input("Add new keyword", "")
        if st.form_submit_button("Add Keyword") and new_keyword.strip():
            kw = new_keyword.strip().lower()
            if kw not in st.session_state.keywords:
                st.session_state.keywords.append(kw)
                st.rerun()

        st.write("**Current Keywords:**")
        for kw in st.session_state.keywords[:]:
            col1, col2 = st.columns([4,1])
            col1.write(f"• {kw}")
            if col2.button("Remove", key=f"kw_{kw}"):
                st.session_state.keywords.remove(kw)
                st.rerun()

        st.divider()
        
        st.subheader("Websites / Sources")
        new_site = st.text_input("Add website (e.g. Indeed)", "")
        if st.form_submit_button("Add Website") and new_site.strip():
            site = new_site.strip()
            if site not in st.session_state.websites:
                st.session_state.websites.append(site)
                st.rerun()

        st.write("**Current Sources:**")
        for site in st.session_state.websites[:]:
            col1, col2 = st.columns([4,1])
            col1.write(f"• {site}")
            if col2.button("Remove", key=f"site_{site}"):
                st.session_state.websites.remove(site)
                st.rer
