import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import datetime
import time
import os
import re
import json

# --- CẤU HÌNH ---
SHEET_NAME = 'PMC Data Center'
YOUTUBE_API_KEY = 'AIzaSyAueu53W-r0VWcYJwYrSSboOKuWYQfLn34' 
CHANNEL_ID = 'UCGRIV5jOtKyAibhjBdIndZQ'

# Link các nguồn dữ liệu
LIVECOUNTS_URL = f"https://livecounts.io/youtube-live-subscriber-counter/UCGRIV5jOtKyAibhjBdIndZQ"
SPOTIFY_URL = "https://open.spotify.com/artist/1BcjfrXV4Oe3fK0c8dnxFF"
TIKTOK_URL = "https://tokcounter.com/vi?user=phuongmychiofficial"
FACEBOOK_URL = "https://www.facebook.com/phuongmychi"

# --- 1. KHỞI ĐỘNG DRIVER (CHUẨN AUTOMATION) ---
def setup_driver():
    options = webdriver.ChromeOptions()
    
    # --- CẤU HÌNH ĐỂ CHẠY TRÊN SERVER/CLOUD ---
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # --- CẤU HÌNH CHỐNG PHÁT HIỆN BOT ---
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

# --- 2. LẤY SỐ VIDEO (API) ---
def get_video_count_api():
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.channels().list(part='statistics', id=CHANNEL_ID)
        response = request.execute()
        if 'items' in response and len(response['items']) > 0:
            return int(response['items'][0]['statistics']['videoCount'])
    except: return 0

# --- 3. LẤY YOUTUBE REAL-TIME ---
def get_youtube_realtime(driver):
    print("   --> [1/4] Đang lấy Youtube (LiveCounts)...")
    sub_val = 0; view_val = 0
    try:
        driver.get(LIVECOUNTS_URL)
        time.sleep(15) 
        
        # Tắt Cookie
        try:
            btns = driver.find_elements(By.XPATH, "//*[contains(text(), 'Agree') or contains(text(), 'Accept')]")
            for b in btns: 
                if b.is_displayed():
                    b.click()
                    break
        except: pass
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        try:
            sub = int(re.sub(r'[^\d]', '', driver.find_element(By.CSS_SELECTOR, ".odometer.odometer-auto-theme").text))
            sub_val = sub
        except: pass
        
        try:
            txt = driver.find_element(By.XPATH, '//*[@id="__next"]/div/section/div[3]/div[4]/div[1]').text
            cln = re.sub(r'[^\d]', '', txt)
            if len(cln) > 9: cln = cln[:9]
            view_val = int(cln)
        except: pass
    except Exception as e: print(f"      ❌ Lỗi YT: {e}")
    return sub_val, view_val

# --- 4. LẤY MẠNG XÃ HỘI KHÁC ---
def get_social_stats(driver):
    sp=0; tt=0; fb=0
    
    # Spotify
    print("   --> [2/4] Đang lấy Spotify...")
    try:
        driver.get(SPOTIFY_URL)
        time.sleep(3)
        m = re.search(r'([\d\.,]+)\s+(monthly listeners|người nghe)', driver.find_element(By.TAG_NAME, "body").text, re.IGNORECASE)
        if m: sp = int(m.group(1).replace(',', '').replace('.', ''))
    except: pass
    
    # TikTok
    print("   --> [3/4] Đang lấy TikTok...")
    try:
        driver.get(TIKTOK_URL)
        time.sleep(10)
        els = driver.find_elements(By.XPATH, "//*[contains(text(), '5.') or contains(text(), '5,')]")
        for e in els:
            c = re.sub(r'[^\d]', '', e.text)
            if c and 3000000 < int(c) < 10000000: tt = int(c); break
        
        if tt == 0:
            nums = re.findall(r'\d[\d,\.\s]*\d', driver.find_element(By.TAG_NAME, "body").text)
            cands = [int(re.sub(r'[^\d]', '', n)) for n in nums if re.sub(r'[^\d]', '', n)]
            cands = [x for x in cands if 3000000 < x < 10000000]
            if cands: tt = max(cands)
    except: pass
    
    # Facebook
    print("   --> [4/4] Đang lấy Facebook...")
    try:
        driver.get(FACEBOOK_URL)
        time.sleep(5)
        # --- ĐOẠN SỬA LỖI SYNTAX ---
        try:
            driver.find_element(By.XPATH, "//div[@aria-label='Close']").click()
        except:
            pass
        # ---------------------------
        
        m = re.search(r'([\d\.,MK]+)\s+(followers|người theo dõi)', driver.find_element(By.TAG_NAME, "body").text, re.IGNORECASE)
        if m:
            t = m.group(1).upper().replace(',', '.').strip(); mul=1
            if 'M' in t: mul=1000000; t=t.replace('M','')
            elif 'K' in t: mul=1000; t=t.replace('K','')
            fb = int(float(t)*mul)
    except: pass
    
    return sp, tt, fb

# --- CHƯƠNG TRÌNH CHÍNH ---
def main():
    print("🚀 BẮT ĐẦU CẬP NHẬT DỮ LIỆU (AUTO MODE)...")
    
    json_creds = os.environ.get("GCP_CREDENTIALS")
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        if json_creds:
            print("   🔑 Phát hiện môi trường Cloud...")
            creds_dict = json.loads(json_creds)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            print("   💻 Phát hiện môi trường Local...")
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)

        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME)
        worksheet = sheet.worksheet("Music_Stats")
    except Exception as e:
        print(f"❌ Lỗi xác thực Google Sheet: {e}")
        return

    vid_count = get_video_count_api()
    driver = setup_driver()
    try:
        yt_sub, yt_view = get_youtube_realtime(driver)
        sp_lis, tik_fl, fb_fl = get_social_stats(driver)
    finally:
        driver.quit()
        
    print("\n" + "="*40)
    print(f"✅ Kết quả: View={yt_view:,} | Sub={yt_sub:,} | TikTok={tik_fl:,}")
    print("="*40)
    
    if yt_view > 0:
        try:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.append_row([current_time, yt_view, yt_sub, vid_count, sp_lis, tik_fl, fb_fl])
            print("🎉 THÀNH CÔNG! Dữ liệu đã được lưu lên Cloud.")
        except Exception as e:
            print(f"❌ Lỗi ghi Sheet: {e}")
    else:
        print("⚠️ Dữ liệu Youtube lỗi (View=0), hủy ghi.")

if __name__ == "__main__":
    main()