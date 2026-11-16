AI Trading Agent

An experimental cryptocurrency trading research platform combining technical analysis, machine learning, news sentiment, and a web dashboard.

Built with Python, FastAPI, Next.js, TypeScript, and scikit-learn.

Research prototype — not a production trading system or financial advice. The project has not demonstrated profitable trading performance. Real order execution is possible through an explicitly enabled gateway configuration and must be treated with caution.

Overview

AI Trading Agent explores how multiple market signals can be combined to support trading decisions.

The system includes:

* A Python agent generating technical trading signals from EMA and RSI indicators.
* A Random Forest classifier trained on historical OHLCV-derived features.
* A FastAPI gateway providing market data, model predictions, sentiment scores, and order-related endpoints.
* A Next.js dashboard displaying price charts, technical indicators, and model output.
* A configurable decision process combining technical and machine-learning signals.

Architecture

Binance Market Data
        |
        +--> Technical Indicators (EMA / RSI)
        |
        +--> Feature Engineering --> Random Forest Model
        |
        +--> News Headlines --> Sentiment Scoring
                                  |
                             FastAPI Gateway
                                  |
                   +--------------+-------------+
                   |                            |
              Python Agent                Next.js Dashboard
                   |
             Decision Logging

Key Features

Technical Analysis

Calculates EMA20, EMA50, and RSI14 to identify potential directional signals.

Machine Learning

Uses a Random Forest classifier with historical return, volatility, moving-average, and RSI features to explore long, exit, and hold classifications.

News Sentiment

Processes cryptocurrency news headlines using keyword-based sentiment scoring, with a configured provider or RSS fallback.

Trading Agent

Combines technical and machine-learning scores to generate decisions. The current agent logs decisions rather than directly submitting orders.

Web Dashboard

Displays market prices, candlestick-derived price history, technical indicators, sentiment, and AI prediction information.

Risk Controls

The gateway includes configurable position-notional and daily drawdown checks. These are prototype controls and should not be relied upon as production-grade safeguards.

Technology Stack

Layer	Technologies
Trading agent	Python, pandas, pandas-ta, CCXT
Machine learning	scikit-learn, NumPy, joblib
Backend API	FastAPI, Pydantic
Frontend	Next.js, React, TypeScript, Recharts
Data sources	Binance market data, cryptocurrency news feeds

Repository Structure

apps/
  agent/
    ema_rsi_agent.py
    train_ml.py
  gateway-api/
    main.py
    requirements.txt
    .env.example
  shared/
    feature_builder.py
  ui/
    app/
models/
  ml/
    model.pkl
run_agent.sh

Development Notes

The gateway’s example environment configuration is located at apps/gateway-api/.env.example.

The backend has a local startup script, and the frontend has standard Next.js development commands.

Before running the system, review the gateway configuration, dependencies, exchange credentials, and execution settings.

Do not enable live order execution with real exchange credentials without independently validating the implementation and its safeguards.

Current Limitations

* No documented out-of-sample performance benchmark or trading profitability validation.
* No verified production-ready backtesting and execution framework.
* The news sentiment approach is keyword-based, not a trained language model.
* The agent’s current decision blend uses technical and ML scores; sentiment is retrieved but is not included in the final weighted decision.
* Risk controls and model behavior require additional validation.
* The repository includes a serialized model artifact; load such files only from trusted sources.

Roadmap

* Add reproducible model evaluation and time-series validation.
* Implement a backtesting framework with fees and slippage.
* Add automated tests and CI checks.
* Improve configuration validation and execution safety.
* Document reproducible installation and startup procedures.
* Add dashboard screenshots and example results.

Disclaimer

This repository is intended for software engineering, financial data analysis, and machine-learning experimentation. It does not provide investment advice or guarantee financial returns.
