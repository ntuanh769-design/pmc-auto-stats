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

# Link ảnh
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

# Dữ liệu khởi tạo Voting (Giống hình 731.jpg)
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
        request = youtube.videos().list(part="snippet,statistics", id=','.join(video_ids))
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
            except: pub_fmt = snippet['publishedAt'][:10]

            data_map[vid_id] = {
                'title': snippet['title'], 'thumb': snippet['thumbnails']['high']['url'],
                'view': int(stats.get('viewCount', 0)), 'like': int(stats.get('likeCount', 0)),
                'comment': int(stats.get('commentCount', 0)), 'published': pub_fmt, 'id': vid_id
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
                valid = df[df[col] > 0][col]
                if not valid.empty: latest[col] = valid.iloc[-1]
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

    /* VIDEO CARD (DỌC) */
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

    /* VOTING TABLE STYLE (Giống hình 731) */
    .voting-header { 
        background: #9575CD; color: white; padding: 15px; border-radius: 12px 12px 0 0; 
        text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 0;
    }
    .vote-table { 
        background: #FDFBF7; color: #333; border-radius: 0 0 12px 12px; padding: 10px; border: 1px solid #9575CD;
    }
    .vote-row { 
        display: flex; justify-content: space-between; align-items: center; 
        padding: 12px 20px; border-bottom: 1px solid #EEE; 
    }
    .vote-row:last-child { border-bottom: none; }
    
    .col-rank { width: 40px; font-weight: bold; font-size: 18px; color: #FFA000; }
    .col-name { flex-grow: 1; font-weight: 600; font-size: 16px; color: #333; }
    .col-total { width: 120px; text-align: right; font-weight: bold; font-size: 16px; color: #333; }
    .col-change { width: 80px; text-align: right; }
    
    .badge-plus { 
        background: #E8F5E9; color: #2E7D32; 
        padding: 4px 10px; border-radius: 12px; font-size: 14px; font-weight: bold; 
    }
    .badge-neutral { 
        background: #F5F5F5; color: #9E9E9E; 
        padding: 4px 10px; border-radius: 12px; font-size: 14px; font-weight: bold; 
    }

    /* FOOTER (Giống hình 583) */
    .footer-container { 
        background: #4A148C; /* Tím đậm */
        padding: 40px; margin-top: 60px; color: white; text-align: left;
    }
    .footer-title { font-size: 24px; font-weight: bold; margin-bottom: 10px; }
    .footer-desc { font-size: 14px; margin-bottom: 30px; line-height: 1.5; color: #E1BEE7; }
    .footer-heading { font-weight: bold; font-size: 18px; margin-bottom: 10px; }
    .footer-text { font-size: 14px; color: #E1BEE7; margin-bottom: 5px; }
    .footer-bottom { 
        margin-top: 30px; border-top: 1px solid rgba(255