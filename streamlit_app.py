import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Haunted House Hub", layout="wide", page_icon="🛠️")

# --- SECURE DATA FETCH ---
def get_google_data(sheet_id, tab_name):
    try:
        # Pulls credentials from Streamlit Secrets
        creds_info = st.secrets["gcp_service_account"]
        scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        
        # Open the sheet and get data
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.worksheet(tab_name)
        df = pd.DataFrame(worksheet.get_all_records())
        
        # Standardize column names to lowercase to prevent "KeyErrors"
        df.columns = [c.strip().lower() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error loading tab '{tab_name}': {e}")
        return pd.DataFrame()

# --- CONFIGURATION ---
# The ID of the sheet the bot can see (where your script is pushing data)
SHEET_ID = "1FuzDffAF4O1zinFsXgyHdvt9iSL91vutrosv_v727_U" 

# Date of your next competition
COMP_DATE = datetime(2027, 1, 10) 

# --- CUSTOM STYLING (CSS) ---
st.markdown("""
    <style>
    .task-card { background: rgba(255, 255, 255, 0.05); padding: 12px; border-radius: 8px; border-left: 5px solid #4F8BF9; margin-bottom: 10px; }
    .news-card { background: rgba(79, 139, 249, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #4F8BF9; margin-bottom: 10px; }
    .bday-card { background: rgba(255, 105, 180, 0.1); padding: 12px; border-radius: 8px; border: 1px solid #FF69B4; margin-bottom: 8px; }
    .quote-box { background: rgba(255, 255, 255, 0.03); padding: 25px; border-radius: 15px; border: 1px solid #4F8BF9; text-align: center; font-style: italic; margin-bottom: 25px; }
    .prio-high { border-left-color: #FF4B4B !important; }
    .prio-medium { border-left-color: #FFA500 !important; }
    </style>
""", unsafe_allow_html=True)

# --- DASHBOARD LOGIC ---
now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
st.title("🛠️ Haunted House Dashbaord")
st.subheader(datetime.now().strftime("%A, %d %B %Y"))

# 1. QUOTE OF THE DAY
quotes_df = get_google_data(SHEET_ID, "Quotes")
if not quotes_df.empty:
    q = quotes_df.sample(n=1).iloc[0]
    st.markdown(f"""
    <div class="quote-box">
        <h2 style="color: #4F8BF9; margin: 0;">“{q.get('quote', 'Keep Pushing!')}”</h2>
        <p style="color: #BDC3C7; margin-top: 10px;">— {q.get('author', 'Team')}</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Main Layout: 2 Columns
col_main, col_side = st.columns([2, 1])

with col_main:
    # 2. ACTIVE TASKS
    st.header("📋 Active Tasks")
    tasks_df = get_google_data(SHEET_ID, "Active Tasks")
    
    if not tasks_df.empty:
        # Filter out "Done" tasks locally
        active_tasks = tasks_df[tasks_df['status'].str.lower() != 'done']
        
        if active_tasks.empty:
            st.success("All tasks complete! Great job team.")
        else:
            for _, row in active_tasks.iterrows():
                prio = str(row.get('priority', '')).lower()
                prio_class = "prio-high" if prio == "high" else "prio-medium" if prio == "medium" else ""
                
                st.markdown(f"""
                <div class="task-card {prio_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold; font-size: 1.1em;">{row.get('task', 'Unnamed Task')}</span>
                        <span style="font-size: 0.85em; background: rgba(255,255,255,0.1); padding: 2px 10px; border-radius: 12px;">
                            👤 {row.get('lead', 'Open')}
                        </span>
                    </div>
                    <div style="font-size: 0.85em; color: #BDC3C7; margin-top: 5px;">
                        Status: {row.get('status', 'In Progress')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Task list is empty.")

with col_side:
    # 3. TEAM NEWS
    st.header("📢 News")
    news_df = get_google_data(SHEET_ID, "News")
    if not news_df.empty:
        for _, row in news_df.iterrows():
            st.markdown(f"""
            <div class="news-card">
                <b>{row.get('headline', 'Update')}</b><br>
                <p style="font-size: 0.9em; margin-top: 5px;">{row.get('content', '')}</p>
            </div>
            """, unsafe_allow_html=True)

    # 4. BIRTHDAYS (Euro Format)
    st.header("🎂 Birthdays")
    bdays_df = get_google_data(SHEET_ID, "Birthdays")
    found_bday = False
    
    if not bdays_df.empty:
        for _, row in bdays_df.iterrows():
            try:
                # Use dayfirst=True for European DD/MM format
                bdate = pd.to_datetime(row['date'], dayfirst=True).replace(hour=0, minute=0, second=0, microsecond=0)
                bdate_this_year = bdate.replace(year=now.year)
                
                if bdate_this_year < now:
                    bdate_this_year = bdate_this_year.replace(year=now.year + 1)
                
                days_until = (bdate_this_year - now).days
                
                if 0 <= days_until <= 7:
                    color = "#FFD700" if days_until == 0 else "#FF69B4"
                    status = "✨ TODAY!" if days_until == 0 else f"In {days_until} days"
                    st.markdown(f"""
                    <div class="bday-card" style="border-left: 5px solid {color};">
                        <b>{row.get('name')}</b> — {status}<br>
                        <small>{bdate_this_year.strftime('%d %B')}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    found_bday = True
            except: continue
            
    if not found_bday:
        st.write("No birthdays this week.")

    st.divider()
    
    # 5. COUNTDOWN
    st.header("⏳ Competition")
    days_to_comp = (COMP_DATE - datetime.now()).days
    st.metric("Days until kick-off", f"{max(0, days_to_comp)}")

# --- REFRESH ---
if st.button("🔄 Refresh Dashboard"):
    st.rerun()