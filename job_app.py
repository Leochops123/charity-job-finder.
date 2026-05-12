import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
from datetime import date
from typing import List, Dict

st.set_page_config(page_title="Charity Job Finder", layout="wide")

st.title("💼 Charity & UK Job Finder + Email Alerts")
st.success("✅ App is working!")

# Session State
if "keywords" not in st.session_state:
    st.session_state.keywords = ["charity", "fundraising", "nonprofit"]

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
            company = "Unknown"
            link = link_el["href"]
            if not link.startswith("http"):
                link = base + link
            jobs.append({"title": title, "company": company, "link": link, "source": "CharityJob"})
        return jobs
    except:
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
            if not link.startswith("http"):
                link = base + link
            jobs.append({"title": title, "company": "Unknown", "link": link, "source": "Reed"})
        return jobs
    except:
        return []


# ------------------- Sidebar -------------------
with st.sidebar:
    st.header("⚙️ Settings")
    email = st.text_input("Your Email for Alerts", "")
    st.subheader("Keywords")
    
    new_kw = st.text_input("Add Keyword", "")
    if st.button("Add") and new_kw.strip():
        kw = new_kw.strip().lower()
        if kw not in st.session_state.keywords:
            st.session_state.keywords.append(kw)
            st.rerun()
    
    for kw in st.session_state.keywords[:]:
        col1, col2 = st.columns([4,1])
        col1.write(f"• {kw}")
        if col2.button("Remove", key=kw):
            st.session_state.keywords.remove(kw)
            st.rerun()

# ------------------- Main -------------------
st.subheader("Search Jobs")
location = st.text_input("Location", "West Yorkshire")

if st.button("🔍 Search Jobs", type="primary", use_container_width=True):
    with st.spinner("Searching CharityJob and Reed..."):
        all_jobs = []
        seen = set()

        for kw in st.session_state.keywords:
            st.info(f"Searching for **{kw}**")
            
            for loc in [location, "remote"]:
                jobs1 = get_charityjob_jobs(kw, loc)
                jobs2 = get_reed_jobs(kw, loc)
                
                for job in jobs1 + jobs2:
                    if job["link"] not in seen:
                        seen.add(job["link"])
                        all_jobs.append(job)
            
            time.sleep(1)

        if all_jobs:
            st.success(f"✅ Found **{len(all_jobs)}** jobs on {date.today()}")
            for job in all_jobs[:20]:
                with st.expander(f"**{job['title']}** — {job['source']}"):
                    st.markdown(f"[🔗 View Job]({job['link']})")
        else:
            st.warning("No jobs found.")

st.caption("Email alert feature will be added once this version is stable.")
