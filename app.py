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

# ==========================================
# --- CẤU HÌNH (GIỮ NGUYÊN) ---
# ==========================================
SHEET_NAME = 'PMC Data Center'
VIDEO_IDS = ['sZrIbpwjTwk', 'BmrdGQ0LRRo', 'V1ah6tmNUz8'] # Thay ID của bạn
YOUTUBE_API_KEY = 'AIzaSyAueu53W-r0VWcYJwYrSSboOKuWYQfLn34' 

# Link ảnh và Mạng xã hội
BANNER_URL = "https://scontent.fvca1-1.fna.fbcdn.net/v/t39.30808-6/600369698_1419646709529546_341344486868245985_n.jpg?_nc_cat=105&ccb=1-7&_nc_sid=833d8c&_nc_eui2=AeE8R8ouge4yL7lfWGQ5Kzk1Enry68g3cr0SevLryDdyvaWspFlBItEaOUW321Od9poGbHjYncGX9_MS7BEcv6Ww&_nc_ohc=WHolhcYE84IQ7kNvwH3WDS7&_nc_oc=AdlMDmMAztdFXjYHzVG6BJpmRMy1E7qVPlz3DWxOrwo2YrZS0MeRHLPCU2rF4_OdTXE&_nc_zt=23&_nc_ht=scontent.fvca1-1.fna&_nc_gid=AXvAnGOph6iEFu_TWBD-SA&oh=00_AfoafS9eKG1wduMrKvUIYzK6Mu4ZIs0Q3Idtuj5CW5qvEg&oe=696F8D56" # Ảnh bìa Concert
AVATAR_URL = "https://scontent.fvca1-1.fna.fbcdn.net/v/t39.30808-6/482242951_1184903749670511_116581152088062484_n.jpg?stp=cp6_dst-jpg_tt6&_nc_cat=105&ccb=1-7&_nc_sid=a5f93a&_nc_eui2=AeHl6z1Zf722SPdydZ2cSXjkZpHk_q-4D51mkeT-r7gPndTlCsa2S-9POMvKIBb4ckII1tv_ascEHrs3kes9q9GO&_nc_ohc=0KAgPDwqVoYQ7kNvwGvYZzT&_nc_oc=AdkiSSI5Nm1z4L60wjOWhF2RlhO42CTckj5fJghrGNCIl1rRcnH9YUwQDlrcIYwvWshnvTSvZ0pqlV2sGzg6tPGG&_nc_zt=23&_nc_ht=scontent.fvca1-1.fna&_nc_gid=VKwmNPd5x84LUuWGX44UBw&oh=00_AfpI8odqVyRf4fYhFFiablQhci6WR8tZfRwbNfW2uoUEig&oe=696F885F" # Ảnh Avatar kênh
SOCIAL_LINKS = {
    "facebook": "https://www.facebook.com/phuongmychi",
    "spotify": "https://open.spotify.com/artist/1BcjfrXV4Oe3fK0c8dnxFF?si=8adGRTLqQ4SKtELO5P0Xjw",
    "youtube": "https://www.youtube.com/channel/UCGRIV5jOtKyAibhjBdIndZQ",
    "instagram": "https://www.instagram.com/phuongmychi/",
    "threads": "https://www.threads.net/@phuongmychi"
}

# ==========================================
# --- CÁC HÀM XỬ LÝ SỐ LIỆU (GIỮ NGUYÊN) ---
# ==========================================
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

# ==========================================
# --- GIAO DIỆN & CSS (THAY ĐỔI LỚN) ---
# ==========================================
st.set_page_config(page_title="Phuong My Chi Official", page_icon="👑", layout="wide")

