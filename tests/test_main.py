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
