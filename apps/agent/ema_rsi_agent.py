import os, time
from datetime import datetime
import pandas as pd
import pandas_ta as ta
import ccxt
import requests
from dotenv import load_dotenv

load_dotenv()

# --- Ayarlar ---
SYMBOL = os.getenv("SYMBOL", "BTC/USDT")
TF = os.getenv("TIMEFRAME", "15m")
LOOKBACK = int(os.getenv("LOOKBACK", "300"))
SLEEP_SEC = int(os.getenv("SLEEP_SEC", "30"))
GATEWAY = os.getenv("GATEWAY_URL", "http://localhost:8000")

# Binance CCXT istemcisi
ex = ccxt.binance({
    "apiKey": os.getenv("BINANCE_API_KEY"),
    "secret": os.getenv("BINANCE_API_SECRET"),
    "enableRateLimit": True,
})
if (os.getenv("BINANCE_TESTNET") or "").lower() == "true":
    ex.set_sandbox_mode(True)

def fetch_candles():
    ohlcv = ex.fetch_ohlcv(SYMBOL, timeframe=TF, limit=LOOKBACK)
    df = pd.DataFrame(ohlcv, columns=["ts","o","h","l","c","v"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms")
    return df

def make_signal(df: pd.DataFrame):
    df = df.copy()
    df["ema_fast"] = ta.ema(df["c"], length=20)
    df["ema_slow"] = ta.ema(df["c"], length=50)
    df["rsi"] = ta.rsi(df["c"], length=14)
    last = df.iloc[-1]

    # Basit kural (örnek):
    # Golden cross + RSI>55 -> LONG sinyali
    # Death cross + RSI<45 -> FLAT (çık) sinyali
    if last.ema_fast > last.ema_slow and last.rsi > 55:
        return {"action": "long", "score": 0.6, "price": float(last.c)}
    if last.ema_fast < last.ema_slow and last.rsi < 45:
        return {"action": "exit", "score": -0.6, "price": float(last.c)}
    return {"action": "hold", "score": 0.0, "price": float(last.c)}

def position_sizing(balance_usdt: float, price: float, risk_per_trade=0.01, stop_pct=0.01):
    # Risk başına miktar (çok basit örnek)
    risk_usd = balance_usdt * risk_per_trade
    if price <= 0: return 0.0
    qty = risk_usd / (price * stop_pct)
    return round(qty, 4)

def main_loop():
    print(f"[{datetime.now()}] Agent started SYMBOL={SYMBOL} TF={TF} (DRY-RUN)")
    while True:
        try:
            df = fetch_candles()
            sig = make_signal(df)
            bal = ex.fetch_balance().get("total", {}).get("USDT", 1000.0)
            px = sig["price"]
            qty = position_sizing(balance_usdt=bal, price=px)

            # DRY-RUN log
            print(f"[{datetime.now()}] {SYMBOL} px={px:.2f} action={sig['action']} score={sig['score']} qty={qty}")

            # Decision logging to API
            try:
                requests.post(f"{GATEWAY}/agent/decision", json={
                    "ts": time.time(),
                    "symbol": SYMBOL,
                    "action": sig["action"],
                    "score": sig["score"],
                    "price": px,
                    "note": "ema20/ema50 + rsi14"
                }, timeout=3)
            except Exception as ex:
                print("decision post failed:", ex)

            # Gerçek emir kapalı: sadece gösteriyoruz
            # Örn: market buy (açmak isterseniz gateway /order'a POST edilebilir)
            # requests.post("http://localhost:8000/order", json={...})

        except Exception as e:
            print("Error:", e)

        time.sleep(SLEEP_SEC)

if __name__ == "__main__":
    main_loop()