# --- SVG ICONS (Monochrome Style) ---
svg_icons = {
    "facebook": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M14 13.5h2.5l1-4H14v-2c0-1.03 0-2 2-2h1.5V2.14c-.326-.043-1.557-.14-2.857-.14C11.928 2 10 3.657 10 6.7v2.8H7v4h3V22h4v-8.5z"/></svg>""",
    "spotify": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.586 14.424c-.18.295-.563.387-.857.207-2.35-1.434-5.305-1.758-8.78-1.022-.328.084-.65-.133-.73-.463-.085-.33.133-.65.463-.73 3.81-.808 7.075-.44 9.7 1.15.293.18.385.563.206.857zm1.228-2.727c-.226.366-.696.482-1.06.26-2.687-1.652-6.785-2.13-9.965-1.164-.41.122-.835-.126-.96-.533-.122-.41.126-.835.533-.96 3.617-1.1 8.205-.557 11.302 1.345.365.225.482.694.26 1.06zm.11-2.786c-3.22-1.91-8.53-2.088-11.596-1.143-.467.146-.976-.105-1.123-.573-.146-.47.105-.977.573-1.124 3.57-1.1 9.46-.88 13.146 1.31.42.245.553.792.308 1.21-.246.42-.793.553-1.21.308z"/></svg>""",
    "youtube": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M21.582,6.186c-0.23-0.86-0.908-1.538-1.768-1.768C18.254,4,12,4,12,4S5.746,4,4.186,4.418 c-0.86,0.23-1.538,0.908-1.768,1.768C2,7.746,2,12,2,12s0,4.254,0.418,5.814c0.23,0.86,0.908,1.538,1.768,1.768 C5.746,20,12,20,12,20s6.254,0,7.814-0.418c0.86-0.23,1.538-0.908,1.768-1.768C22,16.254,22,12,22,12S22,7.746,21.582,6.186z M10,15 V9l5.208,3L10,15z"/></svg>""",
    "instagram": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>""",
    "threads": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M12.274 2.001c-5.536 0-10.002 4.466-10.002 10.001s4.466 10.002 10.002 10.002 10.002-4.467 10.002-10.002-4.466-10.001-10.002-10.001zm.002 18.126c-4.489 0-8.126-3.636-8.126-8.125 0-4.489 3.637-8.125 8.126-8.125 4.489 0 8.125 3.636 8.125 8.125 0 4.489-3.636 8.125-8.125 8.125zm5.692-8.125h-1.506c-.027-1.975-.918-3.353-2.322-3.737 1.733-.456 2.672-1.721 2.672-3.106 0-1.644-1.407-2.854-3.492-2.854-2.158 0-3.679 1.274-3.679 3.113 0 1.379.896 2.65 2.625 3.105-1.406.388-2.298 1.767-2.323 3.479h-1.531c.038-2.552 1.548-4.567 3.806-5.111-1.847-.598-2.89-2.186-2.89-3.859 0-2.428 2.046-4.323 5.054-4.323 2.968 0 4.858 1.862 4.858 4.293 0 1.67-.989 3.214-2.759 3.833 2.184.552 3.659 2.549 3.701 5.169l-.004-.001zm-6.722-6.641c0-1.189.965-2.147 2.158-2.147 1.236 0 2.085.957 2.085 2.053 0 1.158-.887 2.077-2.118 2.181-1.206-.098-2.125-1.023-2.125-2.087zm2.125 3.585c1.437.127 2.555 1.234 2.555 2.639 0 1.495-1.231 2.697-2.737 2.697-1.541 0-2.792-1.247-2.792-2.794 0-1.454 1.167-2.609 2.685-2.682l.289.14z"/></svg>""",
}

