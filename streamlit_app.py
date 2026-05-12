import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Team Hub", layout="wide")

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
        # Standardize column names
        df.columns = [c.strip().lower() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error loading {tab_name}: {e}")
        return pd.DataFrame()

# --- CONFIG ---
# Replace with your actual Sheet ID from the URL
SOCIAL_SHEET_ID = "1FuzDffAF4O1zinFsXgyHdvt9iSL91vutrosv_v727_U" 
# Replace with your actual competition date
COMP_DATE = datetime(2026, 3, 15) 

# --- STYLING ---
st.markdown("""
    <style>
    .news-card { background: rgba(79, 139, 249, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #4F8BF9; margin-bottom: 10px; }
    .bday-card { background: rgba(255, 105, 180, 0.1); padding: 12px; border-radius: 8px; border: 1px solid #FF69B4; margin-bottom: 8px; }
    .quote-box { background: rgba(255, 255, 255, 0.03); padding: 30px; border-radius: 15px; border: 1px solid #4F8BF9; text-align: center; font-style: italic; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- APP START ---
now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
st.title("🛠️ Team Command Center")
st.subheader(datetime.now().strftime("%A, %d %B %Y"))

# 1. QUOTE SECTION
quotes_df = get_google_data(SOCIAL_SHEET_ID, "Quotes")
if not quotes_df.empty:
    q = quotes_df.sample(n=1).iloc[0]
    st.markdown(f"""
    <div class="quote-box">
        <h2 style="color: #4F8BF9; margin: 0;">“{q.get('quote', 'Build robots, build people.')}”</h2>
        <p style="color: #BDC3C7; margin-top: 10px;">— {q.get('author', 'Team Tradition')}</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

col_left, col_right = st.columns([2, 1])

with col_left:
    # 2. NEWS SECTION
    st.header("📢 Team News")
    news_df = get_google_data(SOCIAL_SHEET_ID, "News")
    if not news_df.empty:
        for _, row in news_df.iterrows():
            st.markdown(f"""
            <div class="news-card">
                <b style="font-size: 1.1em;">{row.get('headline', 'Update')}</b><br>
                <p style="margin-top: 5px;">{row.get('content', '')}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("No news updates for today.")

with col_right:
    # 3. BIRTHDAYS SECTION
    st.header("🎂 Birthdays")
    bdays_df = get_google_data(SOCIAL_SHEET_ID, "Birthdays")
    found_bday = False
    
    if not bdays_df.empty:
        for _, row in bdays_df.iterrows():
            try:
                # Force Euro formatting (Day-Month-Year)
                bdate_raw = pd.to_datetime(row['date'], dayfirst=True)
                # Strip time for pure date comparison
                bdate_clean = bdate_raw.replace(year=now.year, hour=0, minute=0, second=0, microsecond=0)
                
                # If date already passed this year, look at next year
                if bdate_clean < now:
                    bdate_clean = bdate_clean.replace(year=now.year + 1)
                
                days_until = (bdate_clean - now).days
                
                # Logic: Today (0) through next 7 days
                if 0 <= days_until <= 7:
                    status = "✨ TODAY!" if days_until == 0 else f"In {days_until} days"
                    color = "#FFD700" if days_until == 0 else "#FF69B4"
                    
                    st.markdown(f"""
                    <div class="bday-card" style="border-left: 5px solid {color};">
                        <b style="font-size: 1.1em;">{row.get('name', 'Unknown')}</b><br>
                        <span style="color: {color};">{status}</span> • {bdate_clean.strftime('%d %b')}
                    </div>
                    """, unsafe_allow_html=True)
                    found_bday = True
            except Exception as e:
                continue # Skip invalid date rows
                
    if not found_bday:
        st.write("No birthdays this week.")

    st.divider()
    
    # 4. COUNTDOWN
    st.header("⏳ Countdown")
    days_left = (COMP_DATE - datetime.now()).days
    st.metric("Days to Competition", f"{max(0, days_left)}")

# 5. REFRESH BUTTON
if st.button("🔄 Sync with Google Sheets"):
    st.rerun()