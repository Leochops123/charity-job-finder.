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
        return jobs[:25]
    except:
        return []

with st.sidebar:
    st.header("Filters")
    new_loc = st.text_input("Location", value=st.session_state.location)
    if new_loc != st.session_state.location:
        st.session_state.location = new_loc

    new_kw = st.text_input("Add Keyword")
    if st.button("Add Keyword") and new_kw.strip():
        kw = new_kw.strip().lower()
        if kw not in st.session_state.keywords:
            st.session_state.keywords.append(kw)
            st.rerun()

st.subheader(f"Jobs in {st.session_state.location}")

if st.button("🔍 Search Last 24 Hours", type="primary", use_container_width=True):
    with st.spinner("Searching..."):
        all_jobs = []
        for kw in st.session_state.keywords:
            jobs = scrape_charityjob(kw, st.session_state.location)
            all_jobs.extend(jobs)
            time.sleep(1)
        
        if all_jobs:
            st.success(f"Found {len(all_jobs)} jobs")
            for job in all_jobs[:30]:
                with st.expander(job["title"]):
                    st.markdown("[View Job](" + job["link"] + ")")
        else:
            st.info("No jobs found. Try location = Any")

st.caption("Clean version")