# --- CSS TÙY CHỈNH ---
st.markdown("""
<style>
    /* === CÀI ĐẶT CHUNG === */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { 
        background-color: #0E1117; /* Nền tối chủ đạo */
        color: #E0E0E0; /* Màu chữ sáng */
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    a { text-decoration: none; transition: all 0.3s ease; }

    /* === HEADER & NAVIGATION === */
    .banner-container {
        width: 100%; height: 350px; overflow: hidden;
        border-radius: 0 0 30px 30px; margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        position: relative;
    }
    .banner-img { width: 100%; height: 100%; object-fit: cover; filter: brightness(0.8); }
    .banner-overlay {
        position: absolute; bottom: 0; left: 0; width: 100%;
        background: linear-gradient(to top, #0E1117, transparent);
        height: 150px;
    }

    .profile-section { 
        display: flex; flex-direction: column; align-items: center; text-align: center;
        margin-top: -80px; position: relative; z-index: 10; padding-bottom: 30px;
    }
    .avatar { 
        border-radius: 50%; width: 150px; height: 150px; object-fit: cover;
        border: 4px solid #FFD700; box-shadow: 0 5px 15px rgba(0,0,0,0.5);
        margin-bottom: 15px;
    }
    .artist-name { font-size: 38px; font-weight: 800; margin: 0; color: #FFFFFF; letter-spacing: 1px; }
    .artist-bio { color: #B0B0B0; font-size: 16px; margin: 10px 0 20px 0; max-width: 600px; }
    
    /* Social Icons (Monochrome) */
    .social-links { display: flex; gap: 20px; justify-content: center; margin-top: 15px; }
    .social-icon svg { 
        fill: #AAAAAA; /* Màu xám mặc định */
        transition: fill 0.3s ease, transform 0.3s ease;
    }
    .social-icon:hover svg { 
        fill: #FFFFFF; /* Màu trắng khi hover */
        transform: translateY(-3px);
    }

    /* Style cho Tabs của Streamlit */
    .stTabs [data-baseweb="tab-list"] {
        justify-content: center;
        background-color: transparent;
        padding-bottom: 10px;
        border-bottom: 1px solid #333;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap;
        background-color: transparent;
        border: none; color: #AAAAAA;
        font-weight: 600; font-size: 16px;
    }
    .stTabs [aria-selected="true"] {
        color: #FFD700 !important; /* Màu vàng khi active */
        border-bottom: 3px solid #FFD700 !important;
    }

    /* === CARD SỐ LIỆU TỔNG (METRICS) === */
    .metric-card { 
        background: linear-gradient(145deg, #1A1F26, #12151A);
        padding: 25px 20px; border-radius: 20px; text-align: center; 
        border: 1px solid #2A2F38; 
        box-shadow: 5px 5px 15px rgba(0,0,0,0.3), -5px -5px 15px rgba(255,255,255,0.02);
        transition: transform 0.3s ease;
    }
    .metric-card:hover { transform: translateY(-5px); border-color: #FFD700; }
    .metric-val { font-size: 32px; font-weight: 800; color: white; margin-top: 10px; }
    .metric-lbl { font-size: 13px; text-transform: uppercase; letter-spacing: 1.2px; color: #888; font-weight: 600; }
    .live-dot { height: 8px; width: 8px; background-color: #FF4B4B; border-radius: 50%; display: inline-block; margin-left: 5px; animation: blink 1.5s infinite; }

    /* === VIDEO CARD (Elegant Dark Style - image_5.png) === */
    .video-card-container { margin-bottom: 25px; }
    .video-card {
        background-color: #16181C; /* Nền rất tối */
        border-radius: 16px; overflow: hidden;
        box-shadow: 0 10px 20px rgba(0,0,0,0.4);
        border: 1px solid #2A2F38;
        transition: all 0.3s ease;
    }
    .video-card:hover { 
        box-shadow: 0 15px 30px rgba(0,0,0,0.6);
        border-color: #555;
    }
    .vid-thumb-wrapper { 
        position: relative; width: 100%; padding-top: 56.25%; /* Tỷ lệ 16:9 */
        overflow: hidden; 
    }
    .vid-thumb { 
        position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
        object-fit: cover; transition: transform 0.5s ease;
        opacity: 0.8; /* Làm tối ảnh một chút */
    }
    .video-card:hover .vid-thumb { transform: scale(1.05); opacity: 1; }
    .vid-play-icon {
        position: absolute; top: 50%; left: 50%;
        transform: translate(-50%, -50%) scale(0.8);
        font-size: 50px; color: rgba(255,255,255,0.8);
        opacity: 0; transition: all 0.3s ease;
    }
    .video-card:hover .vid-play-icon { opacity: 1; transform: translate(-50%, -50%) scale(1); }

    .vid-content { padding: 15px; }
    .vid-title { 
        font-size: 15px; font-weight: 700; color: #FFFFFF;
        margin-bottom: 15px; line-height: 1.4;
        height: 42px; overflow: hidden; /* Giới hạn 2 dòng */
        display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    .vid-footer {
        display: flex; justify-content: space-between;
        border-top: 1px solid #2A2F38;
        padding-top: 12px; font-size: 13px; font-weight: 600;
    }
    .stat-item { display: flex; align-items: center; gap: 5px; }
    /* Màu sắc theo yêu cầu image_5.png */
    .stat-view { color: #64B5F6; } /* Xanh dương nhạt */
    .stat-like { color: #81C784; } /* Xanh lá nhạt */
    .stat-comment { color: #FFD54F; } /* Vàng nhạt */

    /* === CALENDAR (Lịch trình - image_6.png style) === */
    .calendar-container {
        background-color: #1A1F26; padding: 30px;
        border-radius: 25px; border: 1px solid #2A2F38;
    }
    .calendar-header { 
        text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 25px; color: #FFF; 
    }
    .calendar-grid {
        display: grid; grid-template-columns: repeat(7, 1fr); gap: 15px;
        text-align: center;
    }
    .cal-day-name { font-weight: 600; color: #888; margin-bottom: 10px; }
    .cal-date {
        background-color: #242B35; color: #FFF;
        padding: 20px 0; border-radius: 15px;
        font-size: 18px; font-weight: bold;
        cursor: pointer; transition: all 0.2s ease;
        box-shadow: inset 0 0 0 1px #333;
    }
    .cal-date:hover { background-color: #FFD700; color: #000; box-shadow: 0 5px 15px rgba(255,215,0,0.3); }
    .cal-date.empty { background-color: transparent; box-shadow: none; cursor: default; }
    
    /* === FOOTER === */
    .custom-footer {
        margin-top: 50px; padding: 30px 0;
        border-top: 1px solid #2A2F38;
        text-align: center; color: #888; font-size: 14px;
    }
    .footer-links a { color: #AAA; margin: 0 10px; font-weight: 600; }
    .footer-links a:hover { color: #FFD700; }

    /* Animations */
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
</style>
""", unsafe_allow_html=True)

