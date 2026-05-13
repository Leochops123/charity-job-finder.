import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import json
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder")
st.success("Ultra Clean Version - With Email Alerts")

# ===================== SESSION STATE =====================
if "positive_keywords" not in st.session_state:
    st.session_state.positive_keywords = ["fundraising", "manager", "officer", "coordinator"]
if "negative_keywords" not in st.session_state:
    st.session_state.negative_keywords = ["senior", "director", "head of", "intern", "volunteer"]
if "location" not in st.session_state:
    st.session_state.location = "West Yorkshire"

# ===================== SIDEBAR CONFIG =====================
with st.sidebar:
    st.header("⚙️ Settings")
    
    pos_kw = st.text_input("Positive Keywords (comma separated)", 
                          ", ".join(st.session_state.positive_keywords))
    neg_kw = st.text_input("Keywords to Filter Out (exclude)", 
                          ", ".join(st.session_state.negative_keywords))
    location = st.text_input("Location", st.session_state.location)
    
    st.divider()
    st.subheader("📧 Daily Email (9 AM)")
    email_from = st.text_input("Your Email (Gmail recommended)", "")
    email_password = st.text_input("Gmail App
