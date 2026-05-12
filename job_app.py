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

# ------------------- Session State -------------------
if "keywords" not in st.session_state:
    st.session_state.keywords = ["charity", "fundraising", "nonprofit"]
if "email" not in st.session_state:
    st.session_state.email = ""

# ------------------- Email Sender -------------------
def send_job_email(receiver_email: str, jobs: List[Dict], location: str):
    if not jobs or not receiver_email:
        return False
    
    sender_email = st.secrets.get("EMAIL_ADDRESS")
    password = st.secrets.get("EMAIL_PASSWORD")

    if not sender_email or not password:
        st.error("❌ Email credentials not set in Streamlit Secrets.")
        return False

    # Build job list
    job_items = []
    for job in jobs[:20]:
        job_items.append(
            f"<li><strong>{job['title']}</strong><br>"
            f"{job['company']} • {job['source']}<br>"
            f"<a
