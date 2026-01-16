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
# --- 1. CẤU HÌNH DỮ LIỆU (PMC DATA) ---
# ==========================================
SHEET_NAME = 'PMC Data Center'
VIDEO_IDS = ['sZrIbpwjTwk', 'BmrdGQ0LRRo', 'V1ah6tmNUz8'] 
YOUTUBE_API_KEY = 'AIzaSyAueu53W-r0VWcYJwYrSSboOKuWYQfLn34' 

SCHEDULE_IMAGE_URL = "https://images.unsplash.com/photo-1506784983877-45594efa4cbe?q=80&w=2068&auto=format&fit=crop" 
BANNER_URL = "https://scontent.fvca1-1.fna.fbcdn.net/v/t39.30808-6/600369698_1419646709529546_341344486868245985_n.jpg?_nc_cat=105&ccb=1-7&_nc_sid=833d8c&_nc_eui2=AeE8R8ouge4yL7lfWGQ5Kzk1Enry68g3cr0SevLryDdyvaWspFlBItEaOUW321Od9poGbHjYncGX9_MS7BEcv6Ww&_nc_ohc=WHolhcYE84IQ7kNvwH3WDS7&_nc_oc=AdlMDmMAztdFXjYHzVG6BJpmRMy1E7qVPlz3DWxOrwo2YrZS0MeRHLPCU2rF4_OdTXE&_nc_zt=23&_nc_ht=scontent.fvca1-1.fna&_nc_gid=AXvAnGOph6iEFu_TWBD-SA&oh=00_AfoafS9eKG1wduMrKvUIYzK6Mu4ZIs0Q3Idtuj5CW5qvEg&oe=696F8D56"
AVATAR_URL = "https://scontent.fvca1-1.fna.fbcdn.net/v/t39.30808-6/482242951_1184903749670511_116581152088062484_n.jpg?stp=cp6_dst-jpg_tt6&_nc_cat=105&ccb=1-7&_nc_sid=a5f93a&_nc_eui2=AeHl6z1Zf722SPdydZ2cSXjkZpHk_q-4D51mkeT-r7gPndTlCsa2S-9POMvKIBb4ckII1tv_ascEHrs3kes9q9GO&_nc_ohc=0KAgPDwqVoYQ7kNvwGvYZzT&_nc_oc=AdkiSSI5Nm1z4L60wjOWhF2RlhO42CTckj5fJghrGNCIl1rRcnH9YUwQDlrcIYwvWshnvTSvZ0pqlV2sGzg6tPGG&_nc_zt=23&_nc_ht=scontent.fvca1-1.fna&_nc_gid=VKwmNPd5x84LUuWGX44UBw&oh=00_AfpI8odqVyRf4fYhFFiablQhci6WR8tZfRwbNfW2uoUEig&oe=696F885F"

SOCIAL_LINKS = {
    "facebook": "https://www.facebook.com/phuongmychi",
    "instagram": "https://www.instagram.com/phuongmychi/",
    "threads": "https://www.threads.net/@phuongmychi",
    "youtube": "https://www.youtube.com/channel/UCGRIV5jOtKyAibhjBdIndZQ",
    "spotify": "https://open.spotify.com/artist/PMC_LINK"
}

# --- DỮ LIỆU TINH HOA NHÍ (1VOTE.VN) ---
VOTING_INIT = {
    "Thí sinh được yêu thích nhất": [
        {"name": "Nguyễn Vũ Minh Lam", "votes": 85620, "img": "https://via.placeholder.com/80?text=ML"},
        {"name": "Lý Thị Diệp Quỳnh", "votes": 74450, "img": "https://via.placeholder.com/80?text=DQ"},
        {"name": "Hán Y Triệu Vy", "votes": 71900, "img": "https://via.placeholder.com/80?text=TV"},
        {"name": "Nguyễn Thái An Bình", "votes": 62371, "img": ""},
        {"name": "Bùi Đức Huy", "votes": 55888, "img": ""},
        {"name": "Nguyễn Ngọc Bảo Anh", "votes": 42868, "img": ""},
    ]
}

