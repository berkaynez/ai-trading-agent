"use client";
import { useEffect, useState } from "react";
const API = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8000";

type Decision = {
  ts: number; symbol: string; action: string; score: number; price: number; note?: string;
};
export default function AgentPage() {
  const [items, setItems] = useState<Decision[]>([]);
  const load = async () => {
    const r = await fetch(`${API}/agent/decisions?limit=50`);
    const j = await r.json();
    setItems(j.items || []);
  };
  useEffect(() => { load(); const id = setInterval(load, 15000); return () => clearInterval(id); }, []);
  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 600 }}>Agent Decisions</h1>
      <div style={{ marginTop: 12 }}>
        {items.map((d, i) => (
          <div key={i} style={{ padding: 8, border: "1px solid #eee", borderRadius: 8, marginBottom: 8 }}>
            <div><b>{d.symbol}</b> — {d.action.toUpperCase()} (score: {d.score.toFixed(2)})</div>
            <div>price: {d.price.toFixed(2)} | {new Date(d.ts*1000).toLocaleString()}</div>
            {d.note ? <div style={{ color: "#555" }}>{d.note}</div> : null}
          </div>
        ))}
      </div>
    </div>
  );
}
