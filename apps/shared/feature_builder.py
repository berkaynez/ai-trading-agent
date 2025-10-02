import numpy as np
import pandas as pd

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    # df: columns = ts,o,h,l,c,v  (ts ms)
    out = df.copy()
    out["ret_1"] = out["c"].pct_change(1)
    out["ret_3"] = out["c"].pct_change(3)
    out["ret_6"] = out["c"].pct_change(6)
    out["vol_10"] = out["c"].pct_change().rolling(10).std()
    # EMA/RSI
    import pandas_ta as ta
    out["ema20"] = ta.ema(out["c"], length=20)
    out["ema50"] = ta.ema(out["c"], length=50)
    out["rsi14"] = ta.rsi(out["c"], length=14)
    out["ema_spread"] = out["ema20"] - out["ema50"]
    # ileriye dönük getiri (label için)
    out["fwd_ret_3"] = out["c"].shift(-3).pct_change(3)  # ~3 bar sonrası göreceli
    out = out.dropna()
    return out

def make_label(df: pd.DataFrame, thr=0.002):
    # fwd_ret_3 > +0.2% ise 1 (long), < -0.2% ise -1 (exit/short), aksi 0 (hold)
    y = (df["fwd_ret_3"].values)
    lab = np.zeros_like(y, dtype=int)
    lab[y >  thr] = 1
    lab[y < -thr] = -1
    return lab
