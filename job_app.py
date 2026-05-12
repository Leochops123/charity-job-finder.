import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from datetime import date

st.title("💼 Charity & Remote Job Finder (Indeed + CharityJob)")
st.write(
    "Searches live vacancies from Indeed UK and CharityJob. "
    "Displays the latest results for your keywords and location."
)

# ---------- SCRAPERS ----------

def get_indeed_jobs(keyword, location):
    """Scrape jobs from Indeed UK (fully qualified https URLs)."""
    keyword = (keyword or "").strip()
    location = (location or "").strip()

    params = {"q": f"{keyword} {location}", "sort": "date"}
    base_url = "[uk.indeed.com](https://uk.indeed.com/jobs)"
    url = f"{base_url}?{urlencode(params)}"

    st.write("Fetching from Indeed:", url)

    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
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
            "link": "[uk.indeed.com](https://uk.indeed.com)" + card.get("href", "")
        })
    return jobs


def get_charityjob_jobs(keyword, location):
    """Scrape jobs from CharityJob UK."""
    keyword = (keyword or "").strip().replace(" ", "-")
    location = (location or "").strip().replace(" ", "-")

    url = f"[charityjob.co.uk](https://www.charityjob.co.uk/jobs/{keyword}/{location}?sort=Date)"
    st.write("Fetching from CharityJob:", url)

    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    jobs = []
    for card in soup.select(".job-result"):
        link_el = card.select_one("h2 a")
        if not link_el:
            continue
        company_el = card.select_one(".job-result__org")
        jobs.append({
            "source": "CharityJob",
            "title": link_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "Unknown",
            "link": "[charityjob.co.uk](https://www.charityjob.co.uk)" + link_el["href"]
        })
    return jobs


# ---------- STREAMLIT INTERFACE ----------

st.subheader("Enter search details")

keywords_input = st.text_input("Keywords (comma separated)", "charity, fundraising")
location_input = st.text_input("Location", "West Yorkshire")

if st.button("Search Jobs"):
    st.info("Searching… please wait 10–20 seconds.")
    keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
    all_jobs = []

    for kw in keywords:
        try:
            # Local roles
            all_jobs += get_indeed_jobs(kw, location_input)
            all_jobs += get_charityjob_jobs(kw, location_input)
            # Remote roles
            all_jobs += get_indeed_jobs(kw, "remote")
            all_jobs += get_charityjob_jobs(kw, "remote")
        except Exception as e:
            st.error(f"Error while fetching {kw}: {e}")

    if all_jobs:
        st.success(f"✅ Found {len(all_jobs)} jobs on {date.today()}")
        for job in all_jobs[:25]:  # show first 25 results
            st.markdown(
                f"**{job['title']}** — {job['company']} ({job['source']})  \n"
                f"[Apply here]({job['link']})"
            )
            st.markdown("---")
    else:
        st.warning("No jobs found for your search terms today.")

