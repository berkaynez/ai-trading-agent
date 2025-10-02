from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
import ccxt, os
from dotenv import load_dotenv
from typing import Optional
import logging, time
from collections import deque
import pandas as pd
import requests
from datetime import datetime

load_dotenv()

# ---- Sentiment helpers (CryptoPanic + cache) ----
_SENT_CACHE = {"key": "", "ts": 0.0, "data": None}
_SENT_TTL = 60  # sn

def _symbol_base(sym: str) -> str:
    return (sym or "BTC/USDT").split("/")[0].upper()

def fetch_sentiment_real(symbol: str):
    token = (os.getenv("CRYPTOPANIC_TOKEN") or "").strip()
    base = _symbol_base(symbol)
    if not token:
        return {"symbol": symbol, "sent_score": 0.0, "items": []}
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={token}&currencies={base}&filter=hot"
    r = requests.get(url, timeout=5)
    j = r.json()
    items = []
    score = 0.0
    for it in (j.get("results") or [])[:10]:
        title = it.get("title","") or ""
        t = title.lower()
        p = 0
        for w in ["surge","rally","up","bull","breakout","pump","gain"]:
            if w in t: p += 1
        for w in ["dump","down","fall","bear","retrace","selloff","crash"]:
            if w in t: p -= 1
        items.append({"title": title, "domain": it.get("domain",""), "score": p})
    if items:
        score = sum(i["score"] for i in items) / max(1, len(items))
    return {"symbol": symbol, "sent_score": round(float(score), 3), "items": items[:5]}

def fetch_sentiment(symbol: str):
    now = time.time()
    key = symbol.upper()
    if _SENT_CACHE["data"] and _SENT_CACHE["key"] == key and now - _SENT_CACHE["ts"] < _SENT_TTL:
        return _SENT_CACHE["data"]
    try:
        data = fetch_sentiment_real(symbol)
    except Exception:
        # Token yoksa veya hata varsa random yerine 0 puan dönen güvenli fallback:
        data = {"symbol": symbol, "sent_score": 0.0, "items": []}
    _SENT_CACHE.update({"key": key, "ts": now, "data": data})
    # Debug logging
    logger.info(f"[sentiment] symbol={symbol} items={len(data.get('items',[]))} score={data.get('sent_score')}")
    return data

# ---- Risk state (in-memory) ----
_RISK = {"day": None, "baseline": None}

def _today_key():
    return datetime.utcnow().strftime("%Y-%m-%d")

def _get_equity_usdt():
    # basit yaklaşım: toplam USDT (testnet için yeterli)
    bal = binance.fetch_balance()
    total_usdt = float(bal.get("total", {}).get("USDT", 0.0))
    return total_usdt

def _ensure_baseline():
    day = _today_key()
    if _RISK["day"] != day or _RISK["baseline"] is None:
        _RISK["day"] = day
        _RISK["baseline"] = max(_get_equity_usdt(), 1e-6)
    return _RISK["baseline"]

def _dd_ok():
    base = _ensure_baseline()
    eq = _get_equity_usdt()
    dd = (eq - base) / base  # negatifse drawdown
    limit = float(os.getenv("RISK_MAX_DRAWDOWN_DAILY", "0.03"))
    return dd >= -limit, dd, base, eq

def _notional_ok(symbol: str, qty: float):
    tick = binance.fetch_ticker(symbol)
    px = float(tick["last"])
    notional = px * float(qty)
    cap = float(os.getenv("RISK_MAX_POS_USD", "300"))
    return notional <= cap, notional, cap

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")

app = FastAPI(title="AI Trade Gateway (Binance Testnet)")

# CORS configuration from environment
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)
    try:
        body = await request.body()
        body_str = body.decode("utf-8") if body else ""
    except Exception:
        body_str = ""
    logger.info(f"{request.method} {request.url.path} {response.status_code} {duration_ms}ms body={body_str[:200]}")
    return response

binance = ccxt.binance({
    "apiKey": os.getenv("BINANCE_API_KEY"),
    "secret": os.getenv("BINANCE_API_SECRET"),
    "enableRateLimit": True,
})
if (os.getenv("BINANCE_TESTNET") or "").lower() == "true":
    binance.set_sandbox_mode(True)

class OrderReq(BaseModel):
    symbol: str       # "BTC/USDT"
    side: str         # "buy" | "sell"
    qty: float        # base amount
    type: str = "market"  # "market" | "limit"
    price: float | None = None
    
    @field_validator('side')
    @classmethod
    def validate_side(cls, v):
        if v.lower() not in ['buy', 'sell']:
            raise ValueError('side must be "buy" or "sell"')
        return v.lower()
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v.lower() not in ['market', 'limit']:
            raise ValueError('type must be "market" or "limit"')
        return v.lower()

class OcoReq(BaseModel):
    symbol: str           # "BTC/USDT"
    side: str             # "buy" | "sell" (pozisyon açış yönü)
    qty: float
    entry_type: str = "market"    # şimdilik market
    take_profit_pct: float = 0.01 # +%1
    stop_loss_pct: float = 0.005  # -%0.5
    
    @field_validator('side')
    @classmethod
    def validate_side(cls, v):
        if v.lower() not in ['buy', 'sell']:
            raise ValueError('side must be "buy" or "sell"')
        return v.lower()
    
    @field_validator('entry_type')
    @classmethod
    def validate_entry_type(cls, v):
        if v.lower() not in ['market', 'limit']:
            raise ValueError('entry_type must be "market" or "limit"')
        return v.lower()

class Decision(BaseModel):
    ts: float          # time.time()
    symbol: str
    action: str        # long/exit/hold vs
    score: float
    price: float
    note: str | None = None

