import os, sys, ccxt, pandas as pd, numpy as np
from joblib import dump
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Add shared module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from feature_builder import add_features, make_label

load_dotenv()

SYMBOL = os.getenv("TRAIN_SYMBOL", "BTC/USDT")
TF = os.getenv("TRAIN_TF", "15m")
LOOKBACK = int(os.getenv("TRAIN_LOOKBACK", "1500"))  # ~1500 bar
MODEL_PATH = os.getenv("MODEL_PATH", "models/ml/model.pkl")

ex = ccxt.binance({"enableRateLimit": True})
if (os.getenv("BINANCE_TESTNET") or "").lower() == "true":
    ex.set_sandbox_mode(True)

def fetch_ohlcv(symbol, tf, limit):
    o = ex.fetch_ohlcv(symbol, timeframe=tf, limit=limit)
    df = pd.DataFrame(o, columns=["ts","o","h","l","c","v"])
    return df

def main():
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    df = fetch_ohlcv(SYMBOL, TF, LOOKBACK)
    dfF = add_features(df)
    y = make_label(dfF, thr=0.002)
    X = dfF[["ret_1","ret_3","ret_6","vol_10","ema20","ema50","ema_spread","rsi14"]].values

    # train/test split (zaman sırasını koru)
    split = int(len(X)*0.8)
    X_train, y_train = X[:split], y[:split]
    # basit model: RandomForest
    from sklearn.ensemble import RandomForestClassifier
    clf = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)
    dump(clf, MODEL_PATH)
    print("saved:", MODEL_PATH, "train_samples:", len(X_train))

if __name__ == "__main__":
    main()
