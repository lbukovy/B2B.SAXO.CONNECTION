import os
import streamlit as st

def _load_password():
    # 1) Skús st.secrets (Render/Cloud), 2) potom env var (APP_PASSWORD), 3) inak prázdne
    try:
        return st.secrets["APP_PASSWORD"]
    except Exception:
        return os.getenv("APP_PASSWORD", "")

APP_PASSWORD = _load_password()

def require_password():
    # Ak nie je nastavené heslo, neblokuj (dev mód)
    if not APP_PASSWORD:
        return

    def password_entered():
        if st.session_state.get("_password", "") == APP_PASSWORD:
            st.session_state["auth_ok"] = True
            st.session_state.pop("_password", None)
        else:
            st.session_state["auth_ok"] = False

    if not st.session_state.get("auth_ok", False):
        st.title("B2B.saxo.connection — Login")
        st.text_input("Password", type="password", key="_password", on_change=password_entered)
        if st.session_state.get("auth_ok") is False:
            st.error("Nesprávne heslo.")
        st.stop()

require_password()

import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import time
import random

# --- CONFIGURATION ---
EXCEL_URL = "https://saxoconnection.com/data/FIX_API_CT147572INET.xlsx"
LOGO_PATH = "Saxo-Capital-Markets.png"

# --- PAGE SETUP ---
st.set_page_config(page_title="B2B | SAXO CONNECTION", layout="wide")
st.image(LOGO_PATH, width=150)
st.title("B2B.SAXO.CONNECTION")
st.caption("Secure data viewer for banking & account structure")

# --- INPUT ---
query = st.text_input("Enter your query (e.g. STATUS ABC123, CLIENT/ACCOUNT 147572INET/C...) ")

# --- FUNCTION TO LOAD DATA ---
@st.cache_data(ttl=300)
def load_excel():
    response = requests.get(EXCEL_URL, verify=False)
    xls = pd.ExcelFile(BytesIO(response.content))
    sheets = {sheet: xls.parse(sheet, dtype=str) for sheet in xls.sheet_names}

    return sheets

# --- SIMULATED LOADING ---
def simulated_loading():
    duration = random.randint(5, 20)
    with st.spinner(f"Loading data... Please wait up to {duration} seconds..."):
        time.sleep(duration)

# --- MAIN LOGIC ---
def handle_query(query):
    sheets = load_excel()
    query = query.strip()
    if query.startswith("STATUS "):
        ref = query.replace("STATUS ", "").strip()
        for df in sheets.values():
            if "Reference" in df.columns and "Status" in df.columns:
                row = df[df["Reference"] == ref]
                if not row.empty:
                    st.success(row.iloc[0]["Status"])
                    return
        st.error("No matching reference found.")

    elif query.startswith("ACCOUNT "):
        val = query.replace("ACCOUNT ", "").strip()
        for df in sheets.values():
            if val in df.values:
                row = df[df.apply(lambda x: val in x.values, axis=1)]
                st.dataframe(row, use_container_width=True)
                return
        st.error("No matching IP address found.")

    elif query.startswith("CLIENT/ACCOUNT "):
        val = query.replace("CLIENT/ACCOUNT ", "").strip()
        for df in sheets.values():
            if val in df.values:
                row = df[df.apply(lambda x: val in x.values, axis=1)]
                st.dataframe(row, use_container_width=True)
                return
        st.error("No matching account info found.")

    elif query.startswith("CLIENT "):
        val = query.replace("CLIENT ", "").strip()
        for df in sheets.values():
            if val in df.values:
                row = df[df.apply(lambda x: val in x.values, axis=1)]
                st.dataframe(row, use_container_width=True)
                return
        st.error("No matching client found.")


    elif query.strip().replace(" ", "").upper() == "TRADELIST":
        if "TRADELIST" in sheets:
            df = sheets["TRADELIST"]
            df["Instrument"] = df["Instrument"].astype(str).str.replace(".lmx", "", regex=False)
            st.subheader("Trade List")
            st.dataframe(df)
        else:
            st.error("Sheet 'TRADELIST' not found in the Excel file.")

    else:
        st.warning("Please enter a valid query like STATUS ... or CLIENT ...")

# --- PROCESS QUERY ---
if query:
    simulated_loading()
    handle_query(query)
