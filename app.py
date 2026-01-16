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
# --- 1. CẤU HÌNH (DỰA TRÊN CODE CỦA BẠN) ---
# ==========================================
SHEET_NAME = 'PMC Data Center'
VIDEO_IDS = ['sZrIbpwjTwk', 'BmrdGQ0LRRo', 'V1ah6tmNUz8'] 
YOUTUBE_API_KEY = 'AIzaSyAueu53W-r0VWcYJwYrSSboOKuWYQfLn34' 

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

# DỮ LIỆU TINH HOA NHÍ VIỆT NAM (1VOTE.VN)
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
# --- 2. HÀM XỬ LÝ SỐ LIỆU ---
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
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
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
# --- 3. CSS TÙY CHỈNH ---
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
    
    /* VOTING UI (PODIUM & TABLE) */
    .podium-container { display: flex; justify-content: center; align-items: flex-end; gap: 15px; margin-bottom: 30px; padding-top: 20px; }
    .podium-item { text-align: center; width: 120px; }
    .podium-rank { font-size: 24px; font-weight: 900; margin-bottom: 5px; }
    .podium-img { width: 80px; height: 80px; border-radius: 50%; border: 3px solid #FFF; object-fit: cover; }
    .podium-bar { border-radius: 10px 10px 0 0; color: #000; font-weight: bold; padding-top: 10px; }
    .podium-name { font-size: 12px; font-weight: bold; margin-top: 8px; height: 32px; overflow: hidden; color: #FFF; }

    .vote-table-card { background: #FDFBF7; border-radius: 15px; color: #333; overflow: hidden; border: 1px solid #DDD; margin-top: 20px; }
    .vote-header-card { background: #9575CD; color: white; padding: 15px; text-align: center; font-size: 22px; font-weight: bold; }
    .vote-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; border-bottom: 1px solid #EEE; }
    .col-rank { width: 40px; font-weight: bold; color: #F57C00; font-size: 18px; }
    .col-name { flex-grow: 1; font-weight: bold; font-size: 15px; }
    .col-total { width: 100px; text-align: right; font-weight: bold; }
    .badge-p { background: #E8F5E9; color: #2E7D32; padding: 3px 8px; border-radius: 10px; font-size: 12px; font-weight: bold; }
    .badge-n { background: #F5F5F5; color: #999; padding: 3px 8px; border-radius: 10px; font-size: 12px; }

    .metric-card { background: #16181C; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #333; }
    .metric-val { font-size: 28px; font-weight: 800; color: white; }
    .metric-lbl { font-size: 12px; text-transform: uppercase; color: #888; font-weight: bold; }
    .live-dot { height: 8px; width: 8px; background: #FF4B4B; border-radius: 50%; display: inline-block; animation: blink 1.5s infinite; }
    @keyframes blink { 0% {opacity:1} 50% {opacity:0.4} 100% {opacity:1} }
    .content-spacer { height: 60px; }
</style>
""", unsafe_allow_html=True)

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
st.markdown('<div class="profile-section"><img src="' + AVATAR_URL + '" class="avatar"><div class="artist-name">PHƯƠNG MỸ CHI</div><div style="color:#BBB; margin-top:5px; font-weight:600;">"Cô bé dân ca" ngày nào giờ đã trở thành một biểu tượng âm nhạc trẻ trung, năng động và đầy sáng tạo.</div></div>', unsafe_allow_html=True)

tab_h, tab_a, tab_s, tab_st, tab_v = st.tabs(["TRANG CHỦ", "GIỚI THIỆU", "LỊCH TRÌNH", "THỐNG KÊ", "VOTING"])

with tab_h:
    h_metrics, h_videos = st.empty(), st.empty()
with tab_a:
    st.markdown('<div class="content-spacer"></div><div class="main-content">', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    c1.image(AVATAR_URL, width=300)
    c2.markdown("### PHƯƠNG MỸ CHI\n**Phương Mỹ Chi** (sinh năm 2003) là nghệ sĩ tiêu biểu của dòng nhạc dân ca đương đại. Đạt giải Á quân *Giọng hát Việt nhí 2013*, cô không ngừng sáng tạo để kết hợp nét truyền thống vào âm nhạc điện tử hiện đại.")
    st.markdown('</div>', unsafe_allow_html=True)
with tab_s:
    st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)
    st.image(SCHEDULE_IMAGE_URL, use_column_width=True, caption="Lịch trình PMC")
with tab_st:
    st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)
    st_chart_placeholder = st.empty()
with tab_v:
    st.markdown('<div class="content-spacer"></div><div class="main-content">', unsafe_allow_html=True)
    v_cat = st.selectbox("CHỌN HẠNG MỤC BÌNH CHỌN:", list(VOTING_INIT.keys()))
    v_podium, v_table, v_race = st.empty(), st.empty(), st.empty()
    st.markdown('</div>', unsafe_allow_html=True)

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
            
    # Sắp xếp và lưu lịch sử
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

    # Render Voting Podium (Top 3)
    with v_podium.container():
        if len(curr_v) >= 3:
            t1, t2, t3 = curr_v[0], curr_v[1], curr_v[2]
            st.markdown('<div class="podium-container"><div class="podium-item" style="height:150px;"><div style="color:#C0C0C0; font-weight:bold;">#2</div><img src="'+t2['img']+'" class="podium-img" style="border-color:#C0C0C0"><div class="podium-bar" style="height:70px; background:#C0C0C0;">2nd</div><div class="podium-name">'+t2['name']+'</div></div><div class="podium-item" style="height:190px;"><div style="color:#FFD700; font-size:30px;">👑 #1</div><img src="'+t1['img']+'" class="podium-img" style="border-color:#FFD700; width:90px; height:90px;"><div class="podium-bar" style="height:100px; background:#FFD700;">1st</div><div class="podium-name">'+t1['name']+'</div></div><div class="podium-item" style="height:130px;"><div style="color:#CD7F32; font-weight:bold;">#3</div><img src="'+t3['img']+'" class="podium-img" style="border-color:#CD7F32"><div class="podium-bar" style="height:50px; background:#CD7F32;">3rd</div><div class="podium-name">'+t3['name']+'</div></div></div>', unsafe_allow_html=True)

    # Render Voting Table
    with v_table.container():
        rows = ""
        for i, it in enumerate(curr_v):
            badge = '<span class="badge-p">+' + str(it['change']) + '</span>' if it['change'] > 0 else '<span class="badge-n">0</span>'
            rows += '<div class="vote-row"><div class="col-rank">#'+str(i+1)+'</div><div class="col-name">'+it['name']+'</div><div class="col-total">'+"{:,}".format(it['votes'])+'</div><div class="v-change">'+badge+'</div></div>'
        st.markdown('<div class="vote-table-card"><div class="vote-header-card">Bình Chọn Tinh Hoa Nhí</div><div class="vote-table-body">'+rows+'</div></div>', unsafe_allow_html=True)
    
    # Render Race Chart
    with v_race.container():
        st.markdown("#### 📈 DIỄN BIẾN ĐƯỜNG ĐUA")
        df_melt = pd.DataFrame(st.session_state.voting_history).melt(id_vars=['Time'], var_name='Candidate', value_name='Votes')
        fig = px.line(df_melt, x='Time', y='Votes', color='Candidate', template="plotly_dark")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    time.sleep(1)