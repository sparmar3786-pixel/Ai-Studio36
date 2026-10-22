from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app, oi_state, OIState, AnalyzeRequest, make_signal

client = TestClient(app)


def test_oi_classification():
    assert oi_state(2, 3) == OIState.LONG_BUILDUP
    assert oi_state(-2, 3) == OIState.SHORT_BUILDUP
    assert oi_state(2, -3) == OIState.SHORT_COVERING
    assert oi_state(-2, -3) == OIState.LONG_UNWINDING
    assert oi_state(0.1, 0.1) == OIState.NEUTRAL


def test_health_and_no_fake_live_signal():
    assert client.get("/health").json()["live_data_connected"] is False
    payload = client.get("/v1/signals").json()
    assert payload["status"] == "WAIT"
    assert payload["data_fresh"] is False


def test_stale_data_never_signals():
    d = AnalyzeRequest(symbol="NIFTY", option_type="CE", strike=25000, spot=25010,
        premium=100, premium_change_pct=2, oi_change_pct=-2, vwap=25000,
        ema9=25005, ema21=25000, ema50=24990, rsi=60, atr=10,
        opening_range_high=25000, opening_range_low=24900, spread_pct=0.5,
        data_fresh=True, timestamp=datetime.now(timezone.utc)-timedelta(minutes=5))
    assert make_signal(d)["status"] == "WAIT"
