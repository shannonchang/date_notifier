# LINE 農曆日期提醒 — 設計文件（v1：拜土地公）

## 目標

每天自動檢查「明天」是否為農曆初二或十六，若是則在前一天晚上透過 LINE 發訊息提醒使用者準備供品拜土地公。

## 範圍（v1）

- 只涵蓋「拜土地公」規則：每月農曆初二、十六。
- 只發送給使用者個人（LINE Push Message，收件者為固定的 User ID）。
- 不做多人/群組通知、不做互動式指令、不做網頁介面。
- 規則清單設計成可擴充，方便未來新增其他農曆節日提醒，但 v1 不實作額外規則。

## 架構

```
GitHub Actions（cron，每天 UTC 12:00 = 台灣時間 20:00）
        │
        ▼
      main.py
      ├─ 計算「明天」的西曆日期（Asia/Taipei，UTC+8，無日光節約）
      ├─ 用 lunar-python 將西曆轉換為農曆日期
      ├─ 比對 REMINDERS 規則清單
      └─ 若命中 → 組訊息 → 呼叫 LINE Messaging API push message
```

### 元件

- `main.py`：主邏輯，串起「取日期 → 轉農曆 → 比對規則 → 發送」流程。
- `REMINDERS`（`main.py` 內的常數清單）：
  ```python
  REMINDERS = [
      {"name": "拜土地公", "lunar_days": [2, 16]},
  ]
  ```
  未來新增節日提醒只需在此清單加一筆 `{"name": ..., "lunar_days": [...]}`，不需修改比對邏輯。
- `.github/workflows/reminder.yml`：GitHub Actions 排程設定，cron 為 `0 12 * * *`。
- `requirements.txt`：`lunar-python`、`requests`。

### 資料流

1. 取得台灣時區「今天」，計算「明天」的西曆日期。
2. 用 `lunar-python` 將明天的西曆日期轉為農曆日期，取出農曆日（1–30）。
3. 遍歷 `REMINDERS`，若明天的農曆日出現在某規則的 `lunar_days` 中，該規則視為命中。
4. 若有命中規則，組合訊息文字（可能同時列出多個命中的規則名稱），呼叫 LINE Messaging API 的 push endpoint 發送。
5. 若無命中，僅印出 log，正常結束、不發送。

## 認證與密鑰

- `LINE_CHANNEL_ACCESS_TOKEN`、`LINE_USER_ID` 存為 GitHub repo 的 Secrets，程式透過環境變數讀取。
- 不將任何密鑰寫入程式碼或提交進版本控制。

## LINE 發送方式

- 直接用 `requests` 呼叫 `POST https://api.line.me/v2/bot/message/push`，不引入 `line-bot-sdk`，減少相依套件。
- Header 帶 `Authorization: Bearer {LINE_CHANNEL_ACCESS_TOKEN}`。
- Body 範例：
  ```json
  {
    "to": "{LINE_USER_ID}",
    "messages": [{"type": "text", "text": "🙏 明天是農曆十六，記得準備供品拜土地公喔！"}]
  }
  ```

## 時區處理

- GitHub Actions 的 cron 以 UTC 為準；台灣全年固定 UTC+8（無日光節約），因此晚上 8 點固定對應 cron `0 12 * * *`，程式內部運算一律以 `Asia/Taipei` 時區為準（透過 Python 的 `zoneinfo`），不依賴 runner 的系統時區設定。

## 錯誤處理

- LINE API 回傳非 2xx（含網路例外）：印出錯誤訊息並以非 0 狀態碼結束程式，讓該次 GitHub Actions 執行標記為失敗（使用者可在 Actions 頁面或 GitHub 通知信中看到）。
- 不做重試機制（v1 範圍內不需要）。
- 非提醒日：印出「今天不用提醒」的 log，正常結束（exit code 0），不發送訊息。

## 測試方式

- `main.py` 支援可選參數：
  - `--date YYYY-MM-DD`：指定「明天」的日期以測試轉換與比對邏輯，不使用系統當前日期。
  - `--dry-run`：只印出將發送的訊息內容，不實際呼叫 LINE API。
- 兩者可搭配使用，方便在本機驗證任何一天的農曆換算與規則命中結果，也方便未來新增規則時測試。

## 未來可能擴充（不在 v1 範圍）

- 群組通知（Group ID）。
- 更多農曆節日規則（如初一十五、特定神明誕辰的固定農曆日期）。
- 訊息內容客製化（如加入建議供品清單）。
