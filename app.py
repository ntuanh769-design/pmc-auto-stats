import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build # Cần thêm thư viện này
import datetime
import time
import random
import plotly.express as px
import plotly.graph_objects as go
import json

# --- CẤU HÌNH ---
SHEET_NAME = 'PMC Data Center'
# Bạn điền 3 ID Video muốn theo dõi vào đây:
VIDEO_IDS = ['sZrIbpwjTwk', 'BmrdGQ0LRRo', 'V1ah6tmNUz8'] 
# (Nhớ thay ID_VIDEO_2, ID_VIDEO_3 bằng ID thật của bạn)

YOUTUBE_API_KEY = 'AIzaSyAueu53W-r0VWcYJwYrSSboOKuWYQfLn34' 

# --- HÀM LẤY CHI TIẾT 3 VIDEO (API) ---
def get_video_details(video_ids):
    stats_list = []
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.videos().list(
            part="snippet,statistics",
            id=','.join(video_ids)
        )
        response = request.execute()
        
        for item in response['items']:
            stats = item['statistics']
            snippet = item['snippet']
            
            # Format số đẹp (ví dụ: 1.246.130)
            view = "{:,}".format(int(stats.get('viewCount', 0))).replace(',', '.')
            like = "{:,}".format(int(stats.get('likeCount', 0))).replace(',', '.')
            comment = "{:,}".format(int(stats.get('commentCount', 0))).replace(',', '.')
            
            video_data = {
                'title': snippet['title'],
                'thumb': snippet['thumbnails']['high']['url'],
                'view': view,
                'like': like,
                'comment': comment,
                'published': snippet['publishedAt'][:10] # Lấy ngày đăng
            }
            stats_list.append(video_data)
    except Exception as e:
        st.error(f"Lỗi lấy Video: {e}")
    return stats_list

# --- HÀM LOAD DỮ LIỆU TỔNG (Giữ nguyên) ---
def load_data():
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
st.set_page_config(page_title="PMC Dashboard", page_icon="👑", layout="wide")

# CSS ĐỂ TẠO CARD ĐẸP NHƯ HÌNH
st.markdown("""
<style>
    .metric-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px; }
    .metric-label { font-size: 14px; color: #666; }
    .metric-value { font-size: 28px; font-weight: bold; color: #333; }
    
    /* CSS CHO VIDEO CARD (Giao diện đen mờ) */
    .video-card {
        background-color: #1e1e1e; /* Màu nền đen xám */
        border-radius: 15px;
        padding: 0px;
        color: white;
        margin-bottom: 20px;
        overflow: hidden;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        border: 1px solid #333;
    }
    .video-img {
        width: 100%;
        height: auto;
        border-bottom: 1px solid #333;
    }
    .card-content {
        padding: 15px;
    }
    .video-title {
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 15px;
        height: 50px; /* Cố định chiều cao tiêu đề */
        overflow: hidden;
        text-transform: uppercase;
        color: #fff;
    }
    .stat-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        font-size: 14px;
        color: #ccc;
    }
    .stat-val {
        font-weight: bold;
        color: #4CAF50; /* Màu xanh lá cho số liệu */
    }
    .footer-date {
        font-size: 11px;
        color: #666;
        text-align: right;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("👑 PMC Data Center")
st.caption(f"Last Update: {datetime.datetime.now().strftime('%H:%M:%S')}")

# --- KHỞI TẠO STATE ---
if 'view_sim' not in st.session_state:
    df, latest = load_data()
    st.session_state['df'] = df
    st.session_state['latest'] = latest

# --- PHẦN 1: VIDEO NỔI BẬT (GIAO DIỆN MỚI) ---
st.subheader("🎬 Video Nổi Bật (Album Collection)")

# Lấy dữ liệu 3 video
video_stats = get_video_details(VIDEO_IDS)

if video_stats:
    cols = st.columns(3) # Chia làm 3 cột
    for i, vid in enumerate(video_stats):
        with cols[i]:
            # HTML Tạo Card
            st.markdown(f"""
            <div class="video-card">
                <img src="{vid['thumb']}" class="video-img">
                <div class="card-content">
                    <div class="video-title">{vid['title']}</div>
                    <div class="stat-row">
                        <span>Lượt xem:</span>
                        <span class="stat-val" style="color: #3b82f6;">{vid['view']}</span>
                    </div>
                    <div class="stat-row">
                        <span>Lượt thích:</span>
                        <span class="stat-val" style="color: #10b981;">{vid['like']}</span>
                    </div>
                    <div class="stat-row">
                        <span>Bình luận:</span>
                        <span class="stat-val" style="color: #f59e0b;">{vid['comment']}</span>
                    </div>
                    <div class="footer-date">Ngày đăng: {vid['published']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.warning("⚠️ Chưa load được Video. Hãy kiểm tra lại ID Video trong code.")

st.divider()

# --- PHẦN 2: THỐNG KÊ TỔNG (Như cũ) ---
tab1, tab2 = st.tabs(["🔥 LIVE DASHBOARD", "📈 BIỂU ĐỒ"])

with tab2:
    if 'df' in st.session_state and not st.session_state['df'].empty:
        df_chart = st.session_state['df']
        fig_view = px.line(df_chart, x='Time', y='Youtube_View', title='Youtube Views Growth')
        fig_view.update_traces(line_color='#FF0000')
        st.plotly_chart(fig_view, use_container_width=True)

with tab1:
    latest = st.session_state['latest']
    if latest is not None:
        c1, c2, c3 = st.columns(3)
        c1.metric("Youtube Views", "{:,}".format(latest['Youtube_View']))
        c2.metric("Youtube Subs", "{:,}".format(latest['Youtube_Sub']))
        c3.metric("Spotify", "{:,}".format(latest['Spotify_Listener']))
        
        c4, c5, c6 = st.columns(3)
        c4.metric("TikTok", "{:,}".format(latest['TikTok_Follower']))
        c5.metric("Facebook", "{:,}".format(latest['Facebook_Follower']))
        c6.metric("Total Videos", latest['Youtube_Video'])