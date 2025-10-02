"use client";
import { useEffect, useState } from "react";
const API = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8000";

export default function AICard({ symbol="BTC/USDT", tf="15m" }:{symbol?:string; tf?:string}) {
  const [data, setData] = useState<any>(null);
  const load = async () => {
    const r = await fetch(`${API}/ai/predict?symbol=${encodeURIComponent(symbol)}&timeframe=${tf}`);
    setData(await r.json());
  };
  useEffect(()=>{ load(); const id=setInterval(load,30000); return ()=>clearInterval(id); },[symbol, tf]);
  return (
    <div style={{ border:"1px solid #eee", borderRadius:8, padding:12, minWidth:260 }}>
      <div style={{ fontWeight:600, marginBottom:6 }}>AI Predict</div>
      {data ? (
        <ul style={{ margin:0, paddingLeft:16, lineHeight:1.8 }}>
          <li>p_long: <b>{data.p_long}</b></li>
          <li>p_hold: <b>{data.p_hold}</b></li>
          <li>p_exit: <b>{data.p_exit}</b></li>
          <li>sent: <b>{data.sent_score}</b></li>
        </ul>
      ): <div>Loading…</div>}
    </div>
  );
}
