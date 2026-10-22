from datetime import datetime, timezone, timedelta
from app.angelone import FeedHealth


def test_disconnected_feed_is_not_fresh():
    assert not FeedHealth(False, datetime.now(timezone.utc)).is_fresh()


def test_old_tick_is_not_fresh():
    assert not FeedHealth(True, datetime.now(timezone.utc) - timedelta(minutes=3)).is_fresh()


def test_recent_tick_is_fresh():
    assert FeedHealth(True, datetime.now(timezone.utc) - timedelta(seconds=2)).is_fresh()