# ==========================================
# --- 2. HÀM XỬ LÝ DỮ LIỆU ---
# ==========================================
def fetch_video_data_api(video_ids):
    data_map = {}
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.videos().list(part="snippet,statistics", id=','.join(video_ids))
        response = request.execute()
        for item in response['items']:
            stats, snippet = item['statistics'], item['snippet']
            data_map[item['id']] = {
                'title': snippet['title'], 'thumb': snippet['thumbnails']['high']['url'],
                'view': int(stats.get('viewCount', 0)), 'like': int(stats.get('likeCount', 0)),
                'comment': int(stats.get('commentCount', 0)), 'published': snippet['publishedAt'][:10], 'id': item['id']
            }
    except: pass
    return data_map

def load_sheet_data():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        df = pd.DataFrame(client.open(SHEET_NAME).worksheet("Music_Stats").get_all_records())
        cols = ['Youtube_View', 'Youtube_Sub', 'Spotify_Listener', 'TikTok_Follower', 'Facebook_Follower']
        for col in cols: df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('.', ''), errors='coerce').fillna(0).astype(int)
        latest = df.iloc[-1].copy()
        for col in cols:
            if latest[col] == 0:
                valid = df[df[col] > 0][col]
                if not valid.empty: latest[col] = valid.iloc[-1]
        return df, latest
    except: return pd.DataFrame(), None

# ==========================================
# --- 3. CSS TÙY CHỈNH (TÁCH BIỆT HOÀN TOÀN) ---
# ==========================================
st.set_page_config(page_title="PMC Official", page_icon="👑", layout="wide")

