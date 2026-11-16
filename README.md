
# AI Trading Agent

**An experimental cryptocurrency trading research platform combining technical analysis, machine learning, and news sentiment.**

**Tech Stack:** Python · FastAPI · scikit-learn · Next.js · TypeScript · CCXT

> [!WARNING]
> **Research prototype — not a production trading system or financial advice.** Trading profitability has not been established. The gateway contains an optional order-execution path that requires explicit configuration. Never enable live execution without independently validating the implementation.

## Overview

AI Trading Agent explores how multiple market signals can be combined to support cryptocurrency trading decisions.

The platform integrates technical indicators, a machine-learning classifier, cryptocurrency news sentiment, and a web dashboard.

The Python agent currently generates and logs decisions without directly submitting trading orders.

## Key Features

### Technical Analysis
- EMA20 and EMA50 trend indicators
- RSI14 momentum indicator
- Long, exit, and hold signal generation
- Market data retrieval through CCXT

### Machine Learning
- Random Forest classification using scikit-learn
- Historical OHLCV-based feature engineering
- Return, volatility, EMA, and RSI features
- Long, exit, and hold probability estimates

### News Sentiment
- Cryptocurrency news headline analysis
- Keyword-based sentiment scoring
- CryptoPanic integration with RSS fallback
- Short-term sentiment caching

### Trading Agent
- Configurable technical and ML signal weights
- Decision scoring and threshold-based actions
- Decision logging through FastAPI
- Dry-run operation without direct order submission

**Note:** The current agent retrieves sentiment information but does not include it in the final weighted trading decision.

### Web Dashboard
- Market price monitoring
- Interactive price charts
- EMA and RSI indicators
- Sentiment information
- AI prediction display
- Agent decision history

### Risk Controls
- Configurable position-notional limits
- Daily drawdown checks
- Optional gateway order execution
- Testnet configuration support

These controls are experimental and are not sufficient for production trading.

## System Architecture

```text
                  Binance Market Data
                          |
             +------------+------------+
             |                         |
       Technical Analysis        Feature Engineering
         EMA20 / EMA50                  |
             RSI14               Random Forest
             |                         |
             +------------+------------+
                          |
                    Python Agent
                          |
                   Decision Logging
                          |
                    FastAPI Gateway
                          |
                    Next.js Dashboard

          Cryptocurrency News Feeds
                          |
                 Sentiment Scoring
                          |
                    FastAPI Gateway
```

## Technology Stack

| Component | Technologies |
|---|---|
| Trading Agent | Python, pandas, pandas-ta, CCXT |
| Machine Learning | scikit-learn, NumPy, joblib |
| Backend API | FastAPI, Pydantic |
| Frontend | Next.js, React, TypeScript |
| Data Visualization | Recharts |
| Market Data | Binance via CCXT |
| News Sentiment | CryptoPanic, RSS feeds |

## Project Structure

```text
ai-trading-agent/
├── apps/
│   ├── agent/
│   │   ├── ema_rsi_agent.py
│   │   └── train_ml.py
│   ├── gateway-api/
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   └── run.sh
│   ├── shared/
│   │   └── feature_builder.py
│   └── ui/
│       ├── app/
│       └── package.json
├── models/
│   └── ml/
│       └── model.pkl
├── run_agent.sh
└── README.md
```

## Getting Started

> The following commands reflect the repository's existing scripts. They have not been independently executed or verified in this review.

### Prerequisites

- Python and pip
- Node.js and npm
- Internet access for market data
- Exchange API credentials if required by your configuration

### 1. Clone the Repository

```bash
git clone https://github.com/berkaynez/ai-trading-agent.git
cd ai-trading-agent
```

### 2. Start the Backend

```bash
cd apps/gateway-api
bash run.sh
```

The script creates a Python virtual environment, installs dependencies, copies the example environment file when needed, and starts the FastAPI server.

Backend URL:

```text
http://localhost:8000
```

Health endpoint:

```text
http://localhost:8000/health
```

Review the `.env` configuration before supplying credentials or enabling any execution settings.

### 3. Start the Frontend

Open another terminal from the repository root:

```bash
cd apps/ui
npm ci
npm run dev
```

Dashboard URL:

```text
http://localhost:3000
```

The dashboard connects to the local gateway by default.

### 4. Run the Trading Agent

After preparing the gateway Python environment, return to the repository root and run:

```bash
bash run_agent.sh
```

The agent retrieves market data, generates signals, and logs decisions.

**The current Python agent does not directly submit trading orders.**

### 5. Model Training

The model training script is located at:

```text
apps/agent/train_ml.py
```

It uses historical market data and technical features to train a Random Forest classifier.

The default model output path is:

```text
models/ml/model.pkl
```

Model training and evaluation require further validation before predictions can be considered reliable.

## API Endpoints

Selected FastAPI endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /health` | API health check |
| `GET /ticker/{symbol}` | Market ticker |
| `GET /candles/{symbol}` | OHLCV market data |
| `GET /features/{symbol}` | Technical indicators and sentiment |
| `GET /sentiment/{symbol}` | News sentiment |
| `GET /ai/predict` | Machine-learning predictions |
| `GET /agent/decisions` | Logged agent decisions |
| `POST /agent/decision` | Record an agent decision |
| `POST /order` | Order request with risk checks |
| `POST /order/oco` | Prototype OCO calculation |

**Security note:** The gateway's order-execution behavior depends on its configuration. `ENABLE_ORDER_EXECUTION` and `BINANCE_TESTNET` are separate settings. Do not assume that enabling order execution automatically restricts requests to a sandbox.

## Current Limitations

- No documented out-of-sample performance benchmark.
- No verified profitability or production trading results.
- No validated backtesting framework with fees and slippage.
- Sentiment analysis uses keyword-based scoring rather than a trained language model.
- Sentiment is not yet included in the agent's final weighted decision.
- Risk controls require additional validation.
- Decision history is stored in memory and is lost when the gateway restarts.
- Automated test coverage and CI have not been established in this repository review.
- The included serialized model should only be loaded from a trusted source.

## Roadmap

- [ ] Add automated tests and GitHub Actions CI.
- [ ] Implement reproducible time-series model evaluation.
- [ ] Develop a backtesting framework.
- [ ] Include transaction costs and slippage.
- [ ] Improve exchange execution safety.
- [ ] Integrate sentiment into the decision engine.
- [ ] Add verified dashboard screenshots.
- [ ] Document reproducible model training and evaluation.

## Disclaimer

This project is intended for educational and research purposes in software engineering, machine learning, and financial data analysis.

It does not constitute financial advice or guarantee investment returns.
