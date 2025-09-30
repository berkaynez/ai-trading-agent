# AI Trade Gateway — Binance Testnet (MVP)
- FastAPI + ccxt
- /health, /ticker/{symbol}, /order (emir dry-run)

## Kurulum
bash run.sh

## .env
BINANCE_TESTNET=true
BINANCE_API_KEY=...
BINANCE_API_SECRET=...

## Test
- Sağlık: http://localhost:8000/health
- Ticker: http://localhost:8000/ticker/BTC/USDT
- Order (dry-run):
  POST http://localhost:8000/order
  {
    "symbol":"BTC/USDT","side":"buy","qty":0.001,"type":"market"
  }
