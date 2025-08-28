import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function StockCard({ symbol }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    fetch(`http://localhost:8000/api/stock/${symbol}`)
      .then(r => r.json())
      .then(setData)
      .catch(setErr);
  }, [symbol]);

  if (err) return <div>Errore: {String(err)}</div>;
  if (!data) return <div>Caricamento…</div>;

  const chgSign = data.changePct > 0 ? "+" : "";
  return (
    <div style={{border:"1px solid #eee", borderRadius:16, padding:16}}>
      <div style={{display:"flex", justifyContent:"space-between", alignItems:"baseline"}}>
        <h2 style={{margin:0}}>{data.name || data.symbol} ({data.symbol})</h2>
        <small>{data.currency || ""}</small>
      </div>

      <div style={{display:"flex", gap:24, marginTop:12, flexWrap:"wrap"}}>
        <div>
          <div style={{fontSize:28, fontWeight:700}}>
            {data.price?.toFixed(2)}
          </div>
          <div style={{fontSize:14, opacity:.8}}>
            {chgSign}{data.change?.toFixed(2)} ({chgSign}{data.changePct?.toFixed(2)}%) · {data.asOf}
          </div>
        </div>
        <div style={{display:"grid", gridTemplateColumns:"auto auto", gap:"6px 16px"}}>
          <span>Settore</span><strong>{data.sector || "-"}</strong>
          <span>Cap. Mercato</span><strong>{Number(data.marketCap||0).toLocaleString()}</strong>
          <span>P/E</span><strong>{data.pe || "-"}</strong>
          <span>Beta</span><strong>{data.beta || "-"}</strong>
          <span>Div. Yield</span><strong>{data.dividendYield || "-"}</strong>
        </div>
      </div>

      <div style={{height:260, marginTop:16}}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data.timeseries}>
            <XAxis dataKey="date" hide />
            <YAxis domain={["auto","auto"]} />
            <Tooltip />
            <Line type="monotone" dataKey="close" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
