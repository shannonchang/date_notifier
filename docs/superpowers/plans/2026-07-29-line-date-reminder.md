# LINE 農曆日期提醒（拜土地公 v1）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python script that runs daily via GitHub Actions, checks whether tomorrow (Asia/Taipei) is the 2nd or 16th day of the lunar month, and if so sends a LINE push message reminding the user to worship 土地公 (Tudigong).

**Architecture:** A single-file script (`main.py`) with small, independently testable pure functions (get today's date in Taipei time → convert to lunar day → match against a `REMINDERS` rule list → build message → send via LINE Messaging API push endpoint using `requests`). A GitHub Actions workflow runs it daily on a cron schedule using repo Secrets for LINE credentials. CLI flags (`--date`, `--dry-run`) allow local testing without waiting for a real date or sending a real message.

**Tech Stack:** Python 3.11+, `lunar_python` (solar↔lunar conversion), `requests` (HTTP), `tzdata` (IANA timezone data, needed for reliable `zoneinfo` lookups across platforms), `pytest` + `unittest.mock` for tests. GitHub Actions (`ubuntu-latest` runner, cron trigger).

## Global Constraints

- Reminder rule (v1): lunar day is 2 or 16 (`REMINDERS = [{"name": "拜土地公", "lunar_days": [2, 16]}]`), stored so future rules can be added as additional list entries.
- Recipient: single LINE user, via Push Message API (not group, not LINE Notify — LINE Notify is discontinued).
- Credentials `LINE_CHANNEL_ACCESS_TOKEN` and `LINE_USER_ID` are read only from environment variables, never hardcoded, never committed.
- All date/time logic uses `Asia/Taipei` (`zoneinfo.ZoneInfo("Asia/Taipei")`) explicitly — never the runner's local/system timezone.
- Schedule: GitHub Actions cron `0 12 * * *` (UTC) = 20:00 Taipei time, checking whether **tomorrow** matches a reminder rule.
- Non-2xx response (or exception) from the LINE API must cause the process to exit with a non-zero status code.
- No message is sent on non-matching days; the script exits 0 and only logs to stdout.
- No `line-bot-sdk` dependency — use `requests` directly against `https://api.line.me/v2/bot/message/push`.

---

## File Structure

- `main.py` — all application logic (functions below), plus `if __name__ == "__main__":` entry point.
- `tests/test_main.py` — unit tests for every function in `main.py`, using `pytest` and `unittest.mock`.
- `requirements.txt` — production dependencies: `lunar_python`, `requests`, `tzdata`.
- `requirements-dev.txt` — `-r requirements.txt` plus `pytest`.
- `.gitignore` — Python artifacts (`__pycache__/`, `*.pyc`, `.pytest_cache/`, `.venv/`).
- `.github/workflows/reminder.yml` — daily cron workflow that installs `requirements.txt` and runs `python main.py`.
- `README.md` — setup instructions: what secrets to add in GitHub repo settings, how to find your LINE User ID, how to run local tests/dry-runs.

---

### Task 1: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `.gitignore`

**Interfaces:**
- Produces: a working Python dependency setup that later tasks install into a virtualenv.

- [ ] **Step 1: Create `requirements.txt`**

```
lunar_python==1.4.8
requests==2.32.3
tzdata==2025.2
```

- [ ] **Step 2: Create `requirements-dev.txt`**

```
-r requirements.txt
pytest==8.3.3
```

- [ ] **Step 3: Create `.gitignore`**

```
__pycache__/
*.pyc
.pytest_cache/
.venv/
```

- [ ] **Step 4: Verify install works in a clean virtualenv**

Run:
```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements-dev.txt
```
Expected: install completes with no errors, `lunar_python`, `requests`, `tzdata`, and `pytest` all present (`.venv/Scripts/pip list` shows them).

- [ ] **Step 5: Commit**

```bash
git add requirements.txt requirements-dev.txt .gitignore
git commit -m "chore: add project dependencies and gitignore"
```

---

### Task 2: Date and lunar-day conversion

**Files:**
- Create: `main.py`
- Test: `tests/test_main.py`

**Interfaces:**
- Produces:
  - `get_taipei_tomorrow(now: datetime.datetime | None = None) -> datetime.date` — returns tomorrow's date in `Asia/Taipei`. If `now` is given (a timezone-aware `datetime`), compute relative to it (for testability); if `None`, use current time.
  - `get_lunar_day(solar_date: datetime.date) -> int` — returns the lunar day-of-month (1-30) for the given solar date.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_main.py` with:

```python
from datetime import date, datetime
from zoneinfo import ZoneInfo

from main import get_taipei_tomorrow, get_lunar_day


def test_get_taipei_tomorrow_from_fixed_now():
    now = datetime(2026, 7, 29, 10, 0, tzinfo=ZoneInfo("Asia/Taipei"))
    assert get_taipei_tomorrow(now) == date(2026, 7, 30)


def test_get_taipei_tomorrow_crosses_month_boundary():
    now = datetime(2026, 7, 31, 23, 0, tzinfo=ZoneInfo("Asia/Taipei"))
    assert get_taipei_tomorrow(now) == date(2026, 8, 1)


def test_get_lunar_day_known_new_year():
    # 2026-02-17 is confirmed lunar 1/1 (Chinese New Year 2026)
    assert get_lunar_day(date(2026, 2, 17)) == 1


def test_get_lunar_day_known_second_day():
    assert get_lunar_day(date(2026, 2, 18)) == 2


def test_get_lunar_day_known_sixteenth_day():
    # 2026-07-29 is confirmed lunar 6/16
    assert get_lunar_day(date(2026, 7, 29)) == 16


def test_get_lunar_day_known_seventeenth_day():
    assert get_lunar_day(date(2026, 7, 30)) == 17
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_main.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'main'` (file doesn't exist yet).

- [ ] **Step 3: Write minimal implementation**

Create `main.py`:

```python
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from lunar_python import Solar

TAIPEI_TZ = ZoneInfo("Asia/Taipei")


def get_taipei_tomorrow(now: datetime | None = None) -> date:
    if now is None:
        now = datetime.now(TAIPEI_TZ)
    today = now.astimezone(TAIPEI_TZ).date()
    return today + timedelta(days=1)


def get_lunar_day(solar_date: date) -> int:
    solar = Solar.fromYmd(solar_date.year, solar_date.month, solar_date.day)
    return solar.getLunar().getDay()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_main.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add Taipei date and solar-to-lunar day conversion"
```

---

### Task 3: Reminder rule matching

**Files:**
- Modify: `main.py`
- Modify: `tests/test_main.py`

**Interfaces:**
- Consumes: nothing from other tasks (pure function).
- Produces:
  - `REMINDERS: list[dict]` module-level constant — `[{"name": "拜土地公", "lunar_days": [2, 16]}]`.
  - `match_reminders(lunar_day: int, reminders: list[dict]) -> list[str]` — returns the `name` of every reminder whose `lunar_days` contains `lunar_day`, in list order.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_main.py`:

```python
from main import match_reminders, REMINDERS


def test_match_reminders_hits_day_two():
    assert match_reminders(2, REMINDERS) == ["拜土地公"]


def test_match_reminders_hits_day_sixteen():
    assert match_reminders(16, REMINDERS) == ["拜土地公"]


def test_match_reminders_no_match():
    assert match_reminders(10, REMINDERS) == []


def test_match_reminders_multiple_rules():
    rules = [
        {"name": "A", "lunar_days": [2, 16]},
        {"name": "B", "lunar_days": [16]},
    ]
    assert match_reminders(16, rules) == ["A", "B"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_main.py -v`
Expected: FAIL with `ImportError: cannot import name 'match_reminders' from 'main'`

- [ ] **Step 3: Write minimal implementation**

Add to `main.py` (after the imports, before `get_taipei_tomorrow`):

```python
REMINDERS = [
    {"name": "拜土地公", "lunar_days": [2, 16]},
]


def match_reminders(lunar_day: int, reminders: list[dict]) -> list[str]:
    return [r["name"] for r in reminders if lunar_day in r["lunar_days"]]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_main.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add reminder rule matching against lunar day"
```

---

### Task 4: Message building

**Files:**
- Modify: `main.py`
- Modify: `tests/test_main.py`

**Interfaces:**
- Consumes: `matched_names: list[str]` (from `match_reminders`), `lunar_day: int` (from `get_lunar_day`).
- Produces: `build_message(matched_names: list[str], lunar_day: int) -> str`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_main.py`:

```python
from main import build_message


def test_build_message_single_reminder():
    msg = build_message(["拜土地公"], 16)
    assert msg == "🙏 明天是農曆十六，記得準備供品拜土地公喔！"


def test_build_message_lunar_day_two_uses_correct_wording():
    msg = build_message(["拜土地公"], 2)
    assert msg == "🙏 明天是農曆初二，記得準備供品拜土地公喔！"


def test_build_message_multiple_reminders_joins_names():
    msg = build_message(["拜土地公", "其他節日"], 16)
    assert msg == "🙏 明天是農曆十六，記得準備供品拜土地公、其他節日喔！"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_main.py -v`
Expected: FAIL with `ImportError: cannot import name 'build_message' from 'main'`

- [ ] **Step 3: Write minimal implementation**

Add to `main.py`:

```python
_LUNAR_DAY_LABELS = {2: "初二", 16: "十六"}


def build_message(matched_names: list[str], lunar_day: int) -> str:
    day_label = _LUNAR_DAY_LABELS.get(lunar_day, f"{lunar_day}")
    names = "、".join(matched_names)
    return f"🙏 明天是農曆{day_label}，記得準備供品{names}喔！"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_main.py -v`
Expected: PASS (12 tests)

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add reminder message building"
```

---

### Task 5: LINE push message sending

**Files:**
- Modify: `main.py`
- Modify: `tests/test_main.py`

**Interfaces:**
- Consumes: `message: str` (from `build_message`), `token: str`, `user_id: str`.
- Produces: `send_line_message(token: str, user_id: str, message: str) -> None`. Raises `requests.HTTPError` (via `raise_for_status()`) on non-2xx response.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_main.py`:

```python
from unittest.mock import patch, MagicMock
import requests

from main import send_line_message


@patch("main.requests.post")
def test_send_line_message_posts_correct_payload(mock_post):
    mock_post.return_value = MagicMock(status_code=200)
    mock_post.return_value.raise_for_status = MagicMock()

    send_line_message("test-token", "test-user-id", "hello")

    mock_post.assert_called_once_with(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer test-token",
        },
        json={
            "to": "test-user-id",
            "messages": [{"type": "text", "text": "hello"}],
        },
        timeout=10,
    )


