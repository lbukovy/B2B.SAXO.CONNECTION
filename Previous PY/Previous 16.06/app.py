
import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import time
import random

# --- CONFIGURATION ---
EXCEL_URL = "https://saxoconnection.com/data/FIX_API_CT147572INET.xlsx"

# --- PAGE SETUP ---
st.set_page_config(page_title="B2B | SAXO CONNECTION", layout="centered")
st.image("static/logo.png", width=130)
st.markdown("<h1 style='font-size:2.2rem;'>B2B.SAXO.CONNECTION</h1>", unsafe_allow_html=True)
st.caption("Secure data viewer for banking & account structure")

# --- INPUT ---
query = st.text_input("Enter your query (e.g. STATUS ABC123, CLIENT/ACCOUNT 147572INET/C...) ")

# --- FUNCTION TO LOAD DATA ---
@st.cache_data(ttl=300)
def load_excel():
    response = requests.get(EXCEL_URL, verify=False)
    xls = pd.ExcelFile(BytesIO(response.content))
    sheets = {
        "STATUS": xls.parse("STATUS"),
        "ACCOUNT": xls.parse("ACCOUNT"),
        "CLIENT": xls.parse("CLIENT"),
        "CLIENTACCOUNT": xls.parse("CLIENTACCOUNT"),
    }
    return sheets

# --- SIMULATED LOADING ---
def simulated_loading():
    duration = random.randint(5, 20)
    with st.spinner(f"Loading data... Please wait up to {duration} seconds..."):
        time.sleep(duration)

# --- DISPLAY CARD STYLE ---
def display_card(row):
    for label, value in row.items():
        st.markdown(f"**{label}:** {value}")

# --- MAIN LOGIC ---
def handle_query(query):
    sheets = load_excel()
    query = query.strip()

    if query.startswith("STATUS "):
        ref = query.replace("STATUS ", "").strip()
        df = sheets["STATUS"]
        if "Reference" in df.columns and "Status" in df.columns:
            row = df[df["Reference"] == ref]
            if not row.empty:
                st.success(row.iloc[0]["Status"])
                return
        st.error("No matching reference found.")

    elif query.startswith("CLIENT/ACCOUNT "):
        val = query.replace("CLIENT/ACCOUNT ", "").strip()
        df = sheets["CLIENTACCOUNT"]
        row = df[df.apply(lambda x: val in x.values, axis=1)]
        if not row.empty:
            st.subheader("Client Account Info")
            display_card(row.iloc[0])
            return
        st.error("No matching CLIENTACCOUNT data found.")

    elif query.startswith("ACCOUNT "):
        val = query.replace("ACCOUNT ", "").strip()
        df = sheets["ACCOUNT"]
        row = df[df.apply(lambda x: val in x.values, axis=1)]
        if not row.empty:
            st.subheader("Account Info")
            display_card(row.iloc[0])
            return
        st.error("No matching ACCOUNT data found.")

    elif query.startswith("CLIENT "):
        val = query.replace("CLIENT ", "").strip()
        df = sheets["CLIENT"]
        row = df[df.apply(lambda x: val in x.values, axis=1)]
        if not row.empty:
            st.subheader("Client Info")
            display_card(row.iloc[0])
            return
        st.error("No matching CLIENT data found.")

    else:
        st.warning("Please enter a valid query like STATUS ..., CLIENT ..., ACCOUNT ..., CLIENT/ACCOUNT ...")

# --- PROCESS QUERY ---
if query:
    simulated_loading()
    handle_query(query)
