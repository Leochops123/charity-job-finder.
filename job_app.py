import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from datetime import date

st.title("💼 Charity & Remote Job Finder (Indeed + CharityJob)")
st.write("Search live vacancies from Indeed and CharityJob in West Yorkshire or UK remote roles.")

# ---------- Scrapers ----------

def get_indeed_jobs(keyword, location):
    """Scrape Indeed UK."""
    params = {"q": f"{keyword} {location}", "sort": "date"}
    base_url = "[uk.indeed.com](https://uk.indeed.com/jobs)"
    url = f"{base_url}?{urlencode(params)}"
    st.write("Fetching Indeed:", url)
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    jobs = []
    for card in soup.select("a.tapItem"):
        title_el = card.select_one("h2")
        if not title_el:
            continue
        company_el = card.select_one(".companyName")
        jobs.append({
            "source": "Indeed",
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "Unknown",
            "link": "[uk.indeed.com](https://uk.indeed.com)" + card["href"]
        })
    return jobs


def get_charityjob_jobs(keyword, location):
    """Scrape CharityJob UK."""
    safe_kw = keyword.replace(" ", "-")
    safe_loc = location.replace(" ", "-")
    url = f"[charityjob.co.uk](https://www.charityjob.co.uk/jobs/{safe_kw}/{safe_loc}?sort=Date)"
    st.write("Fetching CharityJob:", url)
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    jobs = []
    for card in soup.select(".job-result"):
        title_el = card.select_one("h2 a")
        if not title_el:
            continue
        company_el = card.select_one(".job-result__org")
        jobs.append({
            "source": "CharityJob",
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "Unknown",
            "link": "[charityjob.co.uk](https://www.charityjob.co.uk)" + title_el["href"]
        })
    return jobs


# ---------- Streamlit Interface ----------

keywords = st.text_input("Keywords (comma separated)", "charity, fundraising")
location = st.text_input("Location", "West Yorkshire")

if st.button("Search Jobs"):
    st.info("Searching…")
    keywords_list = [k.strip() for k in keywords.split(",") if k.strip()]
    all_jobs = []
    for kw in keywords_list:
        try:
            all_jobs += get_indeed_jobs(kw, location)
            all_jobs += get_charityjob_jobs(kw, location)
            # also remote jobs
            all_jobs += get_indeed_jobs(kw, "remote")
            all_jobs += get_charityjob_jobs(kw, "remote")
        except Exception as e:
            st.error(f"Error for {kw}: {e}")

    if all_jobs:
        st.success(f"✅ Found {len(all_jobs)} jobs on {date.today()}")
        for j in all_jobs[:20]:  # show first 20 results
            st.write(f"**{j['title']}** — {j['company']} ({j['source']})")
            st.write(j['link'])
            st.markdown("---")
    else:
        st.warning("No jobs found today.")

