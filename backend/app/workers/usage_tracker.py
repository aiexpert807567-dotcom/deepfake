import os
from datetime import datetime, timezone, timedelta

from sqlalchemy import Float, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

WEEKLY_QUOTA_HOURS = 30.0  # App estimate only; Kaggle does not expose a public quota API.


class Base(DeclarativeBase):
    pass


class UsageState(Base):
    __tablename__ = "gpu_usage_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    week_start: Mapped[str] = mapped_column(String(64), nullable=False)
    seconds_used: Mapped[float] = mapped_column(Float, default=0.0)
    session_start: Mapped[str | None] = mapped_column(String(64), nullable=True)


def _engine():
    database_url = os.getenv("DATABASE_URL", "sqlite:///./studio_jobs.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, future=True, pool_pre_ping=True, connect_args=connect_args)
    Base.metadata.create_all(engine)
    return engine


_ENGINE = _engine()


def _current_week_start() -> str:
    now = datetime.now(timezone.utc)
    monday = now - timedelta(days=now.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    return monday.isoformat()


def _get_state(session: Session) -> UsageState:
    state = session.get(UsageState, 1)
    week_start = _current_week_start()
    if state is None:
        state = UsageState(id=1, week_start=week_start, seconds_used=0.0, session_start=None)
        session.add(state)
        session.flush()
    elif state.week_start != week_start:
        # New week: reset accumulated usage but keep an active session running.
        state.week_start = week_start
        state.seconds_used = 0.0
    return state


def start_session():
    with Session(_ENGINE) as session:
        state = _get_state(session)
        if state.session_start is None:
            state.session_start = datetime.now(timezone.utc).isoformat()
        session.commit()


def stop_session():
    with Session(_ENGINE) as session:
        state = _get_state(session)
        if state.session_start:
            started = datetime.fromisoformat(state.session_start)
            elapsed = (datetime.now(timezone.utc) - started).total_seconds()
            state.seconds_used += max(elapsed, 0.0)
            state.session_start = None
        session.commit()


def get_usage() -> dict:
    with Session(_ENGINE) as session:
        state = _get_state(session)
        seconds_used = float(state.seconds_used or 0.0)
        if state.session_start:
            started = datetime.fromisoformat(state.session_start)
            seconds_used += max((datetime.now(timezone.utc) - started).total_seconds(), 0.0)
        week_start_value = state.week_start
        session.commit()

    hours_used = seconds_used / 3600.0
    hours_remaining = max(WEEKLY_QUOTA_HOURS - hours_used, 0.0)
    week_start = datetime.fromisoformat(week_start_value)
    next_reset = week_start + timedelta(days=7)

    return {
        "hours_used_estimate": round(hours_used, 2),
        "hours_remaining_estimate": round(hours_remaining, 2),
        "weekly_quota_hours": WEEKLY_QUOTA_HOURS,
        "resets_at": next_reset.isoformat(),
        "note": "Estimated app-side usage. Kaggle does not provide a public API for exact remaining GPU hours.",
    }
