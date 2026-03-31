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
} from "recharts"

// --- THEME & UTILITY COMPONENTS ---
const THEME = {
  primary: "#003d82",
  primaryLight: "#0066cc",
  success: "#059669",
  danger: "#dc2626",
  secondary: "#6b7280",
  cardBg: "rgba(255,255,255,0.95)",
}

const Badge = ({ children, variant = "secondary", className = "", style }) => {
  const styles = {
    secondary: "bg-gray-100 text-gray-700",
    positive: "bg-green-100 text-green-700",
    negative: "bg-red-100 text-red-700",
    outline: "border border-gray-300 text-gray-600",
  }
  return (
    <span
      className={`inline-block px-2 py-1 rounded text-xs font-medium ${styles[variant]} ${className}`}
      style={style}
    >
      {children}
    </span>
  )
}

const Card = ({ children, className = "" }) => (
  <div className={`bg-white rounded-xl shadow-lg border border-gray-200 ${className}`}>{children}</div>
)
const CardHeader = ({ children, className = "" }) => (
  <div className={`p-6 border-b border-gray-100 ${className}`}>{children}</div>
)
const CardTitle = ({ children }) => <h3 className="text-lg font-bold text-gray-800">{children}</h3>
const CardDescription = ({ children }) => <p className="text-sm text-gray-600 mt-1">{children}</p>
const CardContent = ({ children, className = "" }) => <div className={`p-6 ${className}`}>{children}</div>

// --- DATA & CONSTANTS ---
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
const THAIPBS_COLOR = "#FF8200"

function isThairathAgency(name) {
  const s = String(name || "").toLowerCase()
  return s.includes("thairath") || s.includes("ไทยรัฐ")
}

const domesticFactors = [
  { month: "2025-03", purchasing: 102.5, retail: 3.2, consumption: 2.8 },
  { month: "2025-04", purchasing: 103.1, retail: 3.5, consumption: 3.1 },
  { month: "2025-05", purchasing: 104.2, retail: 4.1, consumption: 3.6 },
  { month: "2025-06", purchasing: 103.8, retail: 3.8, consumption: 3.2 },
  { month: "2025-07", purchasing: 105.5, retail: 4.5, consumption: 4.0 },
  { month: "2025-08", purchasing: 106.2, retail: 4.8, consumption: 4.3 },
]

const setFactors = [
  { month: "2025-03", setIndex: 1580, foreignFlow: -2.3, correlation: 0.65 },
  { month: "2025-04", setIndex: 1595, foreignFlow: 1.8, correlation: 0.68 },
  { month: "2025-05", setIndex: 1612, foreignFlow: 3.2, correlation: 0.72 },
  { month: "2025-06", setIndex: 1605, foreignFlow: -1.5, correlation: 0.7 },
  { month: "2025-07", setIndex: 1628, foreignFlow: 4.1, correlation: 0.75 },
  { month: "2025-08", setIndex: 1645, foreignFlow: 5.5, correlation: 0.78 },
]

const gdpData = [
  { quarter: "Q1 2024", gdp: 2.8, growth: 2.5 },
  { quarter: "Q2 2024", gdp: 2.9, growth: 2.6 },
  { quarter: "Q3 2024", gdp: 3.0, growth: 2.8 },
  { quarter: "Q4 2024", gdp: 3.1, growth: 3.0 },
  { quarter: "Q1 2025", gdp: 3.2, growth: 3.2 },
  { quarter: "Q2 2025", gdp: 3.3, growth: 3.4 },
]

const inflationData = [
  { month: "2025-03", headline: 1.2, core: 0.8 },
  { month: "2025-04", headline: 1.3, core: 0.9 },
  { month: "2025-05", headline: 1.5, core: 1.0 },
  { month: "2025-06", headline: 1.4, core: 0.9 },
  { month: "2025-07", headline: 1.6, core: 1.1 },
  { month: "2025-08", headline: 1.7, core: 1.2 },
]

const asOf = "2025-08-31"

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

// --- HELPERS ---
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
    const g = getGroupKey(n)
    if (!monthKey || !g) return
    groupSet.add(g)
    if (!monthMap[monthKey]) monthMap[monthKey] = {}
    monthMap[monthKey][g] = (monthMap[monthKey][g] || 0) + 1
  })
  const groups = groupsOverride ? [...groupsOverride] : [...groupSet].sort()
  const months = Object.keys(monthMap).sort((a, b) => a.localeCompare(b))
  const data = months.map((month) => {
    const row = { month }
    groups.forEach((g) => (row[g] = monthMap[month][g] || 0))
    return row
  })
  return { data, groups }
}

function toAgencyStack(rows) {
  if (!Array.isArray(rows)) return { data: [], groups: [] }
  const monthMap = {}
  const groupsSet = new Set()
  rows.forEach((r) => {
    const m = r.month
    const g = r.agency || "Unknown"
    const c = Number(r.count || 0)
    groupsSet.add(g)
    if (!monthMap[m]) monthMap[m] = {}
    monthMap[m][g] = (monthMap[m][g] || 0) + c
  })
  const groups = [...groupsSet].sort()
  const months = Object.keys(monthMap).sort()
  const data = months.map((m) => {
    const row = { month: m }
    groups.forEach((g) => (row[g] = monthMap[m][g] || 0))
    return row
  })
  return { data, groups }
}

// --- HOOKS ---
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
      window.history.replaceState({ page: getPageFromHash() }, "", `#${getPageFromHash()}`)
    }
    return () => window.removeEventListener("popstate", onPopState)
  }, [])
  return { page, setPage }
}

// --- UTILITY FUNCTIONS ---
function pickValue(p) {
  return p?.actual ?? p?.pred ?? p?.forecast ?? null
}

