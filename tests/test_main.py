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
