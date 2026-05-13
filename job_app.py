import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
from typing import List, Dict

st.set_page_config(page_title="Third Sector Job Finder", layout="wide")
st.title("💼 Third Sector & Charity Job Finder")
st.success("✅ Last 24 Hours • Simplified Version")

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("Settings")
    location = st.text_input("📍 Location", "West Yorkshire", key="loc")

# ===================== SCRAPERS =====================
def scrape_charityjob(location):
    try:
        url = "https://www.charityjob.co.uk/jobs?Sort=Date"
        if location and location.lower() not in ["any", "anywhere"]:
            url += f"&Location={quote_plus(location)}"
        
        resp = requests
