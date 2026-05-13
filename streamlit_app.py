import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

count = st_autorefresh(interval=300000, key="dashboard_refresh")
# --- PAGE CONFIG ---
st.set_page_config(page_title="Haunted House Dashboard", layout="wide", initial_sidebar_state="collapsed")

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

# --- STYLING ---
st.markdown("""
    <style>
    .main .block-container { padding-top: 1rem !important; max-width: 95%; }
    
    /* Header Styling */
    .title-text { text-align: center; color: #FF4B4B; margin-bottom: 0px; font-size: 2.5rem; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; }
    .date-text { text-align: center; color: #BDC3C7; margin-bottom: 20px; font-size: 1.2rem; }

    /* Layout Containers */
    .scroll-area { max-height: 55vh; overflow-y: auto; padding-right: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); }

    /* Task Cards */
    .task-card { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 8px; border-left: 6px solid #4F8BF9; margin-bottom: 12px; }
    .prio-high { border-left-color: #FF4B4B !important; }
    .prio-medium { border-left-color: #FFA500 !important; }
    
    .status-pill { background: rgba(255,255,255,0.1); padding: 2px 8px; border-radius: 5px; font-size: 0.75em; text-transform: uppercase; }
    .desc-text { color: #BDC3C7; font-size: 0.85em; margin-top: 8px; font-style: italic; }

    .news-card { background: rgba(79, 139, 249, 0.1); padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #4F8BF9; }
    .bday-card { background: rgba(255, 105, 180, 0.1); padding: 12px; border-radius: 8px; border: 1px solid #FF69B4; margin-bottom: 10px; }
    .quote-box { background: rgba(255, 255, 255, 0.03); padding: 15px; border-radius: 12px; border: 1px solid #4F8BF9; text-align: center; font-style: italic; margin-bottom: 15px; }
    
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Header Container - Forces horizontal alignment */
    .header-box { 
        display: flex; 
        flex-direction: row;
        justify-content: space-between; 
        align-items: center; 
        padding: 15px 25px; 
        background: rgba(255,255,255,0.05); 
        border-radius: 15px; 
        margin-bottom: 20px; 
        border: 1px solid rgba(255,75,75,0.3);
        width: 100%;
    }
    .header-item { flex: 1; }
    .header-center { flex: 2; text-align: center; }
    .header-right { flex: 1; text-align: right; border-left: 2px solid #FF4B4B; padding-left: 20px; }

            //from here

   /* The static window that hides the overflow */
    .scroll-area { 
        height: 60vh; 
        overflow: hidden; 
        position: relative;
        background: rgba(0,0,0,0.2);
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.1);
    }

    /* The moving container */
    .auto-scroll-content {
        position: absolute;
        width: 100%;
        left: 0;
        top: 0;
        /* Increase 30s for slower, 10s for faster */
        animation: ticker 30s linear infinite;
    }

    /* Pause when hovering */
    .auto-scroll-content:hover {
        animation-play-state: paused;
    }

    @keyframes ticker {
        0% { transform: translateY(0); }
        100% { transform: translateY(-50%); }
    }
            
    </style>
""", unsafe_allow_html=True)

# --- NEW TOP HEADER SECTION ---
days_left = (COMP_DATE - datetime.now()).days
st.markdown(f"""
    <div class="header-box">
        <div style="flex: 1;">
            <p class="header-subtext">{datetime.now().strftime("%A")}</p>
            <p style="font-weight: bold; margin:0;">{datetime.now().strftime("%d %B %Y")}</p>
        </div>
        <div style="flex: 2; text-align: center;">
            <p class="title-text">🏰 Haunted House Dashboard</p>
        </div>
        <div class="countdown-box" style="flex: 1;">
            <p class="header-subtext">Days until kick-off</p>
            <p style="font-size: 1.5rem; font-weight: bold; color: #FF4B4B; margin:0;">{max(0, days_left)} DAYS LEFT</p>
        </div>
    </div>
""", unsafe_allow_html=True)

now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

# 1. QUOTE
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
        
        # We define the HTML for the list once
        items_html = ""
        for _, row in active_tasks.iterrows():
            prio = str(row.get('priority level', '')).lower()
            prio_class = "prio-high" if prio == "high" else "prio-medium" if prio == "medium" else ""
            person = row.get('assigned to') or row.get('lead') or "Open"
            task_text = row.get('task', 'No description')
            remarks_text = str(row.get('remarks', '')).strip() or "No remarks"
            
            items_html += f"""
                <div class="task-card {prio_class}">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="width: 75%;">
                            <span style="font-weight: bold; font-size: 1.1em; color: white;">{task_text}</span>
                            <div style="color: #BDC3C7; font-size: 0.85em; margin-top: 4px; font-style: italic;">↳ {remarks_text}</div>
                            <div style="margin-top:8px;">
                                <span class="status-pill">{row.get('status', 'Pending')}</span> • 
                                <span style="font-size:0.7em; color:#FFA500; font-weight: bold;">{prio.upper()}</span>
                            </div>
                        </div>
                        <span style="background: #4F8BF9; color: white; padding: 2px 10px; border-radius: 20px; font-size: 0.75em;">{person}</span>
                    </div>
                </div>
            """

        # RENDER: Double the HTML inside the animated div for the loop
        st.markdown(f"""
            <div class="scroll-area">
                <div class="auto-scroll-content">
                    {items_html}
                    {items_html}
                </div>
            </div>
        """, unsafe_allow_html=True)

            
    else:
        st.write("👻 No ghosts... and no tasks.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.subheader("📢 News")
    st.markdown('<div class="scroll-area">', unsafe_allow_html=True)
    news_df = get_google_data(SHEET_ID, "News")
    for _, row in news_df.iterrows():
        st.markdown(f'<div class="news-card"><b>{row.get("headline")}</b><br><small>{row.get("content")}</small></div>', unsafe_allow_html=True)
    
    # 3. BIRTHDAYS SECTION
    st.header("🎂 Birthdays")
    bdays_df = get_google_data(SHEET_ID, "Birthdays")
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
    
    st.markdown('</div>', unsafe_allow_html=True)

