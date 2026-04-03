import React from "react"
import { TrendingUp, Activity, BarChart3 } from "lucide-react"
import wordcloudImg from "./assets/cci_impact_wordcloud.png"
import "./index.css"
import { getSummary, getTimeSeries, getNews, getShap, getAllExplain } from "./api.js"
import { getAgencyVolumeLastNMonths } from "./newsSupabaseApi"

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ReTooltip,
  Legend,
  ResponsiveContainer,
  ReferenceArea,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  ComposedChart,
  Area,
  ReferenceLine,
  Brush,
} from "recharts"

const THEME = {
  navy: "#163A70",
  blue: "#2F6FED",
  blueSoft: "#F4F7FC",
  success: "#0F9F6E",
  danger: "#D64545",
  gray: "#6B7280",
  border: "#E6ECF5",
  cardBg: "#FFFFFF",
}

const ASPECTS_TO_RUN = [
  "การเมือง",
  "ภัยพิบัติ/โรคระบาด",
  "มาตรการของรัฐ",
  "ราคาน้ำมันเชื้อเพลิง",
  "ราคาสินค้าเกษตร",
  "สังคม/ความมั่นคง",
  "เศรษฐกิจโลก",
  "เศรษฐกิจไทย",
]

const CHART_COLORS = [
  "#4e79a7",
  "#f28e2b",
  "#e15759",
  "#76b7b2",
  "#59a14f",
  "#edc948",
  "#b07aa1",
  "#ff9da7",
  "#9c755f",
  "#bab0ac",
]

const THAIRATH_COLOR = "#01B400"

const tagTH = {
  economics: "เศรษฐกิจ",
  tech_innovation: "นวัตกรรมเทคโนโลยี",
  investment: "การลงทุน",
  policy: "นโยบาย",
  personal_finance: "การเงินส่วนบุคคล",
  business_marketing: "ธุรกิจและการตลาด",
}

const tagColors = {
  economics: "#059669",
  tech_innovation: "#3b82f6",
  investment: "#f59e0b",
  policy: "#8b5cf6",
  personal_finance: "#ec4899",
  business_marketing: "#14b8a6",
}

// ── Skeleton shimmer component ──
const Skeleton = ({ className = "", style = {} }) => (
  <div
    className={`rounded-lg ${className}`}
    style={{
      background: "linear-gradient(90deg, #E6ECF5 25%, #F4F7FC 50%, #E6ECF5 75%)",
      backgroundSize: "200% 100%",
      animation: "shimmer 1.4s ease-in-out infinite",
      ...style,
    }}
  />
)

// ── Global keyframes injected once ──
if (typeof document !== "undefined" && !document.getElementById("xecon-styles")) {
  const style = document.createElement("style")
  style.id = "xecon-styles"
  style.textContent = `
    @keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
    @keyframes soft-pulse { 0%,100%{opacity:1} 50%{opacity:0.6} }
    @keyframes fade-in { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
    .xecon-fade-in { animation: fade-in 0.35s ease both; }
    .xecon-pulse { animation: soft-pulse 2.4s ease-in-out infinite; }
    .xecon-aspect-btn:hover { background: #EEF3FB !important; transform: translateX(2px); }
    .xecon-aspect-btn { transition: background 0.15s, transform 0.15s, box-shadow 0.15s; cursor: pointer; }
    .xecon-aspect-btn:hover .xecon-arrow { opacity: 1 !important; transform: translateX(2px); }
    .xecon-arrow { transition: opacity 0.15s, transform 0.15s; }
    .xecon-news-row:hover { background: #F4F7FC; }
    .xecon-news-row { transition: background 0.12s; }
    .xecon-pill-fade::after {
      content: '';
      position: absolute;
      right: 0; top: 0; bottom: 0;
      width: 40px;
      background: linear-gradient(to right, transparent, #1a4280);
      pointer-events: none;
    }
  `
  document.head.appendChild(style)
}

// ── Empty state component ──
const EmptyState = ({ icon, title, description, action }) => (
  <div className="flex flex-col items-center justify-center py-14 text-center xecon-fade-in">
    <div
      className="flex items-center justify-center rounded-2xl mb-4"
      style={{ width: 56, height: 56, background: "#F4F7FC", color: THEME.blue, fontSize: 26 }}
    >
      {icon}
    </div>
    <div className="text-base font-semibold text-gray-700 mb-1">{title}</div>
    {description && <div className="text-sm text-gray-400 max-w-xs">{description}</div>}
    {action && <div className="mt-4">{action}</div>}
  </div>
)

