import React from "react"
import "./index.css"
import { getSummary, getTimeSeries, getNews, getShap, getAllExplain, getAllExplainEN } from "./api.js"
import { getNewsSentimentFromCSV, getAgencyVolumeFromCSV } from "./newsFileApi"
import { getAgencyVolumeLastNMonths } from "./newsSupabaseApi"
import { TrendingUp, Activity, BarChart3, Search, RotateCcw } from "lucide-react"
import InteractiveWordCloud from "./InteractiveWordCloud.jsx"
import forecastsummary from "./assets/forecastsummary.svg"
import summaryicon from "./assets/summary.svg"
import forecastchart from "./assets/forecastchart.svg"
import reasoningpanel from "./assets/reasoning_panel.svg"
import summary2 from "./assets/summary2.svg"
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
  navy: "#122040",       // topbar, subbar bg, badges
  blue: "#056596",       // primary accent — icons, links, actual line, borders
  blueSoft: "#EEF4FF",   // light blue bg for icon boxes, soft fills
  blueCard: "#F4F7FC",   // card inner backgrounds
  success: "#059669",    // up direction, forecast line
  danger: "#D64545",     // down direction
  gray: "#6B7280",       // stable/neutral
  border: "#DDE4EF",     // all borders
  pageBg: "#EEF2F8",     // page background
  subbar: "#1a3260",     // subbar background
  textPrimary: "#1E2F47",// card titles, main text
  textMuted: "#8A9BB8",  // subtitles, labels
  textHint: "#A0B0C8",   // hints, placeholder
  white: "#FFFFFF",        // white
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
const ASPECT_EN = {
  "เศรษฐกิจไทย": "Thai Economy",
  "มาตรการของรัฐ": "Government Policy",
  "การเมือง": "Politics",
  "ราคาสินค้าเกษตร": "Agricultural Prices",
  "สังคม/ความมั่นคง": "Social/Security",
  "เศรษฐกิจโลก": "Global Economy",
  "ราคาน้ำมันเชื้อเพลิง": "Fuel Prices",
  "ภัยพิบัติ/โรคระบาด": "Disaster/Epidemic",
}

// ── Wong colorblind-friendly palette for aspect topics ──
const WONG = {
  "Thai Economy": "#009E73",
  "Government Policy": "#0072B2",
  "Politics": "#D55E00",
  "Agricultural Prices": "#E69F00",
  "Social/Security": "#CC79A7",
  "Global Economy": "#56B4E9",
  "Fuel Prices": "#F0E442",
  "Disaster/Epidemic": "#000000",
}

const EFFECT_COLORS = {
  "Short-term": "#E69F00",
  "Long-term": "#0072B2",
}

const IMPACT_COLORS = {
  "Negative": "#D55E00",
  "Neutral": "#56B4E9",
  "Positive": "#009E73",
}