# ==========================================
# --- KHỞI TẠO DỮ LIỆU (STATE) ---
# ==========================================
if 'init_done' not in st.session_state:
    df, latest = load_sheet_data()
    st.session_state['df'] = df
    st.session_state['latest'] = latest
    if latest is not None:
        # Khởi tạo số view tổng để chạy hiệu ứng
        st.session_state['total_view_sim'] = int(latest['Youtube_View'])
    else:
        st.session_state['total_view_sim'] = 0
    # Load video lần đầu
    st.session_state['video_data'] = fetch_video_data_api(VIDEO_IDS)
    st.session_state['init_done'] = True

# ==========================================
# --- CẤU TRÚC TRANG WEB (LAYOUT) ---
# ==========================================

# 1. Banner & Profile Header (Luôn hiển thị)
st.markdown(f"""
<div class="banner-container">
    <img src="{BANNER_URL}" class="banner-img">
    <div class="banner-overlay"></div>
</div>
<div class="profile-section">
    <img src="{AVATAR_URL}" class="avatar">
    <h1 class="artist-name">PHƯƠNG MỸ CHI</h1>
    <p class="artist-bio">"Cô bé dân ca" - Biểu tượng âm nhạc trẻ trung, năng động và đầy sáng tạo của Việt Nam.</p>
    <div class="social-links">
        <a href="{SOCIAL_LINKS['facebook']}" target="_blank" class="social-icon" title="Facebook">{svg_icons['facebook']}</a>
        <a href="{SOCIAL_LINKS['spotify']}" target="_blank" class="social-icon" title="Spotify">{svg_icons['spotify']}</a>
        <a href="{SOCIAL_LINKS['youtube']}" target="_blank" class="social-icon" title="YouTube">{svg_icons['youtube']}</a>
        <a href="{SOCIAL_LINKS['instagram']}" target="_blank" class="social-icon" title="Instagram">{svg_icons['instagram']}</a>
        <a href="{SOCIAL_LINKS['threads']}" target="_blank" class="social-icon" title="Threads">{svg_icons['threads']}</a>
    </div>
</div>
""", unsafe_allow_html=True)

# 2. Navigation Tabs (Menu chính)
tab_home, tab_about, tab_schedule, tab_stats, tab_vote = st.tabs([
    "🏠 TRANG CHỦ", "ℹ️ GIỚI THIỆU", "📅 LỊCH TRÌNH", "📊 THỐNG KÊ", "🗳️ VOTING"
])

# ==========================================
# --- NỘI DUNG CÁC TAB ---
# ==========================================

# --- TAB 1: TRANG CHỦ (Real-time Dashboard & Videos) ---
with tab_home:
    st.markdown("### 🔥 REAL-TIME SNAPSHOT", unsafe_allow_html=True)
    metrics_placeholder = st.empty() # Placeholder cho số nhảy

    st.markdown("### 🎬 LATEST RELEASES", unsafe_allow_html=True)
    video_placeholder = st.empty() # Placeholder cho video