st.markdown("""
<style>
    #MainMenu, header, footer {visibility: hidden;}
    .stApp { background-color: #0E1117; color: #E0E0E0; font-family: sans-serif; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    .stTabs { background: #0E1117; position: sticky; top: 0; z-index: 999; padding-top: 10px; border-bottom: 1px solid #333; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; gap: 30px; }
    .stTabs [data-baseweb="tab"] { background: transparent; border: none; color: #AAA; font-weight: 700; font-size: 16px; text-transform: uppercase; }
    .stTabs [aria-selected="true"] { color: #FFF !important; border-bottom: 3px solid #FFD700 !important; }
    .banner-container { width: 100vw; height: 650px; overflow: hidden; position: relative; left: 50%; right: 50%; margin-left: -50vw; margin-right: -50vw; }
    .banner-img { width: 100%; height: 100%; object-fit: cover; filter: brightness(0.7); }
    .profile-section { margin-top: -120px; text-align: center; position: relative; z-index: 10; padding-bottom: 30px; }
    .avatar { border-radius: 50%; width: 160px; height: 160px; object-fit: cover; border: 4px solid #FFD700; background: #000; box-shadow: 0 10px 20px rgba(0,0,0,0.6); }
    .artist-name { font-size: 48px; font-weight: 900; color: #FFF; margin: 10px 0 0 0; }
    .social-links { display: flex; gap: 20px; justify-content: center; margin-top: 15px; }
    .social-icon svg { fill: #AAA; transition: 0.3s; }
    .social-icon:hover svg { fill: #FFF; transform: translateY(-3px); }
    .video-card { background: #1A1A1A; border-radius: 10px; overflow: hidden; margin-bottom: 20px; border: 1px solid #333; }
    .vid-thumb-wrapper { position: relative; width: 100%; padding-top: 56.25%; background: #000; }
    .vid-thumb { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; opacity: 0.85; }
    .vid-body { padding: 15px; }
    .vid-title { font-size: 14px; font-weight: 700; color: #FFF; text-transform: uppercase; line-height: 1.4; margin-bottom: 4px; height: 42px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
    .vid-artist { font-size: 12px; color: #888; font-weight: 600; text-transform: uppercase; margin-bottom: 15px; }
    .stat-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 13px; }
    .val-view { color: #64B5F6; font-weight: 700; }
    .val-like { color: #81C784; font-weight: 700; }
    .val-comm { color: #FFD54F; font-weight: 700; }
    .vid-footer { border-top: 1px solid #333; padding-top: 10px; margin-top: 10px; font-size: 11px; color: #666; text-align: right; }
    .vote-card { background: #FDFBF7; border-radius: 15px; border: 1px solid #DDD; overflow: hidden; color: #333; max-width: 700px; margin: 0 auto;}
    .vote-head { background: #9575CD; color: white; text-align: center; padding: 15px; font-size: 22px; font-weight: bold; }
    .vote-row { display: flex; align-items: center; padding: 12px 20px; border-bottom: 1px solid #EEE; }
    .v-rank { width: 50px; font-weight: bold; color: #F57C00; font-size: 18px; }
    .v-name { flex-grow: 1; font-weight: bold; font-size: 15px; }
    .v-total { width: 100px; text-align: right; font-weight: bold; }
    .v-change { width: 70px; text-align: right; }
    .badge-p { background: #E8F5E9; color: #2E7D32; padding: 3px 8px; border-radius: 10px; font-size: 12px; font-weight: bold; }
    .podium-container { display: flex; justify-content: center; align-items: flex-end; gap: 15px; margin-bottom: 30px; padding-top: 20px; }
    .podium-item { text-align: center; width: 120px; }
    .podium-img { width: 80px; height: 80px; border-radius: 50%; border: 3px solid #FFF; object-fit: cover; }
    .podium-bar { border-radius: 10px 10px 0 0; color: #000; font-weight: bold; padding-top: 10px; }
    .f-box { background: #4A148C; padding: 50px 40px; color: white; margin-top: 80px; border-top: 4px solid #311B92; }
    .f-title { font-size: 28px; font-weight: bold; margin-bottom: 10px; }
    .f-info-box { background: rgba(0,0,0,0.15); padding: 20px; border-radius: 8px; display: inline-block; margin-bottom: 40px; }
    .metric-card { background: #16181C; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #333; }
    .metric-val { font-size: 28px; font-weight: 800; color: white; }
    .metric-lbl { font-size: 12px; text-transform: uppercase; color: #888; font-weight: bold; }
    .live-dot { height: 8px; width: 8px; background: #FF4B4B; border-radius: 50%; display: inline-block; animation: blink 1.5s infinite; }
    @keyframes blink { 0% {opacity:1} 50% {opacity:0.4} 100% {opacity:1} }
    .content-spacer { height: 60px; }
</style>
""", unsafe_allow_html=True)

# SVG Icons
svg_icons = {
    "fb": SOCIAL_LINKS["facebook"], "ig": SOCIAL_LINKS["instagram"], "th": SOCIAL_LINKS["threads"], "yt": SOCIAL_LINKS["youtube"], "sp": SOCIAL_LINKS["spotify"]
}

# ==========================================
# --- 4. STATE KHỞI TẠO ---
# ==========================================
if 'init' not in st.session_state:
    df, latest = load_sheet_data()
    st.session_state.latest = latest
    st.session_state.total_view_sim = int(latest['Youtube_View']) if latest is not None else 0
    st.session_state.v_data = fetch_video_data_api(VIDEO_IDS)
    st.session_state.voting_sim = VOTING_INIT
    st.session_state.voting_history = []
    st.session_state.init = True

