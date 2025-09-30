# AI Trade Gateway — Binance Testnet (MVP)
- FastAPI + ccxt
- /health, /ticker/{symbol}, /order, /order/oco, /agent/decisions
- CORS support for UI access
- Input validation for trading parameters

## Kurulum
bash run.sh

## .env
BINANCE_TESTNET=true
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
SYMBOL=BTC/USDT
TIMEFRAME=15m
LOOKBACK=300
SLEEP_SEC=30
CORS_ORIGINS=http://localhost:3000

## Test
- Sağlık: http://localhost:8000/health
- Ticker: http://localhost:8000/ticker/BTC/USDT
- Candles: http://localhost:8000/candles/BTC/USDT?timeframe=15m&limit=100
- Order (dry-run):
  POST http://localhost:8000/order
  {
    "symbol":"BTC/USDT","side":"buy","qty":0.001,"type":"market"
  }
- OCO Simulation:
  POST http://localhost:8000/order/oco
  {
    "symbol":"BTC/USDT","side":"buy","qty":0.001,"take_profit_pct":0.01,"stop_loss_pct":0.005
  }
- Agent Decisions: http://localhost:8000/agent/decisions
