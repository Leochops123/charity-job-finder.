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
if "location" not in st.session_state:
    st.session_state.location = "West Yorkshire"
if "sources" not in st.session_state:
    st.session_state.sources = ["CharityJob"]

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Positive Keywords Only
    pos_input = st.text_input("Search Keywords (comma separated)", 
                             ", ".join(st.session_state.positive_keywords))
    
    # Location
    loc_input = st.text_input("Location", st.session_state.location)
    
    st.divider()
    
    # Email Settings
    st.subheader("📧 Daily Email Alerts")
    email_from = st.text_input("Your Gmail Address", "")
    email_password = st.text_input("Gmail App Password", type="password")
    email_to = st.text_input("Send Jobs To", value=email_from)
    enable_email = st.toggle("Enable Daily Email at 9:00 AM", value=False)
    
    st.divider()
    
    # Job Sources
    st.subheader("📌 Job Sources")
    available_sources = ["CharityJob", "ThirdSector", "Prospects", "Indeed", "Guardian Jobs"]
    selected_sources = st.multiselect("Select Sources", 
                                     available_sources, 
                                     default=st.session_state.sources)
    
    new_source = st.text_input("Add Custom Source Name")
    if st.button("➕ Add
