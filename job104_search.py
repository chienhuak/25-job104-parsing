import os
import requests
import time #計算時間
import datetime #顯示時間戳記
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


def normalize(value):
    """把資料統一轉成 Google Sheets / CSV 可接受的字串"""
    if isinstance(value, list):
        return ", ".join([str(v) for v in value])  # list 轉成逗號分隔字串
    elif value is None:
        return ""
    else:
        return str(value)


def fetch_today_jobs(city_list, kw):
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
            "keyword": kw, # 多關鍵字的變數
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
            
            job_id = job.get("link", {}).get("job", "").split("/")[-1]
            detail = fetch_job_detail(job_id)   
            
            all_jobs.append({
                "時間": datetime.datetime.now().strftime("%Y-%m-%d"),
                "關鍵字": kw,
                "職缺名稱": job.get("jobName"),
                "公司名稱": job.get("custName"),
                "地區": job.get("jobAddrNoDesc"),
                "薪資": job.get("salaryDesc"),
                "工作內容": detail["工作內容"],
                "擅長工具": detail["擅長工具"],
                "其他條件": detail["其他條件"],
                "聯絡人": detail["聯絡人"],
                "電話": detail["電話"],
                "E-mail": detail["E-mail"],
                "網址": f"https://www.104.com.tw/job/{job.get('link', {}).get('job', '').split('/')[-1]}"
                #for字串 "網址": f"https://www.104.com.tw/job/{job.get('link').split('/')[-1]}"
            })
            time.sleep(0.05)  # 避免太快被封

    return all_jobs


def fetch_job_detail(job_id):
    """抓取單一職缺詳細資料"""
    url = f"https://www.104.com.tw/job/ajax/content/{job_id}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": f"https://www.104.com.tw/job/{job_id}",
        "Accept": "application/json"
    }
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    data = res.json()

    job_detail = data.get("data", {}).get("jobDetail", {})
    contact_info = data.get("data", {}).get("contact", {})
    condition = data.get("data", {}).get("condition", {})

    return {
        "工作內容": normalize(job_detail.get("jobDescription", "").strip()),
        "聯絡人": normalize(contact_info.get("hrName", "") or "NA"),
        "E-mail": normalize(contact_info.get("email", "") or "NA"),
        "電話": normalize(contact_info.get("phone", "") or "NA"),
        "擅長工具": normalize([s.get("description") for s in condition.get("skill", [])]),
        "其他條件": normalize(condition.get("other", "").strip())
    }


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
    # 使用update方法，寫入googlesheet時會覆寫資料
    # service.spreadsheets().values().update(
    #     spreadsheetId=SPREADSHEET_ID,
    #     range=f"{SHEET_NAME}!A1",
    #     valueInputOption="RAW",
    #     body=body
    # ).execute()

    # 使用append方法寫入追加第二個關鍵字的資料(欄位名會再寫入)
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",  # 直接新增列，不覆蓋
        body=body
    ).execute()
    

def write_to_csv(jobs, file_path="jobs_backup.csv"):
    """將職缺資料寫入 CSV，若檔案存在就追加"""
    df = pd.DataFrame(jobs)
    # 如果檔案不存在，第一次寫入加上欄位名稱
    if not os.path.exists(file_path):
        df.to_csv(file_path, index=False, encoding="utf-8-sig", header=True)
    else:
        # 檔案已存在，追加到最後一行，不覆蓋原本資料
        df.to_csv(file_path, mode="a", index=False, encoding="utf-8-sig", header=False)


if __name__ == "__main__":
    # 1. 抓取符合條件的職缺、寫入 Google Sheet: 
    keywords = ["資料分析", "flask"]  # 多關鍵字
    cities = ["6001001000", "6001002000"]  # 台北市、新北市代碼
    # all_results = []
    
    for kw in keywords:
        jobs = fetch_today_jobs(cities,kw)  
        if not jobs:
            print("⚠️ 找不到 {kw} 職缺")
            continue
        else:
            write_to_gsheet(jobs)  # 每個關鍵字寫一次
            print(f"✅ 已寫入 {kw} 職缺到 Google Sheet，共 {len(jobs)} 筆")
            write_to_csv(jobs)  # 每個關鍵字寫一次
            print(f"✅ 已備份 {kw} 職缺到 CSV，共 {len(jobs)} 筆")



