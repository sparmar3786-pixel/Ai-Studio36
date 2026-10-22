# Smart Signal — Angel One Trading Signals

A risk-first Android signal dashboard and Python API starter. This repository starts in **signal-only / paper mode**. It does not place broker orders and never promises a daily return.

## Features
- Android Jetpack Compose dashboard with signal, entry, stop-loss, targets, strike, OI state, freshness and risk status.
- FastAPI backend with explicit stale-data gating, OI build-up classification, EMA/RSI/ATR/VWAP-ready strategy inputs and deterministic signal calculation.
- GitHub Actions tests plus Android debug APK build artifact.
- Angel One adapter integration is intentionally isolated: add credentials only as server environment secrets after verifying SmartAPI access. Never embed API keys, PIN, TOTP secret or JWT in the APK or repository.

## Run backend locally
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest -q
```
API: `GET /health`, `GET /v1/signals`, `POST /v1/analyze`. Without a verified live feed the response must remain WAIT / DATA REQUIRED.

## Build Android APK
Open `android/` in Android Studio or run Gradle with JDK 17 and Android SDK:
```bash
cd android
gradle assembleDebug
```
GitHub Actions builds `app-debug.apk` and publishes it as a workflow artifact on successful builds.

## Safety and data contract
- Signal generation requires timestamps and explicit `data_fresh=true`; stale, missing, inconsistent or disconnected feed => **WAIT**, never BUY/SELL.
- OI labels are heuristics based on both premium and OI change; validate against real market data. PCR alone is not an entry signal.
- Stops/targets are estimates, not guaranteed fills. Slippage, gaps, spreads and liquidity can change outcomes.
- No 15% daily-profit guarantee exists. Use paper trading, realistic fees/slippage, out-of-sample backtests and broker/compliance review before live use.
- Current release is a starter, not verified live Angel One integration. API credentials, data entitlement, option-chain token mapping, FCM configuration and end-to-end device tests remain deployment steps.

## References
- [Angel One SmartAPI Python SDK](https://github.com/angel-one/smartapi-python)
- [TA-Lib Python](https://github.com/ta-lib/ta-lib-python)
- [Backtrader](https://github.com/mementum/backtrader)
- [Android Compose samples](https://github.com/android/compose-samples)
- [Firebase Android quickstart](https://github.com/firebase/quickstart-android)
