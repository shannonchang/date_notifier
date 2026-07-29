import argparse
import os
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests

from lunar_python import Solar

TAIPEI_TZ = ZoneInfo("Asia/Taipei")

REMINDERS = [
    {"name": "拜土地公", "lunar_days": [2, 16]},
]


def match_reminders(lunar_day: int, reminders: list[dict]) -> list[str]:
    return [r["name"] for r in reminders if lunar_day in r["lunar_days"]]


def get_taipei_tomorrow(now: datetime | None = None) -> date:
    if now is None:
        now = datetime.now(TAIPEI_TZ)
    today = now.astimezone(TAIPEI_TZ).date()
    return today + timedelta(days=1)


def get_lunar_day(solar_date: date) -> int:
    solar = Solar.fromYmd(solar_date.year, solar_date.month, solar_date.day)
    return solar.getLunar().getDay()


_LUNAR_DAY_LABELS = {2: "初二", 16: "十六"}


def build_message(matched_names: list[str], lunar_day: int) -> str:
    day_label = _LUNAR_DAY_LABELS.get(lunar_day, f"{lunar_day}")
    names = "、".join(matched_names)
    return f"🙏 明天是農曆{day_label}，記得準備供品{names}喔！"


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
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(run())
