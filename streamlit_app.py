import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- PAGE CONFIG ---
st.set_page_config(page_title="Haunted House Dashboard", layout="wide", initial_sidebar_state="collapsed")

# --- AUTO REFRESH (Every 5 Minutes) ---
st_autorefresh(interval=300000, key="datarefresh")

# --- DATA FETCH ---
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
        return pd.DataFrame()

# --- CONFIG ---
SHEET_ID = "1FuzDffAF4O1zinFsXgyHdvt9iSL91vutrosv_v727_U" 
COMP_DATE = datetime(2027, 1, 10) 

# --- STYLING ---
st.markdown(f"""
    <style>
    .main .block-container {{ padding-top: 1rem !important; max-width: 98%; }}
    
    /* Header Box */
    .header-box {{ 
        display: flex; justify-content: space-between; align-items: center; 
        padding: 15px 25px; background: rgba(255,255,255,0.05); 
        border-radius: 15px; margin-bottom: 20px; border: 1px solid rgba(255,75,75,0.3);
    }}
    .title-text {{ color: #FF4B4B; font-size: 2.2rem; font-weight: bold; text-transform: uppercase; margin: 0; }}

    /* THE SCROLLING CAGE */
    .task-window {{
        height: 60vh;
        overflow: hidden;
        position: relative;
        background: rgba(0,0,0,0.2);
        border-radius: 10px;
    }}

    .scroller {{
        display: flex;
        flex-direction: column;
        animation: scroll-up 40s linear infinite;
    }}

    .scroller:hover {{ animation-play-state: paused; }}

    @keyframes scroll-up {{
        0% {{ transform: translateY(0); }}
        100% {{ transform: translateY(-50%); }}
    }}

    /* Card Styling */
    .task-card {{ 
        background: rgba(255, 255, 255, 0.08); padding: 15px; 
        border-radius: 8px; border-left: 6px solid #4F8BF9; margin-bottom: 15px; 
    }}
    .prio-high {{ border-left-color: #FF4B4B !important; }}
    .prio-medium {{ border-left-color: #FFA500 !important; }}
    .status-pill {{ background: rgba(255,255,255,0.1); padding: 2px 8px; border-radius: 5px; font-size: 0.75em; }}
    
    .news-card {{ background: rgba(79, 139, 249, 0.1); padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #4F8BF9; }}
    .bday-card {{ background: rgba(255, 105, 180, 0.1); padding: 10px; border-radius: 8px; border: 1px solid #FF69B4; margin-bottom: 8px; }}
    
    header, footer {{ visibility: hidden; }}
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
days_left = (COMP_DATE - datetime.now()).days
st.markdown(f"""
    <div class="header-box">
        <div style="flex: 1;"><p style="color:#BDC3C7; margin:0;">{datetime.now().strftime("%A")}</p><b>{datetime.now().strftime("%d %B %Y")}</b></div>
        <div style="flex: 2; text-align: center;"><p class="title-text">🏰 Haunted House Dashboard</p></div>
        <div style="flex: 1; text-align: right; border-left: 2px solid #FF4B4B; padding-left: 20px;">
            <p style="color:#BDC3C7; margin:0;">Kick-Off</p><b style="font-size: 1.5rem; color: #FF4B4B;">{max(0, days_left)} DAYS LEFT</b>
        </div>
    </div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1.8, 1])

with col_left:
    st.subheader("📋 Active Tasks")
    df = get_google_data(SHEET_ID, "Active Tasks")
    if not df.empty:
        active = df[~df['status'].str.lower().isin(['done', 'completed'])]
        
        # Build cards
        cards_html = ""
        for _, row in active.iterrows():
            prio = str(row.get('priority level', '')).lower()
            prio_c = "prio-high" if prio == "high" else "prio-medium" if prio == "medium" else ""
            person = row.get('assigned to') or "Open"
            
            cards_html += f"""
            <div class="task-card {prio_c}">
                <div style="display:flex; justify-content:space-between; align-items:start;">
                    <div>
                        <b style="font-size:1.1em; color:white;">{row.get('task', 'No Task')}</b>
                        <div style="color:white; font-size:0.9em; margin-top:4px;">↳ {row.get('remarks') or "No remarks"}</div>
                    </div>
                    <div style="margin-top:8px;"><span class="status-pill">{row.get('status')}</span> 
                    </div>
                    <span style="background:#4F8BF9; color:white; padding:2px 10px; border-radius:20px; font-size:0.8em;">{person}</span>
                </div>
            </div>"""

        # RENDER WITH DOUBLE FOR LOOP
        st.markdown(f'<div class="task-window"><div class="scroller">{cards_html}{cards_html}</div></div>', unsafe_allow_html=True)
    else:
        st.write("No tasks found.")

#what is shown in the right column
with col_right:
    #news section
    st.subheader("📢 News")
    n_df = get_google_data(SHEET_ID, "News")
    for _, row in n_df.iterrows():
        st.markdown(f'<div class="news-card"><b>{row.get("headline")}</b><br><small>{row.get("content")}</small></div>', unsafe_allow_html=True)
    
    #birthday section
    st.subheader("🎂 Birthdays")
    b_df = get_google_data(SHEET_ID, "Birthdays")
    found = False
    for _, row in b_df.iterrows():
        try:
            bday = pd.to_datetime(row['date'], dayfirst=True).replace(year=datetime.now().year)
            if 0 <= (bday - datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).days <= 7:
                st.markdown(f'<div class="bday-card"><b>{row.get("name")}</b> ({bday.strftime("%d %b")})</div>', unsafe_allow_html=True)
                found = True
        except: continue
    if not found: st.markdown('<i style="opacity:0.5;">No birthdays this week</i>', unsafe_allow_html=True)
     
     #quote section
    st.subheader("🔮Quote")
    quotes_df = get_google_data(SHEET_ID, "Quotes")
    if not quotes_df.empty:
        q = quotes_df.sample(n=1).iloc[0]
        st.markdown(f"""
        <div class="quote-box">
            <h2 style="color: #4F8BF9; margin: 0;">“{q.get('quote', 'Keep Pushing!')}”</h2>
            <p style="color: #BDC3C7; margin-top: 10px;">— {q.get('author', 'Team')}</p>
        </div>
        """, unsafe_allow_html=True)