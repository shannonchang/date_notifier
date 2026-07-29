# LINE 農曆日期提醒

每天檢查明天是否為農曆初二或十六，若是則透過 LINE 提醒你準備供品拜土地公。

## 設定

1. 在 GitHub repo 的 Settings → Secrets and variables → Actions 新增兩個 secrets：
   - `LINE_CHANNEL_ACCESS_TOKEN`：你的 LINE Messaging API channel access token。
   - `LINE_USER_ID`：要接收提醒的 LINE User ID。
2. 排程已設定在 `.github/workflows/reminder.yml`，每天 UTC 12:00（台灣時間 20:00）自動執行，也可以到 Actions 頁面手動觸發（workflow_dispatch）做測試。

## 本機測試

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements-dev.txt

# 只印出訊息、不實際發送
.venv/Scripts/python main.py --date 2026-02-17 --dry-run
```

實際發送需先設定環境變數。PowerShell：

```powershell
$env:LINE_CHANNEL_ACCESS_TOKEN="xxx"
$env:LINE_USER_ID="xxx"
.venv/Scripts/python main.py --date 2026-02-17
```

bash / Git Bash：

```bash
export LINE_CHANNEL_ACCESS_TOKEN="xxx"
export LINE_USER_ID="xxx"
.venv/Scripts/python main.py --date 2026-02-17
```

`--date` 指定的是「今天」，程式會檢查「明天」是否命中提醒規則。

## 如何取得 LINE User ID

`LINE_USER_ID` secret 需要的是要接收提醒訊息的 LINE 使用者 ID。取得方式：先讓你的 LINE Bot 收到一則訊息（例如自己傳訊息給它），再從 webhook 收到的請求內容中讀取 `source.userId` 欄位，該值就是你的 User ID。詳細設定步驟請參考 [LINE Developers 官方文件](https://developers.line.biz/en/docs/messaging-api/getting-user-ids/)。

## 執行測試

```bash
.venv/Scripts/pytest tests/ -v
```

## 新增提醒規則

編輯 `main.py` 中的 `REMINDERS` 清單，新增一筆 `{"name": "...", "lunar_days": [...]}` 即可。

## 維護注意事項

GitHub 會在 repository 連續 60 天沒有任何 commit 活動時，自動停用該 repo 的排程（scheduled）Actions workflow，屆時提醒會在你沒察覺的情況下悄悄停止發送。建議定期（例如每 1-2 個月）推送一個小 commit，或到 Actions 頁面手動重新啟用該 workflow；也可以只是把這點記在心裡，偶爾檢查一下排程是否仍在正常運作。
