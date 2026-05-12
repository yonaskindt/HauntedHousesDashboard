import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Team Hub", layout="wide", initial_sidebar_state="collapsed")

# --- SECURE DATA FETCH ---
def get_google_data(sheet_id, tab_name):
    try:
        creds_info = st.secrets["gcp_service_account"]
        scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id)
        df = pd.DataFrame(sheet.worksheet(tab_name).get_all_records())
        # This turns "Assigned to" into "assigned to"
        df.columns = [c.strip().lower() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error loading {tab_name}: {e}")
        return pd.DataFrame()

# --- CONFIG ---
SHEET_ID = "1FuzDffAF4O1zinFsXgyHdvt9iSL91vutrosv_v727_U" 
COMP_DATE = datetime(2026, 3, 15) 

# --- STYLING (The Layout Fix) ---
st.markdown("""
    <style>
    /* Remove huge top margins */
    .main .block-container {
        padding-top: 1rem !important;
        max-width: 95%;
    }
    
    /* Fixed height scroll areas */
    .scroll-area {
        max-height: 60vh; 
        overflow-y: auto;
        padding-right: 10px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }

    .task-card { 
        background: rgba(255, 255, 255, 0.05); 
        padding: 12px; 
        border-radius: 8px; 
        border-left: 6px solid #4F8BF9; 
        margin-bottom: 10px; 
    }
    .prio-high { border-left-color: #FF4B4B !important; }
    .prio-medium { border-left-color: #FFA500 !important; }
    
    .news-card { background: rgba(79, 139, 249, 0.1); padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #4F8BF9; }
    .bday-card { background: rgba(255, 105, 180, 0.1); padding: 10px; border-radius: 8px; border: 1px solid #FF69B4; margin-bottom: 8px; font-size: 0.9em; }
    .quote-box { background: rgba(255, 255, 255, 0.03); padding: 15px; border-radius: 12px; border: 1px solid #4F8BF9; text-align: center; font-style: italic; margin-bottom: 10px; }
    
    /* Hide Streamlit junk */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- APP START ---
now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

# 1. QUOTE SECTION (Compact)
quotes_df = get_google_data(SHEET_ID, "Quotes")
if not quotes_df.empty:
    q = quotes_df.sample(n=1).iloc[0]
    st.markdown(f'<div class="quote-box">“{q.get("quote")}” — <b>{q.get("author")}</b></div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1.8, 1])

with col_left:
    st.subheader("📋 Active Tasks")
    st.markdown('<div class="scroll-area">', unsafe_allow_html=True)
    
    tasks_df = get_google_data(SHEET_ID, "Active Tasks")
    if not tasks_df.empty:
        # Filter for non-completed tasks
        active_tasks = tasks_df[~tasks_df['status'].str.lower().isin(['done', 'completed', 'finished'])]
        
        for _, row in active_tasks.iterrows():
            prio = str(row.get('priority', '')).lower()
            prio_class = "prio-high" if prio == "high" else "prio-medium" if prio == "medium" else ""
            
            # --- THE "Assigned to" FIX ---
            # We check 'assigned to' because we forced the headers to lowercase
            person = row.get('assigned to') or row.get('lead') or "Open"
            
            st.markdown(f"""
                <div class="task-card {prio_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold;">{row.get('task', 'Unnamed Task')}</span>
                        <span style="background: #4F8BF9; color: white; padding: 2px 12px; border-radius: 20px; font-size: 0.8em;">
                            {person}
                        </span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No active tasks found.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.subheader("📢 Updates")
    st.markdown('<div class="scroll-area">', unsafe_allow_html=True)
    
    # News
    news_df = get_google_data(SHEET_ID, "News")
    if not news_df.empty:
        for _, row in news_df.iterrows():
            st.markdown(f'<div class="news-card"><b>{row.get("headline")}</b></div>', unsafe_allow_html=True)
    
    # Birthdays
    st.markdown("---")
    st.markdown("### 🎂 Birthdays")
    bdays_df = get_google_data(SHEET_ID, "Birthdays")
    if not bdays_df.empty:
        for _, row in bdays_df.iterrows():
            try:
                bdate = pd.to_datetime(row['date'], dayfirst=True).replace(year=now.year, hour=0, minute=0, second=0)
                if bdate < now: bdate = bdate.replace(year=now.year + 1)
                days_until = (bdate - now).days
                if 0 <= days_until <= 7:
                    color = "#FF69B4"
                    st.markdown(f'<div class="bday-card" style="border-left: 5px solid {color};"><b>{row.get("name")}</b> ({bdate.strftime("%d %b")})</div>', unsafe_allow_html=True)
            except: continue
    st.markdown('</div>', unsafe_allow_html=True)

# 3. COMPACT FOOTER
st.write("---")
f1, f2 = st.columns([2, 1])
with f1:
    days_left = (COMP_DATE - datetime.now()).days
    st.write(f"⏳ **Competition Countdown:** {max(0, days_left)} Days")
with f2:
    if st.button("🔄 Sync"):
        st.rerun()