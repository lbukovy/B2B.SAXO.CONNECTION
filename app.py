import os, io, time, random, requests
from requests.exceptions import SSLError
import pandas as pd
import streamlit as st

# --- PAGE CONFIG (musí byť ako prvý streamlit príkaz) ---
st.set_page_config(page_title="B2B | SAXO CONNECTION", layout="wide", page_icon="Saxo-Capital-Markets.png")

# --- PASSWORD GATE ---
def _load_password():
    try:
        return st.secrets["APP_PASSWORD"]
    except Exception:
        return os.getenv("APP_PASSWORD", "")

APP_PASSWORD = _load_password()

def require_password():
    if not APP_PASSWORD:
        return  # dev mód bez hesla
    def password_entered():
        if st.session_state.get("_password","") == APP_PASSWORD:
            st.session_state["auth_ok"] = True
            st.session_state.pop("_password", None)
        else:
            st.session_state["auth_ok"] = False
    if not st.session_state.get("auth_ok", False):
        st.image("Saxo-Capital-Markets.png", width=120)
        st.markdown("### B2B.saxo.connection — Login")
        st.text_input("Password", type="password", key="_password", on_change=password_entered)
        if st.session_state.get("auth_ok") is False:
            st.error("Nesprávne heslo.")
        st.stop()

require_password()

# --- CONFIGURATION ---
def _load_excel_url():
    try:
        return st.secrets["EXCEL_URL"]  # Render → Environment (odporúčané)
    except Exception:
        return os.getenv("EXCEL_URL", "https://data.saxoconnection.com/FIX_API_CT147572INET.xlsx")

EXCEL_URL = _load_excel_url()
LOGO_PATH = "Saxo-Capital-Markets.png"

# --- HEADER ---
st.image(LOGO_PATH, width=150)
st.title("B2B.SAXO.CONNECTION")
st.caption("Secure data viewer for banking & account structure")

# --- INPUT ---
query = st.text_input("Enter your query (e.g. STATUS ABC123, CLIENT/ACCOUNT 147572INET/C...) ")

# --- NETWORK HELPER (HTTPS -> HTTP fallback pri self-signed) ---
def _fetch_bytes(url: str) -> bytes:
    try:
        r = requests.get(url, timeout=20)  # verify=True default
