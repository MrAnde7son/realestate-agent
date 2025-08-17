"""Simple wrapper around APScheduler's background scheduler."""

from apscheduler.schedulers.background import BackgroundScheduler


def create_scheduler() -> BackgroundScheduler:
    """Return a configured background scheduler."""
    return BackgroundScheduler()