function currentCCI(arr) {
  if (!arr?.length) return null
  const lastActual = [...arr].reverse().find((p) => p.actual != null)
  if (lastActual) return lastActual.actual
  return pickValue(arr[arr.length - 1])
}

function prevCCI(arr) {
  if (!arr?.length) return null
  const rev = [...arr].reverse()
  const idx = rev.findIndex((p) => pickValue(p) != null)
  const afterFirst = idx >= 0 ? rev.slice(idx + 1) : []
  const prev = afterFirst.find((p) => pickValue(p) != null)
  return pickValue(prev)
}

function pctChange(curr, prev) {
  if (curr == null || prev == null || prev === 0) return null
  return ((curr - prev) / prev) * 100
}

function thaiMonth(dateStr) {
  const months = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
  const d = new Date(dateStr)
  return `${months[d.getMonth()]} ${d.getFullYear() + 543}`
}

function thaiDateShort(dateStr) {
  const months = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
  const d = new Date(dateStr)
  return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`
}

// --- MONTH/YEAR PICKER ---
function MonthYearPicker({ value, onChange, lang }) {
  const [yStr, mStr] = (value || "").split("-")
  const year = parseInt(yStr) || new Date().getFullYear()
  const month = (parseInt(mStr) || new Date().getMonth() + 1) - 1
  const monthsTH = ["มกราคม","กุมภาพันธ์","มีนาคม","เมษายน","พฤษภาคม","มิถุนายน","กรกฎาคม","สิงหาคม","กันยายน","ตุลาคม","พฤศจิกายน","ธันวาคม"]
  const monthsEN = ["January","February","March","April","May","June","July","August","September","October","November","December"]
  const years = Array.from({ length: 25 }, (_, i) => 2010 + i)
  const handleChange = (newY, newM) => {
    const m = String(newM + 1).padStart(2, "0")
    onChange(`${newY}-${m}`)
  }
  return (
    <div className="flex gap-1 border border-gray-300 rounded px-2 py-1 bg-white items-center shadow-sm hover:border-blue-400 transition-colors">
      <select value={month} onChange={(e) => handleChange(year, parseInt(e.target.value))} className="bg-transparent text-sm outline-none cursor-pointer font-medium hover:text-blue-700 pr-1">
        {(lang === "th" ? monthsTH : monthsEN).map((mName, i) => (
          <option key={i} value={i}>{mName}</option>
        ))}
      </select>
      <span className="text-gray-300">|</span>
      <select value={year} onChange={(e) => handleChange(parseInt(e.target.value), month)} className="bg-transparent text-sm outline-none cursor-pointer font-medium hover:text-blue-700 pl-1">
        {years.map((y) => (
          <option key={y} value={y}>{lang === "th" ? y + 543 : y}</option>
        ))}
      </select>
    </div>
  )
}

// --- METRIC CARD ---
function MetricCard({ icon: Icon, title, value, subtitle, tone }) {
  const colors = {
    up: { bg: "#d1fae5", text: "#059669" },
    down: { bg: "#fee2e2", text: "#dc2626" },
    neutral: { bg: "#f3f4f6", text: "#6b7280" },
  }
  const c = colors[tone] || colors.neutral
  return (
    <div className="rounded-xl p-6 shadow-sm" style={{ backgroundColor: c.bg }}>
      <div className="flex items-start gap-3 mb-2">
        {Icon && <Icon className="w-6 h-6" style={{ color: c.text }} />}
        <div className="text-sm font-medium" style={{ color: c.text }}>{title}</div>
      </div>
      <div className="text-3xl font-bold mb-1" style={{ color: c.text }}>{value}</div>
      {subtitle && <div className="text-xs" style={{ color: c.text, opacity: 0.8 }}>{subtitle}</div>}
    </div>
  )
}

function SectionHeader({ title, subtitle, icon: Icon }) {
  return (
    <div className="flex items-center gap-3 mb-4">
      {Icon && <Icon className="w-6 h-6 text-blue-600" />}
      <div>
        <h2 className="text-xl font-bold text-gray-800">{title}</h2>
        {subtitle && <p className="text-sm text-gray-600">{subtitle}</p>}
      </div>
    </div>
  )
}

function TopNav({ t, page, setPage }) {
  const tabs = [
    { id: "forecast", en: "CCI Forecast", th: "พยากรณ์ CCI", icon: TrendingUp },
    { id: "analytics", en: "News Analytics", th: "วิเคราะห์ข่าว", icon: BarChart3 },
  ]
  return (
    <div className="flex gap-2 mb-6">
      {tabs.map((tab) => {
        const active = page === tab.id || (page === "aspectNews" && tab.id === "forecast")
        return (
          <button
            key={tab.id}
            onClick={() => setPage(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${active ? "bg-[#1F3A5F] text-white" : "text-gray-700 hover:bg-gray-100"}`}
          >
            <tab.icon className="w-4 h-4" />
            {t(tab.en, tab.th)}
          </button>
        )
      })}
    </div>
  )
}

