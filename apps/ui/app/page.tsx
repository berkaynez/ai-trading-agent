"use client";
import { useEffect, useMemo, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const API = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8000";
const DEFAULT_SYMBOL = "BTCUSDT";  // Binance format: no slash
const DEFAULT_SYMBOL_DISPLAY = "BTC/USDT";  // Display format with slash
const DEFAULT_TF = "15m";

type Candle = { ts: number; o: number; h: number; l: number; c: number; v: number; };

export default function Page() {
  const [feat, setFeat] = useState<any>(null);
  const [candles, setCandles] = useState<Candle[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [symbol, setSymbol] = useState(DEFAULT_SYMBOL);
  const [tf, setTf] = useState(DEFAULT_TF);

  const load = async () => {
    setErr(null);
    try {
      const [fRes, cRes] = await Promise.all([
        fetch(`${API}/features/${encodeURIComponent(symbol)}`),
        fetch(`${API}/candles/${encodeURIComponent(symbol)}?timeframe=${tf}&limit=200`)
      ]);
      if (!fRes.ok) throw new Error("features error");
      if (!cRes.ok) throw new Error("candles error");
      setFeat(await fRes.json());
      setCandles(await cRes.json());
    } catch (e: any) {
      setErr(e?.message || "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, [symbol, tf]);

  const chartData = useMemo(() => {
    return candles.map(c => ({
      time: new Date(c.ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      close: c.c
    }));
  }, [candles]);

  // Son kapanış fiyatını hesapla
  const lastClose = candles.length ? candles[candles.length - 1].c : null;
  
  // Trend ve momentum hesaplamaları
  const emaBull = feat && feat.ema20 > feat.ema50;
  const rsiZone = feat ? (feat.rsi14 >= 70 ? "Aşırı Alım" : (feat.rsi14 <= 30 ? "Aşırı Satım" : "Nötr")) : "—";

  return (
    <div>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>AI Trading Dashboard</h1>
        <div style={{ marginTop: 6, color: "#555" }}>
          Sembol: <b>{symbol.replace('USDT', '/USDT')}</b> — TF: <b>{tf}</b>
        </div>

      <div style={{ marginTop: 12, display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
        <button onClick={load} style={{ padding: "8px 12px", border: "1px solid #ddd", borderRadius: 8 }}>
          Yenile
        </button>
        <select value={symbol} onChange={(e)=>setSymbol(e.target.value)} style={{ padding: 6, borderRadius: 8, border: "1px solid #ddd" }}>
          <option value="BTCUSDT">BTC/USDT</option>
          <option value="ETHUSDT">ETH/USDT</option>
          <option value="BNBUSDT">BNB/USDT</option>
          <option value="SOLUSDT">SOL/USDT</option>
        </select>
        <select value={tf} onChange={(e)=>setTf(e.target.value)} style={{ padding: 6, borderRadius: 8, border: "1px solid #ddd" }}>
          <option value="1m">1m</option>
          <option value="5m">5m</option>
          <option value="15m">15m</option>
          <option value="1h">1h</option>
          <option value="4h">4h</option>
          <option value="1d">1d</option>
        </select>
        {err && <span style={{ color: "crimson" }}>Hata: {err}</span>}
      </div>

      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 16 }}>
        <div style={{ border: "1px solid #eee", borderRadius: 8, padding: 12, minWidth: 260 }}>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Özet</div>
          {feat ? (
            <ul style={{ margin: 0, paddingLeft: 16, lineHeight: 1.8 }}>
              <li>Fiyat: <b>{feat.price?.toLocaleString?.() ?? feat.price}</b></li>
              <li>EMA20: <b>{feat.ema20?.toLocaleString?.() ?? feat.ema20}</b> | EMA50: <b>{feat.ema50?.toLocaleString?.() ?? feat.ema50}</b></li>
              <li>RSI14: <b>{feat.rsi14?.toFixed?.(2) ?? feat.rsi14}</b></li>
              <li>Sentiment: <b>{feat.sent_score}</b></li>
              <li>Son Kapanış ({tf}): <b>{lastClose ? lastClose.toLocaleString() : "—"}</b></li>
              <li>Trend: <span style={{
                padding: "2px 8px", borderRadius: 12,
                background: emaBull ? "#e6ffed" : "#ffecec",
                border: `1px solid ${emaBull ? "#a6f3b6" : "#ffb3b3"}`,
                fontWeight: 600
              }}>{emaBull ? "Yukarı (EMA20>EMA50)" : "Aşağı (EMA20<EMA50)"}</span></li>
              <li>RSI Bölgesi: <span style={{
                padding: "2px 8px", borderRadius: 12,
                background: rsiZone === "Aşırı Alım" ? "#fff7e6" : rsiZone === "Aşırı Satım" ? "#e6f7ff" : "#f5f5f5",
                border: "1px solid #eee", fontWeight: 600
              }}>{rsiZone}</span></li>
            </ul>
          ) : (
            <div>Veri yok…</div>
          )}
          {feat && feat.sent_score === 0 && (
            <div style={{ marginTop: 6, fontSize: 12, color: "#666" }}>
              Not: CRYPTOPANIC_TOKEN ayarlı değilse sentiment 0 döner.
            </div>
          )}
        </div>
      </div>

      <div style={{ width: "100%", height: 380, marginTop: 16 }}>
        {loading ? (
          <div>Yükleniyor…</div>
        ) : (
          <ResponsiveContainer>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis domain={["dataMin", "dataMax"]} tickFormatter={(v) => v.toLocaleString()} />
              <Tooltip formatter={(value) => [value.toLocaleString(), "Fiyat"]} />
              <Line type="monotone" dataKey="close" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}