# --- TAB 2: GIỚI THIỆU ---
with tab_about:
    st.markdown("""
    ### 🌟 HÀNH TRÌNH ÂM NHẠC
    
    **Phuong My Chi** (sinh năm 2003) là một nữ ca sĩ nổi tiếng Việt Nam, được biết đến rộng rãi sau khi đạt danh hiệu Á quân chương trình *Giọng hát Việt nhí* mùa đầu tiên (2013).
    
    * **2013:** Á quân The Voice Kids Vietnam. Gây bão với "Quê Em Mùa Nước Lũ".
    * **2014-2020:** Theo đuổi dòng nhạc dân ca, trữ tình. Phát hành nhiều album thành công như "Thương về miền Trung", "Chờ người". Đạt giải Mai Vàng, Cống Hiến.
    * **2022-Nay:** Lột xác mạnh mẽ về hình ảnh và phong cách âm nhạc. Kết hợp giữa chất liệu truyền thống và âm nhạc điện tử hiện đại.
    
    **Dấu ấn gần đây:** Album "Vũ Trụ Cò Bay" (2023) là một cú hích lớn, khẳng định tư duy âm nhạc độc đáo và trưởng thành của Phương Mỹ Chi.
    """)
    st.image(BANNER_URL, use_column_width=True)

