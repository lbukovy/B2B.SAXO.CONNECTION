import os, io, time, random, requests
import pandas as pd
import streamlit as st

# musí byť prvý Streamlit príkaz
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
        return
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
        return st.secrets["EXCEL_URL"]             # Render → Environment (odporúčané)
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

# --- DATA LOADER ---
@st.cache_data(ttl=300)
def load_excel():
    r = requests.get(EXCEL_URL, timeout=20)     # verify=True (default)
    r.raise_for_status()
    xls = pd.ExcelFile(io.BytesIO(r.content), engine="openpyxl")
    return {sheet: xls.parse(sheet, dtype=str) for sheet in xls.sheet_names}

# --- SIMULATED LOADING ---
def simulated_loading():
    duration = random.randint(5, 20)
    with st.spinner(f"Loading data... Please wait up to {duration} seconds..."):
        time.sleep(duration)

# --- MAIN LOGIC ---
def handle_query(query):
    sheets = load_excel()
    q = query.strip()

    if q.startswith("STATUS "):
        ref = q.replace("STATUS ", "").strip()
        for df in sheets.values():
            if "Reference" in df.columns and "Status" in df.columns:
                row = df[df["Reference"] == ref]
                if not row.empty:
                    st.success(row.iloc[0]["Status"])
                    return
        st.error("No matching reference found.")

    elif q.startswith("ACCOUNT "):
        val = q.replace("ACCOUNT ", "").strip()
        for df in sheets.values():
            if val in df.values:
                row = df[df.apply(lambda x: val in x.values, axis=1)]
                st.dataframe(row, use_container_width=True)
                return
        st.error("No matching IP address found.")

    elif q.startswith("CLIENT/ACCOUNT "):
        val = q.replace("CLIENT/ACCOUNT ", "").strip()
        for df in sheets.values():
            if val in df.values:
                row = df[df.apply(lambda x: val in x.values, axis=1)]
                st.dataframe(row, use_container_width=True)
                return
        st.error("No matching account info found.")

    elif q.startswith("CLIENT "):
        val = q.replace("CLIENT ", "").strip()
        for df in sheets.values():
            if val in df.values:
                row = df[df.apply(lambda x: val in x.values, axis=1)]
                st.dataframe(row, use_container_width=True)
                return
        st.error("No matching client found.")

    elif q.strip().replace(" ", "").upper() == "TRADELIST":
        if "TRADELIST" in sheets:
            df = sheets["TRADELIST"]
            df["Instrument"] = df["Instrument"].astype(str).str.replace(".lmx", "", regex=False)
            st.subheader("Trade List")
            st.dataframe(df, use_container_width=True)
        else:
            st.error("Sheet 'TRADELIST' not found in the Excel file.")

    else:
        st.warning("Please enter a valid query like STATUS ... or CLIENT ...")

# --- PROCESS QUERY ---
if query:
    simulated_loading()
    handle_query(query)
