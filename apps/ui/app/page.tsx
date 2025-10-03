"use client";
import { useEffect, useMemo, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import AICard from "./components/AICard";

const API = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8000";
const DEFAULT_SYMBOL = "BTC/USDT";
const DEFAULT_TF = "15m";

type Candle = { ts: number; o: number; h: number; l: number; c: number; v: number; };

export default function Page() {
  const [symbol, setSymbol] = useState(DEFAULT_SYMBOL);
  const [tf, setTf] = useState(DEFAULT_TF);
  const [feat, setFeat] = useState<any>(null);
  const [candles, setCandles] = useState<Candle[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const load = async () => {
    setErr(null);
    try {
      // Convert BTC/USDT to BTCUSDT for API
      const apiSymbol = symbol.replace("/", "");
      const [fRes, cRes] = await Promise.all([
        fetch(`${API}/features/${apiSymbol}?timeframe=${tf}&limit=200`),
        fetch(`${API}/candles/${apiSymbol}?timeframe=${tf}&limit=200`)
      ]);
      if (!fRes.ok) throw new Error("features error");
      if (!cRes.ok) throw new Error("candles error");
      setFeat(await fRes.json());
      setCandles(await cRes.json());
    } catch (e:any) {
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

  const chartData = useMemo(() => candles.map(c => ({
    time: new Date(c.ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    close: c.c
  })), [candles]);

  const lastClose = candles.length ? candles[candles.length - 1].c : null;
  const emaBull = feat && feat.ema20 > feat.ema50;
  const rsiZone = feat ? (feat.rsi14 >= 70 ? "Aşırı Alım" : (feat.rsi14 <= 30 ? "Aşırı Satım" : "Nötr")) : "—";

  return (
    <div>
      <div className="header">
        <div>
          <div className="h1">AI Trading Dashboard</div>
          <div className="sub">Sembol ve zaman dilimi seç, verileri canlı izle.</div>
        </div>
        <div className="row">
          <select className="sel" value={symbol} onChange={e=>setSymbol(e.target.value)}>
            <option>BTC/USDT</option><option>ETH/USDT</option><option>BNB/USDT</option><option>SOL/USDT</option>
          </select>
          <select className="sel" value={tf} onChange={e=>setTf(e.target.value)}>
            <option value="1m">1m</option><option value="5m">5m</option><option value="15m">15m</option>
            <option value="1h">1h</option><option value="4h">4h</option><option value="1d">1d</option>
          </select>
          <button className="btn" onClick={load}>Yenile</button>
        </div>
      </div>

      <div className="row">
        <div className="card" style={{minWidth:280, flex:1}}>
          <div style={{fontWeight:600, marginBottom:8}}>Özet</div>
          {feat ? (
            <>
              <ul className="kv">
                <li>Fiyat: <b className="stat">{feat.price?.toLocaleString?.() ?? feat.price}</b></li>
                <li>EMA20: <b className="stat">{feat.ema20?.toLocaleString?.() ?? feat.ema20}</b> | EMA50: <b className="stat">{feat.ema50?.toLocaleString?.() ?? feat.ema50}</b></li>
                <li>RSI14: <b className="stat">{feat.rsi14?.toFixed?.(2) ?? feat.rsi14}</b></li>
                <li>Sentiment: <b>{feat.sent_score}</b></li>
                <li>Son Kapanış ({tf}): <b className="stat">{lastClose ? lastClose.toLocaleString() : "—"}</b></li>
                <li>Trend: <span className={`badge ${emaBull ? "up" : ""}`}>{emaBull ? "Yukarı (EMA20>EMA50)" : "Aşağı (EMA20<EMA50)"}</span></li>
                <li>RSI Bölgesi: <span className="badge">{rsiZone}</span></li>
              </ul>
              {feat.sent_score === 0 && (
                <div className="footer">Not: CRYPTOPANIC_TOKEN ayarlı değilse sentiment 0 döner.</div>
              )}
            </>
          ) : <div>Veri yok…</div>}
        </div>

        <div className="card" style={{minWidth:260}}>
          <AICard symbol={symbol} tf={tf} />
        </div>
      </div>

      <div className="card" style={{marginTop:16}}>
        {loading ? <div>Yükleniyor…</div> : (
          <div style={{ width:"100%", height: 420 }}>
            <ResponsiveContainer>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis domain={["dataMin", "dataMax"]} tickFormatter={(v)=>v.toLocaleString()} />
                <Tooltip />
                <Line type="monotone" dataKey="close" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}