// --- TOP ASPECTS CARD ---
function TopAspectsOnlyCard({ t, news = [], onSelectAspect }) {
  const ranked = React.useMemo(() => {
    const counts = {}
    news.forEach((n) => {
      const a = n.aspect || "Other"
      counts[a] = (counts[a] || 0) + 1
    })
    return Object.entries(counts)
      .map(([aspect, count]) => ({ aspect, count }))
      .sort((a, b) => b.count - a.count)
  }, [news])

  const top3 = ranked.slice(0, 3)

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>{t("Top Aspects", "ประเด็นหลัก (Aspect)")}</CardTitle>
        <CardDescription>{t("Click to open a new page of news in that aspect", "คลิกเพื่อเปิดหน้าใหม่ดูข่าวตามประเด็น")}</CardDescription>
      </CardHeader>
      <CardContent className="p-4 bg-gray-50">
        <div className="mb-4">
          <div className="text-xs font-semibold text-gray-600 mb-2">{t("Top 3", "Top 3")}</div>
          <div className="grid grid-cols-1 gap-2">
            {top3.map((x) => (
              <button
                key={x.aspect}
                onClick={() => onSelectAspect?.(x.aspect)}
                className="bg-white border border-gray-200 rounded-xl p-4 flex items-center justify-between hover:bg-gray-50 transition"
              >
                <div className="font-semibold text-gray-900 text-left">{x.aspect}</div>
                <Badge variant="outline">{t("news", "ข่าว")}: {x.count}</Badge>
              </button>
            ))}
          </div>
        </div>
        <div>
          <div className="text-xs font-semibold text-gray-600 mb-2">{t("All aspects", "ทุกประเด็น")}</div>
          <div className="flex flex-wrap gap-2">
            {ranked.map((x) => (
              <button
                key={x.aspect}
                onClick={() => onSelectAspect?.(x.aspect)}
                className="bg-white border border-gray-200 rounded-lg px-3 py-2 hover:bg-gray-50 transition"
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-gray-800">{x.aspect}</span>
                  <Badge variant="secondary">{x.count}</Badge>
                </div>
              </button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// --- ASPECT NEWS PAGE ---
const PER_PAGE = 15

function AspectNewsPage({ t, lang, aspect, news = [], onBack }) {
  const [currentPage, setCurrentPage] = React.useState(1)

  const newsForAspect = React.useMemo(() => {
    if (!aspect) return []
    return [...news]
      .filter((n) => (n.aspect || "Unknown") === aspect)
      .sort((a, b) => b.date.localeCompare(a.date))
  }, [aspect, news])

  React.useEffect(() => { setCurrentPage(1) }, [aspect])

  const totalPages = Math.max(1, Math.ceil(newsForAspect.length / PER_PAGE))
  const pagedNews = newsForAspect.slice((currentPage - 1) * PER_PAGE, currentPage * PER_PAGE)

  const pageNumbers = React.useMemo(() => {
    const pages = []
    let start = Math.max(1, currentPage - 2)
    let end = Math.min(totalPages, start + 4)
    start = Math.max(1, end - 4)
    for (let i = start; i <= end; i++) pages.push(i)
    return pages
  }, [currentPage, totalPages])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <button onClick={onBack} className="px-4 py-2 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 transition">
          ← {t("Back", "ย้อนกลับ")}
        </button>
        <div className="text-xs text-gray-500">{t("Sorted by newest", "เรียงล่าสุดก่อน")}</div>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>{t("Aspect:", "ประเด็น:")} {aspect ?? t("Not selected", "ยังไม่ได้เลือก")}</CardTitle>
          <CardDescription>
            {t("News list for the selected aspect", "รายการข่าวสำหรับประเด็นที่เลือก")}
            {newsForAspect.length > 0 && (
              <span className="ml-2 text-gray-400">
                ({t(`${newsForAspect.length} total`, `ทั้งหมด ${newsForAspect.length} ข่าว`)})
              </span>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {!aspect ? (
            <div className="p-6 text-sm text-gray-600">{t("Please select an aspect first.", "กรุณาเลือกประเด็นก่อน")}</div>
          ) : newsForAspect.length === 0 ? (
            <div className="p-6 text-sm text-gray-600">{t("No news found for this aspect.", "ไม่พบข่าวสำหรับประเด็นนี้")}</div>
          ) : (
            <>
              <div className="divide-y divide-gray-100">
                {pagedNews.map((n, idx) => {
                  const displayDate = lang === "th" ? thaiDateShort(n.date) : n.date
                  const tagColor = tagColors[n.tag] || "#6b7280"
                  const tagLabel = lang === "th" ? (tagTH[n.tag] || n.tag) : n.tag
                  const globalIdx = (currentPage - 1) * PER_PAGE + idx
                  return (
                    <div key={`${n.date}-${globalIdx}`} className="p-6 hover:bg-gray-50 transition">
                      <div className="text-xs text-gray-500">{displayDate} • {n.source}</div>
                      <a href={n.url} target="_blank" rel="noreferrer" className="text-base font-semibold text-gray-900 mt-1 inline-block hover:underline">
                        {n.title}
                      </a>
                      <div className="mt-2">
                        <Badge
                          variant="outline"
                          className="text-[10px] px-2 py-0.5 border-0 font-semibold uppercase tracking-wider"
                          style={{ backgroundColor: `${tagColor}15`, color: tagColor }}
                        >
                          {tagLabel}
                        </Badge>
                      </div>
                    </div>
                  )
                })}
              </div>
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 p-4 border-t border-gray-100">
                  <button
                    onClick={() => { setCurrentPage((p) => Math.max(1, p - 1)); window.scrollTo({ top: 0, behavior: "smooth" }) }}
                    disabled={currentPage === 1}
                    className="px-3 py-1.5 rounded-lg border border-gray-200 text-sm font-medium transition disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    ← {t("Prev", "ก่อนหน้า")}
                  </button>
                  {pageNumbers[0] > 1 && (
                    <>
                      <button onClick={() => { setCurrentPage(1); window.scrollTo({ top: 0, behavior: "smooth" }) }} className="w-9 h-9 rounded-lg border border-gray-200 text-sm font-medium hover:bg-gray-50 transition">1</button>
                      {pageNumbers[0] > 2 && <span className="text-gray-400 text-sm">…</span>}
                    </>
                  )}
                  {pageNumbers.map((p) => (
                    <button
                      key={p}
                      onClick={() => { setCurrentPage(p); window.scrollTo({ top: 0, behavior: "smooth" }) }}
                      className={`w-9 h-9 rounded-lg text-sm font-medium transition ${p === currentPage ? "bg-[#003d82] text-white shadow" : "border border-gray-200 hover:bg-gray-50"}`}
                    >
                      {p}
                    </button>
                  ))}
                  {pageNumbers[pageNumbers.length - 1] < totalPages && (
                    <>
                      {pageNumbers[pageNumbers.length - 1] < totalPages - 1 && <span className="text-gray-400 text-sm">…</span>}
                      <button onClick={() => { setCurrentPage(totalPages); window.scrollTo({ top: 0, behavior: "smooth" }) }} className="w-9 h-9 rounded-lg border border-gray-200 text-sm font-medium hover:bg-gray-50 transition">{totalPages}</button>
                    </>
                  )}
                  <button
                    onClick={() => { setCurrentPage((p) => Math.min(totalPages, p + 1)); window.scrollTo({ top: 0, behavior: "smooth" }) }}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1.5 rounded-lg border border-gray-200 text-sm font-medium transition disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    {t("Next", "ถัดไป")} →
                  </button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// --- EXPLAIN BOX (fully wired with date picker) ---
function ExplainBox({ t, lang, allExplain = [] }) {
  // derive sorted list of available months from data
  const availableMonths = React.useMemo(
    () => allExplain.map((r) => r.date).filter(Boolean).sort(),
    [allExplain]
  )

  // default to latest month
  const [selectedDate, setSelectedDate] = React.useState("")

  React.useEffect(() => {
    if (availableMonths.length && !selectedDate) {
      setSelectedDate(availableMonths[availableMonths.length - 1])
    }
  }, [availableMonths])

  const row = React.useMemo(
    () => allExplain.find((r) => r.date === selectedDate) || null,
    [allExplain, selectedDate]
  )

  if (!allExplain.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t("Model Explanation", "คำอธิบายโมเดล")}</CardTitle>
          <CardDescription>{t("No explain data yet.", "ยังไม่มี explain data")}</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  const forecastLabel = row
    ? (lang === "th" ? thaiMonth(`${row.date}-01`) : row.date)
    : "-"

  const isUp = row?.direction?.includes("เพิ่ม") || row?.direction?.toLowerCase().includes("up")

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("Model Explanation", "คำอธิบายโมเดล")}</CardTitle>
        <CardDescription>{t("Select a month to view the model's reasoning", "เลือกเดือนเพื่อดูคำอธิบายของโมเดล")}</CardDescription>

        {/* Scrollable month button row */}
        <div className="flex gap-1 flex-wrap mt-3 max-h-24 overflow-y-auto pr-1">
          {availableMonths.map((m) => (
            <button
              key={m}
              onClick={() => setSelectedDate(m)}
              className={`px-2 py-1 text-xs rounded border transition-all whitespace-nowrap ${
                m === selectedDate
                  ? "bg-[#003d82] text-white border-[#003d82]"
                  : "border-gray-300 text-gray-600 hover:bg-gray-100"
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      </CardHeader>

      <CardContent>
        {row ? (
          <>
            {/* Info badges */}
            <div className="flex gap-2 flex-wrap mb-3">
              <Badge variant="outline">
                {t("Month", "เดือน")}: {forecastLabel}
              </Badge>
              {row.predicted != null && (
                <Badge variant="outline">
                  {t("Predicted CCI", "CCI พยากรณ์")}: {Number(row.predicted).toFixed(2)}
                </Badge>
              )}
              {row.direction && (
                <Badge variant={isUp ? "positive" : "negative"}>
                  {row.direction}
                </Badge>
              )}
              {row.top3_shap && (
                <Badge variant="secondary">
                  {t("Key factors", "ปัจจัยหลัก")}: {
                    (() => {
                      try {
                        const parsed = JSON.parse(String(row.top3_shap).replace(/'/g, '"'))
                        return Array.isArray(parsed) ? parsed.join(", ") : String(row.top3_shap)
                      } catch {
                        return String(row.top3_shap)
                      }
                    })()
                  }
                </Badge>
              )}
            </div>

            {/* Reasoning text */}
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
              <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-line">
                {row.reasoning}
              </p>
            </div>
          </>
        ) : (
          <div className="text-sm text-gray-500">
            {t("No data for this month.", "ไม่มีข้อมูลสำหรับเดือนนี้")}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// --- FORECAST PAGE ---
function ForecastPage({ t, lang, series, summary, allExplain, news = [], onSelectAspect }) {
  const [dateRange, setDateRange] = React.useState(["", ""])

  React.useEffect(() => {
    if (series?.length && !dateRange[0] && !dateRange[1]) {
      setDateRange([series[0].date, series[series.length - 1].date])
    }
  }, [series])

  const filteredSeries = React.useMemo(() => {
    if (!series?.length) return []
    const start = dateRange[0] ? new Date(dateRange[0]) : null
    const end = dateRange[1] ? new Date(dateRange[1]) : null
    return series.filter((s) => {
      const d = new Date(s.date)
      if (start && d < start) return false
      if (end && d > end) return false
      return true
    })
  }, [series, dateRange])

  const metrics = React.useMemo(() => {
    if (summary?.latest_value != null && summary?.prev_value != null) {
      const curr = Number(summary.latest_value)
      const prev = Number(summary.prev_value)
      const momPts = Number(summary.mom_change)
      const momPct = prev !== 0 ? (momPts / prev) * 100 : null
      const tone = summary.trend === "UP" ? "up" : summary.trend === "DOWN" ? "down" : "neutral"
      return { curr, prev, momPts, momPct, tone }
    }
    const curr = currentCCI(filteredSeries)
    const prev = prevCCI(filteredSeries)
    const momPct = pctChange(curr, prev)
    const tone = momPct == null ? "neutral" : momPct > 0 ? "up" : "down"
    return { curr, prev, momPts: null, momPct, tone }
  }, [summary, filteredSeries])

  const futureStart = series.findIndex((s) => s.actual === null)
  const futureStartDate = futureStart >= 0 ? series[futureStart].date : filteredSeries[Math.floor(filteredSeries.length * 0.75)]?.date
  const latestActualDate = series.filter((s) => s.actual !== null).slice(-1)[0]?.date || asOf

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <MetricCard
          icon={BarChart3}
          title={t("Current CCI", "ค่า CCI ล่าสุด")}
          value={metrics.curr != null ? metrics.curr.toFixed(1) : "-"}
          subtitle={
            metrics.momPts != null
              ? `MoM ${metrics.momPts >= 0 ? "↑" : "↓"} ${Math.abs(metrics.momPts).toFixed(1)} pts`
              : (metrics.momPct != null
                  ? `MoM ${metrics.momPct >= 0 ? "↑" : "↓"} ${Math.abs(metrics.momPct).toFixed(1)}%`
                  : "N/A")
          }
          tone={metrics.tone}
        />
        <MetricCard
          icon={Activity}
          title={t("Data as of", "ข้อมูล ณ")}
          value={lang === "th" ? thaiMonth(latestActualDate) : latestActualDate.slice(0, 7)}
          subtitle={t("Updated monthly", "อัปเดตทุกเดือน")}
          tone="neutral"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <div className="lg:col-span-2 space-y-6">

          {/* ExplainBox — now uses allExplain with date picker */}
          <ExplainBox t={t} lang={lang} allExplain={allExplain} />

          {/* CCI Chart */}
          <Card>
            <CardHeader>
              <CardTitle>{t("CCI – Thailand", "CCI – ประเทศไทย")}</CardTitle>
              <CardDescription>
                <div className="flex flex-wrap gap-4 items-center">
                  <MonthYearPicker
                    value={dateRange[0]?.slice(0, 7)}
                    onChange={(v) => setDateRange([v + "-01", dateRange[1]])}
                    lang={lang}
                  />
                  →
                  <MonthYearPicker
                    value={dateRange[1]?.slice(0, 7)}
                    onChange={(v) => setDateRange([dateRange[0], v + "-01"])}
                    lang={lang}
                  />
                </div>
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <ComposedChart data={filteredSeries}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(v) => v ? v.slice(0, 7) : v} />
                  <YAxis domain={["dataMin - 5", "dataMax + 5"]} tick={{ fontSize: 11 }} />
                  <ReTooltip content={({ active, payload, label }) => {
                    if (!active || !payload?.length) return null
                    const actualItem = payload.find(p => p.dataKey === "actual")
                    const predItem = payload.find(p => p.dataKey === "pred")
                    const av = actualItem?.value
                    const pv = predItem?.value
                    return (
                      <div style={{ background: "rgba(255,255,255,0.95)", border: "1px solid #ddd", padding: 10, borderRadius: 8 }}>
                        <div style={{ fontWeight: "bold", marginBottom: 4 }}>{label}</div>
                        {av != null && <div style={{ color: THEME.primary }}>{t("Actual", "ค่าจริง")} : {Number(av).toFixed(1)}</div>}
                        {pv != null && <div style={{ color: THEME.primaryLight }}>{t("Forecast", "พยากรณ์")} : {Number(pv).toFixed(1)}</div>}
                      </div>
                    )
                  }} />
                  <Legend verticalAlign="top" height={36} wrapperStyle={{ paddingBottom: "10px" }} />
                  <Line type="monotone" dataKey="actual" stroke={THEME.primary} strokeWidth={2} dot={{ r: 3 }} name={t("Actual", "ค่าจริง")} connectNulls={false} />
                  <Line type="monotone" dataKey="pred" stroke={THEME.primaryLight} strokeWidth={2} strokeDasharray="5 5" dot={{ r: 3 }} name={t("Forecast", "พยากรณ์")} connectNulls={false} />
                  {futureStartDate && (
                    <ReferenceArea
                      x1={futureStartDate}
                      fill={THEME.primaryLight}
                      fillOpacity={0.1}
                      label={{ value: t("Forecast Period", "ช่วงพยากรณ์"), position: "insideTopRight", fontSize: 11 }}
                    />
                  )}
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-1">
          <TopAspectsOnlyCard t={t} news={news} onSelectAspect={onSelectAspect} />
        </div>
      </div>
    </div>
  )
}

// --- ANALYTICS PAGE ---
function AnalyticsPage({ t, lang, news = [], shapData = [] }) {
  const [agencyStack, setAgencyStack] = React.useState({ data: [], groups: [] })
  const [agencyErr, setAgencyErr] = React.useState("")

  const news1y = React.useMemo(() => filterNewsLast12Months(news), [news])
  const aspectStack = React.useMemo(() => {
    return stackCountByMonth(news1y, (n) => n.aspect || "Unknown", ASPECTS_TO_RUN)
  }, [news1y])

  const shapArr = React.useMemo(() => {
    const raw = Array.isArray(shapData) ? shapData : (shapData?.data ?? [])
    return raw
  }, [shapData])

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
    return () => { alive = false }
  }, [])

  const [topEntities, setTopEntities] = React.useState([])
  React.useEffect(() => {
    fetch("/data/top_entities.json")
      .then((r) => r.json())
      .then((data) => setTopEntities(data.slice(0, 12)))
      .catch(() => setTopEntities([]))
  }, [])

  const sentimentHistogram = React.useMemo(() => {
    const bins = Array.from({ length: 10 }, (_, i) => {
      const min = i / 10
      const max = (i + 1) / 10
      let color = "#dc2626"
      if (max > 0.6) color = "#16a34a"
      else if (min >= 0.4 && max <= 0.6) color = "#9ca3af"
      return { range: `${min.toFixed(1)}–${max.toFixed(1)}`, min, max, count: 0, fill: color }
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
      cumulative += n.sentiment
      return {
        date: n.date,
        sentiment: cumulative,
        positive: n.sentiment > 0 ? n.sentiment : 0,
        negative: n.sentiment < 0 ? Math.abs(n.sentiment) : 0,
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
        headline: String(n.title || "").substring(0, 30),
        impactLabel: n.impactType || "Neutral",
        effectLabel: n.effectType || "Short-term",
      }
      if (n.effectType === "Long-term") longTerm.push(point)
      else shortTerm.push(point)
    })
    return { shortTermData: shortTerm, longTermData: longTerm }
  }, [news])

  return (
    <div className="space-y-8">
      <div>
        <SectionHeader title={t("Domestic Factors", "ปัจจัยภายในประเทศ")} icon={Activity} />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-4">
          <Card>
            <CardHeader><CardTitle>{t("Purchasing Power & Consumption", "กำลังซื้อและการบริโภค")}</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={domesticFactors}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
                  <ReTooltip /><Legend />
                  <Line yAxisId="left" type="monotone" dataKey="purchasing" stroke="#3b82f6" name={t("Purchasing Index", "ดัชนีกำลังซื้อ")} strokeWidth={2} />
                  <Line yAxisId="right" type="monotone" dataKey="retail" stroke="#059669" name={t("Retail Growth %", "การค้าปลีก %")} strokeWidth={2} />
                  <Line yAxisId="right" type="monotone" dataKey="consumption" stroke="#f59e0b" name={t("Consumption %", "การบริโภค %")} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>{t("GDP Growth", "การเติบโตของ GDP")}</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={gdpData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="quarter" tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="left" tick={{ fontSize: 11 }} label={{ value: "GDP %", angle: -90, position: "insideLeft" }} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} label={{ value: "Growth %", angle: 90, position: "insideRight" }} />
                  <ReTooltip /><Legend />
                  <Bar yAxisId="left" dataKey="gdp" fill="#003d82" name={t("GDP %", "GDP %")} />
                  <Line yAxisId="right" type="monotone" dataKey="growth" stroke="#f59e0b" strokeWidth={2} name={t("YoY Growth", "การเติบโต YoY")} />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>{t("SET Index & Foreign Flow", "ดัชนี SET และกระแสเงินทุนต่างชาติ")}</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={setFactors}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
                  <ReTooltip /><Legend />
                  <Line yAxisId="left" type="monotone" dataKey="setIndex" stroke="#8b5cf6" strokeWidth={2} name={t("SET Index", "ดัชนี SET")} />
                  <Bar yAxisId="right" dataKey="foreignFlow" fill="#3b82f6" name={t("Foreign Flow (Bn)", "กระแสเงินทุน (พันล้าน)")} />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>{t("Inflation", "อัตราเงินเฟ้อ")}</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={inflationData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} label={{ value: "%", angle: -90, position: "insideLeft" }} />
                  <ReTooltip /><Legend />
                  <Line type="monotone" dataKey="headline" stroke="#dc2626" strokeWidth={2} name={t("Headline Inflation", "เงินเฟ้อทั่วไป")} />
                  <Line type="monotone" dataKey="core" stroke="#f59e0b" strokeWidth={2} name={t("Core Inflation", "เงินเฟ้อพื้นฐาน")} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      </div>

      <div>
        <SectionHeader title={t("News Analysis Visualizations", "การวิเคราะห์ข่าวเชิงลึก")} icon={BarChart3} />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>{t("News Volume by Agency", "ปริมาณข่าวตามสำนักข่าว")}</CardTitle>
              <CardDescription>{t("Stacked by agency per month", "กราฟแท่งซ้อนตามสำนักข่าวรายเดือน")}</CardDescription>
            </CardHeader>
            <CardContent>
              {agencyErr && (
                <div className="mb-3 p-3 rounded border border-red-200 bg-red-50 text-red-700 text-sm">{agencyErr}</div>
              )}
              {!agencyErr && agencyStack.data.length === 0 ? (
                <div className="p-3 text-sm text-gray-600">กำลังโหลดข้อมูลจาก Supabase…</div>
              ) : (
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={agencyStack.data} margin={{ bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <ReTooltip /><Legend />
                    {agencyStack.groups.map((agency, i) => (
                      <Bar key={agency} dataKey={agency} stackId="1"
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
              <CardTitle>{t("News Volume by Aspect", "ปริมาณข่าวตามประเด็น")}</CardTitle>
              <CardDescription>{t("Stacked by aspect per month", "กราฟแท่งซ้อนตามประเด็นรายเดือน")}</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={aspectStack.data} margin={{ bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <ReTooltip /><Legend />
                  {aspectStack.groups.map((asp, i) => (
                    <Bar key={asp} dataKey={asp} stackId="1" fill={CHART_COLORS[i % CHART_COLORS.length]} name={asp} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>{t("Sentiment Distribution", "การกระจาย Sentiment")}</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={sentimentHistogram}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="range" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 11 }} label={{ value: t("Count", "จำนวน"), angle: -90, position: "insideLeft" }} />
                  <ReTooltip />
                  <Bar dataKey="count" fill="#3b82f6" name={t("News Count", "จำนวนข่าว")} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>{t("Sentiment Flow Over Time", "กระแสความรู้สึกตามเวลา")}</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={sentimentFlow}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <ReTooltip /><Legend />
                  <Area type="monotone" dataKey="positive" stackId="1" stroke="#059669" fill="#059669" name={t("Positive", "บวก")} />
                  <Area type="monotone" dataKey="negative" stackId="1" stroke="#dc2626" fill="#dc2626" name={t("Negative", "ลบ")} />
                  <Line type="monotone" dataKey="sentiment" stroke="#1e40af" strokeWidth={2} name={t("Cumulative", "สะสม")} />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t("Impact vs Sentiment Matrix", "เมทริกซ์ผลกระทบกับความรู้สึก")}</CardTitle>
              <CardDescription>{t("Each dot = 1 news article. X=Sentiment, Y=Impact direction", "แต่ละจุด = 1 ข่าว, แกน X=Sentiment, แกน Y=ทิศทางผลกระทบ")}</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={320}>
                <ScatterChart margin={{ bottom: 25, left: 20, right: 10, top: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="sentiment" tick={{ fontSize: 11 }} type="number" name="Sentiment" label={{ value: t("Sentiment Score", "Sentiment Score"), position: "insideBottom", offset: -15 }} />
                  <YAxis dataKey="impact" tick={{ fontSize: 11 }} type="number" ticks={[-1, 0, 1]}
                    tickFormatter={(v) => v === -1 ? "Negative" : v === 0 ? "Neutral" : "Positive"}
                    label={{ value: t("Impact", "ผลกระทบ"), angle: -90, position: "insideLeft", offset: 5 }}
                  />
                  <ReTooltip content={({ payload }) => {
                    if (!payload || !payload.length) return null
                    const d = payload[0]?.payload
                    return (
                      <div className="bg-white border rounded shadow p-2 text-xs max-w-xs">
                        <div className="font-semibold">{d?.headline}</div>
                        <div>Sentiment: {d?.sentiment?.toFixed(2)}</div>
                        <div>Impact: {d?.impactLabel}</div>
                        <div>Effect: {d?.effectLabel}</div>
                      </div>
                    )
                  }} />
                  <Scatter name={t("Short-term", "ระยะสั้น")} data={shortTermData} fill="#3b82f6" opacity={0.6} />
                  <Scatter name={t("Long-term", "ระยะยาว")} data={longTermData} fill="#f59e0b" opacity={0.6} />
                  <Legend verticalAlign="top" height={30} />
                </ScatterChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>{t("Feature Importance", "ปัจจัยที่สำคัญ")}</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={shapRows} layout="vertical" margin={{ top: 10, right: 40, left: 20, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="name" width={200} />
                  <ReTooltip />
                  <Bar dataKey="absValue" name={t("Importance", "ความสำคัญ")} fill="#003d82" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="lg:col-span-2">
            <Card>
              <CardHeader><CardTitle>{t("Word Cloud", "คำที่ปรากฏบ่อย")}</CardTitle></CardHeader>
              <CardContent>
                <div className="w-full bg-white rounded-lg border border-gray-100 overflow-hidden">
                  <img src={wordcloudImg} alt="CCI Impact Word Cloud" className="w-full h-auto rounded" />
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )

  // --- NEW COMPONENT: Interactive Timeline ---
function TimelinePicker({ availableMonths, selectedDate, onChange }) {
  return (
    <div className="flex flex-col space-y-2 mb-6">
      <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
        Select Forecast Horizon
      </label>
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hide">
        {availableMonths.map((m) => {
          const isActive = m === selectedDate;
          const isFuture = new Date(m) > new Date("2025-07-01");
          return (
            <button
              key={m}
              onClick={() => onChange(m)}
              className={`flex flex-col items-center min-w-[80px] p-3 rounded-xl border transition-all ${
                isActive 
                  ? "bg-blue-600 border-blue-600 text-white shadow-lg scale-105" 
                  : "bg-white border-gray-100 text-gray-600 hover:border-blue-300"
              }`}
            >
              <span className="text-[10px] opacity-70">{m.split('-')[0]}</span>
              <span className="text-sm font-bold">{m.split('-')[1]}</span>
              {isFuture && <div className={`w-1 h-1 rounded-full mt-1 ${isActive ? "bg-white" : "bg-blue-400"}`} />}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// --- REDESIGNED FORECAST PAGE ---
function ForecastPage({ t, lang, series, summary, allExplain, news, onSelectAspect }) {
  const [selectedDate, setSelectedDate] = React.useState("2025-08"); // Default to next month

  const availableMonths = React.useMemo(() => 
    allExplain.map(r => r.date).sort(), [allExplain]
  );

  const activeRow = allExplain.find(r => r.date === selectedDate);

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in duration-700">
      
      {/* 1. TOP METRICS GRID */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Actual Value (Past) */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <p className="text-sm text-gray-500 font-medium">{t("Last Actual (July 2025)", "ค่าจริงล่าสุด (ก.ค. 2568)")}</p>
          <div className="flex items-baseline gap-2 mt-2">
            <h2 className="text-4xl font-black text-gray-800">51.7</h2>
            <span className="text-red-500 text-sm font-bold">↓ 1.0</span>
          </div>
        </div>

        {/* Prediction Value (Target) */}
        <div className="bg-[#1F3A5F] p-6 rounded-2xl shadow-xl border border-blue-900 transform scale-105">
          <p className="text-blue-200 text-sm font-medium">
            {t("Forecast Target", "เป้าหมายพยากรณ์")} : {selectedDate}
          </p>
          <div className="flex items-baseline gap-2 mt-2">
            <h2 className="text-4xl font-black text-white">
              {activeRow?.predicted ? Number(activeRow.predicted).toFixed(2) : "---"}
            </h2>
            <Badge variant={activeRow?.direction?.includes("เพิ่ม") ? "positive" : "negative"} className="ml-2">
              {activeRow?.direction || "Stable"}
            </Badge>
          </div>
        </div>

        {/* Confidence / Data Source */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <p className="text-sm text-gray-500 font-medium">{t("Model Status", "สถานะโมเดล")}</p>
          <div className="flex items-center gap-2 mt-3">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
            <span className="font-bold text-gray-700">XAI - Ready</span>
          </div>
        </div>
      </div>

      {/* 2. TIMELINE & EXPLANATION SECTION */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          
          <TimelinePicker 
            availableMonths={availableMonths} 
            selectedDate={selectedDate} 
            onChange={setSelectedDate} 
          />

          <Card className="overflow-hidden border-none shadow-xl">
            <CardHeader className="bg-gradient-to-r from-gray-50 to-white">
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-blue-600" />
                {t("Economic Reasoning", "บทวิเคราะห์เชิงพยากรณ์")}
              </CardTitle>
            </CardHeader>
            <CardContent className="bg-white pt-6">
              {/* Feature Importance Tags (SHAP) */}
              <div className="flex flex-wrap gap-2 mb-6">
                {activeRow?.top3_shap && JSON.parse(activeRow.top3_shap.replace(/'/g, '"')).map(tag => (
                  <span key={tag} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-bold border border-blue-100">
                    # {tag}
                  </span>
                ))}
              </div>
              
              <div className="relative">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500 rounded-full" />
                <p className="pl-6 text-gray-700 leading-relaxed text-lg italic font-serif">
                  "{activeRow?.reasoning}"
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 3. SIDEBAR: IMPACT SUMMARY */}
        <div className="space-y-6">
           <TopAspectsOnlyCard t={t} news={news} onSelectAspect={onSelectAspect} />
           {/* Mini Wordcloud or small Gauge Chart could go here */}
        </div>
      </div>

      {/* 4. MAIN CHART */}
      <Card className="shadow-sm border-gray-100">
        <CardContent className="p-8">
           <ResponsiveContainer width="100%" height={400}>
              {/* Your existing ComposedChart code here... */}
           </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
}

// --- MAIN APP ---
export default function App() {
  const { lang, setLang, t } = useLang()
  const { page, setPage } = useNavigation()
  const [selectedAspect, setSelectedAspect] = React.useState(null)

  const [summary, setSummary] = React.useState(null)
  const [allExplain, setAllExplain] = React.useState([])   // ← was explain
  const [series, setSeries] = React.useState([])
  const [err, setErr] = React.useState("")
  const [newsReal, setNewsReal] = React.useState([])
  const [shapData, setShapData] = React.useState([])

  React.useEffect(() => {
    let alive = true
    async function load() {
      setErr("")
      try {
        const [s, e, ts, newsRows, shapRes] = await Promise.allSettled([
          getSummary(),
          getAllExplain(),          // ← was getLatestExplain()
          getTimeSeries(2000),
          getNews(),
          getShap(),
        ])

        if (!alive) return

        setSummary(s.status === "fulfilled" ? s.value : null)
        setAllExplain(e.status === "fulfilled" ? (e.value?.data || []) : [])  // ← flat array
        setSeries(ts.status === "fulfilled" ? (ts.value?.data || []) : [])
        setNewsReal(newsRows.status === "fulfilled" ? (newsRows.value?.data || []) : [])
        setShapData(shapRes.status === "fulfilled" ? (shapRes.value?.data || []) : [])

      } catch (ex) {
        if (!alive) return
        setErr(String(ex?.message || ex))
      }
    }
    load()
    return () => { alive = false }
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      <div className="bg-[#1F3A5F] text-white shadow-lg sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <Activity className="w-8 h-8 text-white" />
              <div>
                <h1 className="text-xl font-bold">{t("XEconomic", "XEconomic")}</h1>
                <p className="text-sm text-blue-200">{t("CCI Forecast and XAI", "CCI Forecast and XAI")}</p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setLang("en")}
                className={`px-3 py-1 text-xs font-bold rounded transition-all ${lang === "en" ? "bg-white text-[#1F3A5F]" : "text-white border border-white/40 hover:bg-white/10"}`}
              >
                EN
              </button>
              <button
                onClick={() => setLang("th")}
                className={`px-3 py-1 text-xs font-bold rounded transition-all ${lang === "th" ? "bg-white text-[#1F3A5F]" : "text-white border border-white/40 hover:bg-white/10"}`}
              >
                ไทย
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <TopNav t={t} page={page} setPage={setPage} />

        {page === "forecast" && (
          <ForecastPage
            t={t}
            lang={lang}
            series={series}
            summary={summary}
            allExplain={allExplain}        // ← was explain={explain}
            news={newsReal}
            onSelectAspect={(aspect) => {
              setSelectedAspect(aspect)
              setPage("aspectNews")
            }}
          />
        )
        }

        {page === "aspectNews" && (
          <AspectNewsPage
            t={t}
            lang={lang}
            aspect={selectedAspect}
            news={newsReal}
            onBack={() => setPage("forecast")}
          />
        )}

        {page === "analytics" && (
          <AnalyticsPage t={t} lang={lang} news={newsReal} shapData={shapData} />
        )}
      </div>

      <div className="bg-gray-100 border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-6 py-4 text-center text-sm text-gray-600">
          © Copyright SP2025-40 XEconomics
        </div>
      </div>
    </div>
  )
}