/** Get the Wong color for a Thai aspect name */
function getAspectColor(thaiName) {
  const en = ASPECT_EN[thaiName]
  return en ? (WONG[en] || CHART_COLORS[0]) : CHART_COLORS[0]
}
// ── Skeleton shimmer component ──
const Skeleton = ({ className = "", style = {} }) => (
  <div
    className={`rounded-lg ${className}`}
    style={{
      background: `linear-gradient(90deg, ${THEME.border} 25%, #F8FAFC 50%, ${THEME.border} 75%)`,
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
    @keyframes fade-in { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
    .xecon-fade-in { animation: fade-in 0.35s ease both; }
    .xecon-aspect-btn:hover { background: #EEF3FB !important; transform: translateX(2px); }
    .xecon-aspect-btn { transition: background 0.15s, transform 0.15s, box-shadow 0.15s; cursor: pointer; }
    .xecon-aspect-btn:hover .xecon-arrow { opacity: 1 !important; transform: translateX(2px); }
    .xecon-arrow { transition: opacity 0.15s, transform 0.15s; }
    .xecon-news-row:hover { background: THEME.blueCard; }
    .xecon-news-row { transition: background 0.12s; }
    * { font-size: inherit; }
    body, #root { font-size: 14px; }
    h1 { font-size: 22px; }
    h2 { font-size: 18px; }
    h3 { font-size: 16px; }
  `
  document.head.appendChild(style)
}

// ── Empty state component ──
const EmptyState = ({ icon, title, description, action }) => (
  <div className="flex flex-col items-center justify-center py-14 text-center xecon-fade-in">
    <div
      className="flex items-center justify-center rounded-2xl mb-4"
      style={{ width: 56, height: 56, background: THEME.blueCard, color: THEME.blue, fontSize: 26 }}
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

const SectionHeader = ({ title, subtitle, icon: Icon }) => (
  <div className="flex flex-col gap-1 mb-6 mt-4">
    <div className="flex items-center gap-2.5">
      {Icon && (
        <div
          className="flex items-center justify-center rounded-lg flex-shrink-0"
          style={{ width: 28, height: 28, background: THEME.blueSoft }}
        >
          <Icon className="w-4 h-4" style={{ color: THEME.blue }} />
        </div>
      )}
      <span className="text-lg font-medium" style={{ color: THEME.textPrimary }}>{title}</span>
    </div>
    {subtitle && <p className="text-xs" style={{ color: THEME.textMuted, paddingLeft: 38 }}>{subtitle}</p>}
  </div>
)

const CardTitle = ({ children, className = "" }) => (
  <h3 className={`text-base font-semibold text-gray-900 ${className}`}>
    {children}
  </h3>
)

const CardDescription = ({ children, className = "" }) => (
  <p className={`text-sm text-gray-500 mt-1 ${className}`}>{children}</p>
)

const CardContent = ({ children, className = "" }) => <div className={`p-6 ${className}`}>{children}</div>

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

function engMonthYear(dateLike) {
  if (!dateLike) return "-"
  const d = new Date(dateLike.length === 7 ? `${dateLike}-01` : dateLike)
  if (Number.isNaN(d.getTime())) return String(dateLike)

  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
  return `${months[d.getMonth()]} ${d.getFullYear()}`
}

function thaiDateShort(dateStr) {
  const d = new Date(dateStr)
  if (Number.isNaN(d.getTime())) return String(dateStr || "")

  const months = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
  return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`
}

function monthLabel(dateStr, lang) {
  if (!dateStr) return "-"

  const d = new Date(dateStr.length === 7 ? `${dateStr}-01` : dateStr)
  if (Number.isNaN(d.getTime())) return String(dateStr)
  if (lang === "th") return thaiMonthYear(dateStr)

  const monthsEN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

  return `${monthsEN[d.getMonth()]} ${d.getFullYear()}`
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
  const totals = {}

  items.forEach((n) => {
    const monthKey = n.date?.slice(0, 7)
    const group = getGroupKey(n)
    if (!monthKey || !group) return

    groupSet.add(group)
    if (!monthMap[monthKey]) monthMap[monthKey] = {}
    monthMap[monthKey][group] = (monthMap[monthKey][group] || 0) + 1
    totals[group] = (totals[group] || 0) + 1
  })

  const groups = groupsOverride ? [...groupsOverride] : [...groupSet]
  groups.sort((a, b) => (totals[b] || 0) - (totals[a] || 0))
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
  const totals = {}

  rows.forEach((r) => {
    const month = r.month
    const agency = r.agency || "Unknown"

    // กรอง Thai PBS ออกจากกราฟตามที่คุณจีนต้องการ
    if (agency.toLowerCase().includes("thaipbs") || agency.includes("ไทยพีบีเอส")) return;

    const count = Number(r.count || 0)

    groupsSet.add(agency)
    if (!monthMap[month]) monthMap[month] = {}
    monthMap[month][agency] = (monthMap[month][agency] || 0) + count
    totals[agency] = (totals[agency] || 0) + count
  })

  const groups = [...groupsSet].sort((a, b) => totals[b] - totals[a])
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

function ForecastXAxisTick({ x, y, payload, lang, compact }) {
  const raw = payload?.value
  const d = new Date(raw)

  if (Number.isNaN(d.getTime())) {
    return (
      <g transform={`translate(${x},${y})`}>
        <text x={0} y={0} dy={12} textAnchor="middle" fill={THEME.gray} fontSize={10}>
          {String(raw || "")}
        </text>
      </g>
    )
  }

  const monthTH = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
  const monthEN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
  const month = lang === "th" ? monthTH[d.getMonth()] : monthEN[d.getMonth()]
  const year = lang === "th" ? String(d.getFullYear() + 543) : String(d.getFullYear())

  if (compact) {
    return (
      <g transform={`translate(${x},${y})`}>
        <text textAnchor="middle" fill={THEME.gray} fontSize={9}>
          <tspan x="0" dy="12">{month}</tspan>
          <tspan x="0" dy="11">{year}</tspan>
        </text>
      </g>
    )
  }

  return (
    <g transform={`translate(${x},${y})`}>
      <text textAnchor="middle" fill={THEME.gray} fontSize={10}>
        <tspan x="0" dy="12">{month}</tspan>
        <tspan x="0" dy="14">{year}</tspan>
      </text>
    </g>
  )
}

function ForecastPageSkeleton() {
  return (
    <div className="space-y-5">
      {/* Summary card row */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="lg:col-span-3 bg-white rounded-2xl border p-6" style={{ borderColor: THEME.border }}>
          <div className="flex items-center gap-2.5 mb-2 mt-2">
            <Skeleton style={{ width: 36, height: 36, borderRadius: 9 }} />
            <Skeleton style={{ height: 18, width: 260 }} />
          </div>
          <Skeleton className="mb-5" style={{ height: 12, width: 140, marginLeft: 46 }} />
          <div className="grid grid-cols-2 gap-3">
            <Skeleton style={{ height: 110, borderRadius: 12 }} />
            <Skeleton style={{ height: 110, borderRadius: 12 }} />
          </div>
        </div>
        <div className="lg:col-span-2 bg-white rounded-2xl border p-6" style={{ borderColor: THEME.border }}>
          <div className="flex items-center gap-2.5 mb-4">
            <Skeleton style={{ width: 36, height: 36, borderRadius: 9 }} />
            <Skeleton style={{ height: 18, width: 120 }} />
          </div>
          <Skeleton style={{ height: 12, width: "90%" }} className="mb-2" />
          <Skeleton style={{ height: 12, width: "80%" }} className="mb-2" />
          <Skeleton style={{ height: 12, width: "85%" }} className="mb-2" />
          <Skeleton style={{ height: 12, width: "60%" }} />
        </div>
      </div>

      {/* Chart */}
      <div className="bg-white rounded-2xl border p-6" style={{ borderColor: THEME.border }}>
        <div className="flex items-center gap-2.5 mb-4">
          <Skeleton style={{ width: 36, height: 36, borderRadius: 9 }} />
          <Skeleton style={{ height: 18, width: 220 }} />
        </div>
        <Skeleton style={{ height: 420, borderRadius: 12 }} />
      </div>

      {/* Reasoning panel */}
      <div className="bg-white rounded-2xl border p-6" style={{ borderColor: THEME.border }}>
        <div className="flex items-center gap-2.5 mb-6">
          <Skeleton style={{ width: 36, height: 36, borderRadius: 9 }} />
          <Skeleton style={{ height: 18, width: 200 }} />
        </div>
        <div className="flex gap-6">
          <div style={{ flex: "0 0 70%" }} className="flex flex-col gap-3">
            <Skeleton style={{ height: 80, borderRadius: 12 }} />
            <Skeleton style={{ height: 80, borderRadius: 12 }} />
            <Skeleton style={{ height: 80, borderRadius: 12 }} />
          </div>
          <div style={{ flex: "0 0 30%" }} className="flex flex-col gap-3">
            <Skeleton style={{ height: 14, width: 100 }} className="mb-1" />
            {[1, 2, 3, 4, 5].map(i => <Skeleton key={i} style={{ height: 38, borderRadius: 10 }} />)}
          </div>
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
  dataLoaded,
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
    () =>
      allExplain.find(
        (r) => String(r.date || "").slice(0, 7) === selectedForecastMonth
      ) || null,
    [allExplain, selectedForecastMonth]
  )

  const selectedSeriesRow = React.useMemo(
    () => series.find((r) => r.date?.slice(0, 7) === selectedForecastMonth) || null,
    [series, selectedForecastMonth]
  )

  const isLoading = !dataLoaded
  if (isLoading) return <ForecastPageSkeleton />

  return (
    <div className="space-y-5">
      <ForecastSummaryCard
        t={t}
        lang={lang}
        month={selectedForecastMonth}
        predicted={selectedSeriesRow?.pred}
        direction={selectedSeriesRow?.direction}
        comparisonValue={selectedSeriesRow?.compare_value}
        comparisonBasis={selectedSeriesRow?.compare_basis}
        conclusion={activeRow?.conclusion || summary?.conclusion || summary?.summary || ""}
      />

      <ForecastChart
        t={t}
        lang={lang}
        series={series}
        selectedMonth={selectedForecastMonth}
      />

      <ReasoningPanel
        t={t}
        lang={lang}
        activeRow={activeRow}
        selectedMonth={selectedForecastMonth}
        news={news}
        onSelectAspect={onSelectAspect}
      />

      {/* <TopAspectsOnlyCard
        t={t}
        news={news}
        onSelectAspect={onSelectAspect}
        selectedForecastMonth={selectedForecastMonth}
        lang={lang}
      /> */}
    </div>
  )
}

function ForecastSummaryCard({
  t,
  lang,
  month,
  predicted,
  direction,
  comparisonValue,
  comparisonBasis,
  conclusion,
}) {
  const info = normalizeDirection(direction, t)
  const arrow = info.tone === "up" ? "↑" : info.tone === "down" ? "↓" : "→"

  const showDelta =
    predicted != null &&
    comparisonValue != null &&
    Number(comparisonValue) !== 0

  const delta = showDelta ? Number(predicted) - Number(comparisonValue) : 0
  const pct = showDelta ? (delta / Math.abs(Number(comparisonValue))) * 100 : 0
  const isPos = delta >= 0

  const prevMonthLabel = React.useMemo(() => {
    if (!month) return ""
    const [year, mon] = String(month).split("-").map(Number)
    if (!year || !mon) return ""
    const prevDate = new Date(year, mon - 2, 1)
    const prevKey = `${prevDate.getFullYear()}-${String(prevDate.getMonth() + 1).padStart(2, "0")}`
    return monthLabel(prevKey, lang)
  }, [month, lang])

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
      {/* ── CCI card (3 cols) ── */}
      <div
        className="lg:col-span-3 bg-white rounded-2xl border p-6"
        style={{ borderColor: THEME.border }}
      >
        {/* Header with rising-bar icon */}
        <div className="flex items-center gap-2.5 mb-1 mt-2">
          <div
            className="flex items-center justify-center rounded-lg flex-shrink-0" style={{ width: 28, height: 28, background: THEME.blueSoft }}>
            <img src={forecastsummary} width="20" height="20" alt="" />
          </div>
          <span className="text-lg font-medium" style={{ color: THEME.textPrimary }}>
            {t("Consumer Confidence Forecast", "ค่าพยากรณ์ดัชนีความเชื่อมั่นผู้บริโภค (CCI)")}
          </span>
        </div>
        <div className="text-xs mb-5" style={{ color: THEME.textMuted, paddingLeft: 38 }}>
          {t("Forecast Month", "เดือนพยากรณ์")} · {monthLabel(month, lang)}
        </div>

        <div className="grid grid-cols-2 gap-3">
          {/* Actual box */}
          <div
            className="rounded-xl p-4 border flex flex-col gap-2"
            style={{ background: THEME.blueSoft, borderColor: THEME.border }}
          >
            <div className="text-xs font-semibold" style={{ color: THEME.blue }}>
              {comparisonBasis === "predicted"
                ? t("Forecast value —", "ค่าพยากรณ์ของ")
                : t("Actual data —", "ค่าจริง")}{" "}
              {prevMonthLabel}
            </div>
            <div className="text-[38px] font-semibold leading-none" style={{ color: THEME.blue }}>
              {comparisonValue != null ? Number(comparisonValue).toFixed(1) : "—"}
            </div>
            <div className="text-xs mt-1" style={{ color: THEME.blue }}>
              {t("Latest recorded value", "ข้อมูลจริงเดือนล่าสุด")}
            </div>
          </div>

          {/* Forecast box */}
          <div
            className="rounded-xl p-4 border flex flex-col gap-2"
            style={{
              background: info.tone === "down" ? "rgba(214,69,69,0.06)" : info.tone === "up" ? "rgba(5,150,105,0.06)" : THEME.blueCard,
              borderColor: info.tone === "down" ? "rgba(214,69,69,0.3)" : info.tone === "up" ? "rgba(5,150,105,0.3)" : THEME.border,
            }}
          >
            <div className="text-xs font-medium" style={{ color: info.tone === "down" ? THEME.danger : info.tone === "up" ? THEME.success : THEME.gray }}>
              {t("Forecast —", "พยากรณ์")} <span style={{ fontWeight: 600 }}>{monthLabel(month, lang)}</span>
            </div>
            <div className="text-[38px] font-semibold leading-none" style={{ color: info.tone === "down" ? THEME.danger : info.tone === "up" ? THEME.success : THEME.textPrimary }}>
              {predicted != null ? Number(predicted).toFixed(1) : "—"}
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <span
                className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium"
                style={{
                  background: info.tone === "down" ? "rgba(214,69,69,0.15)" : info.tone === "up" ? "rgba(5,150,105,0.15)" : THEME.blueCard,
                  color: info.tone === "down" ? THEME.danger : info.tone === "up" ? THEME.success : THEME.gray,
                  border: `1px solid ${info.tone === "down" ? "rgba(214,69,69,0.3)" : info.tone === "up" ? "rgba(5,150,105,0.3)" : THEME.border}`,
                }}
              >
                {arrow} {info.tone === "up"
                  ? t("Increase", "เพิ่มขึ้น")
                  : info.tone === "down"
                    ? t("Decrease", "ลดลง")
                    : t("Stable", "ทรงตัว")}
              </span>
              {showDelta && (
                <span className="text-xs" style={{ color: THEME.textMuted }}>
                  {isPos ? "+" : ""}{delta.toFixed(1)} ({isPos ? "+" : ""}{pct.toFixed(1)}%)
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── Summary card (2 cols) ── */}
      <SummaryCard t={t} conclusion={conclusion} />
    </div>
  )
}

function SummaryCard({ t, conclusion }) {
  return (
    <div
      className="lg:col-span-2 rounded-2xl border p-6 flex flex-col gap-3"
      style={{ background: THEME.white, borderColor: THEME.border }}
    >
      <div className="flex items-center gap-2.5 mb-1 mt-2">
        <div
          className="flex items-center justify-center rounded-lg flex-shrink-0"
          style={{ width: 28, height: 28, background: THEME.blueSoft }}
        >
          {/* <svg width="15" height="15" viewBox="0 0 22 22" fill="none">
            <rect x="3" y="2" width="10" height="16" rx="1.5" fill="rgba(5,101,150,0.06)" stroke={THEME.blue} strokeWidth="1.3" />
            <line x1="5.5" y1="6" x2="10.5" y2="6" stroke={THEME.blue} strokeWidth="1.1" strokeLinecap="round" opacity="0.5" />
            <line x1="5.5" y1="9" x2="10.5" y2="9" stroke={THEME.blue} strokeWidth="1.1" strokeLinecap="round" opacity="0.5" />
            <line x1="5.5" y1="12" x2="8.5" y2="12" stroke={THEME.blue} strokeWidth="1.1" strokeLinecap="round" opacity="0.5" />
            <path d="M12 12 L18 6 L20 8 L14 14 L11 15 Z" fill="rgba(5,101,150,0.12)" stroke={THEME.blue} strokeWidth="1.2" strokeLinejoin="round" />
            <line x1="16" y1="8" x2="18" y2="10" stroke={THEME.blue} strokeWidth="1" />
          </svg> */}
          <img src={summary2} width="17" height="17" alt="" />
        </div>
        <span className="text-lg font-medium" style={{ color: THEME.textPrimary }}>
          {t("Overview", "ภาพรวมรายงาน")}
        </span>
      </div>

      <div className="flex flex-col justify-start flex-1 pt-5">
        {conclusion ? (
          <p className="text-sm leading-7" style={{ color: THEME.textPrimary }}>
            {conclusion}
          </p>
        ) : (
          <p className="text-sm" style={{ color: THEME.textHint }}>—</p>
        )}
      </div>
    </div>
  )
}

function ForecastChart({ t, lang, series, selectedMonth }) {
  const [activeRange, setActiveRange] = React.useState("2y")

  const filteredSeries = React.useMemo(() => {
    if (!series || series.length === 0) return []
    return [...series].sort((a, b) => String(a.date).localeCompare(String(b.date)))
  }, [series])

  const chartData = React.useMemo(
    () => buildSelectedMonthChartData(filteredSeries, selectedMonth),
    [filteredSeries, selectedMonth]
  )

  const lastActualDate = React.useMemo(() => {
    const actualRows = filteredSeries.filter((s) => s.actual != null)
    return actualRows.length ? actualRows[actualRows.length - 1].date : null
  }, [filteredSeries])

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
    if (!values.length) return [30, 80]
    const min = Math.min(...values)
    const max = Math.max(...values)
    const floor = Math.floor((min - 3) / 5) * 5
    const ceil = Math.ceil((max + 3) / 5) * 5
    return [floor, ceil]
  }, [chartData])

  // Generate explicit tick values as multiples of 5
  const yTicks = React.useMemo(() => {
    const [floor, ceil] = yDomain
    const ticks = []
    for (let v = floor; v <= ceil; v += 5) ticks.push(v)
    return ticks
  }, [yDomain])

  const rangeIndexes = React.useMemo(() => {
    const len = chartData.length
    if (!len) return { startIndex: 0, endIndex: 0 }
    const lastIndex = len - 1
    if (activeRange === "1y") return { startIndex: Math.max(0, len - 15), endIndex: lastIndex }
    if (activeRange === "2y") return { startIndex: Math.max(0, len - 24), endIndex: lastIndex }
    return { startIndex: 0, endIndex: lastIndex }
  }, [chartData, activeRange])

  const [brushRange, setBrushRange] = React.useState(rangeIndexes)

  React.useEffect(() => {
    setBrushRange(rangeIndexes)
  }, [rangeIndexes.startIndex, rangeIndexes.endIndex])

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
    const max = Math.max(...values)
    const ceil = Math.ceil((max + 3) / 5) * 5
    return [yDomain[0], ceil]
  }, [visibleData, yDomain])

  // Ticks for visible range — still multiples of 5
  const visibleYTicks = React.useMemo(() => {
    const [floor, ceil] = visibleYDomain
    const ticks = []
    for (let v = floor; v <= ceil; v += 5) ticks.push(v)
    return ticks
  }, [visibleYDomain])

  const rangeButtons = [
    { key: "1y", en: "1 Year", th: "1 ปี" },
    { key: "2y", en: "2 Years", th: "2 ปี" },
    { key: "all", en: "All", th: "ทั้งหมด" },
  ]

  const xAxisInterval = activeRange === "all"
    ? Math.max(1, Math.floor(visibleData.length / 14))
    : 0

  const xAxisTicks = React.useMemo(() => {
    if (!visibleData.length) return []
    if (activeRange === "all") return visibleData
      .filter((_, i) => i % Math.max(1, Math.floor(visibleData.length / 14)) === 0)
      .map((d) => d.date)
    if (activeRange === "2y") return visibleData
      .map((d) => d.date)
    if (activeRange === "1y") return visibleData
      .filter((_, i) => visibleData.length <= 16 || i % 2 === 0)
      .map((d) => d.date)
    return visibleData.map((d) => d.date)
  }, [visibleData, activeRange])

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-2.5">
            <div
              className="flex items-center justify-center rounded-lg flex-shrink-0"
              style={{ width: 28, height: 28, background: THEME.blueSoft, alignSelf: "flex-start", marginTop: 2 }}
            >
              {/* <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
                <polyline points="1,11 4,7 7,9 10,4 14,6" stroke={THEME.blue} strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
                <line x1="1" y1="13" x2="14" y2="13" stroke={THEME.blue} strokeWidth="1.2" strokeLinecap="round" />
              </svg> */}
              <img src={forecastchart} width="20" height="20" alt="" />

            </div>
            <div>
              <div className="text-lg font-medium" style={{ color: THEME.blueDark }}>
                {t("Consumer Confidence Index Forecast Trend", "กราฟค่าดัชนีความเชื่อมั่นผู้บริโภค (CCI)")}
              </div>
              <div className="text-xs mt-1" style={{ color: THEME.textMuted }}>
                {t("Comparing actual recorded data to forecast values", "เปรียบเทียบค่าจริงและค่าพยากรณ์")}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex gap-1" style={{ background: THEME.blueSoft, borderRadius: 8, padding: 3 }}>
              {rangeButtons.map(({ key, en, th }) => (
                <button
                  key={key}
                  onClick={() => setActiveRange(key)}
                  style={{
                    padding: "4px 12px", borderRadius: 6, fontSize: 12,
                    fontWeight: activeRange === key ? 500 : 400, border: "none",
                    cursor: "pointer",
                    background: activeRange === key ? THEME.navy : "transparent",
                    color: activeRange === key ? THEME.white : THEME.gray,
                    transition: "all 0.15s",
                  }}
                >
                  {t(en, th)}
                </button>
              ))}
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="w-full bg-white" style={{ borderRadius: 12 }}>
          <div style={{ height: 420 }}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={visibleData}
                margin={{ top: 20, right: 20, left: 10, bottom: 10 }}
              >
                <CartesianGrid stroke={THEME.border} horizontal={true} vertical={false} strokeOpacity={0.6} />

                <XAxis
                  dataKey="date"
                  height={55}
                  ticks={xAxisTicks}
                  interval={0}
                  minTickGap={activeRange === "2y" ? -20 : activeRange === "1y" ? -50 : 0}
                  tickMargin={8}
                  tick={<ForecastXAxisTick lang={lang} compact={activeRange === "1y"} />}
                  axisLine={{ stroke: THEME.textPrimary }}
                  tickLine={false}
                />

                <YAxis
                  tick={{ fontSize: 11 }}
                  domain={visibleYDomain}
                  ticks={visibleYTicks}
                  axisLine={{ stroke: THEME.textPrimary }}
                  tickLine={false}
                  allowDataOverflow={true}
                  width={45}
                />
                <ReTooltip
                  content={({ active, payload, label }) => {
                    if (!active || !payload?.length) return null
                    const actualItem = payload.find((p) => p.dataKey === "actual")
                    const predItem = payload.find((p) => p.dataKey === "pred")
                    return (
                      <div className="rounded-xl border bg-white p-3 shadow-lg" style={{ borderColor: THEME.border }}>
                        <div className="text-sm font-semibold text-gray-900 mb-1">
                          {monthLabel(label, lang)}
                        </div>
                        {actualItem?.value != null ? (
                          <div className="text-sm" style={{ color: THEME.blue }}>
                            {t("Actual", "ค่าจริง")}: {Number(actualItem.value).toFixed(2)}
                          </div>
                        ) : null}
                        {predItem?.value != null ? (
                          <div className="text-sm" style={{ color: THEME.success }}>
                            {t("Forecast", "ค่าพยากรณ์")}: {Number(predItem.value).toFixed(2)}
                          </div>
                        ) : null}
                      </div>
                    )
                  }}
                />
                <Legend verticalAlign="top" height={40} />
                {lastActualDate && visibleData[visibleData.length - 1]?.date ? (
                  <ReferenceArea
                    x1={lastActualDate}
                    x2={visibleData[visibleData.length - 1]?.date}
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
                      value: t("Selected period", "เดือนที่เลือก"),
                      position: "insideTopRight",
                      fontSize: 11,
                      fill: THEME.blue,
                    }}
                  />
                ) : null}
                <Line
                  type="monotone"
                  dataKey="actual"
                  stroke={THEME.blue}
                  strokeWidth={2.5}
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                  name={t("Actual", "ค่าจริง")}
                  connectNulls={false}
                />
                <Line
                  type="monotone"
                  dataKey="pred"
                  stroke={THEME.success}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                  strokeDasharray="6 4"
                  name={t("Forecast", "ค่าพยากรณ์")}
                  connectNulls={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          <div className="border-t px-4 py-1 bg-white" style={{ borderColor: THEME.border }}>
            <div style={{ width: "100%", height: 60 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <XAxis dataKey="date" hide />
                  <YAxis hide domain={yDomain} ticks={yTicks} />
                  <Brush
                    dataKey="date"
                    height={28}
                    travellerWidth={10}
                    gap={Math.max(1, Math.floor(chartData.length / 14))}
                    startIndex={brushRange.startIndex}
                    endIndex={brushRange.endIndex}
                    onChange={(range) => {
                      if (range && typeof range.startIndex === "number" && typeof range.endIndex === "number") {
                        setBrushRange({ startIndex: range.startIndex, endIndex: range.endIndex })
                        setActiveRange("all")
                      }
                    }}
                    tickFormatter={(v) => lang === "th" ? thaiMonthYear(v) : engMonthYear(v)}
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



function ReasoningPanel({ t, lang, activeRow, selectedMonth, news, onSelectAspect }) {
  const getPrevious3Months = React.useCallback((targetMonth) => {
    if (!targetMonth) return []
    const [year, month] = targetMonth.split("-").map(Number)
    const base = new Date(year, month - 1, 1)
    const months = []
    for (let i = 3; i >= 1; i--) {
      const d = new Date(base)
      d.setMonth(d.getMonth() - i)
      months.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`)
    }
    return months
  }, [])

  const ranked = React.useMemo(() => {
    const backwardMonths = getPrevious3Months(selectedMonth)
    const filteredNews = (news || []).filter((n) => backwardMonths.includes(String(n.date || "").slice(0, 7)))
    const counts = {}
    filteredNews.forEach((n) => {
      const aspect = n.aspect || "Other"
      counts[aspect] = (counts[aspect] || 0) + 1
    })
    return Object.entries(counts)
      .map(([aspect, count]) => ({ aspect, count }))
      .sort((a, b) => b.count - a.count)
  }, [news, selectedMonth, getPrevious3Months])

  return (
    <Card className="overflow-hidden w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex items-center justify-center rounded-lg flex-shrink-0" style={{ width: 28, height: 28, background: THEME.blueSoft, alignSelf: "flex-start" }}>
              {/* <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 1 L7.8 6.2 L13 7 L7.8 7.8 L7 13 L6.2 7.8 L1 7 L6.2 6.2 Z" fill="none" stroke={THEME.blue} strokeWidth="1.6" strokeLinejoin="round" />
              </svg> */}
              <img src={reasoningpanel} width="20" height="20" alt="" />
            </div>
            <div>
              <span className="text-lg font-medium" style={{ color: THEME.textPrimary }}>
                {t("Key Factors", "ปัจจัยหลักของการพยากรณ์")}
              </span>
              <p className="text-xs mt-0.5" style={{ color: THEME.textMuted }}>
                {t("Description:", "คำอธิบายเดือน:")} {monthLabel(selectedMonth, lang)}
              </p>
            </div>

          </div>
        </div>
      </CardHeader>

      <CardContent>
        {activeRow ? (
          <div className="flex gap-0">
            {/* LEFT — factors */}
            <div
              className="flex flex-col gap-3 pr-6"
              style={{ flex: "0 0 75%", paddingTop: 27, paddingRight: 20 }}
            >
              {activeRow?.factors?.length > 0
                ? activeRow.factors.map((f, idx) => (
                  <div
                    key={idx}
                    className="flex gap-3 rounded-xl p-4 border"
                    style={{ background: THEME.blueSoft, borderColor: THEME.border }}
                  >
                    <div
                      className="flex items-center justify-center rounded-lg flex-shrink-0 mt-0.5"
                      style={{
                        width: 24,
                        height: 24,
                        background: THEME.navy,
                        color: THEME.white,
                        fontSize: 12,
                        fontWeight: 500
                      }}
                    >
                      {idx + 1}
                    </div>

                    <p className="text-sm leading-7" style={{ color: THEME.textPrimary }}>
                      {f.text}
                    </p>
                  </div>
                ))
                : <div className="text-sm text-gray-400 py-4">—</div>}
            </div>

            {/* RIGHT — aspect */}
            <div
              style={{
                flex: "0 0 21%",
                marginLeft: 20,
                borderLeft: `1px solid ${THEME.border}`,
                paddingLeft: 37,
                display: "flex",
                flexDirection: "column",
                gap: 8,
              }}
            >
              <p
                className="text-xs font-medium tracking-wider"
                style={{
                  color: THEME.textMuted,
                  height: 20,
                  display: "flex",
                  alignItems: "center"
                }}
              >
                {t("Explore news by topic", "ดูข่าวตามประเด็น")}
              </p>

              {ranked.length === 0 ? (
                <p className="text-xs" style={{ color: THEME.textHint }}>—</p>
              ) : (
                ranked.map(({ aspect, count }) => (
                  <button
                    key={aspect}
                    onClick={() => onSelectAspect?.(aspect)}
                    className="w-full text-left rounded-xl border"
                    style={{
                      padding: "9px 14px",
                      background: THEME.blueSoft,
                      borderColor: THEME.border,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: 8,
                      transition: "background 0.12s, border-color 0.12s",
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.background = THEME.blueCard
                      e.currentTarget.style.borderColor = THEME.blue
                      e.currentTarget.querySelector(".aspect-arrow").style.opacity = "1"
                      e.currentTarget.querySelector(".aspect-arrow").style.transform = "translateX(3px)"
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.background = THEME.blueSoft
                      e.currentTarget.style.borderColor = THEME.border
                      e.currentTarget.querySelector(".aspect-arrow").style.opacity = "0"
                      e.currentTarget.querySelector(".aspect-arrow").style.transform = "translateX(0)"
                    }}
                  >
                    <span style={{ fontSize: 12, color: THEME.textPrimary, fontWeight: 400 }}>
                      {lang === "en" ? (ASPECT_EN[aspect] ?? aspect) : aspect}
                    </span>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, flexShrink: 0 }}>
                      <span
                        style={{
                          fontSize: 12,
                          fontWeight: 600,
                          color: THEME.blue,
                          background: "rgba(47,111,237,0.12)",
                          minWidth: 38,
                          height: 22,
                          display: "inline-flex",
                          alignItems: "center",
                          justifyContent: "center",
                          borderRadius: 99,
                          padding: "0 8px",
                        }}
                      >
                        {count}
                      </span>
                      <span
                        className="aspect-arrow"
                        style={{
                          fontSize: 13,
                          color: THEME.blue,
                          opacity: 0,
                          transition: "opacity 0.15s, transform 0.15s",
                          transform: "translateX(0)",
                          lineHeight: 1,
                        }}
                      >
                        →
                      </span>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        ) : (
          <div className="text-center py-10 text-sm" style={{ color: THEME.textHint }}>
            {t("No analysis available for this period", "ไม่พบคำอธิบาย")}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

const PER_PAGE = 15

function AspectNewsPage({ t, lang, aspect, news = [], onBack, selectedForecastMonth }) {
  const [currentPage, setCurrentPage] = React.useState(1)
  const [search, setSearch] = React.useState("")

  const backwardMonths = React.useMemo(() => {
    if (!selectedForecastMonth) return null
    const [year, month] = selectedForecastMonth.split("-").map(Number)
    const base = new Date(year, month - 1, 1)
    const months = []
    for (let i = 3; i >= 1; i--) {
      const d = new Date(base)
      d.setMonth(d.getMonth() - i)
      months.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`)
    }
    return months
  }, [selectedForecastMonth])

  const newsForAspect = React.useMemo(() => {
    if (!aspect) return []
    return [...news]
      .filter((n) => {
        if ((n.aspect || "Unknown") !== aspect) return false
        if (backwardMonths) return backwardMonths.includes(String(n.date || "").slice(0, 7))
        return true
      })
      .sort((a, b) => b.date.localeCompare(a.date))
  }, [aspect, news, backwardMonths])

  const filteredNews = React.useMemo(() => {
    if (!search.trim()) return newsForAspect
    const q = search.toLowerCase()
    return newsForAspect.filter(
      (n) => (n.title || "").toLowerCase().includes(q) || (n.source || "").toLowerCase().includes(q)
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
        <span className="text-gray-800 font-semibold"> {aspect ? (lang === "en" ? (ASPECT_EN[aspect] ?? aspect) : aspect) : t("Aspect", "ประเด็น")} </span>
        {filteredNews.length > 0 && (
          <span className="ml-1 text-gray-400">({filteredNews.length})</span>
        )}
      </nav>

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <CardTitle>  {aspect ? (lang === "en" ? (ASPECT_EN[aspect] ?? aspect) : aspect) : t("Not selected", "ยังไม่ได้เลือก")} </CardTitle>
              <CardDescription>
                {t("Articles for the selected topic", "รายการข่าวสำหรับประเด็นที่เลือก")}
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
                  placeholder={t("Search articles…", "ค้นหาข่าว…")}
                  className="pl-8 pr-3 py-1.5 text-sm rounded-lg border bg-white outline-none"
                  style={{
                    borderColor: THEME.border,
                    width: 220,
                    boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
                  }}
                />
                <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
                  <Search className="w-3.5 h-3.5" />
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
              // icon="☝️"
              title={t("Select a topic", "เลือกประเด็น")}
              description={t("Select a topic from the forecast page to view related articles.", "แตะประเด็นจากหน้าพยากรณ์เพื่อดูข่าวที่เกี่ยวข้อง")}
              action={
                <button
                  onClick={onBack}
                  className="px-4 py-2 rounded-xl text-sm font-medium text-white"
                  style={{ background: THEME.blue, border: "none", cursor: "pointer" }}
                >
                  ← {t("Back to Forecast", "ย้อนกลับ")}
                </button>
              }
            />
          ) : filteredNews.length === 0 ? (
            <EmptyState
              icon="📭"
              title={search ? t("No articles found", "ไม่พบผลลัพธ์") : t("No articles available", "ไม่พบข่าว")}
              description={
                search
                  ? t(`No headlines matching "${search}"`, `ไม่พบข่าวที่ตรงกับ "${search}"`)
                  : t("There are no articles associated with this topic.", "ไม่มีข่าวสำหรับประเด็นนี้")
              }
              action={search ? (
                <button
                  onClick={() => setSearch("")}
                  className="px-4 py-2 rounded-xl text-sm font-medium"
                  style={{ border: `1px solid ${THEME.border}`, background: THEME.white, cursor: "pointer" }}
                >
                  {t("Clear filter", "ล้างการค้นหา")}
                </button>
              ) : null}
            />
          ) : (
            <>
              <div className="divide-y divide-gray-100">
                {pagedNews.map((n, idx) => {
                  const displayDate = lang === "th" ? thaiDateShort(n.date) : n.date
                  const tagColor = tagColors[n.tag] || THEME.gray
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
                            {/* <div className="mt-1.5">
                              <Badge
                                variant="outline"
                                className="text-[10px] px-2 py-0.5 border-0 font-semibold uppercase tracking-wider"
                                style={{ backgroundColor: `${tagColor}18`, color: tagColor }}
                              >
                                {tagLabel}
                              </Badge>
                            </div> */}
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
                    ← {t("Previous", "ก่อนหน้า")}
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
                        backgroundColor: p === currentPage ? THEME.navy : THEME.white,
                        color: p === currentPage ? THEME.white : THEME.textPrimary,
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

function AnalyticsPage({ t, lang, news = [] }) {
  const [agencyStack, setAgencyStack] = React.useState({ data: [], groups: [] })
  const [agencyErr, setAgencyErr] = React.useState("")

  const NewsIcon = () => (
    <img src={forecastchart} width={20} height={20} alt="News Icon" />
  )

  // ── ใช้ข่าวทั้งหมด (ไม่จำกัดแค่ 12 เดือน) เพื่อ Brush เลื่อนดูย้อนหลัง ──
  const aspectStackAll = React.useMemo(() => {
    return stackCountByMonth(news, (n) => n.aspect || "Unknown", ASPECTS_TO_RUN)
  }, [news])

  React.useEffect(() => {
    let alive = true

    async function loadAgency() {
      setAgencyErr("")
      try {
        const rows = await getAgencyVolumeLastNMonths(120)
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
  }, [news])

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

  const impactMonthlyVolume = React.useMemo(() => {
    const monthMap = {}
    news.forEach((n) => {
      const m = n.date?.slice(0, 7)
      if (!m) return
      if (!monthMap[m]) monthMap[m] = { Positive: 0, Neutral: 0, Negative: 0, count: 0 }

      const type =
        n.impactType === "Positive"
          ? "Positive"
          : n.impactType === "Negative"
            ? "Negative"
            : "Neutral"

      monthMap[m][type] += 1
      monthMap[m].count += 1
    })

    const months = Object.keys(monthMap).sort()
    return months.map((m) => {
      const d = monthMap[m]
      return {
        month: m,
        Positive: d.Positive,
        Neutral: d.Neutral,
        Negative: d.Negative,
        total: d.count,
      }
    })
  }, [news])

  const impactSummaryByEffect = React.useMemo(() => {
    const counts = {
      Negative: { "Short-term": 0, "Long-term": 0 },
      Neutral: { "Short-term": 0, "Long-term": 0 },
      Positive: { "Short-term": 0, "Long-term": 0 },
    }

    news.forEach((n) => {
      const impact =
        n.impactType === "Positive"
          ? "Positive"
          : n.impactType === "Negative"
            ? "Negative"
            : "Neutral"

      const effect = n.effectType === "Long-term" ? "Long-term" : "Short-term"
      counts[impact][effect] += 1
    })

    return [
      {
        impact: "Negative",
        "Short-term": counts.Negative["Short-term"],
        "Long-term": counts.Negative["Long-term"],
      },
      {
        impact: "Neutral",
        "Short-term": counts.Neutral["Short-term"],
        "Long-term": counts.Neutral["Long-term"],
      },
      {
        impact: "Positive",
        "Short-term": counts.Positive["Short-term"],
        "Long-term": counts.Positive["Long-term"],
      },
    ]
  }, [news])

  const { shortTermData, longTermData } = React.useMemo(() => {
    const impactMap = { Negative: -1, Neutral: 0, Positive: 1 }
    const shortTerm = []
    const longTerm = []

    news.forEach((n, idx) => {
      if (idx % 10 !== 0) return

      const sBase = Number(n.rawSentiment) || 0
      const iBase = impactMap[n.impactType] ?? 0

      const sJitter = Math.random() * 0.16 - 0.08
      const iJitter = Math.random() * 0.6 - 0.3

      const point = {
        sentiment: Math.max(0, Math.min(1, sBase + sJitter)),
        impact: iBase + iJitter,
        headline: String(n.title || "").substring(0, 60),
        impactLabel: n.impactType || "Neutral",
        effectLabel: n.effectType || "Short-term",
      }

      if (n.effectType === "Long-term") longTerm.push(point)
      else shortTerm.push(point)
    })

    return { shortTermData: shortTerm, longTermData: longTerm }
  }, [news])

  const agencyBrushStart = Math.max(0, agencyStack.data.length - 12)
  const aspectBrushStart = Math.max(0, aspectStackAll.data.length - 12)
  const sentimentBrushStart = Math.max(0, impactMonthlyVolume.length - 12)

  const brushStyle = {
    fill: THEME.blueSoft,
    stroke: THEME.blue,
    height: 28,
  }

  const isLoading = !news?.length && !agencyStack.data.length

  return (
    <div className="space-y-8 xecon-fade-in">
      <SectionHeader
        title={t("News Intelligence", "การวิเคราะห์ข่าวเชิงลึก")}
        subtitle={t(
          "Volume, sentiment, impact analysis and model feature importance",
          "ปริมาณข่าว อารมณ์ข่าว ผลกระทบ และความสำคัญของตัวแปร"
        )}
        icon={NewsIcon}
      />

      <div className="grid grid-cols-1 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>{t("News volume by source", "ปริมาณข่าวตามสำนักข่าว")}</CardTitle>
            <CardDescription>
              {t(
                "Drag the slider below the chart to explore different time periods",
                "ลากแถบด้านล่างกราฟเพื่อเลื่อนดูช่วงเวลาต่างๆ ย้อนหลังได้"
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {agencyErr ? (
              <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 text-sm p-3 flex items-center gap-2">
                <span>⚠️</span> {agencyErr}
              </div>
            ) : agencyStack.data.length === 0 ? (
              <Skeleton style={{ height: 380, borderRadius: 8 }} />
            ) : (
              <ResponsiveContainer width="100%" height={380}>
                <BarChart data={agencyStack.data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                  <CartesianGrid stroke={THEME.border} horizontal={true} vertical={false} strokeOpacity={0.6} />
                  <XAxis
                    dataKey="month"
                    tick={{ fontSize: 11, fill: "#6B7A99" }}
                    tickFormatter={(v) => (lang === "th" ? thaiMonthYear(v) : engMonthYear(v))}
                  />
                  <YAxis tick={{ fontSize: 11, fill: "#6B7A99" }} />
                  <ReTooltip
                    contentStyle={{
                      borderRadius: 10,
                      border: "1px solid #DDE4EF",
                      boxShadow: "0 4px 20px rgba(18,32,64,0.08)",
                    }}
                    labelFormatter={(label) => (lang === "th" ? thaiMonthYear(label) : engMonthYear(label))}
                  />
                  <Legend />
                  {agencyStack.groups.map((agency, i) => (
                    <Bar
                      key={agency}
                      dataKey={agency}
                      stackId="1"
                      fill={isThairathAgency(agency) ? THAIRATH_COLOR : CHART_COLORS[i % CHART_COLORS.length]}
                      name={agency}
                      radius={i === agencyStack.groups.length - 1 ? [3, 3, 0, 0] : [0, 0, 0, 0]}
                    />
                  ))}
                  <Brush
                    dataKey="month"
                    height={28}
                    stroke={THEME.blue}
                    fill={THEME.blueSoft}
                    travellerWidth={10}
                    startIndex={agencyBrushStart}
                    endIndex={agencyStack.data.length - 1}
                    tickFormatter={(v) => (lang === "th" ? thaiMonthYear(v) : engMonthYear(v))}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>{t("News volume by topic", "ปริมาณข่าวตามประเด็น")}</CardTitle>
            <CardDescription>
              {t("Drag the slider below to explore topics over time", "ลากแถบด้านล่างเพื่อสำรวจประเด็นข่าวตามช่วงเวลา")}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={380}>
              <BarChart data={aspectStackAll.data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid stroke={THEME.border} horizontal={true} vertical={false} strokeOpacity={0.6} />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 11, fill: "#6B7A99" }}
                  tickFormatter={(v) => (lang === "th" ? thaiMonthYear(v) : engMonthYear(v))}
                />
                <YAxis tick={{ fontSize: 11, fill: "#6B7A99" }} />
                <ReTooltip
                  contentStyle={{
                    borderRadius: 10,
                    border: "1px solid #DDE4EF",
                    boxShadow: "0 4px 20px rgba(18,32,64,0.08)",
                  }}
                  labelFormatter={(label) => (lang === "th" ? thaiMonthYear(label) : engMonthYear(label))}
                />
                <Legend />
                {aspectStackAll.groups.map((asp, i) => {
                  const enName = ASPECT_EN[asp] || asp
                  const label = lang === "en" ? enName : asp
                  return (
                    <Bar
                      key={asp}
                      dataKey={asp}
                      stackId="1"
                      fill={getAspectColor(asp)}
                      name={label}
                      radius={i === aspectStackAll.groups.length - 1 ? [3, 3, 0, 0] : [0, 0, 0, 0]}
                    />
                  )
                })}
                <Brush
                  dataKey="month"
                  height={28}
                  stroke={THEME.blue}
                  fill={THEME.blueSoft}
                  travellerWidth={10}
                  startIndex={aspectBrushStart}
                  endIndex={aspectStackAll.data.length - 1}
                  tickFormatter={(v) => (lang === "th" ? thaiMonthYear(v) : engMonthYear(v))}
                />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>{t("Sentiment distribution", "สรุปภาพรวมข่าวในแต่ละระดับ")}</CardTitle>
            <CardDescription>
              {t(
                "Distribution of news articles across sentiment score ranges",
                "การกระจายตัวของจำนวนข่าวในแต่ละช่วงคะแนนความรู้สึก"
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={sentimentHistogram}>
                <CartesianGrid stroke={THEME.border} horizontal={true} vertical={false} strokeOpacity={0.6} />
                <XAxis dataKey="range" tick={{ fontSize: 10, fill: "#6B7A99" }} />
                <YAxis
                  tick={{ fontSize: 11, fill: "#6B7A99" }}
                  tickFormatter={(v) => (v >= 1000 ? v.toLocaleString() : v)}
                />
                <ReTooltip
                  contentStyle={{
                    borderRadius: 10,
                    border: "1px solid #DDE4EF",
                    boxShadow: "0 4px 20px rgba(18,32,64,0.08)",
                  }}
                />
                <Bar dataKey="count" fill="#0072B2" name={t("News count", "จำนวนข่าว")} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("Impact summary", "สรุปภาพรวมผลกระทบจากข่าว")}</CardTitle>
            <CardDescription>
              {t(
                "Total news count by impact level, split by short-term and long-term effect",
                "จำนวนข่าวรวมทุกเดือน แยกตามระดับผลกระทบและระยะเวลา"
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={impactSummaryByEffect} margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                <CartesianGrid stroke={THEME.border} horizontal={true} vertical={false} strokeOpacity={0.6} />
                <XAxis dataKey="impact" tick={{ fontSize: 13, fill: "#6B7A99", fontWeight: 600 }} />
                <YAxis
                  tick={{ fontSize: 11, fill: "#6B7A99" }}
                  tickFormatter={(v) => (v >= 1000 ? v.toLocaleString() : v)}
                />
                <ReTooltip
                  contentStyle={{
                    borderRadius: 10,
                    border: "1px solid #DDE4EF",
                    boxShadow: "0 4px 20px rgba(18,32,64,0.08)",
                  }}
                />
                <Legend />
                <Bar
                  dataKey="Short-term"
                  fill={EFFECT_COLORS["Short-term"]}
                  name={t("Short-term", "ระยะสั้น")}
                  radius={[3, 3, 0, 0]}
                />
                <Bar
                  dataKey="Long-term"
                  fill={EFFECT_COLORS["Long-term"]}
                  name={t("Long-term", "ระยะยาว")}
                  radius={[3, 3, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>{t("Frequently mentioned terms", "แท็กคลาวด์")}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="w-full bg-white rounded-lg overflow-hidden">
              <InteractiveWordCloud lang={lang} />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
function MonthCalendarPicker({ months, selectedMonth, onSelect, lang, t }) {
  const [open, setOpen] = React.useState(false)
  const [viewYear, setViewYear] = React.useState(() => {
    if (selectedMonth) return parseInt(selectedMonth.slice(0, 4))
    return new Date().getFullYear()
  })
  const ref = React.useRef(null)

  React.useEffect(() => {
    if (!open) return
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [open])

  React.useEffect(() => {
    if (selectedMonth) setViewYear(parseInt(selectedMonth.slice(0, 4)))
  }, [selectedMonth])

  const availableYears = [...new Set(months.map(m => parseInt(m.slice(0, 4))))].sort((a, b) => b - a)
  const monthsInYear = months.filter(m => parseInt(m.slice(0, 4)) === viewYear)
  const monthNamesTH = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
  const monthNamesEN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
  const monthNames = lang === "th" ? monthNamesTH : monthNamesEN
  const isSelected = (m) => m === selectedMonth

  const thaiYear = lang === "th" ? viewYear + 543 : viewYear

  return (
    <div style={{ position: "relative" }} ref={ref}>
      <button
        onClick={() => setOpen(v => !v)}
        style={{
          display: "flex", alignItems: "center", gap: 5,
          padding: "3px 12px", borderRadius: 99,
          fontSize: 12, fontWeight: 500,
          border: "1px dashed rgba(255,255,255,0.22)",
          color: "rgba(255,255,255,0.55)",
          background: open ? "rgba(255,255,255,0.08)" : "transparent",
          cursor: "pointer", flexShrink: 0, transition: "background 0.15s",
        }}
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <rect x="1" y="1.5" width="10" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.1" />
          <line x1="1" y1="4" x2="11" y2="4" stroke="currentColor" strokeWidth="1.1" />
          <line x1="3.5" y1="0.5" x2="3.5" y2="2.5" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" />
          <line x1="8.5" y1="0.5" x2="8.5" y2="2.5" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" />
        </svg>
        {t("Historical", "ย้อนหลัง")}
      </button>

      {open && (
        <div
          style={{
            position: "absolute", top: "calc(100% + 8px)", left: "50%",
            transform: "translateX(-50%)",
            background: THEME.white, borderRadius: 14,
            border: "1px solid theme.border",
            boxShadow: "0 8px 32px rgba(18,32,64,0.14)",
            padding: 16, zIndex: 100, width: 240,
          }}
        >
          {/* Year navigation */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <button
              onClick={() => {
                const idx = availableYears.indexOf(viewYear)
                if (idx < availableYears.length - 1) setViewYear(availableYears[idx + 1])
              }}
              disabled={availableYears.indexOf(viewYear) >= availableYears.length - 1}
              style={{
                width: 28, height: 28, border: `1px solid ${THEME.border}`, borderRadius: 7,
                background: "transparent", cursor: "pointer", display: "flex",
                alignItems: "center", justifyContent: "center", color: THEME.textPrimary,
                opacity: availableYears.indexOf(viewYear) >= availableYears.length - 1 ? 0.3 : 1,
              }}
            >
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><polyline points="7,2 3,5 7,8" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" /></svg>
            </button>
            <span style={{ fontSize: 13, fontWeight: 500, color: THEME.textPrimary }}>{thaiYear}</span>
            <button
              onClick={() => {
                const idx = availableYears.indexOf(viewYear)
                if (idx > 0) setViewYear(availableYears[idx - 1])
              }}
              disabled={availableYears.indexOf(viewYear) <= 0}
              style={{
                width: 28, height: 28, border: `1px solid ${THEME.border}`, borderRadius: 7,
                background: "transparent", cursor: "pointer", display: "flex",
                alignItems: "center", justifyContent: "center", color: THEME.textPrimary,
                opacity: availableYears.indexOf(viewYear) <= 0 ? 0.3 : 1,
              }}
            >
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><polyline points="3,2 7,5 3,8" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" /></svg>
            </button>
          </div>

          {/* Month grid — 4×3 */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 4 }}>
            {monthNames.map((name, idx) => {
              const mKey = `${viewYear}-${String(idx + 1).padStart(2, "0")}`
              const available = monthsInYear.includes(mKey)
              const selected = isSelected(mKey)
              return (
                <button
                  key={mKey}
                  disabled={!available}
                  onClick={() => { onSelect(mKey); setOpen(false) }}
                  style={{
                    padding: "6px 4px", borderRadius: 8, fontSize: 12,
                    fontWeight: selected ? 600 : 400, border: "none",
                    cursor: available ? "pointer" : "default",
                    background: selected ? THEME.navy : available ? THEME.blueCard : "transparent",
                    color: selected ? THEME.white : available ? "#1E2F47" : THEME.border,
                    transition: "background 0.12s",
                  }}
                  onMouseEnter={e => { if (available && !selected) e.currentTarget.style.background = THEME.blueCardS }}
                  onMouseLeave={e => { if (available && !selected) e.currentTarget.style.background = THEME.blueCard }}
                >
                  {name}
                </button>
              )
            })}
          </div>

          {/* Available count hint */}
          <div style={{ marginTop: 10, fontSize: 11, color: THEME.textHint, textAlign: "center" }}>
            {monthsInYear.length > 0
              ? `${monthsInYear.length} ${t("months with data", "เดือนที่มีข้อมูล")}`
              : t("No data available for this year", "ไม่มีข้อมูลปีนี้")}
          </div>
        </div>
      )}
    </div>
  )
}

export default function App() {
  const { lang, setLang, t } = useLang()
  const { page, setPage } = useNavigation()
  const [selectedAspect, setSelectedAspect] = React.useState(null)

  const [summary, setSummary] = React.useState(null)
  const [allExplain, setAllExplain] = React.useState([])
  const [allExplainEN, setAllExplainEN] = React.useState([])
  const [dataLoaded, setDataLoaded] = React.useState(false)

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
      [...new Set(
        (allExplain || [])
          .map((r) => String(r.date || "").slice(0, 7))
          .filter(Boolean)
      )].sort((a, b) => a.localeCompare(b)),
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
        const [s, e, enE, ts, newsRows, shapRes] = await Promise.allSettled([
          getSummary(),
          getAllExplain(),
          getAllExplainEN(),
          getTimeSeries(2000),
          getNewsSentimentFromCSV(),
          getShap(),
        ])

        if (!alive) return

        setSummary(s.status === "fulfilled" ? s.value : null)
        setAllExplain(e.status === "fulfilled" ? e.value?.data || [] : [])
        setAllExplainEN(enE.status === "fulfilled" ? enE.value?.data || [] : [])  // add this
        setSeries(ts.status === "fulfilled" ? ts.value?.data || [] : [])
        setNewsReal(newsRows.status === "fulfilled" ? newsRows.value || [] : [])
        setShapData(shapRes.status === "fulfilled" ? shapRes.value?.data || [] : [])
        setDataLoaded(true)
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
    color: active ? THEME.white : "rgba(255,255,255,0.6)",
    background: active ? "rgba(255,255,255,0.18)" : "transparent",
    border: `1px solid ${active ? "rgba(255,255,255,0.4)" : "rgba(255,255,255,0.15)"}`,
    cursor: "pointer",
    whiteSpace: "nowrap",
    flexShrink: 0,
    transition: "all 0.15s",
  })

  return (
    <div className="min-h-screen" style={{ background: THEME.pageBg }}>
      {/* ── Topbar ── */}
      <div
        className="sticky top-0 z-50 w-full"
        style={{ backgroundColor: THEME.navy, borderBottom: "1px solid rgba(255,255,255,0.08)" }}
      >
        {/* Main bar — 3 columns: brand | tabs | lang */}
        <div
          className="max-w-[1600px] mx-auto px-4 md:px-7 grid items-center"
          style={{ height: 60, gridTemplateColumns: "1fr auto 1fr" }}
        >
          {/* Brand — left */}
          <div className="flex items-center gap-2.5 flex-shrink-0">
            <div
              className="flex items-center justify-center rounded-lg flex-shrink-0"
              style={{ width: 32, height: 32, background: "rgba(255,255,255,0.12)" }}
            >
              <Activity className="text-white" style={{ width: 18, height: 18 }} />
            </div>
            <div className="leading-tight">
              <div className="text-white font-medium" style={{ fontSize: 15 }}>
                XEconomics
              </div>
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", marginTop: 1 }}>
                CCI Forecast &amp; XAI
              </div>
            </div>
          </div>

          {/* Tabs — center */}
          <div className="hidden md:flex items-center" style={{ height: 60 }}>
            {tabs.map(({ id, en, th, Icon }) => {
              const active = page === id || (page === "aspectNews" && id === "forecast")
              return (
                <button
                  key={id}
                  onClick={() => setPage(id)}
                  className="flex items-center gap-1.5 transition-all"
                  style={{
                    padding: "0 20px",
                    height: 60,
                    fontSize: 13,
                    fontWeight: active ? 500 : 400,
                    color: active ? THEME.white : "rgba(255,255,255,0.45)",
                    background: "transparent",
                    border: "none",
                    borderBottom: active ? "2px solid #fff" : "2px solid transparent",
                    cursor: "pointer",
                    whiteSpace: "nowrap",
                    transition: "color 0.15s, border-color 0.15s",
                  }}
                  onMouseEnter={e => { if (!active) { e.currentTarget.style.color = "rgba(255,255,255,0.8)"; e.currentTarget.style.borderBottomColor = "rgba(255,255,255,0.3)" } }}
                  onMouseLeave={e => { if (!active) { e.currentTarget.style.color = "rgba(255,255,255,0.45)"; e.currentTarget.style.borderBottomColor = "transparent" } }}
                >
                  <Icon style={{ width: 13, height: 13 }} />
                  {t(en, th)}
                </button>
              )
            })}
          </div>

          {/* Right side: lang toggle + hamburger — right-aligned */}
          <div className="flex items-center gap-2 justify-end">
            {/* Language toggle */}
            <div
              className="flex items-center gap-0.5 rounded-lg p-[3px]"
              style={{ background: "rgba(255,255,255,0.08)" }}
            >
              {[["en", "EN"], ["th", "TH"]].map(([code, label]) => (
                <button
                  key={code}
                  onClick={() => setLang(code)}
                  style={{
                    padding: "4px 11px",
                    borderRadius: 6,
                    fontSize: 12,
                    fontWeight: 600,
                    background: lang === code ? THEME.white : "transparent",
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
                <span style={{ color: THEME.white, fontSize: 18, lineHeight: 1 }}>✕</span>
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
            style={{ background: THEME.subbar, borderTop: "1px solid rgba(255,255,255,0.1)" }}
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
                    color: active ? THEME.white : "rgba(255,255,255,0.65)",
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
          <div style={{ background: THEME.subbar, borderTop: "1px solid rgba(255,255,255,0.07)" }}>
            <div
              className="max-w-[1600px] mx-auto px-4 md:px-7 flex items-center"
              style={{ height: 44, gap: 0 }}
            >
              {/* Context pill */}
              <div
                className="hidden sm:flex items-center gap-2 flex-shrink-0"
                style={{ paddingRight: 16, borderRight: "1px solid rgba(255,255,255,0.1)" }}
              >
                <div
                  className="rounded-full flex-shrink-0"
                  style={{ width: 6, height: 6, background: isHistorical ? "rgba(255,255,255,0.35)" : "#4ade80" }}
                />
                <span style={{ fontSize: 11, color: "rgba(255,255,255,0.5)", whiteSpace: "nowrap" }}>
                  {isHistorical ? t("Historical", "ประวัติ") : t("Forecast", "พยากรณ์")}
                </span>
                <span style={{ fontSize: 11, fontWeight: 600, color: "rgba(255,255,255,0.9)", whiteSpace: "nowrap" }}>
                  {monthLabel(selectedForecastMonth, lang)}
                </span>
              </div>

              {/* Forecast pills + calendar picker */}
              <div className="flex items-center gap-1.5" style={{ paddingLeft: 20 }}>
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
                    <MonthCalendarPicker
                      months={historicalMonths}
                      selectedMonth={isHistorical ? selectedForecastMonth : ""}
                      onSelect={setSelectedForecastMonth}
                      lang={lang}
                      t={t}
                    />
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Page content ── */}
      <div className="max-w-[1600px] mx-auto px-6 md:px-10 py-6 space-y-5">
        {err && (
          <div
            className="rounded-xl px-4 py-2.5 text-sm flex items-center gap-2"
            style={{ background: "rgba(214,69,69,0.06)", border: "1px solid #FECACA", color: "#B91C1C" }}
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
            allExplain={lang === "en" ? allExplainEN : allExplain}
            news={newsReal}
            selectedForecastMonth={selectedForecastMonth}
            setSelectedForecastMonth={setSelectedForecastMonth}
            availableFutureMonths={availableFutureMonths}
            historicalMonths={historicalMonths}
            dataLoaded={dataLoaded}
            onSelectAspect={(asp) => {
              setSelectedAspect(asp)
              setPage("aspectNews")
            }}
          />
        )}

        {page === "analytics" && (
          <AnalyticsPage t={t} lang={lang} news={newsReal} />
        )}

        {page === "aspectNews" && (
          <AspectNewsPage
            t={t}
            lang={lang}
            aspect={selectedAspect}
            news={newsReal}
            onBack={() => setPage("forecast")}
            selectedForecastMonth={selectedForecastMonth}

          />
        )}
      </div>

      {/* ── Footer ── */}
      <footer style={{ background: THEME.navy, marginTop: 32 }}>
        <div
          className="max-w-[1600px] mx-auto px-6 md:px-10"
          style={{ padding: "20px 40px", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}
        >
          <div style={{ fontSize: 13, color: "rgba(255,255,255,0.4)" }}>
            <span style={{ color: "rgba(255,255,255,0.75)", fontWeight: 500 }}>XEconomics</span>
            {" · "}{t("Consumer Confidence Index Forecast & Explainability Platform", "ระบบพยากรณ์ดัชนีความเชื่อมั่นผู้บริโภค")}
          </div>
          <div style={{ display: "flex", gap: 24 }}>
            {[
              // [t("About the System", "เกี่ยวกับระบบ")],
              // [t("Forecast Methodology", "วิธีการพยากรณ์")],
              // [t("Contact Us", "ติดต่อเรา")],
              // [t("SP2025-40", "SP2025-40")],
            ].map(([label]) => (
              <span key={label} style={{ fontSize: 12, color: "rgba(255,255,255,0.3)", cursor: "pointer" }}>
                {label}
              </span>
            ))}
          </div>
          <div style={{ fontSize: 11, color: "rgba(255,255,255,0.2)" }}>
            {t("Data as of", "อัปเดตล่าสุด")}: {monthLabel(latestActualMonth, lang) || "—"}
          </div>
        </div>
      </footer>
    </div>
  )
}