import streamlit as st
from datetime import date

st.set_page_config(page_title="Charity Job Finder", layout="wide")

st.title("💼 Charity & UK Job Finder + Email Alerts")
st.success("✅ App loaded successfully!")

st.write("Current date:", date.today())

st.subheader("Test Section")
location = st.text_input("Location", "West Yorkshire")
keywords = st.multiselect("Keywords", ["charity", "fundraising", "nonprofit", "trustee"], default=["charity"])

if st.button("Search Jobs"):
    st.info("This is a test. Full scraping will be added once this loads.")
    st.balloons()

st.caption("If you can see this message, the app is working.")
