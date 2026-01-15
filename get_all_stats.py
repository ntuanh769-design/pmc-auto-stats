import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from selenium import webdriver
from selenium.webdriver.common.by import By
import datetime
import time
import os
import re
import json

# --- CẤU HÌNH ---
SHEET_NAME = 'PMC Data Center'
YOUTUBE_API_KEY = 'AIzaSyAueu53W-r0VWcYJwYrSSboOKuWYQfLn34' 
CHANNEL_ID = 'UCGRIV5jOtKyAibhjBdIndZQ'

# Link nguồn
LIVECOUNTS_URL = f"https://livecounts.io/youtube-live-subscriber-counter/UCGRIV5jOtKyAibhjBdIndZQ"
SPOTIFY_URL = "https://open.spotify.com/artist/1BcjfrXV4Oe3fK0c8dnxFF"
TIKTOK_URL = "https://tokcounter.com/vi?user=phuongmychiofficial" 
FACEBOOK_URL = "https://www.facebook.com/phuongmychi"

# --- 1. KHỞI ĐỘNG DRIVER (AUTO UPDATE) ---
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')

    return webdriver.Chrome(options=options)

# --- 2. LẤY SỐ VIDEO (API) ---
def get_video_count_api():
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.channels().list(part='statistics', id=CHANNEL_ID)
        response = request.execute()
        if 'items' in response and len(response['items']) > 0:
            return int(response['items'][0]['statistics']['videoCount'])
    except:
        return 0

# --- 3. LẤY YOUTUBE REAL-TIME ---
def get_youtube_realtime(driver):
    print("   --> [1/4] Đang lấy Youtube (LiveCounts)...")
    sub_val = 0
    view_val = 0
    try:
        driver.get(LIVECOUNTS_URL)
        time.sleep(10)
        
        # 1. Lấy Sub
        try:
            odometer = driver.find_element(By.CSS_SELECTOR, ".odometer.odometer-auto-theme")
            raw_text = odometer.text
            clean_sub = int(re.sub(r'[^\d]', '', raw_text))
            
            if 100000 < clean_sub < 100000000:
                sub_val = clean_sub
            else:
                print(f"      ⚠️ Số Sub ảo ({clean_sub}), bỏ qua.")
        except:
            pass
        
        # 2. Lấy View
        try:
            view_el = driver.find_element(By.XPATH, "//*[contains(text(), 'Channel Views')]/preceding-sibling::div")
            clean_view = int(re.sub(r'[^\d]', '', view_el.text))
            if clean_view > 1000000:
                view_val = clean_view
        except:
            pass
            
    except Exception as e:
        print(f"      ❌ Lỗi YT: {e}")
    return sub_val, view_val

# --- 4. LẤY MẠNG XÃ HỘI KHÁC ---
def get_social_stats(driver):
    sp = 0
    tt = 0
    fb = 0
    
    # --- SPOTIFY ---
    print("   --> [2/4] Đang lấy Spotify...")
    try:
        driver.get(SPOTIFY_URL)
        time.sleep(3)
        body_text = driver.find_element(By.TAG_NAME, "body").text
        m = re.search(r'([\d\.,]+)\s+(monthly listeners|người nghe)', body_text, re.IGNORECASE)
        if m:
            sp = int(m.group(1).replace(',', '').replace('.', ''))
    except:
        pass
    
    # --- TIKTOK ---
    print("   --> [3/4] Đang lấy TikTok...")
    try:
        driver.get(TIKTOK_URL)
        time.sleep(8)
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        nums = re.findall(r'\d[\d,\.\s]*\d', body_text)
        cands = []
        for n in nums:
            try:
                val = int(re.sub(r'[^\d]', '', n))
                if 3000000 < val < 10000000:
                    cands.append(val)
            except:
                continue
            
        if cands:
            tt = max(cands)
            
    except Exception as e: 
        print(f"      ❌ Lỗi TikTok: {e}")
    
    # --- FACEBOOK (ĐÃ SỬA LỖI SYNTAX Ở ĐÂY) ---
    print("   --> [4/4] Đang lấy Facebook...")
    try:
        driver.get(FACEBOOK_URL)
        time.sleep(5)
        
        # Tách dòng rõ ràng để không bị lỗi Syntax
        try: 
            driver.find_element(By.XPATH, "//div[@aria-label='Close']").click()
        except: 
            pass
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        m = re.search(r'([\d\.,MK]+)\s+(followers|người theo dõi)', body_text, re.IGNORECASE)
        if m:
            t = m.group(1).upper().replace(',', '.').strip()
            mul = 1
            if 'M' in t:
                mul = 1000000
                t = t.replace('M','')
            elif 'K' in t:
                mul = 1000
                t = t.replace('K','')
            fb = int(float(t)*mul)
    except:
        pass
    
    return sp, tt, fb

# --- CHƯƠNG TRÌNH CHÍNH ---
def main():
    print("🚀 BẮT ĐẦU CẬP NHẬT DỮ LIỆU (FINAL FIX)...")
    
    json_creds = os.environ.get("GCP_CREDENTIALS")
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        if json_creds:
            print("   🔑 Dùng Cloud Credentials...")
            creds_dict = json.loads(json_creds)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            print("   💻 Dùng Local Credentials...")
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)

        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME)
        worksheet = sheet.worksheet("Music_Stats")
    except Exception as e:
        print(f"❌ Lỗi xác thực: {e}")
        return

    vid = get_video_count_api()
    driver = setup_driver()
    try:
        sub, view = get_youtube_realtime(driver)
        sp, tt, fb = get_social_stats(driver)
    finally:
        driver.quit()
        
    print("\n" + "="*40)
    print(f"✅ KẾT QUẢ: View={view:,} | Sub={sub:,} | TikTok={tt:,}")
    print("="*40)
    
    if sub > 0:
        try:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.append_row([current_time, view, sub, vid, sp, tt, fb])
            print("🎉 ĐÃ LƯU THÀNH CÔNG!")
        except Exception as e:
            print(f"❌ Lỗi ghi file: {e}")
    else:
        print("⚠️ Dữ liệu lỗi (Sub=0), không ghi file.")

if __name__ == "__main__":
    main()