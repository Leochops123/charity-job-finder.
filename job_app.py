import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from datetime import date
import time
from typing import List, Dict

st.set_page_config(page_title="Charity Job Finder", layout="wide")

st.title("💼 Charity & UK Job Finder + Email Alerts")
st.write("Loading...")

# ------------------- Session State -------------------
if "keywords" not in st.session_state:
    st.session_state.keywords = ["charity", "fundraising", "nonprofit"]
if "email" not in st.session_state:
    st.session_state.email = ""

# ------------------- Simple Email Placeholder -------------------
def send_job_email(receiver_email, jobs, location):
    st.error("Email functionality is not configured yet (secrets missing).")
    return False

# ------------------- Scrapers -------------------
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
            company_el = card.select_one(".job-result__org")
            company_name = company_el.get_text(strip=True) if company_el else "Unknown"
            link = link_el["href"]
            if not link.startswith("http"):
                link = base + link
            jobs.append({
                "source": "CharityJob", "title": title, "company": company_name,
                "link": link, "keyword": keyword
            })
        return jobs
    except Exception as e:
        st.warning(f"CharityJob error: {e}")
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
            link_el = card.select_one("a.job-block-link, a.title")
            if not link_el: continue
            title = link_el.get_text(strip=True)
            company_el = card.select_one(".gtmJobListingPostedBy, .company-name")
            company_name = company_el.get_text(strip=True) if company_el else "Unknown"
            link = link_el["href"]
            if not link.startswith("http"):
                link = base + link
            jobs.append({
                "source": "Reed", "title": title, "company": company_name,
                "link": link, "keyword": keyword
            })
        return jobs
    except Exception as e:
        st.warning(f"Reed error: {e}")
        return []


# ------------------- Sidebar -------------------
with st.sidebar:
    st.header("⚙️ Settings")
    email_input = st.text_input("Your Email Address", st.session_state.email, placeholder="you@example.com")
    if email_input:
        st.session_state.email = email_input

    st.subheader("Keywords")
    new_kw = st.text_input("Add new keyword", "")
    if st.button("Add Keyword") and new_kw.strip():
        kw = new_kw.strip().lower()
        if kw not in [k.lower() for k in st.session_state.keywords]:
            st.session_state.keywords.append(kw)
            st.rerun()

    for kw in st.session_state.keywords[:]:
        c1, c2 = st.columns([4,1])
        c1.write(f"• {kw}")
        if c2.button("🗑", key=f"del_{kw}"):
            st
