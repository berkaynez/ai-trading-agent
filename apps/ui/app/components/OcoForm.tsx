"use client";
import { useState } from "react";
const API = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8000";
export default function OcoForm({ symbol="BTC/USDT" }: { symbol?: string }) {
  const [side, setSide] = useState<"buy"|"sell">("buy");
  const [qty, setQty] = useState("0.001");
  const [tp, setTp] = useState("0.01");
  const [sl, setSl] = useState("0.005");
  const [res, setRes] = useState<any>(null);
  const send = async () => {
    const r = await fetch(`${API}/order/oco`, {
      method: "POST",
      headers: { "Content-Type":"application/json" },
      body: JSON.stringify({
        symbol, side, qty: parseFloat(qty),
        take_profit_pct: parseFloat(tp),
        stop_loss_pct: parseFloat(sl)
      })
    });
    setRes(await r.json());
  }
  return (
    <div style={{ border: "1px solid #eee", borderRadius: 8, padding: 12 }}>
      <div style={{ fontWeight: 600, marginBottom: 8 }}>OCO Simulator (DRY-RUN)</div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <label>Side:
          <select value={side} onChange={e=>setSide(e.target.value as any)} style={{ marginLeft: 6 }}>
            <option value="buy">buy</option>
            <option value="sell">sell</option>
          </select>
        </label>
        <label>Qty:
          <input value={qty} onChange={e=>setQty(e.target.value)} style={{ marginLeft: 6, width: 100 }} />
        </label>
        <label>TP%:
          <input value={tp} onChange={e=>setTp(e.target.value)} style={{ marginLeft: 6, width: 80 }} />
        </label>
        <label>SL%:
          <input value={sl} onChange={e=>setSl(e.target.value)} style={{ marginLeft: 6, width: 80 }} />
        </label>
        <button onClick={send} style={{ padding: "6px 10px" }}>Simulate</button>
      </div>
      {res && (
        <div style={{ marginTop: 10, fontSize: 14 }}>
          <div>Entry: <b>{res.entry_price ?? "—"}</b></div>
          <div>TP: <b>{res.take_profit_price ?? "—"}</b> | SL: <b>{res.stop_loss_price ?? "—"}</b></div>
          <div>Status: {res.status}</div>
        </div>
      )}
    </div>
  );
}
