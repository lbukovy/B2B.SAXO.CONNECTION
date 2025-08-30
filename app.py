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
        r.raise_for_status()
        return r.content
    except SSLError:
        if url.startswith("https://"):
            alt = "http://" + url[len("https://"):]
            r = requests.get(alt, timeout=20)
            r.raise_for_status()
            return r.content
        raise

# --- DATA LOADER (čistí Unnamed stĺpce) ---
@st.cache_data(ttl=300)
def load_excel():
    content = _fetch_bytes(EXCEL_URL)
    xls = pd.ExcelFile(io.BytesIO(content), engine="openpyxl")
    sheets = {}
    for name in xls.sheet_names:
        df = xls.parse(name, dtype=str)
        df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
        sheets[name] = df
    return sheets

def get_sheet_by_name(sheets: dict, wanted: str):
    w = wanted.strip().upper()
    for name, df in sheets.items():
        if name.strip().upper() == w:
            return df
    return None

# --- UX: simulované načítanie (aby bol feedback) ---
def simulated_loading():
    duration = random.randint(4, 10)
    with st.spinner(f"Loading data... Please wait up to {duration} seconds..."):
        time.sleep(duration)

# --- MAIN LOGIC (presné routovanie na listy) ---
def handle_query(query: str):
    sheets = load_excel()
    q = query.strip()

    # STATUS -> len STATUS
    if q.startswith("STATUS "):
        ref = q.replace("STATUS ", "", 1).strip()
        df = get_sheet_by_name(sheets, "STATUS")
        if df is None:
            st.error("Sheet 'STATUS' not found.")
            return
        if "Reference" in df.columns and "Status" in df.columns:
            row = df[df["Reference"] == ref]
            if not row.empty:
                st.success(row.iloc[0]["Status"])
                return
        st.error("No matching reference found in 'STATUS'.")
        return

    # ACCOUNT -> len ACCOUNT
    if q.startswith("ACCOUNT "):
        val = q.replace("ACCOUNT ", "", 1).strip()
        df = get_sheet_by_name(sheets, "ACCOUNT")
        if df is None:
            st.error("Sheet 'ACCOUNT' not found.")
            return
        if "Account" in df.columns:
            row = df[df["Account"] == val]
            if row.empty:
                row = df[df.apply(lambda x: val in x.values, axis=1)]
        else:
            row = df[df.apply(lambda x: val in x.values, axis=1)]
        if not row.empty:
            st.dataframe(row, use_container_width=True)
        else:
            st.error("No matching account in 'ACCOUNT'.")
        return

    # CLIENT/ACCOUNT -> len CLIENTACCOUNT
    if q.startswith("CLIENT/ACCOUNT "):
        val = q.replace("CLIENT/ACCOUNT ", "", 1).strip()
        df = get_sheet_by_name(sheets, "CLIENTACCOUNT")
        if df is None:
            st.error("Sheet 'CLIENTACCOUNT' not found.")
            return
        if "Account" in df.columns:
            row = df[df["Account"] == val]
            if row.empty:
                row = df[df.apply(lambda x: val in x.values, axis=1)]
        else:
            row = df[df.apply(lambda x: val in x.values, axis=1)]
        if not row.empty:
            st.dataframe(row, use_container_width=True)
        else:
            st.error("No matching account info in 'CLIENTACCOUNT'.")
        return

    # CLIENT -> len CLIENT
    if q.startswith("CLIENT "):
        val = q.replace("CLIENT ", "", 1).strip()
        df = get_sheet_by_name(sheets, "CLIENT")
        if df is None:
            st.error("Sheet 'CLIENT' not found.")
            return
        key_cols = [c for c in ["Client ID", "ClientID", "Client"] if c in df.columns]
        if key_cols:
            row = pd.concat([df[df[c] == val] for c in key_cols], axis=0)
        else:
            row = df[df.apply(lambda x: val in x.values, axis=1)]
        if not row.empty:
            st.dataframe(row, use_container_width=True)
        else:
            st.error("No matching client in 'CLIENT'.")
        return

    # TRADELIST
    if q.replace(" ", "").upper() == "TRADELIST":
        df = get_sheet_by_name(sheets, "TRADELIST")
        if df is None:
            st.error("Sheet 'TRADELIST' not found.")
            return
        df = df.copy()
        if "Instrument" in df.columns:
            df["Instrument"] = df["Instrument"].astype(str).str.replace(".lmx", "", regex=False)
        st.subheader("Trade List")
        st.dataframe(df, use_container_width=True)
        return

    st.warning("Please enter a valid query like STATUS …, CLIENT …, ACCOUNT … or CLIENT/ACCOUNT …")

# --- RUN ---
if query:
    simulated_loading()
    handle_query(query)