@patch("main.requests.post")
def test_send_line_message_raises_on_http_error(mock_post):
    mock_response = MagicMock(status_code=400)
    mock_response.raise_for_status.side_effect = requests.HTTPError("400 Client Error")
    mock_post.return_value = mock_response

    try:
        send_line_message("test-token", "test-user-id", "hello")
        assert False, "expected HTTPError to be raised"
    except requests.HTTPError:
        pass
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_main.py -v`
Expected: FAIL with `ImportError: cannot import name 'send_line_message' from 'main'`

- [ ] **Step 3: Write minimal implementation**

Add `import requests` to the top of `main.py`, then add:

```python
LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"


def send_line_message(token: str, user_id: str, message: str) -> None:
    response = requests.post(
        LINE_PUSH_URL,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        json={"to": user_id, "messages": [{"type": "text", "text": message}]},
        timeout=10,
    )
    response.raise_for_status()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_main.py -v`
Expected: PASS (14 tests)

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add LINE push message sending"
```

---

### Task 6: CLI orchestration (`main()`)

**Files:**
- Modify: `main.py`
- Modify: `tests/test_main.py`

**Interfaces:**
- Consumes: `get_taipei_tomorrow`, `get_lunar_day`, `match_reminders`, `REMINDERS`, `build_message`, `send_line_message` (all defined in Tasks 2–5).
- Produces: `parse_args(argv: list[str]) -> argparse.Namespace` (fields: `date: str | None`, `dry_run: bool`); `run(argv: list[str] | None = None) -> int` — orchestrates the full flow and returns a process exit code (0 success/no-match, 1 on send failure).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_main.py`:

```python
import os
from main import run


