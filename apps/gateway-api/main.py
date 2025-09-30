from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import ccxt, os
from dotenv import load_dotenv
from typing import Optional
import logging, time
from collections import deque
import pandas as pd

load_dotenv()

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
    
    @validator('side')
    def validate_side(cls, v):
        if v.lower() not in ['buy', 'sell']:
            raise ValueError('side must be "buy" or "sell"')
        return v.lower()
    
    @validator('type')
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
    
    @validator('side')
    def validate_side(cls, v):
        if v.lower() not in ['buy', 'sell']:
            raise ValueError('side must be "buy" or "sell"')
        return v.lower()
    
    @validator('entry_type')
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
def sentiment(symbol: str):
    try:
        # Mock sentiment data - in production, integrate with CryptoPanic API
        import random
        sent_score = round(random.uniform(-3, 3), 2)
        items = [
            {"title": f"Bitcoin price analysis: {symbol} shows strong momentum"},
            {"title": f"Market sentiment for {symbol} remains bullish"},
            {"title": f"Technical indicators suggest {symbol} consolidation"},
            {"title": f"Trading volume for {symbol} increases significantly"},
            {"title": f"Investor confidence in {symbol} reaches new highs"}
        ]
        return {
            "symbol": symbol,
            "sent_score": sent_score,
            "items": items
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/features/{symbol}")
def features(symbol: str):
    try:
        # Get current price
        ticker = binance.fetch_ticker(symbol)
        price = float(ticker["last"])
        
        # Get candles for technical analysis
        ohlcv = binance.fetch_ohlcv(symbol, timeframe="15m", limit=100)
        df = pd.DataFrame(ohlcv, columns=["ts","o","h","l","c","v"])
        
        # Calculate technical indicators
        import pandas_ta as ta
        ema20 = ta.ema(df["c"], length=20).iloc[-1]
        ema50 = ta.ema(df["c"], length=50).iloc[-1]
        rsi14 = ta.rsi(df["c"], length=14).iloc[-1]
        
        # Get sentiment (mock)
        import random
        sent_score = round(random.uniform(-3, 3), 2)
        
        return {
            "symbol": symbol,
            "price": round(price, 2),
            "ema20": round(ema20, 2),
            "ema50": round(ema50, 2),
            "rsi14": round(rsi14, 2),
            "sent_score": sent_score
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
