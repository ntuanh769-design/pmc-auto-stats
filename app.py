import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
import datetime
import time
import random
import plotly.express as px
import json

# --- CẤU HÌNH ---
SHEET_NAME = 'PMC Data Center'
VIDEO_IDS = ['k3C6-1f9gHw', 'sJytolUBttX8', '7P6Wv5_o-2Q'] # Thay ID của bạn
YOUTUBE_API_KEY = 'AIzaSyAueu53W-r0VWcYJwYrSSboOKuWYQfLn34' 

# Link ảnh (Bạn có thể thay bằng link ảnh khác của PMC)
BANNER_URL = "https://images.unsplash.com/photo-1493225255756-d9584f8606e9?q=80&w=2070&auto=format&fit=crop" # Ảnh bìa Concert
AVATAR_URL = "https://yt3.googleusercontent.com/ytc/AIdro_kX4tF4d_1F4d4t4t4t4t4t4t4t4t4t4t4t4t4=s176-c-k-c0x00ffffff-no-rj" # Ảnh Avatar kênh

# --- HÀM 1: LẤY DATA VIDEO (API) ---
def fetch_video_data_api(video_ids):
    data_map = {}
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.videos().list(
            part="snippet,statistics",
            id=','.join(video_ids)
        )
        response = request.execute()
        for item in response['items']:
            vid_id = item['id']
            stats = item['statistics']
            snippet = item['snippet']
            data_map[vid_id] = {
                'title': snippet['title'],
                'thumb': snippet['thumbnails']['high']['url'],
                'view': int(stats.get('viewCount', 0)),
                'like': int(stats.get('likeCount', 0)),
                'comment': int(stats.get('commentCount', 0)),
                'id': vid_id
            }
    except: pass
    return data_map

# --- HÀM 2: LẤY DATA TỔNG (SHEET) ---
def load_sheet_data():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)

        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME)
        worksheet = sheet.worksheet("Music_Stats")
        
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        if df.empty: return df, None

        cols_to_fix = ['Youtube_View', 'Youtube_Sub', 'Spotify_Listener', 'TikTok_Follower', 'Facebook_Follower']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('.', ''), errors='coerce').fillna(0).astype(int)
        
        df['Time'] = pd.to_datetime(df['Time'])
        latest = df.iloc[-1]
        return df, latest
    except: return pd.DataFrame(), None

# --- GIAO DIỆN CHUYÊN NGHIỆP ---
st.set_page_config(page_title="Phuong My Chi - Data Center", page_icon="🎤", layout="wide")

# CSS TÙY CHỈNH (Làm đẹp giao diện)
st.markdown("""
<style>
    /* Ẩn menu mặc định của Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Font chữ và nền */
    .stApp { background-color: #0E1117; color: white; }
    
    /* Style cho Banner */
    .banner-container {
        width: 100%;
        height: 300px;
        overflow: hidden;
        border-radius: 0 0 20px 20px;
        margin-bottom: 20px;
    }
    .banner-img { width: 100%; object-fit: cover; }
    
    /* Style cho Avatar và Bio */
    .profile-container { display: flex; align-items: center; gap: 20px; margin-bottom: 30px; }
    .avatar { border-radius: 50%; width: 120px; border: 3px solid #FFD700; }
    .artist-name { font-size: 32px; font-weight: bold; margin: 0; color: #FFD700; }
    .artist-bio { color: #ccc; font-size: 16px; font-style: italic; }
    
    /* Card số liệu tổng */
    .metric-card { 
        background: linear-gradient(145deg, #1e232a, #161a20);
        padding: 20px; border-radius: 15px; text-align: center; 
        border: 1px solid #333; box-shadow: 5px 5px 10px #0b0e12, -5px -5px 10px #212832;
    }
    .metric-val { font-size: 36px; font-weight: 800; color: white; }
    .metric-lbl { font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: #888; margin-bottom: 5px; }
    .live-dot { height: 10px; width: 10px; background-color: red; border-radius: 50%; display: inline-block; animation: blink 1s infinite; }
    
    /* Card Video */
    .video-card { 
        background-color: #1e1e1e; border-radius: 15px; overflow: hidden; 
        border: 1px solid #333; margin-bottom: 20px; transition: transform 0.2s;
    }
    .video-card:hover { transform: translateY(-5px); border-color: #FFD700; }
    .vid-title { font-weight: bold; padding: 10px; height: 50px; overflow: hidden; font-size: 14px; }
    .vid-stats { padding: 0 10px 10px 10px; font-size: 13px; color: #aaa; display: flex; justify-content: space-between; }
    
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
</style>
""", unsafe_allow_html=True)

