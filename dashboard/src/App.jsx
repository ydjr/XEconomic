import React from "react";
import { TrendingUp, BarChart3 } from "lucide-react";
import { getSummary, getLatestExplain, getTimeSeries } from "./api.js";
import TimeSeriesChart from "./components/TimeSeriesChart.jsx";
import ShapBar from "./components/ShapBar.jsx";

function useLang() {
  const [lang, setLang] = React.useState("th");
  const t = React.useCallback((en, th) => (lang === "th" ? th : en), [lang]);
  return { lang, setLang, t };
}

function fmtMonth(yyyy_mm_dd) {
  if (!yyyy_mm_dd) return "-";
  return String(yyyy_mm_dd).slice(0, 7);
}

function trendFromDelta(delta) {
  if (delta == null) return { label: "N/A", tone: "neutral" };
  const d = Number(delta);
  if (d > 0) return { label: "ขาขึ้น", tone: "pos" };
  if (d < 0) return { label: "ขาลง", tone: "neg" };
  return { label: "ทรงตัว", tone: "neutral" };
}

export default function App() {
  const { lang, setLang, t } = useLang();
  const [page, setPage] = React.useState("forecast");

  const [summary, setSummary] = React.useState(null);
  const [explain, setExplain] = React.useState(null);
  const [series, setSeries] = React.useState([]);
  const [err, setErr] = React.useState("");

  React.useEffect(() => {
    let alive = true;

    async function load() {
      setErr("");
      try {
        const [s, e, ts] = await Promise.all([
          getSummary(),
          getLatestExplain(),
          getTimeSeries(500)
        ]);
        if (!alive) return;

        setSummary(s);
        setExplain(e);
        setSeries(ts?.data || []);
      } catch (ex) {
        if (!alive) return;
        setErr(String(ex?.message || ex));
      }
    }

    load();
    return () => {
      alive = false;
    };
  }, []);

  const lastActualValue = summary?.last_actual_value ?? null;
  const deltaPred = summary?.delta_pred ?? null;
  const forecastMonth = summary?.forecast_month ?? null;
  const trend = trendFromDelta(deltaPred);

  return (
    <div>
      <div className="topbar">
        <div className="topbar-inner">
          <div className="brand">
            <TrendingUp size={26} />
            <div>
              <div className="brand-title">
                {t("BOT CCI Forecast", "พยากรณ์ CCI ธปท.")}
              </div>
              <div className="brand-sub">
                {t("Bank of Thailand", "ธนาคารแห่งประเทศไทย")}
              </div>
            </div>
          </div>

          <div className="lang">
            <button
              className={lang === "en" ? "active" : ""}
              onClick={() => setLang("en")}
            >
              EN
            </button>
            <button
              className={lang === "th" ? "active" : ""}
              onClick={() => setLang("th")}
            >
              ไทย
            </button>
          </div>
        </div>

        <div className="tabs">
          <button
            className={`tab ${page === "forecast" ? "active" : ""}`}
            onClick={() => setPage("forecast")}
          >
            <TrendingUp size={16} />
            {t("CCI Forecast", "พยากรณ์ CCI")}
          </button>
          <button
            className={`tab ${page === "news" ? "active" : ""}`}
            onClick={() => setPage("news")}
          >
            <BarChart3 size={16} />
            {t("News Analytics", "วิเคราะห์ข่าว")}
          </button>
        </div>
      </div>

      <div className="container">
        {err ? (
          <div className="card card-pad" style={{ borderColor: "#fecaca" }}>
            <div style={{ fontWeight: 900, color: "#991b1b" }}>
              {t("Error", "ผิดพลาด")}:
            </div>
            <div className="small">{err}</div>
          </div>
        ) : null}

        {page === "forecast" ? (
          <>
            <div className="grid-metrics">
              <div className="card card-pad" style={{ background: "#fff4f4" }}>
                <div className="metric-label">{t("Latest CCI", "ค่า CCI ล่าสุด")}</div>
                <div className="metric-value" style={{ color: "#b91c1c" }}>
                  {lastActualValue != null ? Number(lastActualValue).toFixed(1) : "-"}
                </div>
                <div className="metric-sub">
                  {t("MoM", "MoM")} {deltaPred != null ? `| ${Math.abs(Number(deltaPred)).toFixed(1)}` : "| -"}
                </div>
              </div>

              <div className="card card-pad" style={{ background: "#fff4f4" }}>
                <div className="metric-label">{t("Trend", "แนวโน้ม")}</div>
                <div className="metric-value" style={{ color: trend.tone === "pos" ? "#166534" : "#b91c1c" }}>
                  {trend.label}
                </div>
                <div className="metric-sub">
                  {t("Based on predicted delta", "อิงจากการเปลี่ยนแปลง")}
                </div>
              </div>

              <div className="card card-pad">
                <div className="metric-label">{t("Data as of", "ข้อมูล ณ")}</div>
                <div className="metric-value" style={{ color: "#003d82" }}>
                  {fmtMonth(forecastMonth)}
                </div>
                <div className="metric-sub">{t("Updated monthly", "อัปเดตทุกเดือน")}</div>
              </div>
            </div>

            <div className="row">
              <div>
                <TimeSeriesChart data={series} />
              </div>

              <div className="card">
                <div className="card-pad">
                  <div style={{ fontWeight: 900, color: "#003d82" }}>
                    {t("Evidence (News)", "หลักฐาน (ข่าว)")}
                  </div>
                  <div className="small">
                    {t("Pulled from reasoning stage", "ดึงจากขั้นตอน reasoning")}
                  </div>

                  <div className="evidence-item">
                    <div className="small">{t("No evidence data", "No evidence data")}</div>
                  </div>
                </div>
              </div>
            </div>

            <ShapBar explain={explain} />
          </>
        ) : (
          <div className="card card-pad">
            <div style={{ fontWeight: 900, color: "#003d82" }}>
              {t("News Analytics", "วิเคราะห์ข่าว")}
            </div>
            <div className="small">
              {t("Coming next. For now, focus on forecast + SHAP.", "ไว้ทำต่อ ตอนนี้โฟกัสพยากรณ์ + SHAP ก่อน")}
            </div>
          </div>
        )}

        <div className="footer">
          © 2025 SP40-Aj.Suppawong by Cream Ploy Jean P.Oat P.Pufah
        </div>
      </div>
    </div>
  );
}
