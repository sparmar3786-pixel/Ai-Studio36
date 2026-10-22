"""Risk-first signal API. No broker order placement is implemented."""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Smart Signal API", version="0.1.0")


class OIState(str, Enum):
    LONG_BUILDUP = "LONG_BUILDUP"
    SHORT_BUILDUP = "SHORT_BUILDUP"
    SHORT_COVERING = "SHORT_COVERING"
    LONG_UNWINDING = "LONG_UNWINDING"
    NEUTRAL = "NEUTRAL"


def oi_state(premium_change_pct: float, oi_change_pct: float, threshold: float = 0.5) -> OIState:
    if premium_change_pct > threshold and oi_change_pct > threshold:
        return OIState.LONG_BUILDUP
    if premium_change_pct < -threshold and oi_change_pct > threshold:
        return OIState.SHORT_BUILDUP
    if premium_change_pct > threshold and oi_change_pct < -threshold:
        return OIState.SHORT_COVERING
    if premium_change_pct < -threshold and oi_change_pct < -threshold:
        return OIState.LONG_UNWINDING
    return OIState.NEUTRAL


class AnalyzeRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=40)
    option_type: str = Field(pattern="^(CE|PE)$")
    strike: int = Field(gt=0)
    spot: float = Field(gt=0)
    premium: float = Field(gt=0)
    premium_change_pct: float
    oi_change_pct: float
    vwap: Optional[float] = None
    ema9: Optional[float] = None
    ema21: Optional[float] = None
    ema50: Optional[float] = None
    rsi: Optional[float] = Field(default=None, ge=0, le=100)
    atr: Optional[float] = Field(default=None, gt=0)
    opening_range_high: Optional[float] = None
    opening_range_low: Optional[float] = None
    spread_pct: Optional[float] = None
    data_fresh: bool = False
    timestamp: Optional[datetime] = None
    max_data_age_seconds: int = Field(default=120, ge=1, le=600)
    risk_per_trade_pct: float = Field(default=0.5, gt=0, le=1.0)


def make_signal(d: AnalyzeRequest) -> dict:
    now = datetime.now(timezone.utc)
    age = None
    if d.timestamp:
        ts = d.timestamp if d.timestamp.tzinfo else d.timestamp.replace(tzinfo=timezone.utc)
        age = max(0.0, (now - ts.astimezone(timezone.utc)).total_seconds())
    fresh = d.data_fresh and age is not None and age <= d.max_data_age_seconds
    oi = oi_state(d.premium_change_pct, d.oi_change_pct)
    required = [d.vwap, d.ema9, d.ema21, d.ema50, d.rsi, d.atr,
                d.opening_range_high, d.opening_range_low, d.spread_pct]
    if not fresh or any(v is None for v in required):
        return {"status": "WAIT", "reason": "DATA REQUIRED: feed stale or required fields missing",
                "data_fresh": fresh, "data_age_seconds": age, "oi_state": oi.value}
    if d.spread_pct > 2:
        return {"status": "WAIT", "reason": "Spread exceeds 2% safety filter",
                "data_fresh": True, "data_age_seconds": age, "oi_state": oi.value}
    bullish = (d.ema9 > d.ema21 > d.ema50 and d.spot > d.vwap
               and d.spot > d.opening_range_high and 50 < d.rsi < 80
               and oi in (OIState.SHORT_COVERING, OIState.LONG_BUILDUP)
               and d.premium_change_pct > 0.5)
    bearish = (d.ema9 < d.ema21 < d.ema50 and d.spot < d.vwap
               and d.spot < d.opening_range_low and 20 < d.rsi < 50
               and oi in (OIState.SHORT_COVERING, OIState.LONG_BUILDUP)
               and d.premium_change_pct > 0.5)
    if not ((d.option_type == "CE" and bullish) or (d.option_type == "PE" and bearish)):
        return {"status": "WAIT", "reason": "Confluence threshold not met",
                "data_fresh": True, "data_age_seconds": age, "oi_state": oi.value}
    # Option premium ATR must be supplied by a validated option-candle feed in production.
    # Use conservative 12% floor until that feed exists; ATR here is not silently treated as option ATR.
    risk = max(d.premium * 0.12, 0.01)
    entry = round(d.premium, 2)
    sl = round(entry - risk, 2)
    return {"status": "SIGNAL", "direction": f"BUY {d.option_type}", "symbol": d.symbol,
            "strike": d.strike, "entry": entry, "stoploss": sl,
            "target1": round(entry + 1.5 * risk, 2),
            "target2": round(entry + 2.5 * risk, 2),
            "target3": round(entry + 4 * risk, 2),
            "risk_per_trade_pct": d.risk_per_trade_pct, "oi_state": oi.value,
            "reason": "OI + trend + VWAP + opening-range confluence",
            "data_fresh": True, "data_age_seconds": age,
            "disclaimer": "Indicative signal only; not a guaranteed fill or return."}


@app.get("/health")
def health():
    return {"status": "ok", "mode": "signal-only", "live_data_connected": False}


@app.get("/v1/signals")
def signals():
    return {"status": "WAIT", "reason": "DATA REQUIRED: live Angel One feed is not configured",
            "data_fresh": False, "signals": []}


@app.post("/v1/analyze")
def analyze(data: AnalyzeRequest):
    return make_signal(data)
