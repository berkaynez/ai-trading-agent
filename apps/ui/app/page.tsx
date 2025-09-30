"use client";
import { useEffect, useMemo, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import SentimentCard from "./components/SentimentCard";
import OcoForm from "./components/OcoForm";

const API = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8000";
const SYMBOL = "BTC/USDT";
const TF = "15m";

type Candle = { ts: number; o: number; h: number; l: number; c: number; v: number; };

export default function Page() {
  const [candles, setCandles] = useState<Candle[]>([]);
  const [price, setPrice] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [ocoResult, setOcoResult] = useState<any>(null);
  const [ocoLoading, setOcoLoading] = useState(false);

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

  const simulateOco = async (formData: any) => {
    setOcoLoading(true);
    try {
      const response = await fetch(`${API}/order/oco`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const result = await response.json();
      setOcoResult(result);
    } catch (e) {
      console.error('OCO simulation failed:', e);
    } finally {
      setOcoLoading(false);
    }
  };

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

      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 16 }}>
        <SentimentCard symbol="BTC/USDT" />
        <OcoForm symbol="BTC/USDT" />
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

      <div style={{ marginTop: 24, padding: 16, border: "1px solid #ddd", borderRadius: 8 }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>OCO Simulation</h2>
        <OcoForm onSubmit={simulateOco} loading={ocoLoading} />
        {ocoResult && (
          <div style={{ marginTop: 16, padding: 12, backgroundColor: "#f5f5f5", borderRadius: 6 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>Simulation Result:</h3>
            <div><strong>Entry:</strong> {ocoResult.entry_price}</div>
            <div><strong>Take Profit:</strong> {ocoResult.take_profit_price} ({ocoResult.params.tp_pct * 100}%)</div>
            <div><strong>Stop Loss:</strong> {ocoResult.stop_loss_price} ({ocoResult.params.sl_pct * 100}%)</div>
            <div><strong>Quantity:</strong> {ocoResult.qty}</div>
          </div>
        )}
      </div>
    </div>
  );
}

function OcoForm({ onSubmit, loading }: { onSubmit: (data: any) => void, loading: boolean }) {
  const [formData, setFormData] = useState({
    symbol: "BTC/USDT",
    side: "buy",
    qty: 0.001,
    take_profit_pct: 0.01,
    stop_loss_pct: 0.005
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "end" }}>
      <div>
        <label style={{ display: "block", fontSize: 14, marginBottom: 4 }}>Symbol:</label>
        <input
          type="text"
          value={formData.symbol}
          onChange={(e) => setFormData({...formData, symbol: e.target.value})}
          style={{ padding: "6px 8px", border: "1px solid #ccc", borderRadius: 4 }}
        />
      </div>
      <div>
        <label style={{ display: "block", fontSize: 14, marginBottom: 4 }}>Side:</label>
        <select
          value={formData.side}
          onChange={(e) => setFormData({...formData, side: e.target.value})}
          style={{ padding: "6px 8px", border: "1px solid #ccc", borderRadius: 4 }}
        >
          <option value="buy">Buy</option>
          <option value="sell">Sell</option>
        </select>
      </div>
      <div>
        <label style={{ display: "block", fontSize: 14, marginBottom: 4 }}>Quantity:</label>
        <input
          type="number"
          step="0.001"
          value={formData.qty}
          onChange={(e) => setFormData({...formData, qty: parseFloat(e.target.value)})}
          style={{ padding: "6px 8px", border: "1px solid #ccc", borderRadius: 4, width: 80 }}
        />
      </div>
      <div>
        <label style={{ display: "block", fontSize: 14, marginBottom: 4 }}>TP %:</label>
        <input
          type="number"
          step="0.001"
          value={formData.take_profit_pct}
          onChange={(e) => setFormData({...formData, take_profit_pct: parseFloat(e.target.value)})}
          style={{ padding: "6px 8px", border: "1px solid #ccc", borderRadius: 4, width: 80 }}
        />
      </div>
      <div>
        <label style={{ display: "block", fontSize: 14, marginBottom: 4 }}>SL %:</label>
        <input
          type="number"
          step="0.001"
          value={formData.stop_loss_pct}
          onChange={(e) => setFormData({...formData, stop_loss_pct: parseFloat(e.target.value)})}
          style={{ padding: "6px 8px", border: "1px solid #ccc", borderRadius: 4, width: 80 }}
        />
      </div>
      <button
        type="submit"
        disabled={loading}
        style={{
          padding: "8px 16px",
          backgroundColor: loading ? "#ccc" : "#007bff",
          color: "white",
          border: "none",
          borderRadius: 4,
          cursor: loading ? "not-allowed" : "pointer"
        }}
      >
        {loading ? "Simulating..." : "Simulate OCO"}
      </button>
    </form>
  );
}
