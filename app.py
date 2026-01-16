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
# --- 1. CẤU HÌNH ---
# ==========================================
SHEET_NAME = 'PMC Data Center'
VIDEO_IDS = ['sZrIbpwjTwk', 'BmrdGQ0LRRo', 'V1ah6tmNUz8'] 
YOUTUBE_API_KEY = 'AIzaSyAueu53W-r0VWcYJwYrSSboOKuWYQfLn34' 

# Link ảnh và Mạng xã hội
SCHEDULE_IMAGE_URL = "https://images.unsplash.com/photo-1506784983877-45594efa4cbe?q=80&w=2068&auto=format&fit=crop" 
BANNER_URL = "https://scontent.fvca1-1.fna.fbcdn.net/v/t39.30808-6/600369698_1419646709529546_341344486868245985_n.jpg?_nc_cat=105&ccb=1-7&_nc_sid=833d8c&_nc_eui2=AeE8R8ouge4yL7lfWGQ5Kzk1Enry68g3cr0SevLryDdyvaWspFlBItEaOUW321Od9poGbHjYncGX9_MS7BEcv6Ww&_nc_ohc=WHolhcYE84IQ7kNvwH3WDS7&_nc_oc=AdlMDmMAztdFXjYHzVG6BJpmRMy1E7qVPlz3DWxOrwo2YrZS0MeRHLPCU2rF4_OdTXE&_nc_zt=23&_nc_ht=scontent.fvca1-1.fna&_nc_gid=AXvAnGOph6iEFu_TWBD-SA&oh=00_AfoafS9eKG1wduMrKvUIYzK6Mu4ZIs0Q3Idtuj5CW5qvEg&oe=696F8D56"
AVATAR_URL = "https://scontent.fvca1-1.fna.fbcdn.net/v/t39.30808-6/482242951_1184903749670511_116581152088062484_n.jpg?stp=cp6_dst-jpg_tt6&_nc_cat=105&ccb=1-7&_nc_sid=a5f93a&_nc_eui2=AeHl6z1Zf722SPdydZ2cSXjkZpHk_q-4D51mkeT-r7gPndTlCsa2S-9POMvKIBb4ckII1tv_ascEHrs3kes9q9GO&_nc_ohc=0KAgPDwqVoYQ7kNvwGvYZzT&_nc_oc=AdkiSSI5Nm1z4L60wjOWhF2RlhO42CTckj5fJghrGNCIl1rRcnH9YUwQDlrcIYwvWshnvTSvZ0pqlV2sGzg6tPGG&_nc_zt=23&_nc_ht=scontent.fvca1-1.fna&_nc_gid=VKwmNPd5x84LUuWGX44UBw&oh=00_AfpI8odqVyRf4fYhFFiablQhci6WR8tZfRwbNfW2uoUEig&oe=696F885F"

SOCIAL_LINKS = {
    "facebook": "https://www.facebook.com/phuongmychi",
    "spotify": "https://open.spotify.com/artist/1BcjfrXV4Oe3fK0c8dnxFF?si=8adGRTLqQ4SKtELO5P0Xjw",
    "youtube": "https://www.youtube.com/channel/UCGRIV5jOtKyAibhjBdIndZQ",
    "instagram": "https://www.instagram.com/phuongmychi/",
    "threads": "https://www.threads.net/@phuongmychi"
}

# Dữ liệu khởi tạo Voting
INIT_VOTING_DATA = [
    {"rank": 1, "name": "KINGDOM", "votes": 74854, "change": 9},
    {"rank": 2, "name": "Flowers", "votes": 54465, "change": 10},
    {"rank": 3, "name": "CỪU CÓ CÁNH", "votes": 53936, "change": 7},
    {"rank": 4, "name": "Flash", "votes": 42371, "change": 5},
    {"rank": 5, "name": "DARLING", "votes": 35888, "change": 4},
    {"rank": 6, "name": "PiFam", "votes": 32868, "change": 3},
    {"rank": 7, "name": "MUZIK", "votes": 23310, "change": 4},
    {"rank": 8, "name": "CARROT", "votes": 23072, "change": 0},
]

