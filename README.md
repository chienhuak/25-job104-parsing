# 25-job104-parsing 專案說明
此專案爬取 104 職缺資料並寫入 Google Sheets。

## Google Sheet 寫入位置
- [職缺清單連結](https://docs.google.com/spreadsheets/d/1PluvChUHCzKsuHJwKdSNKJ9vC6BI3V52C0tIb01u5F8/edit?gid=0#gid=0)

## 套件用途
- `requests`：發送 HTTP 請求（GET、POST 等），抓取 API 或網頁資料 (從104 抓職缺清單)
- `google-api-python-client`：讓 Python 可以直接呼叫 Google Sheets API、Drive API 等
- `google-auth-httplib2`：Google API 在驗證時，需要用這個處理 HTTP 請求和 OAuth Token
- `google-auth-oauthlib`：OAuth 2.0 驗證，用 credentials.json 做登入授權，產生 token.json
- `oauth2client`：舊版 Google 驗證工具（部分第三方套件仍需）
- `gspread`：第三方 Google Sheets API 客戶端，可用簡單的語法存取 Google Sheets
- `pandas`：資料整理與 CSV 輸出

## 依賴一鍵安裝
使用以下指令安裝：
```bash
pip install -r requirements.txt
```

## 使用方法
1. 安裝套件
2. 準備 credentials.json（從 Google Cloud Console 下載）
3. 執行爬蟲
