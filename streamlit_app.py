import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- SECURE DATA FETCH ---
def get_google_data(sheet_id, tab_name):
    try:
        # Pulls the "badge" from Streamlit's secret vault
        creds_info = st.secrets["gcp_service_account"]
        scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key(sheet_id)
        df = pd.DataFrame(sheet.worksheet(tab_name).get_all_records())
        df.columns = [c.strip().lower() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()


st.title("🛠️ Team Hub Dashboard")
now = datetime.now()

# 1. QUOTE SECTION
q_df = get_google_data(1913582248, "Quotes")
if not q_df.empty:
    q = q_df.sample(n=1).iloc[0]
    st.markdown(f"> “{q['quote']}” — **{q['author']}**")

col1, col2 = st.columns(2)
with col1:
    st.header("📢 News")
    n_df = get_google_data(0, "News")
    for _, row in n_df.iterrows():
        st.info(f"**{row['headline']}**\n\n{row['content']}")

with col2:
    st.header("🎂 Birthdays")
    b_df = get_google_data(2004163720, "Birthdays")
    # (Simple logic: just show all for now to verify it works)
    for _, row in b_df.iterrows():
        st.write(f"🎈 {row['name']} - {row['date']}")