# ==========================================
# --- 5. MAIN LAYOUT ---
# ==========================================
st.markdown('<div class="banner-container"><img src="' + BANNER_URL + '" class="banner-img"></div>', unsafe_allow_html=True)
st.markdown('<div class="profile-section"><img src="' + AVATAR_URL + '" class="avatar"><div class="artist-name">PHƯƠNG MỸ CHI</div><div style="color:#BBB; margin-top:5px; font-weight:600;">"Cô bé dân ca" ngày nào giờ đã trở thành một biểu tượng âm nhạc trẻ trung, năng động và đầy sáng tạo.</div><div class="social-links"><a href="'+svg_icons["fb"]+'" target="_blank" class="social-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path d="M14 13.5h2.5l1-4H14v-2c0-1.03 0-2 2-2h1.5V2.14c-.326-.043-1.557-.14-2.857-.14C11.928 2 10 3.657 10 6.7v2.8H7v4h3V22h4v-8.5z"/></svg></a><a href="'+svg_icons["ig"]+'" target="_blank" class="social-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg></a><a href="'+svg_icons["th"]+'" target="_blank" class="social-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path d="M12.274 2.001c-5.536 0-10.002 4.466-10.002 10.001s4.466 10.002 10.002 10.002 10.002-4.467 10.002-10.002-4.466-10.001-10.002-10.001zm.002 18.126c-4.489 0-8.126-3.636-8.126-8.125 0-4.489 3.637-8.125 8.126-8.125 4.489 0 8.125 3.636 8.125 8.125 0 4.489-3.636 8.125-8.125 8.125zm5.692-8.125h-1.506c-.027-1.975-.918-3.353-2.322-3.737 1.733-.456 2.672-1.721 2.672-3.106 0-1.644-1.407-2.854-3.492-2.854-2.158 0-3.679 1.274-3.679 3.113 0 1.379.896 2.65 2.625 3.105-1.406.388-2.298 1.767-2.323 3.479h-1.531c.038-2.552 1.548-4.567 3.806-5.111-1.847-.598-2.89-2.186-2.89-3.859 0-2.428 2.046-4.323 5.054-4.323 2.968 0 4.858 1.862 4.858 4.293 0 1.67-.989 3.214-2.759 3.833 2.184.552 3.659 2.549 3.701 5.169l-.004-.001zm-6.722-6.641c0-1.189.965-2.147 2.158-2.147 1.236 0 2.085.957 2.085 2.053 0 1.158-.887 2.077-2.118 2.181-1.206-.098-2.125-1.023-2.125-2.087zm2.125 3.585c1.437.127 2.555 1.234 2.555 2.639 0 1.495-1.231 2.697-2.737 2.697-1.541 0-2.792-1.247-2.792-2.794 0-1.454 1.167-2.609 2.685-2.682l.289.14z"/></svg></a><a href="'+svg_icons["yt"]+'" target="_blank" class="social-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path d="M21.582,6.186c-0.23-0.86-0.908-1.538-1.768-1.768C18.254,4,12,4,12,4S5.746,4,4.186,4.418 c-0.86,0.23-1.538,0.908-1.768,1.768C2,7.746,2,12,2,12s0,4.254,0.418,5.814c0.23,0.86,0.908,1.538,1.768,1.768 C5.746,20,12,20,12,20s6.254,0,7.814-0.418c0.86-0.23,1.538-0.908,1.768-1.768C22,16.254,22,12,22,12S22,7.746,21.582,6.186z M10,15 V9l5.208,3L10,15z"/></svg></a><a href="'+svg_icons["sp"]+'" target="_blank" class="social-icon"><svg viewBox="0 0 24 24" width="24" height="24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.586 14.424c-.18.295-.563.387-.857.207-2.35-1.434-5.305-1.758-8.78-1.022-.328.084-.65-.133-.73-.463-.085-.33.133-.65.463-.73 3.81-.808 7.075-.44 9.7 1.15.293.18.385.563.206.857zm1.228-2.727c-.226.366-.696.482-1.06.26-2.687-1.652-6.785-2.13-9.965-1.164-.41.122-.835-.126-.96-.533-.122-.41.126-.835.533-.96 3.617-1.1 8.205-.557 11.302 1.345.365.225.482.694.26 1.06zm.11-2.786c-3.22-1.91-8.53-2.088-11.596-1.143-.467.146-.976-.105-1.123-.573-.146-.47.105-.977.573-1.124 3.57-1.1 9.46-.88 13.146 1.31.42.245.553.792.308 1.21-.246.42-.793.553-1.21.308z"/></svg></a></div></div>', unsafe_allow_html=True)

tab_h, tab_a, tab_s, tab_st, tab_v = st.tabs(["TRANG CHỦ", "GIỚI THIỆU", "LỊCH TRÌNH", "THỐNG KÊ", "VOTING"])

