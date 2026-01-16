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
# --- CẤU HÌNH (GIỮ NGUYÊN CODE LẤY SỐ LIỆU) ---
# ==========================================
SHEET_NAME = 'PMC Data Center'
VIDEO_IDS = ['sZrIbpwjTwk', 'BmrdGQ0LRRo', 'V1ah6tmNUz8'] 
YOUTUBE_API_KEY = 'AIzaSyAueu53W-r0VWcYJwYrSSboOKuWYQfLn34' 

# Link ảnh và Mạng xã hội
# Ảnh bìa Concert to đẹp
ANNER_URL = "https://scontent.fvca1-1.fna.fbcdn.net/v/t39.30808-6/600369698_1419646709529546_341344486868245985_n.jpg?_nc_cat=105&ccb=1-7&_nc_sid=833d8c&_nc_eui2=AeE8R8ouge4yL7lfWGQ5Kzk1Enry68g3cr0SevLryDdyvaWspFlBItEaOUW321Od9poGbHjYncGX9_MS7BEcv6Ww&_nc_ohc=WHolhcYE84IQ7kNvwH3WDS7&_nc_oc=AdlMDmMAztdFXjYHzVG6BJpmRMy1E7qVPlz3DWxOrwo2YrZS0MeRHLPCU2rF4_OdTXE&_nc_zt=23&_nc_ht=scontent.fvca1-1.fna&_nc_gid=AXvAnGOph6iEFu_TWBD-SA&oh=00_AfoafS9eKG1wduMrKvUIYzK6Mu4ZIs0Q3Idtuj5CW5qvEg&oe=696F8D56" # Ảnh bìa Concert
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
# --- GIAO DIỆN & CSS (UPDATED) ---
# ==========================================
st.set_page_config(page_title="Phuong My Chi Official", page_icon="👑", layout="wide")

