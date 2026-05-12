import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- SECURE DATA FETCH ---
def get_google_data(sheet_id, tab_name):
    try:
        creds_info = st.secrets["gcp_service_account"]
        scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        
        # This is where the 404 happens if sheet_id is wrong
        sheet = client.open_by_key(sheet_id) 
        
        worksheet = sheet.worksheet(tab_name)
        return pd.DataFrame(worksheet.get_all_records())
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()


SOCIAL_SHEET_ID = "1FuzDffAF4O1zinFsXgyHdvt9iSL91vutrosv_v727_U"

st.title("🛠️ Team Hub Dashboard")
now = datetime.now()

# 1. QUOTE SECTION
q_df = get_google_data(SOCIAL_SHEET_ID, "Quotes")
if not q_df.empty:
    q = q_df.sample(n=1).iloc[0]
    st.markdown(f"> “{q['quote']}” — **{q['author']}**")

col1, col2 = st.columns(2)
with col1:
    st.header("📢 News")
    n_df = get_google_data(SOCIAL_SHEET_ID, "News")
    for _, row in n_df.iterrows():
        st.info(f"**{row['headline']}**\n\n{row['content']}")

with col2:
    st.header("🎂 Birthdays")
b_df = get_google_data(SOCIAL_SHEET_ID, "Birthdays")

if not b_df.empty:
    found_bday = False
    now = datetime.now()
    
    for _, row in b_df.iterrows():
        try:
            # dayfirst=True tells Python to expect DD/MM/YYYY
            bdate = pd.to_datetime(row['date'], dayfirst=True)
            
            # Adjust the year to 'this year' to check if it's coming up
            bdate_this_year = bdate.replace(year=now.year)
            
            # If the birthday already happened this year, check against next year 
            # (useful for late December/early January dates)
            if bdate_this_year < now - timedelta(days=1):
                bdate_this_year = bdate_this_year.replace(year=now.year + 1)
            
            # Calculate days until the birthday
            days_until = (bdate_this_year - now).days
            
            # ONLY SHOW if it's in the next 7 days (or today)
            if 0 <= days_until <= 7:
                st.markdown(f"""
                <div class="bday-card">
                    🎈 <b>{row['name']}</b><br>
                    <span style="font-size: 0.8em;">{bdate_this_year.strftime('%d %B')}</span>
                </div>
                """, unsafe_allow_html=True)
                found_bday = True
        except Exception as e:
            # This skips rows that aren't valid dates
            continue
            
    if not found_bday:
        st.write("No birthdays in the next 7 days.")