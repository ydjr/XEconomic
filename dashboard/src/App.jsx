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
  previousMonthActual,
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
              {t("Previous month actual data", "ข้อมูลจริงของเดือนก่อนหน้า")}
            </div>
            <div className="text-3xl font-black text-gray-900 leading-none">
              {previousMonthActual != null ? Number(previousMonthActual).toFixed(1) : "-"}
            </div>
          </div>

          <div
            className="rounded-2xl border p-4 flex-1"
            style={{
              borderColor: THEME.border,
              backgroundColor: tone.soft,
            }}
          >
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              <div className="min-w-0">
                <div className="text-xs text-gray-500 mb-1">
                  {t("Target month predicted data", "ข้อมูลพยากรณ์ของเดือนเป้าหมาย")}
                </div>
                <div className="text-4xl font-black text-gray-900 leading-none mb-2">
                  {predicted != null ? Number(predicted).toFixed(1) : "-"}
                </div>
              </div>

              <div className="flex items-center gap-4 md:justify-end">
                {/* <div className="text-sm text-gray-600">
                  {t(
                    "Direction compared target month predicted data to the previous month actual data",
                    "ทิศทางเมื่อเปรียบเทียบข้อมูลพยากรณ์ของเดือนเป้าหมายกับข้อมูลจริงของเดือนก่อนหน้า"
                  )}
                </div> */}
                <div
                  className={`text-6xl font-light leading-none ${info.tone === "up"
                    ? "animate-bounce"
                    : info.tone === "down"
                      ? "animate-pulse"
                      : ""
                    }`}
                  style={{ color: tone.text }}
                >
                  {arrow}
                </div>

                <div className="flex flex-col">
                  <div
                    className="inline-flex w-fit px-3 py-1 rounded-full text-sm font-semibold mb-2"
                    style={{
                      backgroundColor: tone.bg,
                      color: tone.text,
                    }}
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
            {t("Period", "ช่วงเวลา")}: {periodText}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="min-h-[320px]">
        {ranked.length === 0 ? (
          <div className="text-sm text-gray-500">
            {t("No aspect data for this period.", "ไม่พบข้อมูลประเด็นสำหรับช่วงเวลานี้")}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {ranked.map((item) => (
              <button
                key={item.aspect}
                onClick={() => onSelectAspect?.(item.aspect)}
                className="w-full px-4 py-3 rounded-xl border hover:bg-slate-50 transition text-left"
                style={{ borderColor: THEME.border }}
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-semibold text-gray-800">{item.aspect}</span>
                  <Badge variant="secondary">{item.count}</Badge>
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

    const lastDate = new Date(series[series.length - 1].date)
    const cutoff = new Date(lastDate)
    cutoff.setFullYear(cutoff.getFullYear() - 2)

    return series.filter((d) => new Date(d.date) >= cutoff)
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

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("CCI timeline", "กราฟ CCI")}</CardTitle>
        <CardDescription>{t("Actual values and future forecast on one chart", "แสดงค่าจริงและค่าพยากรณ์ในกราฟเดียว")}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="w-full overflow-x-auto">
          <div style={{ width: chartData.length * 50, height: 420 }}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) =>
                    lang === "th" ? thaiMonthYear(v).replace(" ", "\n") : String(v).slice(0, 7)
                  }
                />
                <YAxis tick={{ fontSize: 11 }} />
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
                            {t("Forecast", "พยากรณ์")}: {Number(predItem.value).toFixed(2)}
                          </div>
                        ) : null}
                      </div>
                    )
                  }}
                />
                <Legend verticalAlign="top" height={40} />

                {forecastStartDate ? (
                  <ReferenceArea x1={forecastStartDate} fill={THEME.blue} fillOpacity={0.05} />
                ) : null}

                {selectedDate ? (
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
                  name={t("Actual", "ค่าจริง")}
                  connectNulls={false}
                />
                <Line
                  type="monotone"
                  dataKey="pred"
                  stroke={THEME.blue}
                  strokeWidth={2.5}
                  dot={{ r: 3 }}
                  strokeDasharray="6 6"
                  name={t("Forecast", "พยากรณ์")}
                  connectNulls={false}
                />
                {/* <Line
                  type="monotone"
                  dataKey="selectedPred"
                  stroke={THEME.blue}
                  strokeWidth={4}
                  dot={{ r: 5 }}
                  activeDot={{ r: 6 }}
                  name={t("Selected forecast", "ค่าพยากรณ์ที่เลือก")}
                  connectNulls={false}
                /> */}
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      </CardContent>
    </Card>
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

  return (
    <div className="space-y-6">
      <ForecastSummaryCard
        t={t}
        lang={lang}
        month={selectedForecastMonth}
        predicted={selectedSeriesRow?.pred}
        direction={selectedSeriesRow?.direction}
        previousMonthActual={previousMonthActual}
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
          <div className="text-sm text-gray-500">
            {t("No explanation found for this month.", "ไม่พบคำอธิบายสำหรับเดือนนี้")}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

const PER_PAGE = 15

function AspectNewsPage({ t, lang, aspect, news = [], onBack }) {
  const [currentPage, setCurrentPage] = React.useState(1)

  const newsForAspect = React.useMemo(() => {
    if (!aspect) return []
    return [...news]
      .filter((n) => (n.aspect || "Unknown") === aspect)
      .sort((a, b) => b.date.localeCompare(a.date))
  }, [aspect, news])

  React.useEffect(() => {
    setCurrentPage(1)
  }, [aspect])

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
        <button
          onClick={onBack}
          className="px-4 py-2 rounded-xl bg-white hover:bg-gray-50 transition"
          style={{ border: `1px solid ${THEME.border}` }}
        >
          ← {t("Back", "ย้อนกลับ")}
        </button>
        <div className="text-xs text-gray-500">{t("Sorted by newest", "เรียงล่าสุดก่อน")}</div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            {t("Aspect", "ประเด็น")}: {aspect ?? t("Not selected", "ยังไม่ได้เลือก")}
          </CardTitle>
          <CardDescription>
            {t("News list for the selected aspect", "รายการข่าวสำหรับประเด็นที่เลือก")}
            {newsForAspect.length > 0 ? (
              <span className="ml-2 text-gray-400">({t(`${newsForAspect.length} total`, `ทั้งหมด ${newsForAspect.length} ข่าว`)})</span>
            ) : null}
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
                  const tagLabel = lang === "th" ? tagTH[n.tag] || n.tag : n.tag
                  const globalIdx = (currentPage - 1) * PER_PAGE + idx

                  return (
                    <div key={`${n.date}-${globalIdx}`} className="p-6 hover:bg-gray-50 transition">
                      <div className="text-xs text-gray-500">
                        {displayDate} • {n.source}
                      </div>
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

  return (
    <div className="space-y-8">
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
              <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 text-sm p-3">{agencyErr}</div>
            ) : agencyStack.data.length === 0 ? (
              <div className="text-sm text-gray-500">{t("Loading from Supabase…", "กำลังโหลดข้อมูลจาก Supabase…")}</div>
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

  // ── Month state lifted up so the subbar can access it ──
  const [selectedForecastMonth, setSelectedForecastMonth] = React.useState("")

  const latestActualMonth = React.useMemo(() => {
    const actualRows = (series || []).filter((r) => r.actual != null && r.date)
    if (!actualRows.length) return null
    return actualRows[actualRows.length - 1].date.slice(0, 7)
  }, [series])

  const forecastMonths = React.useMemo(() => {
    if (!latestActualMonth) return []
    const [year, month] = latestActualMonth.split("-").map(Number)
    const base = new Date(year, month - 1, 1)
    const months = []
    for (let i = 1; i <= 3; i++) {
      const d = new Date(base)
      d.setMonth(d.getMonth() + i)
      months.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`)
    }
    return months
  }, [latestActualMonth])

  const explainMonths = React.useMemo(
    () => [...new Set((allExplain || []).map((r) => r.date).filter(Boolean))].sort((a, b) => a.localeCompare(b)),
    [allExplain]
  )

  const seriesMonths = React.useMemo(
    () => [...new Set((series || []).map((r) => r.date?.slice(0, 7)).filter(Boolean))].sort((a, b) => a.localeCompare(b)),
    [series]
  )

  const availableFutureMonths = React.useMemo(
    () => forecastMonths.filter((m) => explainMonths.includes(m) || seriesMonths.includes(m)),
    [forecastMonths, explainMonths, seriesMonths]
  )

  const historicalMonths = React.useMemo(
    () => explainMonths.filter((m) => !forecastMonths.includes(m)),
    [explainMonths, forecastMonths]
  )

  React.useEffect(() => {
    const allPossibleMonths = [...new Set([...availableFutureMonths, ...historicalMonths])].sort((a, b) => a.localeCompare(b))
    if (!allPossibleMonths.length) return
    if (!allPossibleMonths.includes(selectedForecastMonth)) {
      setSelectedForecastMonth(
        availableFutureMonths.length > 0
          ? availableFutureMonths[0]
          : allPossibleMonths[allPossibleMonths.length - 1]
      )
    }
  }, [availableFutureMonths, historicalMonths, selectedForecastMonth])

  // ── Data loading ──
  React.useEffect(() => {
    let alive = true
    async function load() {
      setErr("")
      try {
        const [s, e, ts, newsRows, shapRes] = await Promise.allSettled([
          getSummary(), getAllExplain(), getTimeSeries(2000), getNews(), getShap(),
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
    return () => { alive = false }
  }, [])

  const isHistorical = historicalMonths.includes(selectedForecastMonth)
  const showSubbar = page === "forecast" || page === "aspectNews"

  const tabs = [
    { id: "forecast",  en: "Forecast & Reasoning",  th: "การพยากรณ์และคำอธิบาย",    Icon: TrendingUp },
    { id: "analytics", en: "News & Analytics",       th: "ข้อมูลข่าวและการวิเคราะห์", Icon: BarChart3  },
  ]

  return (
    <div className="min-h-screen" style={{ background: "#F0F4FA" }}>

      {/* ── Topbar ── */}
      <div
        className="sticky top-0 z-50 w-full"
        style={{ backgroundColor: THEME.navy, borderBottom: "1px solid rgba(255,255,255,0.08)" }}
      >
        {/* Main bar */}
        <div
          className="max-w-[1400px] mx-auto px-7 flex items-center justify-between gap-6"
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
              <div className="text-white font-semibold" style={{ fontSize: 20 }}>XEconomic</div>
              <div style={{ fontSize: 13, color: "rgba(255,255,255,0.45)", marginTop: 1 }}>
                CCI Forecast &amp; XAI
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div
            className="flex items-center gap-0.5 rounded-[10px] p-[3px]"
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

          {/* Language toggle */}
          <div
            className="flex items-center gap-0.5 rounded-lg p-[3px] flex-shrink-0"
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
        </div>

        {/* Subbar — forecast context + month picker */}
        {showSubbar && (
          <div style={{ background: "#1a4280", borderTop: "1px solid rgba(255,255,255,0.07)" }}>
            <div
              className="max-w-[1400px] mx-auto px-7 flex items-center"
              style={{ height: 44, gap: 0 }}
            >
              {/* Context pill */}
              <div
                className="flex items-center gap-2 flex-shrink-0"
                style={{ paddingRight: 20, borderRight: "1px solid rgba(255,255,255,0.1)" }}
              >
                <div
                  className="rounded-full flex-shrink-0"
                  style={{
                    width: 6, height: 6,
                    background: isHistorical ? "rgba(255,255,255,0.35)" : "#4ade80",
                  }}
                />
                <span style={{ fontSize: 12, color: "rgba(255,255,255,0.5)" }}>
                  {isHistorical
                    ? t("Viewing history for", "กำลังดูประวัติ")
                    : t("Viewing forecast for", "กำลังดูการพยากรณ์")}
                </span>
                <span style={{ fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,0.9)" }}>
                  {monthLabel(selectedForecastMonth, lang)}
                </span>
              </div>

              {/* Month pills + historical picker */}
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
                    style={{
                      padding: "3px 11px",
                      borderRadius: 99,
                      fontSize: 12,
                      fontWeight: m === selectedForecastMonth ? 600 : 500,
                      color: m === selectedForecastMonth ? "#fff" : "rgba(255,255,255,0.6)",
                      background: m === selectedForecastMonth ? "rgba(255,255,255,0.18)" : "transparent",
                      border: `1px solid ${m === selectedForecastMonth ? "rgba(255,255,255,0.4)" : "rgba(255,255,255,0.15)"}`,
                      cursor: "pointer",
                      whiteSpace: "nowrap",
                      flexShrink: 0,
                      transition: "all 0.15s",
                    }}
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
                      <option value="" style={{ background: THEME.navy }}>{t("Select month…", "เลือกเดือน…")}</option>
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
      <div className="max-w-[1400px] mx-auto px-7 py-6 space-y-5">
        {err && (
          <div
            className="rounded-xl px-4 py-2.5 text-sm"
            style={{ background: "#FEF2F2", border: "1px solid #FECACA", color: "#B91C1C" }}
          >
            {err}
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
            onSelectAspect={(asp) => { setSelectedAspect(asp); setPage("aspectNews") }}
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