with tab_h:
    h_metrics, h_videos = st.empty(), st.empty()
with tab_a:
    st.markdown('<div class="content-spacer"></div><div class="main-content">', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    c1.image(AVATAR_URL, width=300)
    c2.markdown("### PHƯƠNG MỸ CHI\n**Phương Mỹ Chi** (sinh năm 2003) là nghệ sĩ tiêu biểu của dòng nhạc dân ca đương đại. Đạt giải Á quân *Giọng hát Việt nhí 2013*, cô không ngừng sáng tạo để kết hợp nét truyền thống vào âm nhạc điện tử hiện đại.\n\n* **Album tiêu biểu:** Vũ Trụ Cò Bay (2023).")
    st.markdown('</div>', unsafe_allow_html=True)
with tab_s:
    st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)
    st.image(SCHEDULE_IMAGE_URL, use_column_width=True, caption="Lịch trình PMC")
with tab_st:
    st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)
    st_chart = st.empty()
with tab_v:
    st.markdown('<div class="content-spacer"></div><div class="main-content">', unsafe_allow_html=True)
    v_cat = st.selectbox("CHỌN HẠNG MỤC BÌNH CHỌN:", list(VOTING_INIT.keys()))
    v_podium, v_table, v_race = st.empty(), st.empty(), st.empty()
    st.markdown('</div>', unsafe_allow_html=True)

f_placeholder = st.empty()