const Badge = ({ children, variant = "secondary", className = "", style = {} }) => {
  const styles = {
    secondary: "bg-gray-100 text-gray-700",
    positive: "bg-green-100 text-green-700",
    negative: "bg-red-100 text-red-700",
    outline: "border border-gray-300 text-gray-600",
    navy: "text-white",
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${styles[variant] || styles.secondary
        } ${className}`}
      style={variant === "navy" ? { backgroundColor: THEME.navy, ...style } : style}
    >
      {children}
    </span>
  )
}

const Card = ({ children, className = "" }) => (
  <div
    className={`bg-white rounded-2xl border ${className}`}
    style={{
      borderColor: THEME.border,
      boxShadow: "0 10px 30px rgba(22,58,112,0.06)",
    }}
  >
    {children}
  </div>
)

const CardHeader = ({ children, className = "" }) => (
  <div className={`p-6 border-b ${className}`} style={{ borderColor: THEME.border }}>
    {children}
  </div>
)

const CardTitle = ({ children, className = "" }) => (
  <h3 className={`text-lg font-bold text-gray-800 ${className}`}>{children}</h3>
)

const CardDescription = ({ children, className = "" }) => (
  <p className={`text-sm text-gray-500 mt-1 ${className}`}>{children}</p>
)

const CardContent = ({ children, className = "" }) => <div className={`p-6 ${className}`}>{children}</div>

function SectionHeader({ title, subtitle, icon: Icon }) {
  return (
    <div className="flex items-center gap-3">
      {Icon && <Icon className="w-6 h-6" style={{ color: THEME.blue }} />}
      <div>
        <h2 className="text-xl font-bold text-gray-800">{title}</h2>
        {subtitle ? <p className="text-sm text-gray-500">{subtitle}</p> : null}
      </div>
    </div>
  )
}

function isThairathAgency(name) {
  const s = String(name || "").toLowerCase()
  return s.includes("thairath") || s.includes("ไทยรัฐ")
}

function thaiMonthYear(dateLike) {
  if (!dateLike) return "-"
  const d = new Date(dateLike.length === 7 ? `${dateLike}-01` : dateLike)
  if (Number.isNaN(d.getTime())) return String(dateLike)

  const months = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
  return `${months[d.getMonth()]} ${d.getFullYear() + 543}`
}

function thaiDateShort(dateStr) {
  const d = new Date(dateStr)
  if (Number.isNaN(d.getTime())) return String(dateStr || "")

  const months = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
  return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`
}

function monthLabel(dateStr, lang) {
  if (!dateStr) return "-"
  if (lang === "th") return thaiMonthYear(dateStr)
  return dateStr.length >= 7 ? dateStr.slice(0, 7) : String(dateStr)
}

function parseTop3Shap(raw) {
  if (!raw) return []
  if (Array.isArray(raw)) return raw

  try {
    const normalized = String(raw).replace(/'/g, '"')
    const parsed = JSON.parse(normalized)
    return Array.isArray(parsed) ? parsed : [String(raw)]
  } catch {
    return String(raw)
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)
  }
}

function normalizeDirection(direction, t) {
  const text = String(direction || "").toLowerCase()

  if (text.includes("เพิ่ม") || text.includes("up")) {
    return {
      tone: "up",
      label: t("Increase", "เพิ่มขึ้น"),
      badge: direction || t("Increase", "เพิ่มขึ้น"),
    }
  }

  if (text.includes("ลด") || text.includes("down")) {
    return {
      tone: "down",
      label: t("Decrease", "ลดลง"),
      badge: direction || t("Decrease", "ลดลง"),
    }
  }

  return {
    tone: "neutral",
    label: t("Stable", "ทรงตัว"),
    badge: direction || t("Stable", "ทรงตัว"),
  }
}

function toneClasses(tone) {
  if (tone === "up") {
    return { bg: "#DCFCE7", text: THEME.success, soft: "#ECFDF3" }
  }
  if (tone === "down") {
    return { bg: "#FEE2E2", text: THEME.danger, soft: "#FEF2F2" }
  }
  return { bg: "#F3F4F6", text: THEME.gray, soft: "#F9FAFB" }
}

function filterNewsLast12Months(items) {
  if (!items?.length) return []

  const maxDateStr = [...items].map((x) => x.date).sort().slice(-1)[0]
  const maxDate = new Date(maxDateStr)
  const end = new Date(maxDate.getFullYear(), maxDate.getMonth(), 1)
  const start = new Date(end)
  start.setMonth(start.getMonth() - 11)

  return items.filter((n) => {
    const d = new Date(n.date)
    const m = new Date(d.getFullYear(), d.getMonth(), 1)
    return m >= start && m <= end
  })
}

function stackCountByMonth(items, getGroupKey, groupsOverride = null) {
  const monthMap = {}
  const groupSet = new Set(groupsOverride || [])

  items.forEach((n) => {
    const monthKey = n.date?.slice(0, 7)
    const group = getGroupKey(n)
    if (!monthKey || !group) return

    groupSet.add(group)
    if (!monthMap[monthKey]) monthMap[monthKey] = {}
    monthMap[monthKey][group] = (monthMap[monthKey][group] || 0) + 1
  })

  const groups = groupsOverride ? [...groupsOverride] : [...groupSet].sort()
  const months = Object.keys(monthMap).sort((a, b) => a.localeCompare(b))

  const data = months.map((month) => {
    const row = { month }
    groups.forEach((g) => {
      row[g] = monthMap[month][g] || 0
    })
    return row
  })

  return { data, groups }
}

function toAgencyStack(rows) {
  if (!Array.isArray(rows)) return { data: [], groups: [] }

  const monthMap = {}
  const groupsSet = new Set()

  rows.forEach((r) => {
    const month = r.month
    const agency = r.agency || "Unknown"
    const count = Number(r.count || 0)

    groupsSet.add(agency)
    if (!monthMap[month]) monthMap[month] = {}
    monthMap[month][agency] = (monthMap[month][agency] || 0) + count
  })

  const groups = [...groupsSet].sort()
  const months = Object.keys(monthMap).sort()

  const data = months.map((m) => {
    const row = { month: m }
    groups.forEach((g) => {
      row[g] = monthMap[m][g] || 0
    })
    return row
  })

  return { data, groups }
}

function buildSelectedMonthChartData(series = [], selectedMonth) {
  if (!series?.length) return []
  return series.map((row) => ({
    ...row,
    selectedPred: row.date?.slice(0, 7) === selectedMonth ? row.pred : null,
  }))
}

function useLang() {
  const [lang, setLang] = React.useState("th")
  const t = React.useCallback((en, th) => (lang === "th" ? th : en), [lang])
  return { lang, setLang, t }
}

function useNavigation() {
  const getPageFromHash = () => {
    const hash = window.location.hash.replace("#", "")
    if (["forecast", "analytics", "aspectNews"].includes(hash)) return hash
    return "forecast"
  }

  const [page, setPageState] = React.useState(getPageFromHash)

  const setPage = React.useCallback((newPage) => {
    setPageState(newPage)
    const currentHash = window.location.hash.replace("#", "")
    if (currentHash !== newPage) {
      window.history.pushState({ page: newPage }, "", `#${newPage}`)
    }
  }, [])

  React.useEffect(() => {
    const onPopState = (e) => {
      const pg = e.state?.page || getPageFromHash()
      setPageState(pg)
    }

    window.addEventListener("popstate", onPopState)

    if (!window.history.state?.page) {
      const current = getPageFromHash()
      window.history.replaceState({ page: current }, "", `#${current}`)
    }

    return () => window.removeEventListener("popstate", onPopState)
  }, [])

  return { page, setPage }
}

function ForecastSummaryCard({
  t,
  lang,
  month,
  predicted,
  direction,
  comparisonValue,
  comparisonBasis,
}) {
  const info = normalizeDirection(direction, t)
  const tone = toneClasses(info.tone)

  const arrow =
    info.tone === "up" ? "↑" :
      info.tone === "down" ? "↓" :
        "→"

  return (
    <Card>
      <CardContent className="p-6">
        <div className="text-sm font-semibold text-gray-500 mb-1">
          {t("Forecast target", "เป้าหมายพยากรณ์")}
        </div>

        <div className="text-xl font-bold text-gray-800 mb-5">
          {monthLabel(month, lang)}
        </div>

        <div className="flex flex-col md:flex-row gap-4">
          <div
            className="rounded-2xl border p-4 md:w-[280px] flex-shrink-0"
            style={{ borderColor: THEME.border, backgroundColor: "#FFFFFF" }}
          >
            <div className="text-xs text-gray-500 mb-1">
              {comparisonBasis === "predicted"
                ? t("Previous month predicted data", "ข้อมูลพยากรณ์ของเดือนก่อนหน้า")
                : t("Previous month actual data", "ข้อมูลจริงของเดือนก่อนหน้า")}
            </div>
            <div className="text-3xl font-black text-gray-900 leading-none">
              {comparisonValue != null ? Number(comparisonValue).toFixed(1) : "-"}
            </div>
          </div>

          <div
            className="rounded-2xl border p-4 flex-1 xecon-fade-in"
            style={{ borderColor: THEME.border, backgroundColor: tone.soft }}
          >
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              <div className="min-w-0">
                <div className="text-xs text-gray-500 mb-1">
                  {t("Target month predicted data", "ข้อมูลพยากรณ์ของเดือนเป้าหมาย")}
                </div>
                <div className="text-4xl font-black text-gray-900 leading-none mb-2">
                  {predicted != null ? Number(predicted).toFixed(1) : "-"}
                </div>
                {/* Delta — lives directly under the predicted number */}
                {predicted != null && comparisonValue != null && Number(comparisonValue) !== 0 && (() => {
                  const delta = Number(predicted) - Number(comparisonValue)
                  const pct = (delta / Math.abs(Number(comparisonValue))) * 100
                  const isPos = delta >= 0
                  return (
                    <div
                      className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full"
                      style={{ backgroundColor: isPos ? "#DCFCE7" : "#FEE2E2", color: isPos ? THEME.success : THEME.danger }}
                    >
                      {isPos ? "↑" : "↓"}
                      {isPos ? "+" : ""}{delta.toFixed(1)} ({isPos ? "+" : ""}{pct.toFixed(1)}%)
                      <span className="font-normal opacity-70 ml-0.5">{t("vs prev", "เทียบเดือนก่อน")}</span>
                    </div>
                  )
                })()}
              </div>

              <div className="flex items-center gap-4 md:justify-end">
                <div
                  className="text-6xl font-light leading-none xecon-pulse"
                  style={{ color: tone.text }}
                >
                  {arrow}
                </div>

                <div className="flex flex-col">
                  <div
                    className="inline-flex w-fit px-3 py-1 rounded-full text-sm font-semibold mb-2"
                    style={{ backgroundColor: tone.bg, color: tone.text }}
                  >
                    {info.tone === "up"
                      ? t("Up", "เพิ่มขึ้น")
                      : info.tone === "down"
                        ? t("Down", "ลดลง")
                        : t("Stable", "ทรงตัว")}
                  </div>
                  <div className="text-sm text-gray-700">
                    {direction || t("No direction data", "ไม่มีข้อมูล")}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function TopAspectsOnlyCard({ t, news = [], onSelectAspect, selectedForecastMonth, lang }) {
  const getPrevious3Months = React.useCallback((targetMonth) => {
    if (!targetMonth) return []

    const [year, month] = targetMonth.split("-").map(Number)
    const base = new Date(year, month - 1, 1)

    const months = []
    for (let i = 3; i >= 1; i--) {
      const d = new Date(base)
      d.setMonth(d.getMonth() - i)
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, "0")
      months.push(`${y}-${m}`)
    }
    return months
  }, [])

  const backwardMonths = React.useMemo(
    () => getPrevious3Months(selectedForecastMonth),
    [getPrevious3Months, selectedForecastMonth]
  )

  const filteredNews = React.useMemo(() => {
    if (!backwardMonths.length) return []
    return news.filter((n) => backwardMonths.includes(String(n.date || "").slice(0, 7)))
  }, [news, backwardMonths])

  const ranked = React.useMemo(() => {
    const counts = {}
    filteredNews.forEach((n) => {
      const aspect = n.aspect || "Other"
      counts[aspect] = (counts[aspect] || 0) + 1
    })

    return Object.entries(counts)
      .map(([aspect, count]) => ({ aspect, count }))
      .sort((a, b) => b.count - a.count)
  }, [filteredNews])

  const periodText =
    backwardMonths.length === 3
      ? lang === "th"
        ? `${thaiMonthYear(backwardMonths[0])} - ${thaiMonthYear(backwardMonths[2])}`
        : `${backwardMonths[0]} to ${backwardMonths[2]}`
      : "-"

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <CardTitle>{t("Related aspects", "ประเด็นที่เกี่ยวข้อง")}</CardTitle>
            <CardDescription>
              {t(
                "News counts from the 3 months before the selected forecast month",
                "จำนวนข่าวจาก 3 เดือนย้อนหลังของเดือนพยากรณ์ที่เลือก"
              )}
            </CardDescription>
          </div>

          <Badge variant="outline">
            {t("Period", "ช่วงเวลา")} : {periodText}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="min-h-[320px]">
        {ranked.length === 0 ? (
          <EmptyState
            icon="📰"
            title={t("No aspects found", "ไม่พบประเด็น")}
            description={t(
              "No news data available for the 3 months before this forecast period.",
              "ไม่พบข้อมูลข่าวสำหรับ 3 เดือนก่อนช่วงพยากรณ์นี้"
            )}
          />
        ) : (
          <div className="grid grid-cols-1 gap-2">
            {ranked.map((item) => (
              <button
                key={item.aspect}
                onClick={() => onSelectAspect?.(item.aspect)}
                className="xecon-aspect-btn w-full px-4 py-3 rounded-xl border text-left"
                style={{ borderColor: THEME.border, background: "#fff", cursor: "pointer" }}
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-semibold text-gray-800">{item.aspect}</span>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">{item.count}</Badge>
                    <span
                      className="xecon-arrow text-gray-400 text-sm"
                      style={{ opacity: 0 }}
                    >→</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function ForecastChart({ t, lang, series, selectedMonth }) {
  const filteredSeries = React.useMemo(() => {
    if (!series || series.length === 0) return []
    return [...series].sort((a, b) => String(a.date).localeCompare(String(b.date)))
  }, [series])

  const chartData = React.useMemo(
    () => buildSelectedMonthChartData(filteredSeries, selectedMonth),
    [filteredSeries, selectedMonth]
  )

  const forecastStartDate = React.useMemo(() => {
    const firstForecast = filteredSeries.find((s) => s.actual == null && s.pred != null)
    return firstForecast?.date || null
  }, [filteredSeries])

  const selectedDate = selectedMonth ? `${selectedMonth}-01` : null

  const yDomain = React.useMemo(() => {
    const values = chartData
      .flatMap((d) => [d.actual, d.pred])
      .filter((v) => v != null && !Number.isNaN(Number(v)))
      .map(Number)

    if (!values.length) return [0, 100]

    const min = Math.min(...values)
    const max = Math.max(...values)
    const pad = Math.max((max - min) * 0.1, 1)

    return [Math.floor(min - pad), Math.ceil(max + pad)]
  }, [chartData])

  const defaultBrushRange = React.useMemo(() => {
    const len = chartData.length
    if (!len) return { startIndex: 0, endIndex: 0 }

    const lastIndex = len - 1
    const startIndex = Math.max(0, len - 24) // last 24 months = 2 years

    return { startIndex, endIndex: lastIndex }
  }, [chartData])

  const [brushRange, setBrushRange] = React.useState(defaultBrushRange)

  React.useEffect(() => {
    setBrushRange(defaultBrushRange)
  }, [defaultBrushRange.startIndex, defaultBrushRange.endIndex])

  const visibleData = React.useMemo(() => {
    if (!chartData.length) return []
    const start = Math.max(0, brushRange.startIndex ?? 0)
    const end = Math.min(chartData.length - 1, brushRange.endIndex ?? chartData.length - 1)
    return chartData.slice(start, end + 1)
  }, [chartData, brushRange])

  const visibleYDomain = React.useMemo(() => {
    const values = visibleData
      .flatMap((d) => [d.actual, d.pred])
      .filter((v) => v != null && !Number.isNaN(Number(v)))
      .map(Number)

    if (!values.length) return yDomain

    const min = Math.min(...values)
    const max = Math.max(...values)
    const pad = Math.max((max - min) * 0.1, 1)

    return [Math.floor(min - pad), Math.ceil(max + pad)]
  }, [visibleData, yDomain])

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle>{t("CCI Timeline", "กราฟดัชนีความเชื่อมั่น (CCI)")}</CardTitle>
            <CardDescription>
              {t(
                "Showing the last 2 years by default. Drag the range selector below to adjust.",
                "แสดงข้อมูลย้อนหลัง 2 ปีล่าสุด ปรับช่วงเวลาได้จากแถบด้านล่าง"
              )}
            </CardDescription>
          </div>

          <button
            onClick={() => setBrushRange(defaultBrushRange)}
            className="px-3 py-2 rounded-lg text-sm font-medium border bg-white hover:bg-gray-50 transition"
            style={{ borderColor: THEME.border }}
          >
            {t("Reset view", "รีเซ็ตมุมมอง")}
          </button>
        </div>
      </CardHeader>

      <CardContent>
        <div
          className="w-full rounded-xl border bg-white overflow-hidden"
          style={{ borderColor: THEME.border }}
        >
          <div className="flex w-full" style={{ height: 420 }}>
            {/* Fixed Y axis */}
            <div
              className="flex-shrink-0 bg-white border-r"
              style={{ width: 90, borderColor: THEME.border }}
            >
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={visibleData}
                  margin={{ top: 60, right: 0, left: 0, bottom: 45 }}
                  syncId="forecast-chart"
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" horizontal vertical={false} />
                  <YAxis
                    tick={{ fontSize: 11 }}
                    width={75}
                    domain={visibleYDomain}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Main chart */}
            <div className="flex-1 overflow-hidden">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart
                  data={visibleData}
                  margin={{ top: 20, right: 20, left: 0, bottom: 45 }}
                  syncId="forecast-chart"
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11 }}
                    minTickGap={20}
                    tickFormatter={(v) =>
                      lang === "th"
                        ? thaiMonthYear(v).replace(" ", "\n")
                        : String(v).slice(0, 7)
                    }
                  />
                  <YAxis hide domain={visibleYDomain} />

                  <ReTooltip
                    content={({ active, payload, label }) => {
                      if (!active || !payload?.length) return null

                      const actualItem = payload.find((p) => p.dataKey === "actual")
                      const predItem = payload.find((p) => p.dataKey === "pred")

                      return (
                        <div
                          className="rounded-xl border bg-white p-3 shadow-lg"
                          style={{ borderColor: THEME.border }}
                        >
                          <div className="font-semibold text-gray-900 mb-1">
                            {monthLabel(label, lang)}
                          </div>

                          {actualItem?.value != null ? (
                            <div className="text-sm" style={{ color: THEME.navy }}>
                              {t("Actual", "ค่าจริง")}: {Number(actualItem.value).toFixed(2)}
                            </div>
                          ) : null}

                          {predItem?.value != null ? (
                            <div className="text-sm" style={{ color: THEME.blue }}>
                              {t("Forecast", "ค่าพยากรณ์")}: {Number(predItem.value).toFixed(2)}
                            </div>
                          ) : null}
                        </div>
                      )
                    }}
                  />

                  <Legend verticalAlign="top" height={40} />

                  {forecastStartDate ? (
                    <ReferenceArea
                      x1={forecastStartDate}
                      fill={THEME.blue}
                      fillOpacity={0.05}
                    />
                  ) : null}

                  {selectedDate && visibleData.some((d) => d.date === selectedDate) ? (
                    <ReferenceLine
                      x={selectedDate}
                      stroke={THEME.blue}
                      strokeDasharray="4 4"
                      label={{
                        value: t("Selected", "เดือนที่เลือก"),
                        position: "insideTopRight",
                        fontSize: 11,
                        fill: THEME.blue,
                      }}
                    />
                  ) : null}

                  <Line
                    type="monotone"
                    dataKey="actual"
                    stroke={THEME.navy}
                    strokeWidth={2.5}
                    dot={{ r: 3 }}
                    activeDot={{ r: 5 }}
                    name={t("Actual", "ค่าจริง")}
                    connectNulls={false}
                  />

                  <Line
                    type="monotone"
                    dataKey="pred"
                    stroke={THEME.blue}
                    strokeWidth={2.5}
                    dot={{ r: 3 }}
                    activeDot={{ r: 5 }}
                    strokeDasharray="6 6"
                    name={t("Forecast", "ค่าพยากรณ์")}
                    connectNulls={false}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Brush / zoom control */}
          <div
            className="border-t px-4 py-3 bg-white"
            style={{ borderColor: THEME.border }}
          >
            <div style={{ width: "100%", height: 90 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <XAxis dataKey="date" hide />
                  <YAxis hide domain={yDomain} />

                  {/* NO lines here — completely clean */}

                  <Brush
                    dataKey="date"
                    height={28}
                    travellerWidth={10}
                    startIndex={brushRange.startIndex}
                    endIndex={brushRange.endIndex}
                    onChange={(range) => {
                      if (
                        range &&
                        typeof range.startIndex === "number" &&
                        typeof range.endIndex === "number"
                      ) {
                        setBrushRange({
                          startIndex: range.startIndex,
                          endIndex: range.endIndex,
                        })
                      }
                    }}
                    tickFormatter={(v) =>
                      lang === "th" ? thaiMonthYear(v) : String(v).slice(0, 7)
                    }
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function ForecastPageSkeleton() {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl border p-6" style={{ borderColor: "#E6ECF5" }}>
        <Skeleton className="mb-2" style={{ height: 14, width: 120 }} />
        <Skeleton className="mb-6" style={{ height: 22, width: 180 }} />
        <div className="flex gap-4">
          <Skeleton style={{ height: 88, width: 280, borderRadius: 16 }} />
          <Skeleton style={{ height: 88, flex: 1, borderRadius: 16 }} />
        </div>
      </div>
      <div className="bg-white rounded-2xl border p-6" style={{ borderColor: "#E6ECF5" }}>
        <Skeleton className="mb-2" style={{ height: 18, width: 160 }} />
        <Skeleton style={{ height: 400, borderRadius: 12 }} />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-2xl border p-6" style={{ borderColor: "#E6ECF5" }}>
          <Skeleton className="mb-4" style={{ height: 18, width: 200 }} />
          <Skeleton style={{ height: 160, borderRadius: 12 }} />
        </div>
        <div className="bg-white rounded-2xl border p-6" style={{ borderColor: "#E6ECF5" }}>
          <Skeleton className="mb-4" style={{ height: 18, width: 140 }} />
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="mb-2" style={{ height: 44, borderRadius: 12 }} />)}
        </div>
      </div>
    </div>
  )
}

function ForecastPage({
  t,
  lang,
  series,
  summary,
  allExplain,
  news = [],
  onSelectAspect,
  selectedForecastMonth,
}) {
  const previousMonthActual = React.useMemo(() => {
    if (!selectedForecastMonth || !series?.length) return null

    const [year, month] = selectedForecastMonth.split("-").map(Number)
    const prev = new Date(year, month - 2, 1)
    const prevKey = `${prev.getFullYear()}-${String(prev.getMonth() + 1).padStart(2, "0")}`

    const prevRow = series.find((r) => r.date?.slice(0, 7) === prevKey)
    return prevRow?.actual ?? null
  }, [selectedForecastMonth, series])

  const activeRow = React.useMemo(
    () => allExplain.find((r) => r.date === selectedForecastMonth) || null,
    [allExplain, selectedForecastMonth]
  )

  const selectedSeriesRow = React.useMemo(
    () => series.find((r) => r.date?.slice(0, 7) === selectedForecastMonth) || null,
    [series, selectedForecastMonth]
  )

  const isLoading = !series?.length && !allExplain?.length

  if (isLoading) return <ForecastPageSkeleton />

  return (
    <div className="space-y-6">
      <ForecastSummaryCard
        t={t}
        lang={lang}
        month={selectedForecastMonth}
        predicted={selectedSeriesRow?.pred}
        direction={selectedSeriesRow?.direction}
        comparisonValue={selectedSeriesRow?.compare_value}
        comparisonBasis={selectedSeriesRow?.compare_basis}
      />

      <ForecastChart
        t={t}
        lang={lang}
        series={series}
        selectedMonth={selectedForecastMonth}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <div className="lg:col-span-2">
          <ReasoningPanel
            t={t}
            lang={lang}
            activeRow={activeRow}
            selectedMonth={selectedForecastMonth}
          />
        </div>

        <div className="lg:col-span-1">
          <TopAspectsOnlyCard
            t={t}
            news={news}
            onSelectAspect={onSelectAspect}
            selectedForecastMonth={selectedForecastMonth}
            lang={lang}
          />
        </div>
      </div>
    </div>
  )
}

function ReasoningPanel({ t, lang, activeRow, selectedMonth }) {
  const directionInfo = normalizeDirection(activeRow?.direction, t)
  const directionTone = toneClasses(directionInfo.tone)

  return (
    <Card className="overflow-hidden">
      <CardHeader className="bg-gradient-to-r from-slate-50 to-white">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" style={{ color: THEME.blue }} />
              {t("Forecast reasoning", "เหตุผลประกอบการพยากรณ์")}
            </CardTitle>
            <CardDescription>
              {t("Narrative explanation for the selected month", "คำอธิบายเชิงเหตุผลสำหรับเดือนที่เลือก")}
            </CardDescription>
          </div>

          <div className="flex flex-wrap gap-2">
            <Badge variant="outline">
              {t("Month", "เดือน")}: {monthLabel(selectedMonth, lang)}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {activeRow ? (
          <div
            className="rounded-2xl p-5 border"
            style={{
              backgroundColor: directionTone.soft,
              borderColor: THEME.border,
            }}
          >
            <div className="flex items-start gap-4">
              <div
                className="w-1.5 self-stretch rounded-full"
                style={{ backgroundColor: directionTone.text }}
              />
              <div className="flex-1">
                <div className="text-sm font-semibold mb-2" style={{ color: directionTone.text }}>
                  {t("Model interpretation", "บทวิเคราะห์ของโมเดล")}
                </div>
                <p className="text-[15px] leading-8 text-gray-700 whitespace-pre-line">
                  {activeRow?.reasoning || t("No reasoning available.", "ยังไม่มีคำอธิบาย")}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <EmptyState
            icon="🔍"
            title={t("No explanation available", "ไม่พบคำอธิบาย")}
            description={t(
              "No forecast reasoning was found for this month.",
              "ไม่พบคำอธิบายเชิงเหตุผลสำหรับเดือนนี้"
            )}
          />
        )}
      </CardContent>
    </Card>
  )
}

const PER_PAGE = 15

function AspectNewsPage({ t, lang, aspect, news = [], onBack }) {
  const [currentPage, setCurrentPage] = React.useState(1)
  const [search, setSearch] = React.useState("")

  const newsForAspect = React.useMemo(() => {
    if (!aspect) return []
    return [...news]
      .filter((n) => (n.aspect || "Unknown") === aspect)
      .sort((a, b) => b.date.localeCompare(a.date))
  }, [aspect, news])

  const filteredNews = React.useMemo(() => {
    if (!search.trim()) return newsForAspect
    const q = search.toLowerCase()
    return newsForAspect.filter(
      (n) =>
        (n.title || "").toLowerCase().includes(q) ||
        (n.source || "").toLowerCase().includes(q)
    )
  }, [newsForAspect, search])

  React.useEffect(() => {
    setCurrentPage(1)
  }, [aspect, search])

  const totalPages = Math.max(1, Math.ceil(filteredNews.length / PER_PAGE))
  const pagedNews = filteredNews.slice((currentPage - 1) * PER_PAGE, currentPage * PER_PAGE)

  const pageNumbers = React.useMemo(() => {
    const pages = []
    let start = Math.max(1, currentPage - 2)
    let end = Math.min(totalPages, start + 4)
    start = Math.max(1, end - 4)
    for (let i = start; i <= end; i++) pages.push(i)
    return pages
  }, [currentPage, totalPages])

  return (
    <div className="space-y-6 xecon-fade-in">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm">
        <button
          onClick={onBack}
          className="text-gray-500 hover:text-gray-800 transition font-medium"
          style={{ cursor: "pointer", background: "none", border: "none", padding: 0 }}
        >
          {t("Forecast", "การพยากรณ์")}
        </button>
        <span className="text-gray-300">›</span>
        <span className="text-gray-800 font-semibold">{aspect ?? t("Aspect", "ประเด็น")}</span>
        {filteredNews.length > 0 && (
          <span className="ml-1 text-gray-400">({filteredNews.length})</span>
        )}
      </nav>

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <CardTitle>{aspect ?? t("Not selected", "ยังไม่ได้เลือก")}</CardTitle>
              <CardDescription>
                {t("News list for the selected aspect", "รายการข่าวสำหรับประเด็นที่เลือก")}
                {newsForAspect.length > 0 && (
                  <span className="ml-2 text-gray-400">
                    ({t(`${newsForAspect.length} total`, `ทั้งหมด ${newsForAspect.length} ข่าว`)})
                  </span>
                )}
              </CardDescription>
            </div>
            {newsForAspect.length > 0 && (
              <div className="relative flex-shrink-0">
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder={t("Search headlines…", "ค้นหาข่าว…")}
                  className="pl-8 pr-3 py-1.5 text-sm rounded-lg border bg-white outline-none"
                  style={{
                    borderColor: THEME.border,
                    width: 220,
                    boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
                  }}
                />
                <span
                  className="absolute left-2.5 top-1/2 text-gray-400"
                  style={{ transform: "translateY(-50%)", fontSize: 14, pointerEvents: "none" }}
                >
                  🔍
                </span>
                {search && (
                  <button
                    onClick={() => setSearch("")}
                    className="absolute right-2.5 top-1/2 text-gray-400 hover:text-gray-600"
                    style={{ transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", fontSize: 14 }}
                  >
                    ✕
                  </button>
                )}
              </div>
            )}
          </div>
        </CardHeader>

        <CardContent className="p-0">
          {!aspect ? (
            <EmptyState
              icon="☝️"
              title={t("Select an aspect", "เลือกประเด็น")}
              description={t("Tap an aspect from the forecast page to see related news.", "แตะประเด็นจากหน้าพยากรณ์เพื่อดูข่าวที่เกี่ยวข้อง")}
              action={
                <button
                  onClick={onBack}
                  className="px-4 py-2 rounded-xl text-sm font-medium text-white"
                  style={{ background: THEME.blue, border: "none", cursor: "pointer" }}
                >
                  ← {t("Go back", "ย้อนกลับ")}
                </button>
              }
            />
          ) : filteredNews.length === 0 ? (
            <EmptyState
              icon="📭"
              title={search ? t("No results found", "ไม่พบผลลัพธ์") : t("No news found", "ไม่พบข่าว")}
              description={
                search
                  ? t(`No headlines matching "${search}"`, `ไม่พบข่าวที่ตรงกับ "${search}"`)
                  : t("No news articles available for this aspect.", "ไม่มีข่าวสำหรับประเด็นนี้")
              }
              action={search ? (
                <button
                  onClick={() => setSearch("")}
                  className="px-4 py-2 rounded-xl text-sm font-medium"
                  style={{ border: `1px solid ${THEME.border}`, background: "#fff", cursor: "pointer" }}
                >
                  {t("Clear search", "ล้างการค้นหา")}
                </button>
              ) : null}
            />
          ) : (
            <>
              <div className="divide-y divide-gray-100">
                {pagedNews.map((n, idx) => {
                  const displayDate = lang === "th" ? thaiDateShort(n.date) : n.date
                  const tagColor = tagColors[n.tag] || "#6b7280"
                  const tagLabel = lang === "th" ? tagTH[n.tag] || n.tag : n.tag
                  const globalIdx = (currentPage - 1) * PER_PAGE + idx

                  return (
                    <div key={`${n.date}-${globalIdx}`} className="xecon-news-row px-6 py-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="text-xs text-gray-400 mb-1">
                            {displayDate}
                            {n.source && <span className="ml-2 font-medium" style={{ color: THEME.blue }}>{n.source}</span>}
                          </div>
                          <a
                            href={n.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-sm font-semibold text-gray-900 hover:text-blue-700 transition leading-snug block"
                          >
                            {n.title}
                          </a>
                          <div className="mt-1.5">
                            <Badge
                              variant="outline"
                              className="text-[10px] px-2 py-0.5 border-0 font-semibold uppercase tracking-wider"
                              style={{ backgroundColor: `${tagColor}18`, color: tagColor }}
                            >
                              {tagLabel}
                            </Badge>
                          </div>
                        </div>
                        <span className="text-gray-300 text-sm flex-shrink-0 mt-1">↗</span>
                      </div>
                    </div>
                  )
                })}
              </div>

              {totalPages > 1 ? (
                <div className="flex items-center justify-center gap-2 p-4 border-t" style={{ borderColor: THEME.border }}>
                  <button
                    onClick={() => {
                      setCurrentPage((p) => Math.max(1, p - 1))
                      window.scrollTo({ top: 0, behavior: "smooth" })
                    }}
                    disabled={currentPage === 1}
                    className="px-3 py-1.5 rounded-lg text-sm font-medium transition disabled:opacity-40 disabled:cursor-not-allowed"
                    style={{ border: `1px solid ${THEME.border}` }}
                  >
                    ← {t("Prev", "ก่อนหน้า")}
                  </button>

                  {pageNumbers[0] > 1 ? (
                    <>
                      <button
                        onClick={() => {
                          setCurrentPage(1)
                          window.scrollTo({ top: 0, behavior: "smooth" })
                        }}
                        className="w-9 h-9 rounded-lg text-sm font-medium hover:bg-gray-50 transition"
                        style={{ border: `1px solid ${THEME.border}` }}
                      >
                        1
                      </button>
                      {pageNumbers[0] > 2 ? <span className="text-gray-400 text-sm">…</span> : null}
                    </>
                  ) : null}

                  {pageNumbers.map((p) => (
                    <button
                      key={p}
                      onClick={() => {
                        setCurrentPage(p)
                        window.scrollTo({ top: 0, behavior: "smooth" })
                      }}
                      className="w-9 h-9 rounded-lg text-sm font-medium transition"
                      style={{
                        backgroundColor: p === currentPage ? THEME.navy : "#FFFFFF",
                        color: p === currentPage ? "#FFFFFF" : "#111827",
                        border: `1px solid ${p === currentPage ? THEME.navy : THEME.border}`,
                      }}
                    >
                      {p}
                    </button>
                  ))}

                  {pageNumbers[pageNumbers.length - 1] < totalPages ? (
                    <>
                      {pageNumbers[pageNumbers.length - 1] < totalPages - 1 ? <span className="text-gray-400 text-sm">…</span> : null}
                      <button
                        onClick={() => {
                          setCurrentPage(totalPages)
                          window.scrollTo({ top: 0, behavior: "smooth" })
                        }}
                        className="w-9 h-9 rounded-lg text-sm font-medium hover:bg-gray-50 transition"
                        style={{ border: `1px solid ${THEME.border}` }}
                      >
                        {totalPages}
                      </button>
                    </>
                  ) : null}

                  <button
                    onClick={() => {
                      setCurrentPage((p) => Math.min(totalPages, p + 1))
                      window.scrollTo({ top: 0, behavior: "smooth" })
                    }}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1.5 rounded-lg text-sm font-medium transition disabled:opacity-40 disabled:cursor-not-allowed"
                    style={{ border: `1px solid ${THEME.border}` }}
                  >
                    {t("Next", "ถัดไป")} →
                  </button>
                </div>
              ) : null}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function AnalyticsPage({ t, lang, news = [], shapData = [] }) {
  const [agencyStack, setAgencyStack] = React.useState({ data: [], groups: [] })
  const [agencyErr, setAgencyErr] = React.useState("")

  const news1y = React.useMemo(() => filterNewsLast12Months(news), [news])

  const aspectStack = React.useMemo(() => {
    return stackCountByMonth(news1y, (n) => n.aspect || "Unknown", ASPECTS_TO_RUN)
  }, [news1y])

  const shapArr = React.useMemo(() => (Array.isArray(shapData) ? shapData : shapData?.data ?? []), [shapData])

  const shapRows = React.useMemo(() => {
    return shapArr
      .map((d) => ({
        name: String(d.name),
        value: Number(d.value) || 0,
        absValue: Math.abs(Number(d.value) || 0),
      }))
      .sort((a, b) => b.absValue - a.absValue)
  }, [shapArr])

  React.useEffect(() => {
    let alive = true

    async function loadAgency() {
      setAgencyErr("")
      try {
        const rows = await getAgencyVolumeLastNMonths(12)
        if (!alive) return
        setAgencyStack(toAgencyStack(rows))
      } catch (e) {
        if (!alive) return
        setAgencyErr(String(e?.message || e))
      }
    }

    loadAgency()
    return () => {
      alive = false
    }
  }, [])

  const sentimentHistogram = React.useMemo(() => {
    const bins = Array.from({ length: 10 }, (_, i) => {
      const min = i / 10
      const max = (i + 1) / 10
      return { range: `${min.toFixed(1)}–${max.toFixed(1)}`, count: 0 }
    })

    news.forEach((n) => {
      const s = Number(n.rawSentiment)
      if (!Number.isFinite(s)) return
      const val = Math.max(0, Math.min(1, s))
      const idx = val === 1 ? 9 : Math.floor(val * 10)
      bins[idx].count += 1
    })

    return bins
  }, [news])

  const sentimentFlow = React.useMemo(() => {
    const sorted = [...news].sort((a, b) => a.date.localeCompare(b.date))
    let cumulative = 0

    return sorted.map((n) => {
      const val = Number(n.rawSentiment) || 0
      cumulative += val

      return {
        date: n.date,
        sentiment: cumulative,
        positive: val > 0 ? val : 0,
        negative: val < 0 ? Math.abs(val) : 0,
      }
    })
  }, [news])

  const { shortTermData, longTermData } = React.useMemo(() => {
    const impactMap = { Negative: -1, Neutral: 0, Positive: 1 }
    const shortTerm = []
    const longTerm = []

    news.forEach((n) => {
      const point = {
        sentiment: Number(n.rawSentiment) || 0,
        impact: impactMap[n.impactType] ?? 0,
        headline: String(n.title || "").substring(0, 60),
        impactLabel: n.impactType || "Neutral",
        effectLabel: n.effectType || "Short-term",
      }

      if (n.effectType === "Long-term") longTerm.push(point)
      else shortTerm.push(point)
    })

    return { shortTermData: shortTerm, longTermData: longTerm }
  }, [news])

  const isLoading = !news?.length && !shapData?.length && !agencyStack.data.length

  return (
    <div className="space-y-8 xecon-fade-in">
      <SectionHeader
        title={t("News analysis visualizations", "การวิเคราะห์ข่าวเชิงลึก")}
        subtitle={t("Volume, sentiment, impact, and feature importance", "ปริมาณข่าว อารมณ์ข่าว ผลกระทบ และความสำคัญของตัวแปร")}
        icon={BarChart3}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>{t("News volume by agency", "ปริมาณข่าวตามสำนักข่าว")}</CardTitle>
            <CardDescription>{t("Stacked by agency per month", "กราฟแท่งซ้อนตามสำนักข่าวรายเดือน")}</CardDescription>
          </CardHeader>
          <CardContent>
            {agencyErr ? (
              <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 text-sm p-3 flex items-center gap-2">
                <span>⚠️</span> {agencyErr}
              </div>
            ) : agencyStack.data.length === 0 ? (
              <Skeleton style={{ height: 320, borderRadius: 8 }} />
            ) : (
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={agencyStack.data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <ReTooltip />
                  <Legend />
                  {agencyStack.groups.map((agency, i) => (
                    <Bar
                      key={agency}
                      dataKey={agency}
                      stackId="1"
                      fill={isThairathAgency(agency) ? THAIRATH_COLOR : CHART_COLORS[i % CHART_COLORS.length]}
                      name={agency}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("News volume by aspect", "ปริมาณข่าวตามประเด็น")}</CardTitle>
            <CardDescription>{t("Stacked by aspect per month", "กราฟแท่งซ้อนตามประเด็นรายเดือน")}</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={aspectStack.data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <ReTooltip />
                <Legend />
                {aspectStack.groups.map((asp, i) => (
                  <Bar key={asp} dataKey={asp} stackId="1" fill={CHART_COLORS[i % CHART_COLORS.length]} name={asp} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("Sentiment distribution", "การกระจาย Sentiment")}</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={sentimentHistogram}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <ReTooltip />
                <Bar dataKey="count" fill={THEME.blue} name={t("News count", "จำนวนข่าว")} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("Sentiment flow over time", "กระแสความรู้สึกตามเวลา")}</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={sentimentFlow}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <ReTooltip />
                <Legend />
                <Area type="monotone" dataKey="positive" stackId="1" stroke={THEME.success} fill={THEME.success} name={t("Positive", "บวก")} />
                <Area type="monotone" dataKey="negative" stackId="1" stroke={THEME.danger} fill={THEME.danger} name={t("Negative", "ลบ")} />
                <Line type="monotone" dataKey="sentiment" stroke={THEME.navy} strokeWidth={2} name={t("Cumulative", "สะสม")} />
              </ComposedChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("Impact vs sentiment matrix", "เมทริกซ์ผลกระทบกับความรู้สึก")}</CardTitle>
            <CardDescription>{t("Each dot is one news article", "แต่ละจุดคือข่าว 1 ชิ้น")}</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={320}>
              <ScatterChart margin={{ bottom: 25, left: 20, right: 10, top: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="sentiment"
                  tick={{ fontSize: 11 }}
                  type="number"
                  label={{ value: t("Sentiment score", "คะแนน Sentiment"), position: "insideBottom", offset: -15 }}
                />
                <YAxis
                  dataKey="impact"
                  tick={{ fontSize: 11 }}
                  type="number"
                  ticks={[-1, 0, 1]}
                  tickFormatter={(v) => (v === -1 ? "Negative" : v === 0 ? "Neutral" : "Positive")}
                  label={{ value: t("Impact", "ผลกระทบ"), angle: -90, position: "insideLeft", offset: 5 }}
                />
                <ReTooltip
                  content={({ payload }) => {
                    if (!payload || !payload.length) return null
                    const d = payload[0]?.payload

                    return (
                      <div className="bg-white border rounded shadow p-2 text-xs max-w-xs">
                        <div className="font-semibold">{d?.headline}</div>
                        <div>Sentiment: {Number(d?.sentiment || 0).toFixed(2)}</div>
                        <div>Impact: {d?.impactLabel}</div>
                        <div>Effect: {d?.effectLabel}</div>
                      </div>
                    )
                  }}
                />
                <Scatter name={t("Short-term", "ระยะสั้น")} data={shortTermData} fill={THEME.blue} opacity={0.6} />
                <Scatter name={t("Long-term", "ระยะยาว")} data={longTermData} fill="#F59E0B" opacity={0.6} />
                <Legend verticalAlign="top" height={30} />
              </ScatterChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("Feature importance", "ปัจจัยที่สำคัญ")}</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={shapRows} layout="vertical" margin={{ top: 10, right: 40, left: 20, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="category" dataKey="name" width={200} />
                <ReTooltip />
                <Bar dataKey="absValue" name={t("Importance", "ความสำคัญ")} fill={THEME.navy} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>{t("Word cloud", "คำที่ปรากฏบ่อย")}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="w-full bg-white rounded-lg overflow-hidden">
                <img src={wordcloudImg} alt="CCI Impact Word Cloud" className="w-full h-auto rounded-xl" />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
export default function App() {
  const { lang, setLang, t } = useLang()
  const { page, setPage } = useNavigation()
  const [selectedAspect, setSelectedAspect] = React.useState(null)

  const [summary, setSummary] = React.useState(null)
  const [allExplain, setAllExplain] = React.useState([])
  const [series, setSeries] = React.useState([])
  const [err, setErr] = React.useState("")
  const [newsReal, setNewsReal] = React.useState([])
  const [shapData, setShapData] = React.useState([])

  const [selectedForecastMonth, setSelectedForecastMonth] = React.useState("")

  const latestActualMonth = React.useMemo(() => {
    const actualRows = (series || [])
      .filter((r) => r.actual != null && r.date)
      .sort((a, b) => String(a.date).localeCompare(String(b.date)))

    if (!actualRows.length) return null
    return actualRows[actualRows.length - 1].date.slice(0, 7)
  }, [series])

  const availableFutureMonths = React.useMemo(() => {
    if (!series?.length || !latestActualMonth) return []

    return [...new Set(
      series
        .filter((r) => r.pred != null && r.date)
        .map((r) => r.date.slice(0, 7))
        .filter((m) => m > latestActualMonth)
    )].sort((a, b) => a.localeCompare(b))
  }, [series, latestActualMonth])

  const explainMonths = React.useMemo(
    () =>
      [...new Set((allExplain || []).map((r) => r.date).filter(Boolean))].sort((a, b) =>
        a.localeCompare(b)
      ),
    [allExplain]
  )

  const historicalMonths = React.useMemo(() => {
    return explainMonths.filter((m) => !availableFutureMonths.includes(m))
  }, [explainMonths, availableFutureMonths])

  React.useEffect(() => {
    const allPossibleMonths = [...new Set([...availableFutureMonths, ...historicalMonths])].sort((a, b) =>
      a.localeCompare(b)
    )

    if (!allPossibleMonths.length) return

    if (!allPossibleMonths.includes(selectedForecastMonth)) {
      setSelectedForecastMonth(
        availableFutureMonths.length > 0
          ? availableFutureMonths[0]
          : allPossibleMonths[allPossibleMonths.length - 1]
      )
    }
  }, [availableFutureMonths, historicalMonths, selectedForecastMonth])

  React.useEffect(() => {
    let alive = true

    async function load() {
      setErr("")
      try {
        const [s, e, ts, newsRows, shapRes] = await Promise.allSettled([
          getSummary(),
          getAllExplain(),
          getTimeSeries(2000),
          getNews(),
          getShap(),
        ])

        if (!alive) return

        setSummary(s.status === "fulfilled" ? s.value : null)
        setAllExplain(e.status === "fulfilled" ? e.value?.data || [] : [])
        setSeries(ts.status === "fulfilled" ? ts.value?.data || [] : [])
        setNewsReal(newsRows.status === "fulfilled" ? newsRows.value?.data || [] : [])
        setShapData(shapRes.status === "fulfilled" ? shapRes.value?.data || [] : [])
      } catch (ex) {
        if (!alive) return
        setErr(String(ex?.message || ex))
      }
    }

    load()
    return () => {
      alive = false
    }
  }, [])

  const isHistorical = historicalMonths.includes(selectedForecastMonth)
  const showSubbar = page === "forecast" || page === "aspectNews"
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false)

  // ── All selectable months for keyboard nav (forecast + historical) ──
  const allSelectableMonths = React.useMemo(
    () => [...new Set([...availableFutureMonths, ...historicalMonths])].sort((a, b) => a.localeCompare(b)),
    [availableFutureMonths, historicalMonths]
  )

  // ── Keyboard navigation: ← → step through months, Escape closes mobile menu ──
  React.useEffect(() => {
    if (!showSubbar) return
    const onKey = (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return
      if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
        e.preventDefault()
        const idx = allSelectableMonths.indexOf(selectedForecastMonth)
        if (idx === -1) return
        const next =
          e.key === "ArrowRight"
            ? allSelectableMonths[Math.min(allSelectableMonths.length - 1, idx + 1)]
            : allSelectableMonths[Math.max(0, idx - 1)]
        if (next !== selectedForecastMonth) setSelectedForecastMonth(next)
      }
      if (e.key === "Escape") setMobileMenuOpen(false)
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [showSubbar, allSelectableMonths, selectedForecastMonth, setSelectedForecastMonth])

  // Close mobile menu on page change
  React.useEffect(() => { setMobileMenuOpen(false) }, [page])

  const tabs = [
    { id: "forecast", en: "Forecast & Reasoning", th: "การพยากรณ์และคำอธิบาย", Icon: TrendingUp },
    { id: "analytics", en: "News & Analytics", th: "ข้อมูลข่าวและการวิเคราะห์", Icon: BarChart3 },
  ]

  const pillStyle = (active) => ({
    padding: "3px 11px",
    borderRadius: 99,
    fontSize: 12,
    fontWeight: active ? 600 : 500,
    color: active ? "#fff" : "rgba(255,255,255,0.6)",
    background: active ? "rgba(255,255,255,0.18)" : "transparent",
    border: `1px solid ${active ? "rgba(255,255,255,0.4)" : "rgba(255,255,255,0.15)"}`,
    cursor: "pointer",
    whiteSpace: "nowrap",
    flexShrink: 0,
    transition: "all 0.15s",
  })

  return (
    <div className="min-h-screen" style={{ background: "#F0F4FA" }}>
      {/* ── Topbar ── */}
      <div
        className="sticky top-0 z-50 w-full"
        style={{ backgroundColor: THEME.navy, borderBottom: "1px solid rgba(255,255,255,0.08)" }}
      >
        {/* Main bar */}
        <div
          className="max-w-[1400px] mx-auto px-4 md:px-7 flex items-center justify-between gap-4 md:gap-6"
          style={{ height: 60 }}
        >
          {/* Brand */}
          <div className="flex items-center gap-2.5 flex-shrink-0">
            <div
              className="flex items-center justify-center rounded-lg flex-shrink-0"
              style={{ width: 35, height: 35, background: "rgba(255,255,255,0.15)" }}
            >
              <Activity className="text-white" style={{ width: 20, height: 20 }} />
            </div>
            <div className="leading-tight">
              <div className="text-white font-semibold" style={{ fontSize: 18 }}>
                XEconomic
              </div>
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.45)", marginTop: 1 }}>
                CCI Forecast &amp; XAI
              </div>
            </div>
          </div>

          {/* Desktop Tabs — hidden on mobile */}
          <div
            className="hidden md:flex items-center gap-0.5 rounded-[10px] p-[3px]"
            style={{ background: "rgba(255,255,255,0.08)" }}
          >
            {tabs.map(({ id, en, th, Icon }) => {
              const active = page === id || (page === "aspectNews" && id === "forecast")
              return (
                <button
                  key={id}
                  onClick={() => setPage(id)}
                  className="flex items-center gap-1.5 rounded-lg transition-all"
                  style={{
                    padding: "6px 16px",
                    fontSize: 13,
                    fontWeight: active ? 600 : 500,
                    background: active ? "#fff" : "transparent",
                    color: active ? THEME.navy : "rgba(255,255,255,0.6)",
                    border: "none",
                    cursor: "pointer",
                    whiteSpace: "nowrap",
                  }}
                >
                  <Icon style={{ width: 13, height: 13 }} />
                  {t(en, th)}
                </button>
              )
            })}
          </div>

          {/* Right side: lang toggle + hamburger */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {/* Language toggle */}
            <div
              className="flex items-center gap-0.5 rounded-lg p-[3px]"
              style={{ background: "rgba(255,255,255,0.08)" }}
            >
              {[["en", "EN"], ["th", "ไทย"]].map(([code, label]) => (
                <button
                  key={code}
                  onClick={() => setLang(code)}
                  style={{
                    padding: "4px 11px",
                    borderRadius: 6,
                    fontSize: 12,
                    fontWeight: 600,
                    background: lang === code ? "#fff" : "transparent",
                    color: lang === code ? THEME.navy : "rgba(255,255,255,0.55)",
                    border: "none",
                    cursor: "pointer",
                    transition: "all 0.15s",
                  }}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Hamburger — mobile only */}
            <button
              className="md:hidden flex flex-col justify-center items-center gap-1"
              onClick={() => setMobileMenuOpen((v) => !v)}
              aria-label="Menu"
              style={{
                width: 36, height: 36, background: "rgba(255,255,255,0.1)",
                border: "none", borderRadius: 8, cursor: "pointer", flexShrink: 0,
              }}
            >
              {mobileMenuOpen ? (
                <span style={{ color: "#fff", fontSize: 18, lineHeight: 1 }}>✕</span>
              ) : (
                <>
                  <span style={{ display: "block", width: 16, height: 2, background: "rgba(255,255,255,0.8)", borderRadius: 2 }} />
                  <span style={{ display: "block", width: 16, height: 2, background: "rgba(255,255,255,0.8)", borderRadius: 2 }} />
                  <span style={{ display: "block", width: 16, height: 2, background: "rgba(255,255,255,0.8)", borderRadius: 2 }} />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Mobile menu drawer */}
        {mobileMenuOpen && (
          <div
            className="md:hidden"
            style={{ background: "#1a4280", borderTop: "1px solid rgba(255,255,255,0.1)" }}
          >
            {tabs.map(({ id, en, th, Icon }) => {
              const active = page === id || (page === "aspectNews" && id === "forecast")
              return (
                <button
                  key={id}
                  onClick={() => setPage(id)}
                  className="flex items-center gap-3 w-full text-left"
                  style={{
                    padding: "14px 20px",
                    fontSize: 15,
                    fontWeight: active ? 600 : 400,
                    color: active ? "#fff" : "rgba(255,255,255,0.65)",
                    background: active ? "rgba(255,255,255,0.08)" : "transparent",
                    border: "none",
                    borderBottom: "1px solid rgba(255,255,255,0.06)",
                    cursor: "pointer",
                    width: "100%",
                  }}
                >
                  <Icon style={{ width: 16, height: 16 }} />
                  {t(en, th)}
                  {active && <span style={{ marginLeft: "auto", fontSize: 12, color: "#4ade80" }}>●</span>}
                </button>
              )
            })}
          </div>
        )}

        {/* Subbar */}
        {showSubbar && (
          <div style={{ background: "#1a4280", borderTop: "1px solid rgba(255,255,255,0.07)" }}>
            <div
              className="max-w-[1400px] mx-auto px-4 md:px-7 flex items-center"
              style={{ height: 44, gap: 0 }}
            >
              {/* Context pill — hidden on very small screens */}
              <div
                className="hidden sm:flex items-center gap-2 flex-shrink-0"
                style={{ paddingRight: 16, borderRight: "1px solid rgba(255,255,255,0.1)" }}
              >
                <div
                  className="rounded-full flex-shrink-0"
                  style={{
                    width: 6, height: 6,
                    background: isHistorical ? "rgba(255,255,255,0.35)" : "#4ade80",
                  }}
                />
                <span style={{ fontSize: 11, color: "rgba(255,255,255,0.5)", whiteSpace: "nowrap" }}>
                  {isHistorical ? t("History", "ประวัติ") : t("Forecast", "พยากรณ์")}
                </span>
                <span style={{ fontSize: 11, fontWeight: 600, color: "rgba(255,255,255,0.9)", whiteSpace: "nowrap" }}>
                  {monthLabel(selectedForecastMonth, lang)}
                </span>
              </div>

              {/* Month pills + historical dropdown */}
              <div
                className="flex items-center gap-1.5 overflow-x-auto"
                style={{ paddingLeft: 20, scrollbarWidth: "none" }}
              >
                <span style={{ fontSize: 11, fontWeight: 500, color: "rgba(255,255,255,0.4)", marginRight: 2, flexShrink: 0 }}>
                  {t("Forecast", "พยากรณ์")}
                </span>

                {availableFutureMonths.map((m) => (
                  <button
                    key={m}
                    onClick={() => setSelectedForecastMonth(m)}
                    style={pillStyle(m === selectedForecastMonth)}
                  >
                    {monthLabel(m, lang)}
                  </button>
                ))}

                {historicalMonths.length > 0 && (
                  <>
                    <div style={{ width: 1, height: 20, background: "rgba(255,255,255,0.12)", flexShrink: 0, margin: "0 6px" }} />
                    <span style={{ fontSize: 11, fontWeight: 500, color: "rgba(255,255,255,0.4)", flexShrink: 0 }}>
                      {t("Historical", "ย้อนหลัง")}
                    </span>
                    <select
                      value={isHistorical ? selectedForecastMonth : ""}
                      onChange={(e) => { if (e.target.value) setSelectedForecastMonth(e.target.value) }}
                      style={{
                        background: "transparent",
                        border: "1px solid rgba(255,255,255,0.15)",
                        borderRadius: 99,
                        color: "rgba(255,255,255,0.6)",
                        fontSize: 12,
                        fontWeight: 500,
                        padding: "3px 11px",
                        cursor: "pointer",
                        outline: "none",
                        flexShrink: 0,
                      }}
                    >
                      <option value="" style={{ background: THEME.navy }}>
                        {t("Select month…", "เลือกเดือน…")}
                      </option>
                      {historicalMonths.map((m) => (
                        <option key={m} value={m} style={{ background: THEME.navy }}>
                          {monthLabel(m, lang)}
                        </option>
                      ))}
                    </select>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Page content ── */}
      <div className="max-w-[1400px] mx-auto px-4 md:px-7 py-5 md:py-6 space-y-5">
        {err && (
          <div
            className="rounded-xl px-4 py-2.5 text-sm flex items-center gap-2"
            style={{ background: "#FEF2F2", border: "1px solid #FECACA", color: "#B91C1C" }}
          >
            <span>⚠️</span> {err}
          </div>
        )}

        {page === "forecast" && (
          <ForecastPage
            t={t}
            lang={lang}
            series={series}
            summary={summary}
            allExplain={allExplain}
            news={newsReal}
            selectedForecastMonth={selectedForecastMonth}
            setSelectedForecastMonth={setSelectedForecastMonth}
            availableFutureMonths={availableFutureMonths}
            historicalMonths={historicalMonths}
            onSelectAspect={(asp) => {
              setSelectedAspect(asp)
              setPage("aspectNews")
            }}
          />
        )}

        {page === "analytics" && (
          <AnalyticsPage t={t} lang={lang} news={newsReal} shapData={shapData} />
        )}

        {page === "aspectNews" && (
          <AspectNewsPage
            t={t}
            lang={lang}
            aspect={selectedAspect}
            news={newsReal}
            onBack={() => setPage("forecast")}
          />
        )}
      </div>
    </div>
  )
}