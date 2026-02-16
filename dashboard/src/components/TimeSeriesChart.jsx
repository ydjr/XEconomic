import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceArea
} from "recharts";

export default function TimeSeriesChart({ data, title = "CCI – ประเทศไทย" }) {
  const safe = Array.isArray(data) ? data : [];

  // Shade forecast region after last actual point
  const lastActual = [...safe].reverse().find((d) => d && d.actual != null);
  const shadeFrom = lastActual?.date || null;
  const shadeTo = safe.length ? safe[safe.length - 1].date : null;

  function CustomTooltip({ active, payload, label }) {
    if (!active || !payload || payload.length === 0) return null;

    const actualItem = payload.find((p) => p.dataKey === "actual");
    const predItem = payload.find((p) => p.dataKey === "pred");

    const actualVal = actualItem?.value;
    const predVal = predItem?.value;

    return (
      <div
        style={{
          background: "white",
          border: "1px solid #e5e7eb",
          padding: 10,
          borderRadius: 10
        }}
      >
        <div style={{ fontWeight: 800, marginBottom: 6 }}>{label}</div>

        <div style={{ fontSize: 13, lineHeight: 1.6 }}>
          <div>
            Actual : {actualVal != null ? Number(actualVal).toFixed(1) : "-"}
          </div>
          <div>
            Pred : {predVal != null ? Number(predVal).toFixed(1) : "-"}
          </div>
        </div>
      </div>
    );
  }


  return (
    <div className="card">
      <div className="card-pad">
        <div style={{ fontWeight: 900, color: "#003d82" }}>{title}</div>
        <div className="small">จริง vs พยากรณ์</div>
      </div>

      <div className="card-pad chart-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={safe}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />

            {/* Actual */}
            <Line
              type="monotone"
              dataKey="actual"
              name="Actual"
              strokeWidth={2}
              dot={false}
              connectNulls={false}
            />

            {/* Pred (make dot visible for 1-step forecast) */}
            <Line
              type="monotone"
              dataKey="pred"
              name="Pred"
              strokeWidth={2}
              dot={{ r: 3 }}
              connectNulls={false}
            />

            {shadeFrom && shadeTo && shadeFrom !== shadeTo ? (
              <ReferenceArea x1={shadeFrom} x2={shadeTo} fillOpacity={0.08} />
            ) : null}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