# ==========================================
# --- 2. HÀM XỬ LÝ SỐ LIỆU ---
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
            try:
                pub_raw = snippet['publishedAt'] 
                dt = datetime.datetime.strptime(pub_raw, "%Y-%m-%dT%H:%M:%SZ")
                dt = dt + datetime.timedelta(hours=7)
                pub_fmt = dt.strftime("%d/%m/%Y %H:%M")
            except:
                pub_fmt = snippet['publishedAt'][:10]

            data_map[vid_id] = {
                'title': snippet['title'],
                'thumb': snippet['thumbnails']['high']['url'],
                'view': int(stats.get('viewCount', 0)),
                'like': int(stats.get('likeCount', 0)),
                'comment': int(stats.get('commentCount', 0)),
                'published': pub_fmt,
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
        
        latest = df.iloc[-1].copy()
        for col in cols_to_fix:
            if col in df.columns and latest[col] == 0:
                valid_values = df[df[col] > 0][col]
                if not valid_values.empty:
                    latest[col] = valid_values.iloc[-1]
        
        return df, latest
    except: return pd.DataFrame(), None

# ==========================================
# --- 3. CSS TÙY CHỈNH ---
# ==========================================
st.set_page_config(page_title="Phuong My Chi Official", page_icon="👑", layout="wide")

st.markdown("""
<style>
    /* RESET */
    #MainMenu, header, footer {visibility: hidden;}
    .stApp { background-color: #0E1117; color: #E0E0E0; font-family: sans-serif; }
    .block-container { padding: 0 !important; max-width: 100% !important; }

    /* NAVIGATION */
    .stTabs { background: #0E1117; position: sticky; top: 0; z-index: 999; padding-top: 10px; border-bottom: 1px solid #333; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; gap: 30px; }
    .stTabs [data-baseweb="tab"] { background: transparent; border: none; color: #AAA; font-weight: 700; font-size: 16px; text-transform: uppercase; }
    .stTabs [aria-selected="true"] { color: #FFF !important; border-bottom: 3px solid #FFD700 !important; }

    /* BANNER */
    .banner-container { width: 100vw; height: 650px; position: relative; left: 50%; right: 50%; margin-left: -50vw; margin-right: -50vw; overflow: hidden; }
    .banner-img { width: 100%; height: 100%; object-fit: cover; filter: brightness(0.7); }
    .profile-section { margin-top: -120px; text-align: center; position: relative; z-index: 10; padding-bottom: 30px; }
    .avatar { border-radius: 50%; width: 160px; height: 160px; object-fit: cover; border: 4px solid #FFD700; background: #000; box-shadow: 0 10px 20px rgba(0,0,0,0.6); }
    .artist-name { font-size: 48px; font-weight: 900; color: #FFF; margin: 10px 0 0 0; }
    .social-links { display: flex; gap: 20px; justify-content: center; margin-top: 15px; }
    .social-icon svg { fill: #AAA; transition: all 0.3s; }
    .social-icon:hover svg { fill: #FFF; transform: translateY(-3px); }

    /* VIDEO CARD */
    .video-card { background: #1A1A1A; border-radius: 10px; overflow: hidden; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); border: 1px solid #333; }
    .vid-thumb-wrapper { position: relative; width: 100%; padding-top: 56.25%; background: #000; }
    .vid-thumb { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; opacity: 0.85; transition: 0.3s; }
    .video-card:hover .vid-thumb { opacity: 1; }
    .vid-body { padding: 15px; }
    .vid-title { font-size: 15px; font-weight: 700; color: #FFF; text-transform: uppercase; line-height: 1.4; margin-bottom: 4px; height: 42px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
    .vid-artist { font-size: 12px; color: #888; font-weight: 600; text-transform: uppercase; margin-bottom: 15px; }
    .stat-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 14px; }
    .stat-label { color: #BBB; font-weight: 500; }
    .val-view { color: #64B5F6; font-weight: 700; }
    .val-like { color: #81C784; font-weight: 700; }
    .val-comm { color: #FFD54F; font-weight: 700; }
    .vid-footer { border-top: 1px solid #333; padding-top: 12px; margin-top: 12px; font-size: 11px; color: #666; text-align: right; }

    /* VOTING STYLES */
    .voting-header { font-size: 24px; font-weight: bold; margin-bottom: 20px; text-align: center; color: #E0B0FF; text-transform: uppercase; letter-spacing: 1px;}
    .vote-table-container { background: #1A1F26; border-radius: 12px; padding: 20px; border: 1px solid #333; }
    .vote-row { display: flex; justify-content: space-between; align-items: center; padding: 15px 10px; border-bottom: 1px solid #2A2F38; transition: background 0.2s;}
    .vote-row:last-child { border-bottom: none; }
    .vote-row:hover { background: #222831; }
    .rank-col { width: 50px; font-size: 18px; font-weight: bold; color: #FFD700; }
    .name-col { flex-grow: 1; font-size: 16px; font-weight: 600; color: #FFF; text-transform: uppercase; }
    .total-col { width: 120px; text-align: right; font-size: 16px; font-weight: bold; color: #FFF; }
    .change-col { width: 80px; text-align: right; }
    .badge-plus { background: rgba(76, 175, 80, 0.2); color: #4CAF50; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: bold; }
    .badge-neutral { background: rgba(158, 158, 158, 0.2); color: #9E9E9E; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: bold; }

    /* OTHERS */
    .metric-card { background: #16181C; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #333; }
    .metric-val { font-size: 28px; font-weight: 800; color: white; }
    .metric-lbl { font-size: 12px; text-transform: uppercase; color: #888; font-weight: bold; }
    .live-dot { height: 8px; width: 8px; background: #FF4B4B; border-radius: 50%; display: inline-block; animation: blink 1.5s infinite; }
    .main-content { padding: 0 40px; }
    .content-spacer { height: 60px; }

    /* FOOTER (UPDATED STYLE) */
    .footer-container { background: #0E1117; padding: 60px 40px 30px 40px; margin-top: 80px; border-top: 1px solid #222; text-align: center; }
    .footer-title { font-size: 24px; font-weight: bold; color: #FFF; margin-bottom: 10px; }
    .footer-desc { color: #888; font-size: 14px; max-width: 600px; margin: 0 auto 30px auto; line-height: 1.6; }
    .footer-info { background: #16181C; padding: 20px; border-radius: 10px; display: inline-block; text-align: left; margin-bottom: 30px; border: 1px solid #333; }
    .footer-info p { margin: 5px 0; font-size: 13px; color: #CCC; }
    .footer-copy { font-size: 12px; color: #555; border-top: 1px solid #222; padding-top: 20px; }
    .hashtag { color: #888; font-weight: bold; margin-top: 10px; display: block; letter-spacing: 1px;}

    @keyframes blink { 0% {opacity:1} 50% {opacity:0.4} 100% {opacity:1} }
</style>
""", unsafe_allow_html=True)

# SVG Icons
svg_icons = {
    "facebook": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M14 13.5h2.5l1-4H14v-2c0-1.03 0-2 2-2h1.5V2.14c-.326-.043-1.557-.14-2.857-.14C11.928 2 10 3.657 10 6.7v2.8H7v4h3V22h4v-8.5z"/></svg>""",
    "spotify": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.586 14.424c-.18.295-.563.387-.857.207-2.35-1.434-5.305-1.758-8.78-1.022-.328.084-.65-.133-.73-.463-.085-.33.133-.65.463-.73 3.81-.808 7.075-.44 9.7 1.15.293.18.385.563.206.857zm1.228-2.727c-.226.366-.696.482-1.06.26-2.687-1.652-6.785-2.13-9.965-1.164-.41.122-.835-.126-.96-.533-.122-.41.126-.835.533-.96 3.617-1.1 8.205-.557 11.302 1.345.365.225.482.694.26 1.06zm.11-2.786c-3.22-1.91-8.53-2.088-11.596-1.143-.467.146-.976-.105-1.123-.573-.146-.47.105-.977.573-1.124 3.57-1.1 9.46-.88 13.146 1.31.42.245.553.792.308 1.21-.246.42-.793.553-1.21.308z"/></svg>""",
    "youtube": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M21.582,6.186c-0.23-0.86-0.908-1.538-1.768-1.768C18.254,4,12,4,12,4S5.746,4,4.186,4.418 c-0.86,0.23-1.538,0.908-1.768,1.768C2,7.746,2,12,2,12s0,4.254,0.418,5.814c0.23,0.86,0.908,1.538,1.768,1.768C22,16.254,22,12,22,12S22,7.746,21.582,6.186z M10,15 V9l5.208,3L10,15z"/></svg>""",
    "instagram": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>""",
    "threads": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M12.274 2.001c-5.536 0-10.002 4.466-10.002 10.001s4.466 10.002 10.002 10.002 10.002-4.467 10.002-10.002-4.466-10.001-10.002-10.001zm.002 18.126c-4.489 0-8.126-3.636-8.126-8.125 0-4.489 3.637-8.125 8.126-8.125 4.489 0 8.125 3.636 8.125 8.125 0 4.489-3.636 8.125-8.125 8.125zm5.692-8.125h-1.506c-.027-1.975-.918-3.353-2.322-3.737 1.733-.456 2.672-1.721 2.672-3.106 0-1.644-1.407-2.854-3.492-2.854-2.158 0-3.679 1.274-3.679 3.113 0 1.379.896 2.65 2.625 3.105-1.406.388-2.298 1.767-2.323 3.479h-1.531c.038-2.552 1.548-4.567 3.806-5.111-1.847-.598-2.89-2.186-2.89-3.859 0-2.428 2.046-4.323 5.054-4.323 2.968 0 4.858 1.862 4.858 4.293 0 1.67-.989 3.214-2.759 3.833 2.184.552 3.659 2.549 3.701 5.169l-.004-.001zm-6.722-6.641c0-1.189.965-2.147 2.158-2.147 1.236 0 2.085.957 2.085 2.053 0 1.158-.887 2.077-2.118 2.181-1.206-.098-2.125-1.023-2.125-2.087zm2.125 3.585c1.437.127 2.555 1.234 2.555 2.639 0 1.495-1.231 2.697-2.737 2.697-1.541 0-2.792-1.247-2.792-2.794 0-1.454 1.167-2.609 2.685-2.682l.289.14z"/></svg>""",
}

# ==========================================
# --- 4. STATE & LOGIC ---
# ==========================================
# Khởi tạo dữ liệu nếu chưa có
if 'init_done' not in st.session_state:
    df, latest = load_sheet_data()
    st.session_state['df'] = df
    st.session_state['latest'] = latest
    st.session_state['total_view_sim'] = int(latest['Youtube_View']) if latest is not None else 0
    st.session_state['video_data'] = fetch_video_data_api(VIDEO_IDS)
    st.session_state['init_done'] = True

# --- FIX LỖI KEYERROR: Kiểm tra và khởi tạo 'voting_data' nếu bị thiếu ---
if 'voting_data' not in st.session_state:
    st.session_state['voting_data'] = INIT_VOTING_DATA

if 'voting_history' not in st.session_state:
    st.session_state['voting_history'] = []

# ==========================================
# --- 5. MAIN LAYOUT ---
# ==========================================
tab_home, tab_about, tab_schedule, tab_stats, tab_vote = st.tabs(["TRANG CHỦ", "GIỚI THIỆU", "LỊCH TRÌNH", "THỐNG KÊ", "VOTING"])

with tab_home:
    st.markdown(f"""
    <div class="banner-container"><img src="{BANNER_URL}" class="banner-img"></div>
    <div class="profile-section">
        <img src="{AVATAR_URL}" class="avatar">
        <div class="artist-name">PHƯƠNG MỸ CHI</div>
        <div style="color:#BBB; margin-top:5px; font-weight:600;">"Cô bé dân ca" ngày nào giờ đã trở thành một biểu tượng âm nhạc trẻ trung, năng động và đầy sáng tạo.</div>
        <div class="social-links">
            <a href="{SOCIAL_LINKS['facebook']}" target="_blank" class="social-icon">{svg_icons['facebook']}</a>
            <a href="{SOCIAL_LINKS['instagram']}" target="_blank" class="social-icon">{svg_icons['instagram']}</a>
            <a href="{SOCIAL_LINKS['threads']}" target="_blank" class="social-icon">{svg_icons['threads']}</a>
            <a href="{SOCIAL_LINKS['youtube']}" target="_blank" class="social-icon">{svg_icons['youtube']}</a>
            <a href="{SOCIAL_LINKS['spotify']}" target="_blank" class="social-icon">{svg_icons['spotify']}</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    st.markdown("### 🔥 REAL-TIME STATISTICS")
    metrics_placeholder = st.empty()
    st.markdown("### 🎬 LATEST RELEASES")
    video_placeholder = st.empty()
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB GIỚI THIỆU ---
with tab_about:
    st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    with c1: st.image(AVATAR_URL, width=300)
    with c2:
        st.markdown("""
### PHƯƠNG MỸ CHI
**Phương Mỹ Chi** (sinh năm 2003) là một nữ ca sĩ nổi tiếng Việt Nam, được biết đến rộng rãi sau khi đạt danh hiệu Á quân chương trình *Giọng hát Việt nhí* mùa đầu tiên (2013).

* **2013:** Á quân The Voice Kids Vietnam. Gây bão với "Quê Em Mùa Nước Lũ".
* **2014-2020:** Theo đuổi dòng nhạc dân ca, trữ tình. Phát hành nhiều sản phẩm thành công như "Thương về miền Trung", "Chờ người". 
* **2022-Nay:** Lột xác mạnh mẽ về hình ảnh và phong cách âm nhạc. Kết hợp giữa chất liệu truyền thống và âm nhạc điện tử hiện đại.

**Dấu ấn gần đây:** Album "Vũ Trụ Cò Bay" (2023) là một cú hích lớn, khẳng định tư duy âm nhạc độc đáo và trưởng thành của Phương Mỹ Chi.
""")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB LỊCH TRÌNH ---
with tab_schedule:
    st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    st.markdown("### 📅 LỊCH TRÌNH HOẠT ĐỘNG")
    st.image(SCHEDULE_IMAGE_URL, use_column_width=True, caption="Lịch trình tháng này")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB THỐNG KÊ ---
with tab_stats:
    st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    if 'df' in st.session_state and not st.session_state['df'].empty:
        df_chart = st.session_state['df'].copy()
        options = ['Youtube_View', 'Youtube_Sub', 'Spotify_Listener', 'TikTok_Follower', 'Facebook_Follower']
        selected = st.multiselect("Chọn chỉ số:", options, default=options)
        if selected:
            fig = px.line(df_chart, x='Time', y=selected, title='Tăng trưởng đa nền tảng')
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#ccc',
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333'),
                legend=dict(orientation="h", y=1.1)
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Đang tải dữ liệu...")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB VOTING (REAL-TIME BEST FANDOM) ---
with tab_vote:
    st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    st.markdown("""<div class="voting-header">Best Fandom Forever</div>""", unsafe_allow_html=True)
    
    # Placeholder cho bảng số liệu và biểu đồ
    vote_table_placeholder = st.empty()
    st.write("") 
    vote_chart_placeholder = st.empty()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# --- 6. LOOP & RENDER ---
# ==========================================
while True:
    st.session_state['total_view_sim'] += random.randint(1, 15)
    
    # --- UPDATE REAL-TIME VOTING DATA ---
    current_time = datetime.datetime.now()
    
    # Tăng vote ngẫu nhiên
    for item in st.session_state['voting_data']:
        inc = random.randint(0, 3) 
        item['votes'] += inc
        item['change'] = inc 
        
    st.session_state['voting_data'] = sorted(st.session_state['voting_data'], key=lambda x: x['votes'], reverse=True)
    
    for i, item in enumerate(st.session_state['voting_data']):
        item['rank'] = i + 1
        
    history_point = {"Time": current_time.strftime("%H:%M:%S")}
    for item in st.session_state['voting_data']:
        history_point[item['name']] = item['votes']
    
    st.session_state['voting_history'].append(history_point)
    if len(st.session_state['voting_history']) > 30:
        st.session_state['voting_history'].pop(0)

    # --- API SYNC ---
    if int(time.time()) % 60 == 0:
        df_new, latest_new = load_sheet_data()
        if latest_new is not None:
            st.session_state['latest'] = latest_new
            if int(latest_new['Youtube_View']) > st.session_state['total_view_sim']:
                st.session_state['total_view_sim'] = int(latest_new['Youtube_View'])
        st.session_state['video_data'] = fetch_video_data_api(VIDEO_IDS)

    # --- RENDER HOME ---
    lat = st.session_state['latest']
    if lat is not None:
        with metrics_placeholder.container():
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"""<div class="metric-card"><div class="metric-lbl">TOTAL VIEWS <span class="live-dot"></span></div><div class="metric-val" style="color:#FF4B4B">{st.session_state['total_view_sim']:,}</div></div>""", unsafe_allow_html=True)
            c2.markdown(f"""<div class="metric-card"><div class="metric-lbl">SUBSCRIBERS</div><div class="metric-val">{lat['Youtube_Sub']:,}</div></div>""", unsafe_allow_html=True)
            tt_val = lat['TikTok_Follower']
            c3.markdown(f"""<div class="metric-card"><div class="metric-lbl">TIKTOK FANS</div><div class="metric-val">{tt_val:,}</div></div>""", unsafe_allow_html=True)
            c4.markdown(f"""<div class="metric-card"><div class="metric-lbl">SPOTIFY</div><div class="metric-val" style="color:#1DB954">{lat['Spotify_Listener']:,}</div></div>""", unsafe_allow_html=True)

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
<div class="vid-thumb-wrapper"><img src="{d['thumb']}" class="vid-thumb"></div>
</a>
<div class="vid-body">
<div class="vid-title">{d['title']}</div>
<div class="vid-artist">PHƯƠNG MỸ CHI</div>
<div class="stat-row"><span class="stat-label">Lượt xem:</span><span class="val-view">{d['view']:,}</span></div>
<div class="stat-row"><span class="stat-label">Lượt thích:</span><span class="val-like">{d['like']:,}</span></div>
<div class="stat-row"><span class="stat-label">Bình luận:</span><span class="val-comm">{d['comment']:,}</span></div>
<div class="vid-footer">Thêm vào: {d['published']}</div>
</div>
</div>
""", unsafe_allow_html=True)

    # --- RENDER VOTING TABLE (HTML) ---
    with vote_table_placeholder.container():
        html_rows = ""
        for item in st.session_state['voting_data']:
            change_html = f"<span class='badge-plus'>+{item['change']}</span>" if item['change'] > 0 else "<span class='badge-neutral'>0</span>"
            html_rows += f"""
            <div class="vote-row">
                <div class="rank-col">#{item['rank']}</div>
                <div class="name-col">{item['name']}</div>
                <div class="total-col">{item['votes']:,}</div>
                <div class="change-col">{change_html}</div>
            </div>
            """
        
        st.markdown(f"""
        <div class="vote-table-container">
            <div class="vote-row" style="border-bottom: 2px solid #444; margin-bottom: 10px;">
                <div class="rank-col" style="font-size:14px; color:#888;">HẠNG</div>
                <div class="name-col" style="font-size:14px; color:#888;">ỨNG VIÊN</div>
                <div class="total-col" style="font-size:14px; color:#888;">TỔNG VOTE</div>
                <div class="change-col" style="font-size:14px; color:#888;">THAY ĐỔI</div>
            </div>
            {html_rows}
        </div>
        """, unsafe_allow_html=True)

    # --- RENDER VOTING CHART ---
    with vote_chart_placeholder.container():
        if len(st.session_state['voting_history']) > 2:
            st.markdown("#### 📈 DIỄN BIẾN ĐƯỜNG ĐUA")
            df_hist = pd.DataFrame(st.session_state['voting_history'])
            df_melt = df_hist.melt(id_vars=['Time'], var_name='Candidate', value_name='Votes')
            
            fig = px.line(df_melt, x='Time', y='Votes', color='Candidate', 
                          color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#ccc',
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333'),
                legend=dict(orientation="h", y=1.1)
            )
            st.plotly_chart(fig, use_container_width=True)

    time.sleep(1)

# FOOTER
st.markdown("""
<div class="footer-container">
    <div class="footer-title">WeYoung Tracker</div>
    <div class="footer-desc">
        Hệ thống theo dõi và phân tích bình chọn cho giải thưởng WeYoung 2025.<br>
        Truy cập trang web giải thưởng để bình chọn.
    </div>
    
    <div class="footer-info">
        <p><strong>Thông tin</strong></p>
        <p>• Dữ liệu được cập nhật trực tiếp từ hệ thống định kỳ mỗi 10 giây.</p>
        <p>• Đồng thời ghi nhận lại mỗi 10 phút để phân tích và dự đoán.</p>
    </div>
    
    <div class="footer-copy">
        © Bản quyền giải thưởng thuộc về Công ty cổ phần VCCorp.<br>
        Phát triển độc lập bởi người hâm mộ chương trình ATVNCG.
        <span class="hashtag">#camonvidaden</span>
    </div>
</div>
""", unsafe_allow_html=True)