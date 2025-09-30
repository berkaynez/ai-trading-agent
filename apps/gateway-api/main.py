from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ccxt, os
from dotenv import load_dotenv
from typing import Optional
import logging, time, json

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")

app = FastAPI(title="AI Trade Gateway (Binance Testnet)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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

class OcoReq(BaseModel):
    symbol: str           # "BTC/USDT"
    side: str             # "buy" | "sell" (pozisyon açış yönü)
    qty: float
    entry_type: str = "market"    # şimdilik market
    take_profit_pct: float = 0.01 # +%1
    stop_loss_pct: float = 0.005  # -%0.5

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