# ==========================================
# --- 6. LOOP REAL-TIME ---
# ==========================================
while True:
    st.session_state.total_view_sim += random.randint(1, 15)
    for cat in st.session_state.voting_sim:
        for cand in st.session_state.voting_sim[cat]:
            inc = random.randint(0, 5)
            cand['votes'] += inc
            cand['change'] = inc
    curr_v = sorted(st.session_state.voting_sim[v_cat], key=lambda x: x['votes'], reverse=True)
    history_point = {"Time": datetime.datetime.now().strftime("%H:%M:%S")}
    for item in curr_v: history_point[item['name']] = item['votes']
    st.session_state.voting_history.append(history_point)
    if len(st.session_state.voting_history) > 30: st.session_state.voting_history.pop(0)

    # Render Home
    lat = st.session_state.latest
    if lat is not None:
        with h_metrics.container():
            st.markdown("### 🔥 REAL-TIME STATISTICS")
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown('<div class="metric-card"><div class="metric-lbl">TOTAL VIEWS <span class="live-dot"></span></div><div class="metric-val" style="color:#FF4B4B">'+ "{:,}".format(st.session_state.total_view_sim) +'</div></div>', unsafe_allow_html=True)
            c2.markdown('<div class="metric-card"><div class="metric-lbl">SUBSCRIBERS</div><div class="metric-val">'+ "{:,}".format(lat['Youtube_Sub']) +'</div></div>', unsafe_allow_html=True)
            c3.markdown('<div class="metric-card"><div class="metric-lbl">TIKTOK FANS</div><div class="metric-val">'+ "{:,}".format(lat['TikTok_Follower']) +'</div></div>', unsafe_allow_html=True)
            c4.markdown('<div class="metric-card"><div class="metric-lbl">SPOTIFY</div><div class="metric-val" style="color:#1DB954">'+ "{:,}".format(lat['Spotify_Listener']) +'</div></div>', unsafe_allow_html=True)
        with h_videos.container():
            st.markdown("### 🎬 LATEST RELEASES")
            cols = st.columns(3)
            for i, vid_id in enumerate(VIDEO_IDS):
                if vid_id in st.session_state.v_data:
                    d = st.session_state.v_data[vid_id]
                    with cols[i]: st.markdown('<div class="video-card"><a href="https://www.youtube.com/watch?v='+d['id']+'" target="_blank"><div class="vid-thumb-wrapper"><img src="'+d['thumb']+'" class="vid-thumb"></div></a><div class="vid-body"><div class="vid-title">'+d['title']+'</div><div class="vid-artist">PHƯƠNG MỸ CHI</div><div class="stat-row"><span class="stat-label">Lượt xem:</span><span class="val-view">'+"{:,}".format(d['view'])+'</span></div><div class="stat-row"><span class="stat-label">Lượt thích:</span><span class="val-like">'+"{:,}".format(d['like'])+'</span></div><div class="stat-row"><span class="stat-label">Bình luận:</span><span class="val-comm">'+"{:,}".format(d['comment'])+'</span></div><div class="vid-footer">Thêm vào: '+d['published']+'</div></div></div>', unsafe_allow_html=True)

    # Render Voting
    with v_podium.container():
        if len(curr_v) >= 3:
            t1, t2, t3 = curr_v[0], curr_v[1], curr_v[2]
            st.markdown('<div class="podium-container"><div class="podium-item" style="height:150px;"><div style="color:#C0C0C0; font-weight:bold;">#2</div><img src="'+(t2['img'] if t2['img'] else 'https://via.placeholder.com/80')+'" class="podium-img" style="border-color:#C0C0C0"><div class="podium-bar" style="height:70px; background:#C0C0C0;">2nd</div><div class="podium-name">'+t2['name']+'</div></div><div class="podium-item" style="height:190px;"><div style="color:#FFD700; font-size:30px;">👑 #1</div><img src="'+(t1['img'] if t1['img'] else 'https://via.placeholder.com/80')+'" class="podium-img" style="border-color:#FFD700; width:90px; height:90px;"><div class="podium-bar" style="height:100px; background:#FFD700;">1st</div><div class="podium-name">'+t1['name']+'</div></div><div class="podium-item" style="height:130px;"><div style="color:#CD7F32; font-weight:bold;">#3</div><img src="'+(t3['img'] if t3['img'] else 'https://via.placeholder.com/80')+'" class="podium-img" style="border-color:#CD7F32"><div class="podium-bar" style="height:50px; background:#CD7F32;">3rd</div><div class="podium-name">'+t3['name']+'</div></div></div>', unsafe_allow_html=True)
    with v_table.container():
        rows = ""
        for i, it in enumerate(curr_v):
            badge = '<span class="badge-p">+' + str(it['change']) + '</span>' if it['change'] > 0 else '<span class="badge-n">0</span>'
            rows += '<div class="vote-row"><div class="col-rank">#'+str(i+1)+'</div><div class="col-name">'+it['name']+'</div><div class="col-total">'+"{:,}".format(it['votes'])+'</div><div class="v-change">'+badge+'</div></div>'
        st.markdown('<div class="vote-card"><div class="vote-head">Bình Chọn Tinh Hoa Nhí</div><div class="vote-table-body">'+rows+'</div></div>', unsafe_allow_html=True)
    with v_race.container():
        st.markdown("#### 📈 DIỄN BIẾN ĐƯỜNG ĐUA")
        df_melt = pd.DataFrame(st.session_state.voting_history).melt(id_vars=['Time'], var_name='Candidate', value_name='Votes')
        fig = px.line(df_melt, x='Time', y='Votes', color='Candidate', template="plotly_dark")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    # --- RENDER FOOTER (TRONG LOOP) ---
    with f_placeholder.container():
        st.markdown('<div class="f-box"><div class="f-title">WeYoung Tracker</div><div class="f-desc">Hệ thống theo dõi và phân tích bình chọn cho giải thưởng WeYoung 2025. Truy cập trang web giải thưởng để bình chọn.</div><div class="f-info"><div style="font-weight:bold; margin-bottom:5px;">Thông tin</div><p class="footer-text">• Dữ liệu được cập nhật trực tiếp từ hệ thống định kỳ mỗi 10 giây.</p><p class="footer-text">• Đồng thời ghi nhận lại mỗi 10 phút để phân tích và dự đoán.</p></div><div class="f-bottom">© Bản quyền giải thưởng thuộc về Công ty cổ phần VCCorp.<br>Phát triển độc lập bởi người hâm mộ chương trình ATVNCG.<br><strong style="color:white;">#camonvidaden</strong></div></div>', unsafe_allow_html=True)

    time.sleep(1)