import os
import requests
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Google Sheets 權限 (讀+寫)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# 你的 Google Sheet ID
SPREADSHEET_ID = "1PluvChUHCzKsuHJwKdSNKJ9vC6BI3V52C0tIb01u5F8"  # 改成自己的 Google Sheet ID
SHEET_NAME = "sheet1"  # 你 Google Sheet 裡的分頁名稱

# 104 API 設定
API_URL = "https://www.104.com.tw/jobs/search/list"

def fetch_jobs(city_list):
    """抓取 104 職缺資料，只要指定的城市"""
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.104.com.tw/jobs/search/"
    }

    all_jobs = []
    for city in city_list:
        params = {
            "ro": "0",
            "kwop": "7",
            "keyword": "SQL", # 參數設成 "SQL" 就是找關鍵字含 SQL 的職缺
            "area": city,  # 城市代碼
            "isnew": "0",  # 參數設成 "0" 是今天更新職缺（0 代表今天，3 是三天內，7 是一週內，依官方規範）
            "mode": "l",
            "page": 1,
            "order": "11",
            "asc": "0"
        }
        res = requests.get(API_URL, headers=headers, params=params)
        res.raise_for_status()
        data = res.json()
        jobs = data['data']['list']

        for job in jobs:
            all_jobs.append({
                "職缺名稱": job.get("jobName"),
                "公司名稱": job.get("custName"),
                "地區": job.get("jobAddrNoDesc"),
                "薪資": job.get("salaryDesc"),
                "網址": f"https://www.104.com.tw/job/{job.get('link', {}).get('job', '').split('/')[-1]}"
                #for字串 "網址": f"https://www.104.com.tw/job/{job.get('link').split('/')[-1]}"
            })

    return all_jobs

def get_gsheet_service():
    """登入 Google Sheets API"""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("sheets", "v4", credentials=creds)

def write_to_gsheet(data):
    """將資料寫入 Google Sheet"""
    service = get_gsheet_service()
    values = [list(data[0].keys())]  # 標題
    for row in data:
        values.append(list(row.values()))

    body = {"values": values}
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1",
        valueInputOption="RAW",
        body=body
    ).execute()

if __name__ == "__main__":
    # 1. 抓取台北 & 新北
    jobs = fetch_jobs(["6001001000", "6001002000"])  # 台北市、新北市代碼
    if not jobs:
        print("⚠️ 找不到職缺")
        exit()

    # 2. 備份到 CSV
    df = pd.DataFrame(jobs)
    df.to_csv("jobs_backup.csv", index=False, encoding="utf-8-sig")
    print(f"✅ 已備份 CSV，共 {len(jobs)} 筆")

    # 3. 寫入 Google Sheet
    write_to_gsheet(jobs)
    print(f"✅ 已寫入 Google Sheet，共 {len(jobs)} 筆")
