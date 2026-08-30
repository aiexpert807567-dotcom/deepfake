import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

_USAGE_FILE = Path(__file__).resolve().parent / "_usage.json"
WEEKLY_QUOTA_HOURS = 30.0  # Kaggle's published free-tier baseline; not guaranteed by Kaggle, just our assumption


def _load() -> dict:
    if _USAGE_FILE.exists():
        try:
            return json.loads(_USAGE_FILE.read_text())
        except Exception:
            pass
    return {"week_start": None, "seconds_used": 0.0, "session_start": None}


def _save(data: dict):
    _USAGE_FILE.write_text(json.dumps(data))


def _current_week_start() -> str:
    now = datetime.now(timezone.utc)
    monday = now - timedelta(days=now.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    return monday.isoformat()


def _maybe_reset_week(data: dict) -> dict:
    week_start = _current_week_start()
    if data.get("week_start") != week_start:
        data = {"week_start": week_start, "seconds_used": 0.0, "session_start": data.get("session_start")}
    return data


def start_session():
    data = _maybe_reset_week(_load())
    if data.get("session_start") is None:
        data["session_start"] = datetime.now(timezone.utc).isoformat()
    _save(data)


def stop_session():
    data = _maybe_reset_week(_load())
    if data.get("session_start"):
        started = datetime.fromisoformat(data["session_start"])
        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        data["seconds_used"] = data.get("seconds_used", 0.0) + max(elapsed, 0.0)
        data["session_start"] = None
    _save(data)


def get_usage() -> dict:
    data = _maybe_reset_week(_load())
    seconds_used = data.get("seconds_used", 0.0)
    if data.get("session_start"):
        started = datetime.fromisoformat(data["session_start"])
        seconds_used += max((datetime.now(timezone.utc) - started).total_seconds(), 0.0)

    hours_used = seconds_used / 3600.0
    hours_remaining = max(WEEKLY_QUOTA_HOURS - hours_used, 0.0)

    week_start = datetime.fromisoformat(data["week_start"]) if data.get("week_start") else datetime.now(timezone.utc)
    next_reset = week_start + timedelta(days=7)

    return {
        "hours_used_estimate": round(hours_used, 2),
        "hours_remaining_estimate": round(hours_remaining, 2),
        "weekly_quota_hours": WEEKLY_QUOTA_HOURS,
        "resets_at": next_reset.isoformat(),
        "note": "Estimated by this app based on when the GPU was toggled on/off — not an official number from Kaggle, which has no public quota API.",
    }
