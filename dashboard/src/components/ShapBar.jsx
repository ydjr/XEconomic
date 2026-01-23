import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip
} from "recharts";

function formatFeatureName(s) {
  if (!s) return "";
  return String(s);
}

export default function ShapBar({ explain }) {
  const items = explain?.explanations || [];
  const data = items.map((x) => ({
    feature: formatFeatureName(x.feature),
    shap_value: Number(x.shap_value ?? 0)
  }));

  // sort by abs shap desc
  data.sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value));

  return (
    <div className="card" style={{ marginTop: 14 }}>
      <div className="card-pad">
        <div style={{ fontWeight: 900, color: "#003d82" }}>SHAP (ล่าสุด)</div>
        <div className="small">ตัวแปรสำคัญที่ขับเคลื่อนผลพยากรณ์</div>
      </div>

      <div className="card-pad" style={{ height: 360 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 30 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis
              type="category"
              dataKey="feature"
              width={160}
              tick={{ fontSize: 11 }}
            />
            <Tooltip />
            <Bar dataKey="shap_value" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
