"use client";
import { useEffect, useMemo, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";

const API = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8000";
const SYMBOL = "BTC/USDT";
const TF = "15m";

type Candle = { ts: number; o: number; h: number; l: number; c: number; v: number; };

export default function Page() {
  const [candles, setCandles] = useState<Candle[]>([]);
  const [price, setPrice] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const [tickRes, canRes] = await Promise.all([
        fetch(`${API}/ticker/${encodeURIComponent(SYMBOL)}`),
        fetch(`${API}/candles/${encodeURIComponent(SYMBOL)}?timeframe=${TF}&limit=200`)
      ]);
      const tick = await tickRes.json();
      const raws: Candle[] = await canRes.json();
      setPrice(tick?.last ?? tick?.close ?? null);
      setCandles(
        raws.map(r => ({
          ...r,
          // recharts datayı x olarak string ister; ts -> hh:mm
          // 15m için kısa format:
          ts: r.ts
        }))
      );
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 30_000);
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
      <h1 style={{ fontSize: 22, fontWeight: 600 }}>AI Trading Dashboard</h1>
      <p style={{ marginTop: 8, color: "#444" }}>
        Sembol: <b>{SYMBOL}</b> — Zaman Dilimi: <b>{TF}</b>
      </p>

      <div style={{
        marginTop: 16, display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap"
      }}>
        <div style={{ padding: "8px 12px", border: "1px solid #eee", borderRadius: 8 }}>
          Son Fiyat: <b>{price ? Number(price).toFixed(2) : "—"}</b>
        </div>
        <button onClick={load} style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #ddd" }}>
          Yenile
        </button>
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