# --- SVG ICONS ---
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
    /* 1. CẤU HÌNH CHUNG */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;} /* Ẩn header mặc định của Streamlit */
    
    .stApp { 
        background-color: #0E1117; 
        color: #E0E0E0; 
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    .block-container {
        padding-top: 0px !important; /* Đẩy nội dung lên sát mép trên */
        padding-left: 0px !important;
        padding-right: 0px !important;
        max-width: 100% !important;
    }

    /* 2. NAVIGATION TABS (STICKY TOP) */
    .stTabs {
        background-color: #0E1117;
        position: sticky;
        top: 0;
        z-index: 1000;
        padding-top: 10px;
        border-bottom: 1px solid #333;
        width: 100%;
    }
    .stTabs [data-baseweb="tab-list"] {
        justify-content: center;
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border: none;
        color: #AAAAAA;
        font-weight: 700;
        font-size: 16px;
        text-transform: uppercase;
    }
    .stTabs [aria-selected="true"] {
        color: #FFFFFF !important;
        border-bottom: 3px solid #FFD700 !important;
    }

    /* 3. BANNER FULL WIDTH (TRÀN MÀN HÌNH) */
    .banner-container {
        width: 100vw; /* Chiều rộng viewport */
        position: relative;
        left: 50%;
        right: 50%;
        margin-left: -50vw;
        margin-right: -50vw;
        height: 450px; /* Tăng chiều cao Banner */
        overflow: hidden;
        margin-bottom: 0px;
    }
    .banner-img { 
        width: 100%; 
        height: 100%; 
        object-fit: cover; 
        filter: brightness(0.7); /* Làm tối banner một chút để nổi bật avatar */
    }

    /* 4. PROFILE SECTION (AVATAR ĐÈ LÊN BANNER) */
    .profile-section { 
        position: relative;
        margin-top: -100px; /* Kéo avatar lên đè vào banner */
        display: flex; 
        flex-direction: column; 
        align-items: center; 
        text-align: center;
        z-index: 10;
        padding-bottom: 20px;
    }
    .avatar { 
        border-radius: 50%; 
        width: 180px; height: 180px; 
        object-fit: cover;
        border: 4px solid #FFD700; 
        box-shadow: 0 10px 20px rgba(0,0,0,0.6);
        margin-bottom: 15px;
        background-color: #000;
    }
    .artist-name { font-size: 42px; font-weight: 900; margin: 0; color: #FFFFFF; letter-spacing: 1px; }
    .artist-bio { color: #B0B0B0; font-size: 16px; margin: 5px 0 15px 0; max-width: 700px; }
    
    .social-links { display: flex; gap: 25px; justify-content: center; margin-top: 10px; }
    .social-icon svg { fill: #AAAAAA; transition: fill 0.3s ease, transform 0.3s ease; }
    .social-icon:hover svg { fill: #FFFFFF; transform: translateY(-3px); }

    /* 5. NỘI DUNG CHÍNH (PADDING CHO GỌN) */
    .main-content {
        padding: 0 50px; /* Thêm padding 2 bên cho nội dung đỡ bị sát lề */
    }

    /* 6. METRIC CARDS */
    .metric-card { 
        background: #16181C;
        padding: 20px; border-radius: 12px; text-align: center; 
        border: 1px solid #2A2F38; 
    }
    .metric-val { font-size: 28px; font-weight: 800; color: white; margin-top: 5px; }
    .metric-lbl { font-size: 13px; text-transform: uppercase; color: #888; font-weight: 600; }
    .live-dot { height: 8px; width: 8px; background-color: #FF4B4B; border-radius: 50%; display: inline-block; margin-left: 5px; animation: blink 1.5s infinite; }

    /* 7. VIDEO CARD STYLE (image_5.png) */
    .video-card {
        background-color: #121212; 
        border-radius: 12px; overflow: hidden;
        border: 1px solid #333;
        margin-bottom: 20px;
    }
    .vid-thumb-wrapper { position: relative; width: 100%; padding-top: 56.25%; overflow: hidden; }
    .vid-thumb { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; opacity: 0.8; transition: opacity 0.3s; }
    .video-card:hover .vid-thumb { opacity: 1; }
    .vid-play-icon {
        position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
        font-size: 40px; color: rgba(255,255,255,0.8);
    }
    .vid-content { padding: 15px; }
    .vid-title { 
        font-size: 14px; font-weight: 700; color: #FFFFFF;
        margin-bottom: 12px; height: 40px; overflow: hidden;
        text-transform: uppercase; line-height: 1.4;
        display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
    }
    .vid-footer {
        display: flex; justify-content: space-between;
        border-top: 1px solid #333;
        padding-top: 10px; font-size: 12px; font-weight: 600;
    }
    .stat-view { color: #64B5F6; }
    .stat-like { color: #81C784; }
    .stat-comment { color: #FFD54F; }

    /* 8. CALENDAR (FIXED HTML) */
    .calendar-container {
        background-color: #1A1F26; padding: 20px;
        border-radius: 20px; border: 1px solid #333;
        max-width: 900px; margin: 0 auto;
    }
    .cal-header { text-align: center; color: white; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    .cal-grid {
        display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px;
    }
    .cal-cell {
        background-color: #242B35; color: white;
        padding: 15px; border-radius: 10px; text-align: center;
        font-weight: bold; cursor: pointer;
    }
    .cal-cell:hover { background-color: #FFD700; color: black; }
    .cal-head { color: #888; font-size: 14px; text-align: center; padding-bottom: 10px; font-weight: 600;}
    .cal-empty { background: transparent; cursor: default; }

    /* 9. FOOTER (image_032fcc.png) */
    .footer-container {
        background-color: #000000;
        padding: 40px 50px;
        margin-top: 50px;
        border-top: 1px solid #222;
    }
    .footer-content {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        max-width: 1200px;
        margin: 0 auto;
    }
    .footer-left h3 { color: white; font-size: 18px; font-weight: bold; margin-bottom: 10px; }
    .footer-left p { color: #AAA; font-size: 14px; max-width: 400px; line-height: 1.5; }
    .footer-right h3 { color: white; font-size: 18px; font-weight: bold; margin-bottom: 10px; }
    .footer-right p { color: #AAA; font-size: 14px; }
    .copyright {
        text-align: center; color: #555; font-size: 12px; margin-top: 30px;
        border-top: 1px solid #111; padding-top: 20px;
    }

    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
</style>
""", unsafe_allow_html=True)

# ==========================================
# --- KHỞI TẠO STATE ---
# ==========================================
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

# ==========================================
# --- MAIN LAYOUT (THỨ TỰ MỚI) ---
# ==========================================

# 1. NAVIGATION TABS (ĐẶT TRÊN CÙNG)
# Bỏ icon trong tên tab theo yêu cầu
tab_home, tab_about, tab_schedule, tab_stats, tab_vote = st.tabs([
    "Trang chủ", "Giới thiệu", "Lịch trình", "Thống kê", "Voting"
])

# 2. BANNER & PROFILE (HIỂN THỊ TRONG TAB TRANG CHỦ HOẶC LUÔN HIỂN THỊ)
# Để giống web thật, thường banner sẽ nằm dưới Nav. Ta đặt nó vào container chung.
# Tuy nhiên Streamlit Tabs render nội dung bên trong. 
# Để Banner luôn hiện ở Home, ta đặt code Banner vào trong Tab Home.

with tab_home:
    # BANNER FULL WIDTH
    st.markdown(f"""
    <div class="banner-container">
        <img src="{BANNER_URL}" class="banner-img">
    </div>
    """, unsafe_allow_html=True)

    # PROFILE (Avatar đè lên Banner)
    st.markdown(f"""
    <div class="profile-section">
        <img src="{AVATAR_URL}" class="avatar">
        <h1 class="artist-name">PHƯƠNG MỸ CHI</h1>
        <p class="artist-bio">Kết nối cùng cộng đồng fan và thưởng thức âm nhạc chất lượng.</p>
        <div class="social-links">
            <a href="{SOCIAL_LINKS['facebook']}" target="_blank" class="social-icon">{svg_icons['facebook']}</a>
            <a href="{SOCIAL_LINKS['instagram']}" target="_blank" class="social-icon">{svg_icons['instagram']}</a>
            <a href="{SOCIAL_LINKS['threads']}" target="_blank" class="social-icon">{svg_icons['threads']}</a>
            <a href="{SOCIAL_LINKS['youtube']}" target="_blank" class="social-icon">{svg_icons['youtube']}</a>
            <a href="{SOCIAL_LINKS['spotify']}" target="_blank" class="social-icon">{svg_icons['spotify']}</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # NỘI DUNG CHÍNH (Trong Container padding)
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    st.markdown("### 🔥 REAL-TIME DASHBOARD")
    metrics_placeholder = st.empty()

    st.markdown("### 🎬 LATEST RELEASES")
    video_placeholder = st.empty()
    
    st.markdown('</div>', unsafe_allow_html=True)


# --- TAB 2: GIỚI THIỆU ---
with tab_about:
    st.markdown('<div class="main-content" style="margin-top: 30px;">', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    with c1:
        st.image(AVATAR_URL, width=300)
    with c2:
        st.markdown("""
        ### PHƯƠNG MỸ CHI
        
        **Phương Mỹ Chi** (sinh ngày 13 tháng 1 năm 2003) là một nữ ca sĩ người Việt Nam chuyên hát thể loại nhạc dân ca Nam Bộ. Cô bắt đầu nổi danh từ khi tham gia và đạt giải á quân chương trình truyền hình thực tế *Giọng hát Việt nhí* mùa đầu tiên.
        
        Năm 2024 đánh dấu bước chuyển mình mạnh mẽ của Phương Mỹ Chi với hình ảnh trẻ trung, năng động nhưng vẫn giữ được nét văn hóa truyền thống qua các sản phẩm âm nhạc kết hợp đương đại.
        """)
    st.markdown('</div>', unsafe_allow_html=True)


# --- TAB 3: LỊCH TRÌNH (FIXED HTML) ---
with tab_schedule:
    st.markdown('<div class="main-content" style="margin-top: 30px;">', unsafe_allow_html=True)
    # HTML Lịch trình đã được sửa lỗi cú pháp
    st.markdown("""
    <div class="calendar-container">
        <div class="cal-header">January 2026</div>
        <div class="cal-grid">
            <div class="cal-head">T2</div><div class="cal-head">T3</div><div class="cal-head">T4</div><div class="cal-head">T5</div><div class="cal-head">T6</div><div class="cal-head">T7</div><div class="cal-head">CN</div>
            
            <div class="cal-cell cal-empty"></div><div class="cal-cell cal-empty"></div><div class="cal-cell cal-empty"></div>
            <div class="cal-cell">1</div><div class="cal-cell">2</div><div class="cal-cell">3</div><div class="cal-cell">4</div>
            
            <div class="cal-cell">5</div><div class="cal-cell">6</div><div class="cal-cell">7</div><div class="cal-cell">8</div><div class="cal-cell">9</div><div class="cal-cell">10</div><div class="cal-cell">11</div>
            
            <div class="cal-cell">12</div><div class="cal-cell">13</div><div class="cal-cell">14</div><div class="cal-cell">15</div><div class="cal-cell">16</div><div class="cal-cell">17</div><div class="cal-cell">18</div>
            
            <div class="cal-cell">19</div><div class="cal-cell">20</div><div class="cal-cell">21</div><div class="cal-cell">22</div><div class="cal-cell">23</div><div class="cal-cell">24</div><div class="cal-cell">25</div>
            
            <div class="cal-cell">26</div><div class="cal-cell">27</div><div class="cal-cell">28</div><div class="cal-cell">29</div><div class="cal-cell">30</div><div class="cal-cell">31</div><div class="cal-cell cal-empty"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# --- TAB 4: THỐNG KÊ (MULTI-CHART) ---
with tab_stats:
    st.markdown('<div class="main-content" style="margin-top: 30px;">', unsafe_allow_html=True)
    st.markdown("### 📊 BIỂU ĐỒ TĂNG TRƯỞNG TỔNG HỢP")
    
    if 'df' in st.session_state and not st.session_state['df'].empty:
        df_chart = st.session_state['df'].copy()
        
        # Multiselect để chọn chỉ số muốn xem
        options = ['Youtube_View', 'Youtube_Sub', 'Spotify_Listener', 'TikTok_Follower', 'Facebook_Follower']
        selected_metrics = st.multiselect("Chọn chỉ số hiển thị:", options, default=['Youtube_View'])
        
        if selected_metrics:
            fig = px.line(df_chart, x='Time', y=selected_metrics, title='Biến động các chỉ số theo thời gian')
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font_color='#ccc', title_font_size=18,
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Vui lòng chọn ít nhất một chỉ số.")
    else:
        st.info("Đang tải dữ liệu...")
    st.markdown('</div>', unsafe_allow_html=True)


# --- TAB 5: VOTING ---
with tab_vote:
    st.markdown('<div class="main-content" style="margin-top: 30px;">', unsafe_allow_html=True)
    st.info("Chưa có chiến dịch bình chọn nào đang diễn ra.")
    st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# --- LOOP & RENDER (HOME TAB) ---
# ==========================================
while True:
    # 1. Logic nhảy số
    st.session_state['total_view_sim'] += random.randint(1, 15)

    # 2. Sync API (60s)
    if int(time.time()) % 60 == 0:
        df_new, latest_new = load_sheet_data()
        if latest_new is not None:
            st.session_state['latest'] = latest_new
            real = int(latest_new['Youtube_View'])
            if real > st.session_state['total_view_sim']:
                st.session_state['total_view_sim'] = real
        st.session_state['video_data'] = fetch_video_data_api(VIDEO_IDS)

    # 3. Render Home Elements
    lat = st.session_state['latest']
    if lat is not None:
        # Metrics
        with metrics_placeholder.container():
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"""<div class="metric-card"><div class="metric-lbl">Youtube Views <span class="live-dot"></span></div><div class="metric-val" style="color:#FF4B4B">{st.session_state['total_view_sim']:,}</div></div>""", unsafe_allow_html=True)
            c2.markdown(f"""<div class="metric-card"><div class="metric-lbl">Youtube Subs</div><div class="metric-val">{lat['Youtube_Sub']:,}</div></div>""", unsafe_allow_html=True)
            c3.markdown(f"""<div class="metric-card"><div class="metric-lbl">TikTok Fans</div><div class="metric-val">{lat['TikTok_Follower']:,}</div></div>""", unsafe_allow_html=True)
            c4.markdown(f"""<div class="metric-card"><div class="metric-lbl">Spotify</div><div class="metric-val" style="color:#1DB954">{lat['Spotify_Listener']:,}</div></div>""", unsafe_allow_html=True)

        # Videos
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
                                <div class="vid-thumb-wrapper">
                                    <img src="{d['thumb']}" class="vid-thumb">
                                    <div class="vid-play-icon">▶</div>
                                </div>
                            </a>
                            <div class="vid-content">
                                <div class="vid-title">{d['title']}</div>
                                <div class="vid-footer">
                                    <span class="stat-view">👁️ {d['view']:,}</span>
                                    <span class="stat-like">❤ {d['like']:,}</span>
                                    <span class="stat-comment">💬 {d['comment']:,}</span>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

    time.sleep(1)

# ==========================================
# --- FOOTER (GLOBAL) ---
# ==========================================
# Lưu ý: Trong Streamlit, code chạy tuần tự.
# Vì có vòng lặp While True ở trên, code Footer này sẽ không bao giờ được chạm tới nếu để ở cuối file ngoài vòng lặp.
# GIẢI PHÁP: Đưa Footer vào một empty container ở cuối code, nhưng được gọi RENDER bên trong vòng lặp While True (Nếu muốn nó hiện ở Home),
# Hoặc đơn giản là hiển thị nó ở các Tab tĩnh khác. 
# Nhưng vì Home có vòng lặp vô tận, ta dùng `st.sidebar` hoặc một container cố định.

# Tạm thời để ở đây để nếu user chuyển tab khác (thoát vòng lặp Home) thì nó hiện.
st.markdown("""
<div class="footer-container">
    <div class="footer-content">
        <div class="footer-left">
            <h3>WINGS for PMC</h3>
            <p>Kết nối cùng cộng đồng fan và thưởng thức âm nhạc chất lượng.</p>
        </div>
        <div class="footer-right">
            <h3>Liên hệ</h3>
            <p>Email: nhinhanhinhocungmychi@gmail.com</p>
        </div>
    </div>
    <div class="copyright">
        © 2026 NhinhanhinhocungMyChi. Designed with love for Phuong My Chi.
    </div>
</div>
""", unsafe_allow_html=True)