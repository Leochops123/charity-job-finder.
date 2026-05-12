import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from datetime import date

st.title("💼 Charity & UK Job Finder (CharityJob + Reed)")
st.write(
    "Searches current vacancies from CharityJob and Reed across the UK. "
    "Enter keywords and a location (e.g. West Yorkshire or remote)."
)

# ---------- SCRAPERS ----------

def get_charityjob_jobs(keyword, location):
    """Scrape jobs from CharityJob UK."""
    keyword = (keyword or "").strip().replace(" ", "-")
    location = (location or "").strip().replace(" ", "-")
    url = f"[charityjob.co.uk](https://www.charityjob.co.uk/jobs/{keyword}/{location}?sort=Date)"

    st.write("Fetching from CharityJob:", url)
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
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


def get_reed_jobs(keyword, location):
    """Scrape jobs from Reed UK."""
    keyword = (keyword or "").strip().replace(" ", "-")
    location = (location or "").strip().replace(" ", "-")
    url = f"[reed.co.uk](https://www.reed.co.uk/jobs/{quote_plus(keyword)}-jobs-in-{quote_plus(location)})"

    st.write("Fetching from Reed:", url)
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    jobs = []
    for card in soup.select("article.job-result-card"):
        link_tag = card.select_one("a.job-block-link")
        if not link_tag:
            continue
        title = link_tag.get_text(strip=True)
        company = card.select_one(".gtmJobListingPostedBy")
        company_name = company.get_text(strip=True) if company else "Unknown"
        jobs.append({
            "source": "Reed",
            "title": title,
            "company": company_name,
            "link": "[reed.co.uk](https://www.reed.co.uk)" + link_tag["href"]
        })
    return jobs


# ---------- STREAMLIT USER INTERFACE ----------

st.subheader("Enter search details")

keywords_input = st.text_input("Keywords (comma separated)", "charity, fundraising")
location_input = st.text_input("Location", "West Yorkshire")

if st.button("Search Jobs"):
    st.info("Searching… please wait 10–20 seconds.")
    keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
    all_jobs = []

    for kw in keywords:
        try:
            charity_local = get_charityjob_jobs(kw, location_input)
            charity_remote = get_charityjob_jobs(kw, "remote")
            reed_local = get_reed_jobs(kw, location_input)
            reed_remote = get_reed_jobs(kw, "remote")
            total = charity_local + charity_remote + reed_local + reed_remote
            all_jobs += total
            st.write(f"Fetched {len(total)} jobs for '{kw}'.")
        except Exception as e:
            st.error(f"Error while fetching '{kw}': {e}")

    if all_jobs:
        st.success(f"✅ Found {len(all_jobs)} total jobs on {date.today()}")
        for job in all_jobs[:25]:
            st.markdown(
                f"**{job['title']}** — {job['company']} ({job['source']})  \n"
                f"[View job posting]({job['link']})"
            )
            st.markdown("---")
    else:
        st.warning("No jobs found for your search terms today.")
