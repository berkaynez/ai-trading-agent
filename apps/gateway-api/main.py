from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ccxt, os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Trade Gateway (Binance Testnet)")

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

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/ticker/{symbol}")
def ticker(symbol: str):
    try:
        return binance.fetch_ticker(symbol)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/order")
def order(o: OrderReq):
    try:
        params = {}
        if o.type == "limit" and o.price is None:
            raise ValueError("Limit emri için price gerekli.")
        # Güvenlik: İlk aşamada emir göndermeyi kapalı tutalım:
        # return binance.create_order(o.symbol, o.type, o.side, o.qty, o.price, params)
        return {"status": "DRY_RUN", "echo": o.dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
