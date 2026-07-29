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

# 實際發送（需先設定環境變數）
$env:LINE_CHANNEL_ACCESS_TOKEN="xxx"
$env:LINE_USER_ID="xxx"
.venv/Scripts/python main.py --date 2026-02-17
```

`--date` 指定的是「今天」，程式會檢查「明天」是否命中提醒規則。

## 執行測試

```bash
.venv/Scripts/pytest tests/ -v
```

## 新增提醒規則

編輯 `main.py` 中的 `REMINDERS` 清單，新增一筆 `{"name": "...", "lunar_days": [...]}` 即可。