@patch("main.send_line_message")
def test_run_sends_message_on_matching_date(mock_send, monkeypatch):
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("LINE_USER_ID", "uid")

    exit_code = run(["--date", "2026-02-17"])  # tomorrow = 2026-02-18 = lunar day 2

    assert exit_code == 0
    mock_send.assert_called_once_with(
        "tok", "uid", "🙏 明天是農曆初二，記得準備供品拜土地公喔！"
    )


@patch("main.send_line_message")
def test_run_does_not_send_on_non_matching_date(mock_send, monkeypatch):
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("LINE_USER_ID", "uid")

    exit_code = run(["--date", "2026-02-20"])  # tomorrow = 2026-02-21, not a match

    assert exit_code == 0
    mock_send.assert_not_called()


@patch("main.send_line_message")
def test_run_dry_run_does_not_send(mock_send, monkeypatch):
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("LINE_USER_ID", "uid")

    exit_code = run(["--date", "2026-02-17", "--dry-run"])

    assert exit_code == 0
    mock_send.assert_not_called()


@patch("main.send_line_message")
def test_run_returns_nonzero_on_send_failure(mock_send, monkeypatch):
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("LINE_USER_ID", "uid")
    mock_send.side_effect = requests.HTTPError("boom")

    exit_code = run(["--date", "2026-02-17"])

    assert exit_code == 1
