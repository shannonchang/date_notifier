from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

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
