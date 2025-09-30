"use client";
import { useEffect, useState } from "react";
const API = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8000";
export default function SentimentCard({ symbol = "BTC/USDT" }: { symbol?: string }) {
  const [data, setData] = useState<any>(null);
  const load = async () => {
    const r = await fetch(`${API}/sentiment/${encodeURIComponent(symbol)}`);
    setData(await r.json());
  };
  useEffect(() => { load(); const id = setInterval(load, 45000); return () => clearInterval(id); }, []);
  return (
    <div style={{ border: "1px solid #eee", borderRadius: 8, padding: 12, minWidth: 280 }}>
      <div style={{ fontWeight: 600 }}>Sentiment — {symbol}</div>
      <div style={{ marginTop: 6 }}>Score: <b>{data?.sent_score ?? "—"}</b></div>
      <ul style={{ marginTop: 6, paddingLeft: 16 }}>
        {(data?.items || []).map((it: any, i: number) => (
          <li key={i} title={it.title}>{(it.title || "").slice(0, 80)}{(it.title||"").length>80?"…":""}</li>
        ))}
      </ul>
    </div>
  );
}
