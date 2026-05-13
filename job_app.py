import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
from typing import List, Dict

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder")
st.success("✅ Last 24 Hours • Multi-Source • Fixed")

if "custom_sources" not in st.session_state:
    st.session_state.custom_sources = [
        {"name": "CharityJob", "active": True},
        {"name": "Indeed", "active": True},
        {"name": "Third Sector", "active": True},
    ]

def scrape_charityjob(keyword, location):
    try:
        url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(keyword)}&Sort=Date"
        if location and location.lower() not in ["any", "anywhere"]:
            url += f"&Location={quote_plus(location)}"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []
        for card in soup.select("div.job-result, article")[:12]:
            a = card.select_one("a[href*='/jobs/']")
            if a:
                title = a.get_text(strip=True)
                if len(title) > 10:
                    link = a["href"]
                    full = "https://www.charityjob.co.uk" + link if link.startswith("/") else link
                    jobs.append({"title": title, "link": full, "source": "CharityJob"})
        return jobs
    except:
        return []

def scrape_indeed(keyword, location):
    try:
        url = f"https://uk.indeed.com/jobs?q={quote_plus(keyword)}&l={quote_plus(location)}&sort=date"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []
        for card in soup.select("div.job_seen_beacon")[:12]:
            a = card.select_one("h2 a")
            if a:
                title = a.get_text(strip=True)
                link = a.get("href", "")
                if link.startswith("/"):
                    link = "https://uk.indeed.com" + link
                jobs.append({"title": title, "link": link, "source": "Indeed"})
        return jobs
    except:
        return []

def scrape_thirdsector(keyword):
    try:
        url = f"https://jobs.thirdsector.co.uk/jobs?keywords={quote_plus(keyword)}"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []
        for card in soup.select("article, div.job")[:10]:
            a = card.select_one("a[href*='/job']")
            if a:
                title = a.get_text(strip=True)
                if len(title) > 15:
                    link = a["href"]
                    full = "https://jobs.thirdsector.co.uk" + link if link.startswith("/") else link
                    jobs.append({"title": title, "link": full, "source": "Third Sector"})
        return jobs
    except:
        return []

with st.sidebar:
    st.header("Settings")
    location = st.text_input("Location", "West Yorkshire", key="loc")

st.subheader("🔍 Search Jobs Posted in Last 24 Hours")

if st.button("🔍 Search Last 24 Hours", type="primary", use_container_width=True):
    with st.spinner("Searching..."):
        all_jobs = []
        for source in st.session_state.custom_sources:
            if not source.get("active"):
                continue
            st.info(f"Scanning {source['name']}...")
            
            if source["name"] == "CharityJob":
                jobs = scrape_charityjob("manager", location)
            elif source["name"] == "Indeed":
                jobs = scrape_indeed("manager", location)
            elif source["name"] == "Third Sector":
                jobs = scrape_thirdsector("manager")
            else:
                jobs = []
            
            all_jobs.extend(jobs)
            time.sleep(1)

        if all_jobs:
            st.success(f"Found {len(all_jobs)} jobs")
            for job in all_jobs[:25]:
                with st.expander(f"{job['title']} — {job['source']}"):
                    st.markdown(f"[🔗 View Job]({job['link']})")
        else:
            st.warning("No jobs found this time.")

st.caption("✅ Clean & Fixed Version")
