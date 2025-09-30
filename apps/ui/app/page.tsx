"use client";
import { useEffect, useMemo, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const API = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8000";
const SYMBOL = "BTC/USDT";
const TF = "15m";

type Candle = { ts: number; o: number; h: number; l: number; c: number; v: number; };

export default function Page() {
  const [feat, setFeat] = useState<any>(null);
  const [candles, setCandles] = useState<Candle[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const load = async () => {
    setErr(null);
    try {
      const [fRes, cRes] = await Promise.all([
        fetch(`${API}/features/${encodeURIComponent(SYMBOL)}`),
        fetch(`${API}/candles/${encodeURIComponent(SYMBOL)}?timeframe=${TF}&limit=200`)
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
  }, []);

  const chartData = useMemo(() => {
    return candles.map(c => ({
      time: new Date(c.ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      close: c.c
    }));
  }, [candles]);

  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 700 }}>AI Trading Dashboard</h1>
      <div style={{ marginTop: 6, color: "#555" }}>
        Sembol: <b>{SYMBOL}</b> — TF: <b>{TF}</b>
      </div>

      <div style={{ marginTop: 12, display: "flex", gap: 12, flexWrap: "wrap" }}>
        <button onClick={load} style={{ padding: "8px 12px", border: "1px solid #ddd", borderRadius: 8 }}>
          Yenile
        </button>
        {err && <span style={{ color: "crimson" }}>Hata: {err}</span>}
      </div>

      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 16 }}>
        <div style={{ border: "1px solid #eee", borderRadius: 8, padding: 12, minWidth: 260 }}>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Özet</div>
          {feat ? (
            <ul style={{ margin: 0, paddingLeft: 16, lineHeight: 1.8 }}>
              <li>Fiyat: <b>{feat.price}</b></li>
              <li>EMA20: <b>{feat.ema20}</b> | EMA50: <b>{feat.ema50}</b></li>
              <li>RSI14: <b>{feat.rsi14}</b></li>
              <li>Sentiment: <b>{feat.sent_score}</b></li>
            </ul>
          ) : (
            <div>Veri yok…</div>
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
              <YAxis domain={["dataMin", "dataMax"]} />
              <Tooltip />
              <Line type="monotone" dataKey="close" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}