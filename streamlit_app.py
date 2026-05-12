import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Team Command Center", layout="wide", initial_sidebar_state="collapsed")

# --- SECURE DATA FETCH ---
def get_google_data(sheet_id, tab_name):
    try:
        creds_info = st.secrets["gcp_service_account"]
        scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id)
        df = pd.DataFrame(sheet.worksheet(tab_name).get_all_records())
        df.columns = [c.strip().lower() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error loading {tab_name}: {e}")
        return pd.DataFrame()

# --- CONFIG ---
SHEET_ID = "1FuzDffAF4O1zinFsXgyHdvt9iSL91vutrosv_v727_U" 
COMP_DATE = datetime(2027, 1, 10) 

# --- STYLING (KIOSK MODE) ---
st.markdown("""
    <style>
    /* Force full screen layout */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        height: 100vh;
        overflow: hidden;
    }
    
    /* Internal scrolling for Task area */
    .scroll-area {
        height: 65vh; 
        overflow-y: auto;
        padding-right: 15px;
    }

    .task-card { 
        background: rgba(255, 255, 255, 0.05); 
        padding: 15px; 
        border-radius: 8px; 
        border-left: 6px solid #4F8BF9; 
        margin-bottom: 12px; 
    }
    .prio-high { border-left-color: #FF4B4B !important; }
    .prio-medium { border-left-color: #FFA500 !important; }
    
    .news-card { background: rgba(79, 139, 249, 0.1); padding: 12px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid #4F8BF9; }
    .bday-card { background: rgba(255, 105, 180, 0.1); padding: 10px; border-radius: 8px; border: 1px solid #FF69B4; margin-bottom: 8px; }
    .quote-box { background: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 15px; border: 1px solid #4F8BF9; text-align: center; font-style: italic; margin-bottom: 15px; }
    
    /* Hide Streamlit elements for clean look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- APP START ---
now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

st.title("🛠️ Team Command Center")

# 1. QUOTE SECTION
quotes_df = get_google_data(SHEET_ID, "Quotes")
if not quotes_df.empty:
    q = quotes_df.sample(n=1).iloc[0]
    st.markdown(f'<div class="quote-box">“{q.get("quote")}” — <b>{q.get("author")}</b></div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1.8, 1])

with col_left:
    st.header("📋 Active Tasks")
    st.markdown('<div class="scroll-area">', unsafe_allow_html=True)
    
    tasks_df = get_google_data(SHEET_ID, "Active Tasks")
    if not tasks_df.empty:
        # Filter for non-completed tasks
        active_tasks = tasks_df[~tasks_df['status'].str.lower().isin(['done', 'completed', 'finished'])]
        
        for _, row in active_tasks.iterrows():
            prio = str(row.get('priority', '')).lower()
            prio_class = "prio-high" if prio == "high" else "prio-medium" if prio == "medium" else ""
            
            # --- THE FIX: Try multiple column names for the person assigned ---
            # It checks 'lead', then 'people', then 'assigned', then defaults to 'Open'
            person = row.get('lead') or row.get('people') or row.get('assigned') or "Open"
            
            st.markdown(f"""
                <div class="task-card {prio_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.2em; font-weight: bold;">{row.get('task', 'Unnamed Task')}</span>
                        <span style="background: #4F8BF9; color: white; padding: 2px 10px; border-radius: 20px; font-size: 0.8em; font-weight: bold;">
                            {person}
                        </span>
                    </div>
                    <div style="font-size: 0.85em; color: #BDC3C7; margin-top: 8px;">
                        Status: {row.get('status', 'In Progress')}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No active tasks found.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    # 2. NEWS & BIRTHDAYS (Combined scroll area)
    st.header("📢 Updates")
    st.markdown('<div class="scroll-area">', unsafe_allow_html=True)
    
    # News
    news_df = get_google_data(SHEET_ID, "News")
    for _, row in news_df.iterrows():
        st.markdown(f'<div class="news-card"><b>{row.get("headline")}</b><br><small>{row.get("content")}</small></div>', unsafe_allow_html=True)
    
    # Birthdays
    st.markdown("### 🎂 Birthdays")
    bdays_df = get_google_data(SHEET_ID, "Birthdays")
    if not bdays_df.empty:
        for _, row in bdays_df.iterrows():
            try:
                bdate = pd.to_datetime(row['date'], dayfirst=True).replace(year=now.year, hour=0, minute=0, second=0)
                if bdate < now: bdate = bdate.replace(year=now.year + 1)
                days_until = (bdate - now).days
                if 0 <= days_until <= 7:
                    color = "#FFD700" if days_until == 0 else "#FF69B4"
                    st.markdown(f'<div class="bday-card" style="border-left: 5px solid {color};"><b>{row.get("name")}</b> ({bdate.strftime("%d %b")})</div>', unsafe_allow_html=True)
            except: continue

    st.markdown('</div>', unsafe_allow_html=True)

# 3. FIXED FOOTER
st.write("---")
f_col1, f_col2, f_col3 = st.columns([1,1,1])
with f_col1:
    days_left = (COMP_DATE - datetime.now()).days
    st.metric("Competition Countdown", f"{max(0, days_left)} Days")
with f_col3:
    if st.button("🔄 Refresh System"):
        st.rerun()