import streamlit as st
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from urllib.parse import quote_plus
def get_jobs(keyword, location):
    """Return a list of job dicts from Indeed for a given keyword/location."""
    from urllib.parse import urlencode
    keyword = (keyword or "").strip()
    location = (location or "").strip()

    # build the URL safely
    query_string = urlencode({"q": f"{keyword} {location}", "sort": "date"})
    url = f"[uk.indeed.com](https://uk.indeed.com/jobs?{query_string})"

    # double‑check what URL was built (for debugging)
    print("Fetching:", url)
    st.write("DEBUG URL:", url)
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()   # will crash clearly if site is unreachable
    soup = BeautifulSoup(resp.text, "html.parser")

    jobs = []
    for card in soup.select("a.tapItem"):
        title_el = card.select_one("h2")
        if not title_el:
            continue
        company_el = card.select_one(".companyName")
        jobs.append({
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "Unknown",
            "link": "[uk.indeed.com](https://uk.indeed.com)" + card.get("href", "")
        })
    return jobs




def send_email(from_addr, app_pass, to_addr, jobs, location):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Charity & Remote Jobs – {location} – {date.today()}"
    msg["From"] = from_addr
    msg["To"] = to_addr
    html = "<h3>New Jobs</h3><ul>"
    for j in jobs:
        html += f"<li><b>{j['title']}</b> — {j['company']}<br><a href='{j['link']}'>Apply</a></li>"
    html += "</ul>"
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(from_addr, app_pass)
        s.send_message(msg)

st.title("💼 Charity & Remote Job Finder")
keywords = st.text_input("Keywords (comma separated)", "charity, fundraising")
location = st.text_input("Location", "West Yorkshire")
gmail = st.text_input("Your Gmail address")
app_password = st.text_input("Gmail App Password", type="password")
send_to = st.text_input("Send results to (leave blank to use Gmail address)")
if st.button("Search and Email Jobs"):
    all_jobs = []
    for k in [k.strip() for k in keywords.split(",") if k.strip()]:
        all_jobs += get_jobs(k, location)
        all_jobs += get_jobs(k, "remote")
    if all_jobs:
        send_email(gmail, app_password, send_to or gmail, all_jobs, location)
        st.success(f"✅ Sent {len(all_jobs)} jobs to {send_to or gmail}")
    else:
        st.warning("No jobs found.")