# --- TAB 3: LỊCH TRÌNH (Calendar UI Placeholder) ---
with tab_schedule:
    st.markdown("""
    ### 📅 LỊCH TRÌNH HOẠT ĐỘNG THÁNG 1/2026
    *Lưu ý: Đây là lịch trình mô phỏng.*
    """)
    # Tạo giao diện lịch bằng HTML/CSS (Mô phỏng image_6.png)
    st.markdown("""
    <div class="calendar-container">
        <div class="calendar-header">January 2026</div>
        <div class="calendar-grid">
            <div class="cal-day-name">T2</div><div class="cal-day-name">T3</div><div class="cal-day-name">T4</div><div class="cal-day-name">T5</div><div class="cal-day-name">T6</div><div class="cal-day-name">T7</div><div class="cal-day-name">CN</div>
            
            <div class="cal-date empty"></div><div class="cal-date empty"></div><div class="cal-date empty"></div>
            <div class="cal-date" title="Sự kiện A">1</div><div class="cal-date">2</div><div class="cal-date" title="Show diễn B">3</div><div class="cal-date">4</div>
            
            <div class="cal-date">5</div><div class="cal-date">6</div><div class="cal-date" title="Quay MV">7</div><div class="cal-date">8</div><div class="cal-date">9</div><div class="cal-date">10</div><div class="cal-date">11</div>
            
            <div class="cal-date">12</div><div class="cal-date">13</div><div class="cal-date">14</div><div class="cal-date" title="Họp báo">15</div><div class="cal-date">16</div><div class="cal-date">17</div><div class="cal-date">18</div>
            
            <div class="cal-date">19</div><div class="cal-date">20</div><div class="cal-date">21</div><div class="cal-date">22</div><div class="cal-date">23</div><div class="cal-date" title="Concert">24</div><div class="cal-date">25</div>
             <div class="cal-date">26</div><div class="cal-date">27</div><div class="cal-date">28</div><div class="cal-date">29</div><div class="cal-date">30</div><div class="cal-date">31</div><div class="cal-date empty"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- TAB 4: THỐNG KÊ CHI TIẾT ---
with tab_stats:
    st.markdown("### 📊 BIỂU ĐỒ TĂNG TRƯỞNG")
    if 'df' in st.session_state and not st.session_state['df'].empty:
        df_chart = st.session_state['df']
        # Tạo biểu đồ với Plotly theme tối
        fig = px.line(df_chart, x='Time', y='Youtube_View', title='Tổng View Kênh Youtube (Theo thời gian)')
        fig.update_traces(line_color='#FF0000', line_width=3)
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font_color='#ccc', title_font_size=20,
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333')
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Đang tải dữ liệu biểu đồ...")

# --- TAB 5: VOTING ---
with tab_vote:
    st.markdown("### 🗳️ CỔNG BÌNH CHỌN")
    st.info("Hiện tại chưa có chiến dịch bình chọn nào đang diễn ra. Vui lòng quay lại sau!")
    # Placeholder cho tương lai
    # st.progress(75, text="Giải thưởng Cống Hiến - Hạng mục Nữ ca sĩ của năm (Đang dẫn đầu!)")


# ==========================================
# --- MAIN LOOP (CHẠY NGẦM ĐỂ CẬP NHẬT LIVE Ở TAB TRANG CHỦ) ---
# ==========================================
# Chỉ chạy vòng lặp update khi đang ở Tab Trang chủ (để tối ưu hiệu năng)
# Tuy nhiên, Streamlit không hỗ trợ detect tab active dễ dàng. 
# Nên ta vẫn chạy ngầm, nhưng chỉ render vào placeholder nếu nó tồn tại.

while True:
    # 1. SIMULATION: Tăng View Ảo cho Tổng Kênh
    st.session_state['total_view_sim'] += random.randint(1, 12)

    # 2. SYNC API: Đồng bộ dữ liệu thật mỗi 60 giây
    if int(time.time()) % 60 == 0:
        df_new, latest_new = load_sheet_data()
        if latest_new is not None:
            st.session_state['latest'] = latest_new
            real_val = int(latest_new['Youtube_View'])
            if real_val > st.session_state['total_view_sim']:
                st.session_state['total_view_sim'] = real_val
        # Cập nhật lại video
        st.session_state['video_data'] = fetch_video_data_api(VIDEO_IDS)

    # 3. RENDER: Cập nhật giao diện TRANG CHỦ
    lat = st.session_state['latest']
    if lat is not None:
        # Render Metrics (Số nhảy)
        with metrics_placeholder.container():
            c1, c2, c3, c4 = st.columns(4)
            # View tổng dùng số mô phỏng (sim)
            c1.markdown(f"""<div class="metric-card"><div class="metric-lbl">TOTAL VIEWS <span class="live-dot"></span></div><div class="metric-val" style="color:#FF4B4B">{st.session_state['total_view_sim']:,}</div></div>""", unsafe_allow_html=True)
            # Các số khác dùng số thật từ sheet
            c2.markdown(f"""<div class="metric-card"><div class="metric-lbl">SUBSCRIBERS</div><div class="metric-val">{lat['Youtube_Sub']:,}</div></div>""", unsafe_allow_html=True)
            c3.markdown(f"""<div class="metric-card"><div class="metric-lbl">TIKTOK FANS</div><div class="metric-val">{lat['TikTok_Follower']:,}</div></div>""", unsafe_allow_html=True)
            c4.markdown(f"""<div class="metric-card"><div class="metric-lbl">SPOTIFY MONTHLY</div><div class="metric-val" style="color:#1DB954">{lat['Spotify_Listener']:,}</div></div>""", unsafe_allow_html=True)

        # Render Video Cards (Số tĩnh - Style mới image_5.png)
        with video_placeholder.container():
            cols = st.columns(3)
            v_data = st.session_state['video_data']
            for i, vid_id in enumerate(VIDEO_IDS):
                if vid_id in v_data:
                    d = v_data[vid_id]
                    with cols[i % 3]:
                        # HTML cấu trúc card mới
                        st.markdown(f"""
                        <div class="video-card-container">
                            <div class="video-card">
                                <a href="https://www.youtube.com/watch?v={d['id']}" target="_blank" class="vid-link">
                                    <div class="vid-thumb-wrapper">
                                        <img src="{d['thumb']}" class="vid-thumb">
                                        <div class="vid-play-icon">▶</div>
                                    </div>
                                </a>
                                <div class="vid-content">
                                    <div class="vid-title">{d['title']}</div>
                                    <div class="vid-footer">
                                        <div class="stat-item stat-view">👁️ {d['view']:,}</div>
                                        <div class="stat-item stat-like">❤ {d['like']:,}</div>
                                        <div class="stat-item stat-comment">💬 {d['comment']:,}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
    
    # 4. FOOTER (Luôn hiển thị cuối trang)
    # Dùng empty container để footer không bị đẩy lên khi nội dung thay đổi
    footer_container = st.empty()
    with footer_container.container():
        st.divider()
        st.markdown("""
        <div class="custom-footer">
            <div class="footer-links">
                <a href="#">Trang chủ</a> | <a href="#">Liên hệ</a> | <a href="#">Điều khoản</a> | <a href="#">Bảo mật</a>
            </div>
            <p style="margin-top: 20px;">© 2026 Nhi Nha Nhi Nhô Cùng Mỹ Chi </p>
            <p style="font-size: 12px; color: #666;">Designed for PMC Fandom.</p>
        </div>
        """, unsafe_allow_html=True)

    time.sleep(1) # Cập nhật mỗi giây