DECISIONS = deque(maxlen=500)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/ticker/{symbol}")
def ticker(symbol: str):
    try:
        return binance.fetch_ticker(symbol)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/candles/{symbol}")
def candles(symbol: str, timeframe: Optional[str] = "15m", limit: Optional[int] = 200):
    try:
        raw = binance.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        return [
            {"ts": o[0], "o": o[1], "h": o[2], "l": o[3], "c": o[4], "v": o[5]}
            for o in raw
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/order")
def order(o: OrderReq):
    try:
        params = {}
        if o.type == "limit" and o.price is None:
            raise ValueError("Limit emri için price gerekli.")
        
        # Risk guards
        ok_dd, dd, base, eq = _dd_ok()
        ok_notional, notion, cap = _notional_ok(o.symbol, o.qty)
        if not ok_dd or not ok_notional:
            msg = {
                "status": "BLOCKED_BY_RISK",
                "dd": round(dd, 4),
                "baseline": round(base, 2),
                "equity": round(eq, 2),
                "notional": round(notion, 2),
                "cap": cap
            }
            return msg  # EXEC=true olsa bile güvenlik için blokluyoruz
        
        enable_exec = (os.getenv("ENABLE_ORDER_EXECUTION") or "").lower() == "true"
        if enable_exec:
            # Gerçek emir (testnet veya gerçek) – dikkat!
            return binance.create_order(o.symbol, o.type, o.side, o.qty, o.price, params)
        # Dry-run: ENABLE_ORDER_EXECUTION=false iken sadece yansıtır
        return {"status": "DRY_RUN", "echo": o.dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/order/oco")
def order_oco(req: OcoReq):
    try:
        # Son fiyatı al
        ticker = binance.fetch_ticker(req.symbol)
        last = float(ticker["last"])

        # Yön: long açıyorsak TP yukarı, SL aşağı. Short için tersi.
        if req.side.lower() == "buy":
            entry = last
            tp = entry * (1 + req.take_profit_pct)
            sl = entry * (1 - req.stop_loss_pct)
        elif req.side.lower() == "sell":
            entry = last
            tp = entry * (1 - req.take_profit_pct)
            sl = entry * (1 + req.stop_loss_pct)
        else:
            raise ValueError("side 'buy' veya 'sell' olmalı")

        # Risk guards
        ok_dd, dd, base, eq = _dd_ok()
        ok_notional, notion, cap = _notional_ok(req.symbol, req.qty)
        if not ok_dd or not ok_notional:
            return {
                "status": "BLOCKED_BY_RISK",
                "dd": round(dd, 4),
                "baseline": round(base, 2),
                "equity": round(eq, 2),
                "notional": round(notion, 2),
                "cap": cap
            }

        enable_exec = (os.getenv("ENABLE_ORDER_EXECUTION") or "").lower() == "true"
        if enable_exec:
            # UYARI: Binance/ccxt ile gerçek OCO emri API detay ister.
            # İlk etapta: market entry + ayrı TP/SL emirleri oluşturmak gerekir.
            # Şimdilik güvenli olmak için kapalı tutalım.
            pass

        return {
            "status": "DRY_RUN",
            "symbol": req.symbol,
            "side": req.side.lower(),
            "entry_price": round(entry, 6),
            "qty": req.qty,
            "take_profit_price": round(tp, 6),
            "stop_loss_price": round(sl, 6),
            "params": {
                "tp_pct": req.take_profit_pct,
                "sl_pct": req.stop_loss_pct
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/agent/decision")
def post_decision(d: Decision):
    DECISIONS.append(d.dict())
    return {"ok": True, "size": len(DECISIONS)}

@app.get("/agent/decisions")
def get_decisions(limit: int = 50):
    data = list(DECISIONS)[-limit:]
    return {"items": data[::-1]}  # son gelen ilk gelsin

@app.get("/sentiment/{symbol}")
def sentiment(symbol: str, force: bool = Query(False)):
    try:
        global _SENT_CACHE
        if force:
            _SENT_CACHE = {"key": "", "ts": 0.0, "data": None}
        return fetch_sentiment(symbol)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/features/{symbol}")
def features(symbol: str, timeframe: str = Query("15m"), limit: int = Query(100)):
    try:
        # Get current price
        ticker = binance.fetch_ticker(symbol)
        price = float(ticker["last"])
        
        # Get candles for technical analysis
        ohlcv = binance.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=["ts","o","h","l","c","v"])
        
        # Calculate technical indicators
        import pandas_ta as ta
        ema20_series = ta.ema(df["c"], length=20)
        ema50_series = ta.ema(df["c"], length=50)
        rsi14_series = ta.rsi(df["c"], length=14)
        
        # Handle cases where indicators might be None (insufficient data)
        ema20 = ema20_series.iloc[-1] if ema20_series is not None and not ema20_series.empty else None
        ema50 = ema50_series.iloc[-1] if ema50_series is not None and not ema50_series.empty else None
        rsi14 = rsi14_series.iloc[-1] if rsi14_series is not None and not rsi14_series.empty else None
        
        # If any indicator is None, we need more data
        if ema20 is None or ema50 is None or rsi14 is None:
            raise HTTPException(status_code=400, detail=f"Insufficient data for timeframe {timeframe}. Try a shorter timeframe or increase limit.")
        
        # Get sentiment (real)
        sent = fetch_sentiment(symbol)
        sent_score = float(sent.get("sent_score", 0.0))
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "price": round(price, 2),
            "ema20": round(ema20, 2),
            "ema50": round(ema50, 2),
            "rsi14": round(rsi14, 2),
            "sent_score": sent_score
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
