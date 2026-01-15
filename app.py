import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import datetime
import random
import plotly.express as px
import plotly.graph_objects as go
import json

# --- CẤU HÌNH ---
SHEET_NAME = 'PMC Data Center'

# --- HÀM LOAD DỮ LIỆU THÔNG MINH (Cloud + Local) ---
def load_data():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # 1. Thử đọc từ Secrets (Trên Streamlit Cloud)
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            # Fix lỗi định dạng private_key trên Cloud
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        
        # 2. Nếu không có Secrets, thử đọc file Local (Trên máy tính)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)

        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME)
        worksheet = sheet.worksheet("Music_Stats")
        
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        if df.empty: return df, None

        # Xử lý dữ liệu
        df['Time'] = pd.to_datetime(df['Time'])
        cols_to_fix = ['Youtube_View', 'Youtube_Sub', 'Spotify_Listener', 'TikTok_Follower', 'Facebook_Follower']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '').str.replace('.', '')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        latest = df.iloc[-1]
        return df, latest

    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return pd.DataFrame(), None

# --- GIAO DIỆN ---
st.set_page_config(page_title="PMC Omni Dashboard", page_icon="👑", layout="wide")

st.markdown("""
<style>
    .metric-card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 10px; }
    .metric-label { font-size: 16px; color: #666; }
    .metric-value { font-size: 32px; font-weight: bold; color: #333; }
    .live-badge { background-color: #ff4b4b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
    .yt-color { color: #FF0000 !important; }
    .sp-color { color: #1DB954 !important; }
    .tt-color { color: #000000 !important; }
    .fb-color { color: #1877F2 !important; }
</style>
""", unsafe_allow_html=True)

st.title("👑 PMC Data Center - All Platforms")
st.caption(f"Last Update: {datetime.datetime.now().strftime('%H:%M:%S')}")

# --- KHỞI TẠO STATE ---
if 'view_sim' not in st.session_state:
    df, latest = load_data()
    st.session_state['df'] = df
    st.session_state['latest'] = latest
    if latest is not None:
        st.session_state['view_sim'] = int(latest['Youtube_View'])
    else:
        st.session_state['view_sim'] = 0

# --- TẠO TAB ---
tab1, tab2 = st.tabs(["🔥 LIVE DASHBOARD", "📈 BIỂU ĐỒ"])

# PHẦN 1: BIỂU ĐỒ (TAB 2)
with tab2:
    st.subheader("📊 Lịch sử tăng trưởng")
    if 'df' in st.session_state and not st.session_state['df'].empty:
        df_chart = st.session_state['df']
        if len(df_chart) > 1:
            # Youtube View
            fig_view = px.line(df_chart, x='Time', y='Youtube_View', title='Youtube Views', markers=True)
            fig_view.update_traces(line_color='#FF0000', marker_size=8)
            fig_view.update_layout(yaxis=dict(tickformat=",")) 
            st.plotly_chart(fig_view, use_container_width=True)
            
            # Social Comparison
            fig_social = go.Figure()
            fig_social.add_trace(go.Scatter(x=df_chart['Time'], y=df_chart['Youtube_Sub'], name='YT Sub', line=dict(color='red')))
            fig_social.add_trace(go.Scatter(x=df_chart['Time'], y=df_chart['TikTok_Follower'], name='TikTok', line=dict(color='black')))
            fig_social.add_trace(go.Scatter(x=df_chart['Time'], y=df_chart['Facebook_Follower'], name='Facebook', line=dict(color='blue')))
            fig_social.update_layout(title='Fan Growth', hovermode="x unified", yaxis=dict(tickformat=","))
            st.plotly_chart(fig_social, use_container_width=True)
        else:
            st.info("Đang thu thập dữ liệu... Cần ít nhất 2 điểm để vẽ biểu đồ.")

# PHẦN 2: LIVE DASHBOARD (TAB 1)
with tab1:
    placeholder = st.empty()
    while True:
        # Giả lập tăng view nhẹ
        st.session_state['view_sim'] += random.randint(0, 3)
        
        # Mỗi 30s tải lại dữ liệu thật 1 lần
        if int(time.time()) % 30 == 0:
            df_new, latest_new = load_data()
            if latest_new is not None:
                st.session_state['df'] = df_new
                st.session_state['latest'] = latest_new
                real_view = int(latest_new['Youtube_View'])
                if real_view > st.session_state['view_sim']:
                    st.session_state['view_sim'] = real_view
        
        # Hiển thị
        latest = st.session_state['latest']
        if latest is not None:
            with placeholder.container():
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"""<div class="metric-card"><div class="metric-label">Youtube Views <span class="live-badge">LIVE</span></div><div class="metric-value yt-color">{st.session_state['view_sim']:,}</div></div>""", unsafe_allow_html=True)
                c2.markdown(f"""<div class="metric-card"><div class="metric-label">Youtube Subs</div><div class="metric-value">{latest['Youtube_Sub']:,}</div></div>""", unsafe_allow_html=True)
                c3.markdown(f"""<div class="metric-card"><div class="metric-label">Spotify Listeners</div><div class="metric-value sp-color">{latest['Spotify_Listener']:,}</div></div>""", unsafe_allow_html=True)
                
                c4, c5, c6 = st.columns(3)
                c4.markdown(f"""<div class="metric-card"><div class="metric-label">TikTok Followers</div><div class="metric-value tt-color">{latest['TikTok_Follower']:,}</div></div>""", unsafe_allow_html=True)
                c5.markdown(f"""<div class="metric-card"><div class="metric-label">Facebook Followers</div><div class="metric-value fb-color">{latest['Facebook_Follower']:,}</div></div>""", unsafe_allow_html=True)
                c6.markdown(f"""<div class="metric-card"><div class="metric-label">Total Videos</div><div class="metric-value">{latest['Youtube_Video']}</div></div>""", unsafe_allow_html=True)
        
        time.sleep(1)