```

Note: `--date` supplies the date to treat as "today" (a fixed reference point), and `run` computes tomorrow from it — this mirrors real usage where "today" is the actual current date and we always check tomorrow.

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_main.py -v`
Expected: FAIL with `ImportError: cannot import name 'run' from 'main'`

- [ ] **Step 3: Write minimal implementation**

Add `import argparse`, `import os`, `import sys` to the top of `main.py`, then add:

```python
def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LINE 農曆日期提醒")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Override 'today' as YYYY-MM-DD for testing (default: real current date)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the message instead of sending it via LINE",
    )
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if args.date:
        y, m, d = (int(part) for part in args.date.split("-"))
        now = datetime(y, m, d, tzinfo=TAIPEI_TZ)
    else:
        now = None

    tomorrow = get_taipei_tomorrow(now)
    lunar_day = get_lunar_day(tomorrow)
    matched = match_reminders(lunar_day, REMINDERS)

    if not matched:
        print(f"{tomorrow} (農曆{lunar_day}日) 沒有符合的提醒規則，不發送。")
        return 0

    message = build_message(matched, lunar_day)

    if args.dry_run:
        print(f"[dry-run] 將發送訊息：{message}")
        return 0

    token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
    user_id = os.environ["LINE_USER_ID"]

    try:
        send_line_message(token, user_id, message)
    except requests.HTTPError as exc:
        print(f"發送 LINE 訊息失敗：{exc}", file=sys.stderr)
        return 1

    print(f"已發送提醒：{message}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_main.py -v`
Expected: PASS (18 tests)

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add CLI orchestration with --date and --dry-run support"
```

---

### Task 7: GitHub Actions workflow and setup docs

**Files:**
- Create: `.github/workflows/reminder.yml`
- Create: `README.md`

**Interfaces:**
- Consumes: `main.py` as the entry point (`python main.py`), `requirements.txt` for install, `LINE_CHANNEL_ACCESS_TOKEN` / `LINE_USER_ID` as required GitHub Actions secrets.

- [ ] **Step 1: Create the workflow file**

Create `.github/workflows/reminder.yml`:

```yaml
name: LINE Date Reminder

on:
  schedule:
    - cron: "0 12 * * *"
  workflow_dispatch: {}

jobs:
  send-reminder:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - run: pip install -r requirements.txt

      - name: Run reminder check
        env:
          LINE_CHANNEL_ACCESS_TOKEN: ${{ secrets.LINE_CHANNEL_ACCESS_TOKEN }}
          LINE_USER_ID: ${{ secrets.LINE_USER_ID }}
        run: python main.py
```

`workflow_dispatch` is included so the workflow can be triggered manually from the GitHub Actions tab for a real end-to-end test.

- [ ] **Step 2: Create `README.md`**

```markdown
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
```

- [ ] **Step 3: Validate the workflow YAML syntax**

Run:
```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/reminder.yml', encoding='utf-8'))"
```
Expected: no exception raised. (If `pyyaml` isn't installed, run `pip install pyyaml` first — it's only needed for this one-off validation, not added to requirements.)

- [ ] **Step 4: Full local dry-run smoke test**

Run:
```bash
.venv/Scripts/python main.py --date 2026-02-17 --dry-run
```
Expected output includes: `[dry-run] 將發送訊息：🙏 明天是農曆初二，記得準備供品拜土地公喔！`

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/reminder.yml README.md
git commit -m "docs: add GitHub Actions workflow and setup instructions"
```

---

## Post-Plan Manual Steps (not automatable by the engineer executing this plan)

- User must add `LINE_CHANNEL_ACCESS_TOKEN` and `LINE_USER_ID` as GitHub Actions secrets on the actual repo before the scheduled workflow can succeed.
- User should trigger the workflow once manually via `workflow_dispatch` after secrets are set, to confirm an end-to-end real LINE message arrives.
