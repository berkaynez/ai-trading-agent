import os, time, requests, math
from datetime import datetime
import pandas as pd
import pandas_ta as ta
import ccxt
from dotenv import load_dotenv

load_dotenv()

# --- Ayarlar ---
SYMBOL = os.getenv("SYMBOL", "BTC/USDT")
TF = os.getenv("TIMEFRAME", "15m")
LOOKBACK = int(os.getenv("LOOKBACK", "300"))
SLEEP_SEC = int(os.getenv("SLEEP_SEC", "30"))
GATEWAY = os.getenv("GATEWAY_URL", "http://localhost:8000")
W_TECH = float(os.getenv("W_TECH", "0.5"))
W_ML = float(os.getenv("W_ML", "0.5"))
W_SENT = float(os.getenv("W_SENT", "0.0"))

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

def get_sentiment(symbol: str):
    try:
        r = requests.get(f"{GATEWAY}/sentiment/{symbol}", timeout=3)
        j = r.json()
        return float(j.get("sent_score", 0.0))
    except Exception:
        return 0.0

def get_ai_prob(symbol: str, tf: str):
    try:
        r = requests.get(f"{GATEWAY}/ai/predict", params={"symbol": symbol, "timeframe": tf}, timeout=3)
        j = r.json()
        return j.get("p_long", 0.0), j.get("p_exit", 0.0), j.get("sent_score", 0.0)
    except Exception:
        return 0.0, 0.0, 0.0

def main_loop():
    print(f"[{datetime.now()}] Agent started SYMBOL={SYMBOL} TF={TF} (DRY-RUN)")
    while True:
        try:
            df = fetch_candles()
            sig = make_signal(df)
            # DRY-RUN mode: use fixed balance instead of real API call
            bal = 1000.0  # Fixed balance for testing
            px = sig["price"]
            qty = position_sizing(balance_usdt=bal, price=px)

            # Sentiment + Technical blend
            # AI + Sentiment + Technical blend
            p_long, p_exit, sent = get_ai_prob(SYMBOL, TF)
            tech_score = sig["score"]          # -1..+1 (EMA/RSI kuralından)
            edge_ml = (p_long - p_exit)        # -1..+1 benzeri
            
            # Ağırlıklı karar
            edge = W_TECH * tech_score + W_ML * edge_ml
            
            action = "hold"
            if edge > 0.25:
                action = "long"
            elif edge < -0.25:
                action = "exit"

            # DRY-RUN log
            print(f"[AI] p_long={p_long:.2f} p_exit={p_exit:.2f} sent={sent:.2f} tech={tech_score:.2f} edge={edge:.2f} => {action}")

            # Decision logging to API
            try:
                requests.post(f"{GATEWAY}/agent/decision", json={
                    "ts": time.time(),
                    "symbol": SYMBOL,
                    "action": action,
                    "score": round(edge, 3),
                    "price": px,
                    "note": f"p_long={p_long:.2f} p_exit={p_exit:.2f} tech={tech_score:.2f}"
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