# --- 1. PHẦN HEADER (BANNER & INFO) ---
# Banner
st.markdown(f"""
<div class="banner-container">
    <img src="{BANNER_URL}" class="banner-img" style="width:100%; height:300px; object-fit:cover;">
</div>
""", unsafe_allow_html=True)

# Profile Artist
c1, c2 = st.columns([1, 4])
with c1:
    st.markdown(f'<div style="text-align:center"><img src="{AVATAR_URL}" class="avatar"></div>', unsafe_allow_html=True)
with c2:
    st.markdown("""
    <div style="padding-top: 10px;">
        <p class="artist-name">PHƯƠNG MỸ CHI OFFICIAL 👑</p>
        <p class="artist-bio">"Cô bé dân ca" ngày nào giờ đã trở thành một biểu tượng âm nhạc trẻ trung, năng động và đầy sáng tạo.</p>
        <p>🌐 <a href="https://www.facebook.com/phuongmychi" style="color:#1877F2; text-decoration:none;">Facebook</a> &nbsp;|&nbsp; 
           🎵 <a href="#" style="color:#1DB954; text-decoration:none;">Spotify</a> &nbsp;|&nbsp; 
           ▶️ <a href="https://www.youtube.com/channel/UCGRIV5jOtKyAibhjBdIndZQ" style="color:#FF0000; text-decoration:none;">Youtube</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# --- KHỞI TẠO STATE ---
if 'init_done' not in st.session_state:
    df, latest = load_sheet_data()
    st.session_state['df'] = df
    st.session_state['latest'] = latest
    if latest is not None:
        st.session_state['total_view_sim'] = int(latest['Youtube_View'])
    else:
        st.session_state['total_view_sim'] = 0
    st.session_state['video_data'] = fetch_video_data_api(VIDEO_IDS)
    st.session_state['init_done'] = True

# --- 2. PHẦN LIVE DASHBOARD (PLACEHOLDER) ---
st.markdown("### 🔥 REAL-TIME STATISTICS")
metrics_placeholder = st.empty()

st.markdown("### 🎬 LATEST RELEASES")
video_placeholder = st.empty()

# --- VÒNG LẶP CHÍNH ---
while True:
    # 1. Tăng View Ảo (Chỉ cho View Tổng)
    st.session_state['total_view_sim'] += random.randint(1, 15)

    # 2. Đồng bộ API (Mỗi 60s)
    if int(time.time()) % 60 == 0:
        df_new, latest_new = load_sheet_data()
        if latest_new is not None:
            st.session_state['latest'] = latest_new
            real = int(latest_new['Youtube_View'])
            if real > st.session_state['total_view_sim']:
                st.session_state['total_view_sim'] = real
        st.session_state['video_data'] = fetch_video_data_api(VIDEO_IDS)

    # 3. Hiển thị Metrics (View Tổng nhảy số)
    lat = st.session_state['latest']
    if lat is not None:
        with metrics_placeholder.container():
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""<div class="metric-card"><div class="metric-lbl">TOTAL VIEWS <span class="live-dot"></span></div><div class="metric-val" style="color:#FF4B4B">{st.session_state['total_view_sim']:,}</div></div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""<div class="metric-card"><div class="metric-lbl">SUBSCRIBERS</div><div class="metric-val">{lat['Youtube_Sub']:,}</div></div>""", unsafe_allow_html=True)
            with col3:
                st.markdown(f"""<div class="metric-card"><div class="metric-lbl">TIKTOK FANS</div><div class="metric-val">{lat['TikTok_Follower']:,}</div></div>""", unsafe_allow_html=True)
            with col4:
                st.markdown(f"""<div class="metric-card"><div class="metric-lbl">SPOTIFY</div><div class="metric-val" style="color:#1DB954">{lat['Spotify_Listener']:,}</div></div>""", unsafe_allow_html=True)

    # 4. Hiển thị Video (Số Tĩnh)
    with video_placeholder.container():
        cols = st.columns(3)
        v_data = st.session_state['video_data']
        for i, vid_id in enumerate(VIDEO_IDS):
            if vid_id in v_data:
                d = v_data[vid_id]
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="video-card">
                        <a href="https://www.youtube.com/watch?v={d['id']}" target="_blank">
                            <img src="{d['thumb']}" style="width:100%; border-bottom:1px solid #333;">
                        </a>
                        <div class="vid-title">{d['title']}</div>
                        <div class="vid-stats">
                            <span style="color:#4CAF50">👁️ {d['view']:,}</span>
                            <span style="color:#2196F3">👍 {d['like']:,}</span>
                            <span style="color:#FFC107">💬 {d['comment']:,}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    time.sleep(1)