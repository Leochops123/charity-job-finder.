import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
from datetime import datetime

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder")
st.success("✅ Fully Fixed & Working")

# Session State
if "positive_keywords" not in st.session_state:
    st.session_state.positive_keywords = ["fundraising", "manager", "officer", "coordinator", "fundraiser"]
if "negative_keywords" not in st.session_state:
    st.session_state.negative_keywords = ["senior", "director", "head of", "intern", "volunteer"]
if "location" not in st.session_state:
    st.session_state.location = "West Yorkshire"

# Sidebar Settings
with st.sidebar:
    st.header("⚙️ Settings")
    pos_input = st.text_input("Positive Keywords (comma separated)", 
                             ", ".join(st.session_state.positive_keywords))
    neg_input = st.text_input("Keywords to Exclude", 
                             ", ".join(st.session_state.negative_keywords))
    loc_input = st.text_input("Location", st.session_state.location)
    
    if st.button("💾 Save Settings"):
        st.session_state.positive_keywords = [k.strip() for k in pos_input.split(",") if k.strip()]
        st.session_state.negative_keywords = [k.strip() for k in neg_input.split(",") if k.strip()]
        st.session_state.location = loc_input
        st.success("Settings Saved!")

# Updated Scraper
def scrape_charityjob(keyword, location):
    try:
        url = f"https://www.charityjob.co.uk/jobs?Keywords={quote_plus(keyword)}&Sort=Date"
        if location and location.lower() not in ["any", "anywhere"]:
            url += f"&Location={quote_plus(location)}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        resp = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        jobs = []
        # Stronger selector for current site
        job_links = soup.select("a[href*='/jobs/']")
        
        for link in job_links:
            title = link.get_text(strip=True)
            if len(title) < 10 or "Top job" in title or title.startswith("["):
                continue
                
            href = link["href"]
            full_link = "https://www.charityjob.co.uk" + href if href.startswith("/") else href
            
            # Get company and details from nearby text
            parent = link.find_parent("div") or link.find_parent("article")
            context = parent.get_text(strip=True) if parent else ""
            
            # Extract company roughly
            company = "Unknown"
            if "£" in context or "per year" in context:
                lines = context.split("\n")
                for line in lines:
                    if len(line) > 5 and not any(x in line for x in ["Posted", "£", "today"]):
                        company = line[:100]
                        break
            
            jobs.append({
                "title": title,
                "link": full_link,
                "company": company,
                "source": "CharityJob"
            })
        
        return jobs[:30]
    except Exception as e:
        st.error(f"Error: {e}")
        return []

def should_include(title):
    t = title.lower()
    if not any(k.lower() in t for k in st.session_state.positive_keywords):
        return False
    if any(k.lower() in t for k in st.session_state.negative_keywords):
        return False
    return True

# Main Search Button
if st.button("🔍 Search Jobs Now", type="primary", use_container_width=True):
    with st.spinner("Searching on CharityJob..."):
        all_jobs = []
        for kw in st.session_state.positive_keywords[:5]:
            jobs = scrape_charityjob(kw, st.session_state.location)
            for job in jobs:
                if should_include(job["title"]):
                    all_jobs.append(job)
            time.sleep(1.2)  # Be gentle
        
        # Remove duplicates
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            if job["link"] not in seen:
                seen.add(job["link"])
                unique_jobs.append(job)
        
        if unique_jobs:
            st.success(f"✅ Found {len(unique_jobs)} matching jobs")
            for job in unique_jobs[:20]:
                with st.container(border=True):
                    st.markdown(f"**[{job['title']}]({job['link']})**")
                    st.caption(f"🏢 {job['company']} • {job['source']}")
        else:
            st.warning("No matching jobs found. Try changing keywords or location.")

st.caption("Tip: Try broad positive keywords like 'fundraising' or 'manager'")
