import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from datetime import date
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict

st.set_page_config(page_title="Charity Job Finder", layout="wide")

st.title("💼 Charity & UK Job Finder + Email Alerts")
st.caption("Search jobs and send results to your email")

# ------------------- Session State -------------------
if "keywords" not in st.session_state:
    st.session_state.keywords = ["charity", "fundraising", "nonprofit"]
if "email" not in st.session_state:
    st.session_state.email = ""

# ------------------- Email Sender Function -------------------
def send_job_email(receiver_email: str, jobs: List[Dict], location: str):
    if not jobs:
        return False
    
    sender_email = st.secrets.get("EMAIL_ADDRESS")      # e.g. yourgmail@gmail.com
    password = st.secrets.get("EMAIL_PASSWORD")         # App Password (NOT regular password)

    if not sender_email or not password:
        st.error("Email credentials not configured in secrets. Contact the owner.")
        return False

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"New Charity Jobs Found - {date.today()} ({len(jobs)} jobs)"

    # Build HTML email
    html = f"""
    <h2>Job Updates for {location}</h2>
    <p>
