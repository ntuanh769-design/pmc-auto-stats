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
# Thay 3 ID Video của bạn vào đây:
VIDEO_IDS = ['sZrIbpwjTwk', 'BmrdGQ0LRRo', 'V1ah6tmNUz8']
YOUTUBE_API_KEY = 'AIzaSyAueu53W-r0VWcYJwYrSSboOKuWYQfLn34' 

# --- HÀM 1: LẤY DATA 3 VIDEO (API) ---
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
                'published': snippet['publishedAt'][:10]
            }
    except Exception as e:
        pass
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
    except:
        return pd.DataFrame(), None

# --- GIAO DIỆN ---
st.set_page_config(page_title="PMC Live Dashboard", page_icon="👑", layout="wide")

st.markdown("""
<style>
    /* CSS cho Card Tổng */
    .metric-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px; }
    .metric-label { font-size: 14px; color: #666; }
    .metric-value { font-size: 32px; font-weight: bold; color: #333; }
    
    /* CSS cho Card Video (Đen) */
    .video-card {
        background-color: #1e1e1e; color: white;
        border-radius: 12px; margin-bottom: 10px; overflow: hidden;
        border: 1px solid #333; box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    .video-img { width: 100%; border-bottom: 1px solid #333; }
    .card-content { padding: 12px; }
    .video-title { 
        font-size: 14px; font-weight: bold; margin-bottom: 10px; 
        height: 40px; overflow: hidden; text-transform: uppercase;
        display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
        color: #fff;
    }
    .stat-row { display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 13px; color: #ccc; }
    .live-badge { background-color: #ff4b4b; color: white; padding: 1px 6px; border-radius: 4px; font-size: 10px; margin-left: 5px; vertical-align: middle; }
    
    /* Màu số liệu */
    .yt-color { color: #FF0000 !important; }
    .sp-color { color: #1DB954 !important; }
    .fb-color { color: #1877F2 !important; }
</style>
""", unsafe_allow_html=True)

st.title("👑 PMC Data Center (Real-Time)")
st.caption(f"Last Update: {datetime.datetime.now().strftime('%H:%M:%S')}")

# --- KHỞI TẠO STATE ---
if 'init_done' not in st.session_state:
    # 1. Load Tổng
    df, latest = load_sheet_data()
    st.session_state['df'] = df
    st.session_state['latest'] = latest
    # Khởi tạo số view tổng để nhảy
    if latest is not None:
        st.session_state['total_view_sim'] = int(latest['Youtube_View'])
    else:
        st.session_state['total_view_sim'] = 0
        
    # 2. Load 3 Video lẻ (Lần đầu)
    st.session_state['video_data'] = fetch_video_data_api(VIDEO_IDS)
    st.session_state['init_done'] = True

# --- TẠO KHUNG CHỨA (PLACEHOLDERS) ---
video_container = st.empty()
st.divider()
metrics_container = st.empty()

# --- VÒNG LẶP REAL-TIME ---
while True:
    # === 1. TÍNH TOÁN NHẢY SỐ (SIMULATION) ===
    
    # A. CHỈ Nhảy số View Tổng (View kênh)
    st.session_state['total_view_sim'] += random.randint(1, 10)
    
    # B. KHÔNG Nhảy số Video lẻ nữa (Đã xóa đoạn code random)

    # === 2. ĐỒNG BỘ DATA THẬT (MỖI 60 GIÂY) ===
    if int(time.time()) % 60 == 0:
        # Load lại Sheet (Tổng)
        df_new, latest_new = load_sheet_data()
        if latest_new is not None:
            st.session_state['latest'] = latest_new
            real_val = int(latest_new['Youtube_View'])
            if real_val > st.session_state['total_view_sim']:
                 st.session_state['total_view_sim'] = real_val
        
        # Load lại API Video (Cập nhật số liệu thực tế cho 3 video)
        real_video_data = fetch_video_data_api(VIDEO_IDS)
        st.session_state['video_data'] = real_video_data

    # === 3. VẼ GIAO DIỆN ===
    
    # A. Vẽ 3 Video Card (Số Tĩnh)
    with video_container.container():
        st.subheader("🎬 Top Videos Collection")
        cols = st.columns(3)
        v_data = st.session_state['video_data']
        for i, vid_id in enumerate(VIDEO_IDS):
            if vid_id in v_data:
                info = v_data[vid_id]
                v_view = "{:,}".format(info['view']).replace(',', '.')
                v_like = "{:,}".format(info['like']).replace(',', '.')
                v_comm = "{:,}".format(info['comment']).replace(',', '.')
                
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="video-card">
                        <img src="{info['thumb']}" class="video-img">
                        <div class="card-content">
                            <div class="video-title">{info['title']}</div>
                            <div class="stat-row">
                                <span>Views</span> <span style="color: #3b82f6; font-weight:bold;">{v_view}</span>
                            </div>
                            <div class="stat-row">
                                <span>Likes</span>
                                <span style="color: #10b981; font-weight:bold;">{v_like}</span>
                            </div>
                            <div class="stat-row">
                                <span>Comments</span>
                                <span style="color: #f59e0b; font-weight:bold;">{v_comm}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # B. Vẽ View Tổng (Số Nhảy)
    with metrics_container.container():
        st.subheader("🔥 Kênh Tổng Hợp")
        lat = st.session_state['latest']
        if lat is not None:
            c1, c2, c3 = st.columns(3)
            # View tổng vẫn giữ hiệu ứng LIVE
            c1.markdown(f"""<div class="metric-card"><div class="metric-label">Youtube Views <span class="live-badge">LIVE</span></div><div class="metric-value yt-color">{st.session_state['total_view_sim']:,}</div></div>""", unsafe_allow_html=True)
            c2.markdown(f"""<div class="metric-card"><div class="metric-label">Youtube Subs</div><div class="metric-value">{lat['Youtube_Sub']:,}</div></div>""", unsafe_allow_html=True)
            c3.markdown(f"""<div class="metric-card"><div class="metric-label">Spotify Listeners</div><div class="metric-value sp-color">{lat['Spotify_Listener']:,}</div></div>""", unsafe_allow_html=True)
            
            c4, c5, c6 = st.columns(3)
            c4.markdown(f"""<div class="metric-card"><div class="metric-label">TikTok Followers</div><div class="metric-value">{lat['TikTok_Follower']:,}</div></div>""", unsafe_allow_html=True)
            c5.markdown(f"""<div class="metric-card"><div class="metric-label">Facebook Followers</div><div class="metric-value fb-color">{lat['Facebook_Follower']:,}</div></div>""", unsafe_allow_html=True)
            c6.markdown(f"""<div class="metric-card"><div class="metric-label">Total Videos</div><div class="metric-value">{lat['Youtube_Video']}</div></div>""", unsafe_allow_html=True)

    time.sleep(1)