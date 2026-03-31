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
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
        styles[variant] || styles.secondary
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
            className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition ${
              active ? "text-white" : "text-gray-700 hover:bg-white"
            }`}
            style={{
              backgroundColor: active ? THEME.navy : "transparent",
              boxShadow: active ? "0 8px 20px rgba(22,58,112,0.18)" : "none",
            }}
          >
            <tab.icon className="w-4 h-4" />
            {t(tab.en, tab.th)}
          </button>
        )
      })}
    </div>
  )
}

function ForecastMonthSelector({ t, selectedMonth, onSelectMonth, futureMonths, historicalMonths, lang }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="text-sm font-semibold text-gray-800">{t("Forecast horizon", "ช่วงเดือนพยากรณ์")}</div>
          <div className="text-xs text-gray-500 mt-1">
            {t("Choose a month to inspect prediction and reasoning", "เลือกเดือนเพื่อดูค่าพยากรณ์และเหตุผลประกอบ")}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {futureMonths.map((m) => {
            const active = m === selectedMonth

            return (
              <button
                key={m}
                onClick={() => onSelectMonth(m)}
                className="px-4 py-2 rounded-xl text-sm font-semibold transition"
                style={{
                  backgroundColor: active ? THEME.blue : "#FFFFFF",
                  color: active ? "#FFFFFF" : "#334155",
                  border: `1px solid ${active ? THEME.blue : THEME.border}`,
                  boxShadow: active ? "0 10px 20px rgba(47,111,237,0.20)" : "none",
                }}
              >
                {lang === "th" ? thaiMonthYear(m) : m}
              </button>
            )
          })}

          {historicalMonths.length > 0 ? (
            <select
              value={historicalMonths.includes(selectedMonth) ? selectedMonth : ""}
              onChange={(e) => {
                if (e.target.value) onSelectMonth(e.target.value)
              }}
              className="px-3 py-2 rounded-xl text-sm bg-white"
              style={{ border: `1px solid ${THEME.border}` }}
            >
              <option value="">{t("Historical explanation", "คำอธิบายย้อนหลัง")}</option>
              {historicalMonths.map((m) => (
                <option key={m} value={m}>
                  {lang === "th" ? thaiMonthYear(m) : m}
                </option>
              ))}
            </select>
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}

function HeroMetricCard({ title, value, subtitle, tone = "neutral", highlight = false }) {
  const toneMap = toneClasses(tone)

  return (
    <div
      className="rounded-2xl p-6 border h-full"
      style={{
        background: highlight ? `linear-gradient(135deg, ${THEME.navy} 0%, ${THEME.blue} 100%)` : "#FFFFFF",
        borderColor: highlight ? "transparent" : THEME.border,
        boxShadow: highlight ? "0 18px 40px rgba(22,58,112,0.18)" : "0 10px 30px rgba(22,58,112,0.06)",
      }}
    >
      <div className={`text-sm font-medium ${highlight ? "text-blue-100" : "text-gray-500"}`}>{title}</div>
      <div className={`mt-3 text-4xl font-black ${highlight ? "text-white" : "text-gray-900"}`}>{value}</div>
      {subtitle ? (
        <div
          className={`mt-2 text-sm ${highlight ? "text-blue-100" : ""}`}
          style={!highlight ? { color: toneMap.text } : {}}
        >
          {subtitle}
        </div>
      ) : null}
    </div>
  )
}

function ReasoningPanel({ t, lang, activeRow, selectedMonth }) {
  const shapTags = parseTop3Shap(activeRow?.top3_shap)
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
            <CardDescription>{t("Narrative explanation for the selected month", "คำอธิบายเชิงเหตุผลสำหรับเดือนที่เลือก")}</CardDescription>
          </div>

          <div className="flex flex-wrap gap-2">
            <Badge variant="outline">
              {t("Month", "เดือน")}: {monthLabel(selectedMonth, lang)}
            </Badge>
            {activeRow?.predicted != null ? (
              <Badge variant="navy">
                {t("Predicted CCI", "CCI พยากรณ์")}: {Number(activeRow.predicted).toFixed(2)}
              </Badge>
            ) : null}
            <Badge variant={directionInfo.tone === "up" ? "positive" : directionInfo.tone === "down" ? "negative" : "secondary"}>
              {directionInfo.badge}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {activeRow ? (
          <div className="space-y-5">
            {/* {shapTags.length > 0 ? (
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                  {t("Key drivers", "ปัจจัยขับเคลื่อนหลัก")}
                </div>
                <div className="flex flex-wrap gap-2">
                  {shapTags.map((tag) => (
                    <span
                      key={tag}
                      className="px-3 py-1.5 rounded-full text-xs font-semibold"
                      style={{
                        backgroundColor: "#EFF6FF",
                        color: THEME.blue,
                        border: "1px solid #DBEAFE",
                      }}
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              </div>
            ) : null} */}

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
                    {activeRow.reasoning || t("No reasoning available.", "ยังไม่มีคำอธิบาย")}
                  </p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-sm text-gray-500">{t("No explanation found for this month.", "ไม่พบคำอธิบายสำหรับเดือนนี้")}</div>
        )}
      </CardContent>
    </Card>
  )
}

function TopAspectsOnlyCard({ t, news = [], onSelectAspect }) {
  const ranked = React.useMemo(() => {
    const counts = {}
    news.forEach((n) => {
      const aspect = n.aspect || "Other"
      counts[aspect] = (counts[aspect] || 0) + 1
    })
    return Object.entries(counts)
      .map(([aspect, count]) => ({ aspect, count }))
      .sort((a, b) => b.count - a.count)
  }, [news])

  const top3 = ranked.slice(0, 3)

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>{t("Top aspects", "ประเด็นหลัก (Aspect)")}</CardTitle>
        <CardDescription>{t("Click an aspect to open its related news page", "คลิกประเด็นเพื่อเปิดหน้ารวมข่าวของประเด็นนั้น")}</CardDescription>
      </CardHeader>

      <CardContent className="space-y-5">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">{t("Top 3", "Top 3")}</div>
          <div className="grid grid-cols-1 gap-2">
            {top3.map((item) => (
              <button
                key={item.aspect}
                onClick={() => onSelectAspect?.(item.aspect)}
                className="text-left rounded-xl p-4 border bg-white hover:bg-slate-50 transition"
                style={{ borderColor: THEME.border }}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="font-semibold text-gray-900">{item.aspect}</div>
                  <Badge variant="outline">
                    {t("news", "ข่าว")}: {item.count}
                  </Badge>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">{t("All aspects", "ทุกประเด็น")}</div>
          <div className="flex flex-wrap gap-2">
            {ranked.map((item) => (
              <button
                key={item.aspect}
                onClick={() => onSelectAspect?.(item.aspect)}
                className="px-3 py-2 rounded-xl border hover:bg-slate-50 transition"
                style={{ borderColor: THEME.border }}
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-800">{item.aspect}</span>
                  <Badge variant="secondary">{item.count}</Badge>
                </div>
              </button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function ForecastChart({ t, lang, series, selectedMonth }) {
  const chartData = React.useMemo(() => buildSelectedMonthChartData(series, selectedMonth), [series, selectedMonth])

  const forecastStartDate = React.useMemo(() => {
    const firstForecast = series.find((s) => s.actual == null && s.pred != null)
    return firstForecast?.date || null
  }, [series])

  const selectedDate = selectedMonth ? `${selectedMonth}-01` : null

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("CCI timeline", "กราฟ CCI")}</CardTitle>
        <CardDescription>{t("Actual values and future forecast on one chart", "แสดงค่าจริงและค่าพยากรณ์ในกราฟเดียว")}</CardDescription>
      </CardHeader>

      <CardContent>
        <ResponsiveContainer width="100%" height={420}>
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11 }}
              tickFormatter={(v) => (lang === "th" ? thaiMonthYear(v).replace(" ", "\n") : String(v).slice(0, 7))}
            />
            <YAxis tick={{ fontSize: 11 }} />
            <ReTooltip
              content={({ active, payload, label }) => {
                if (!active || !payload?.length) return null

                const actualItem = payload.find((p) => p.dataKey === "actual")
                const predItem = payload.find((p) => p.dataKey === "pred")

                return (
                  <div className="rounded-xl border bg-white p-3 shadow-lg" style={{ borderColor: THEME.border }}>
                    <div className="font-semibold text-gray-900 mb-1">{monthLabel(label, lang)}</div>
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

            {forecastStartDate ? <ReferenceArea x1={forecastStartDate} fill={THEME.blue} fillOpacity={0.05} /> : null}

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
            <Line
              type="monotone"
              dataKey="selectedPred"
              stroke={THEME.blue}
              strokeWidth={4}
              dot={{ r: 5 }}
              activeDot={{ r: 6 }}
              name={t("Selected forecast", "ค่าพยากรณ์ที่เลือก")}
              connectNulls={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

function ForecastPage({ t, lang, series, summary, allExplain, news = [], onSelectAspect }) {
  const forecastMonths = React.useMemo(() => ["2025-08", "2025-09", "2025-10"], [])
  const allMonths = React.useMemo(
    () => [...new Set((allExplain || []).map((r) => r.date).filter(Boolean))].sort((a, b) => a.localeCompare(b)),
    [allExplain]
  )
  const historicalMonths = React.useMemo(() => allMonths.filter((m) => !forecastMonths.includes(m)), [allMonths, forecastMonths])

  const [selectedForecastMonth, setSelectedForecastMonth] = React.useState("2025-08")

  React.useEffect(() => {
    if (!allMonths.length) return

    if (!allMonths.includes(selectedForecastMonth)) {
      if (forecastMonths.some((m) => allMonths.includes(m))) {
        const firstFuture = forecastMonths.find((m) => allMonths.includes(m))
        if (firstFuture) setSelectedForecastMonth(firstFuture)
      } else {
        setSelectedForecastMonth(allMonths[allMonths.length - 1])
      }
    }
  }, [allMonths, selectedForecastMonth, forecastMonths])

  const activeRow = React.useMemo(
    () => allExplain.find((r) => r.date === selectedForecastMonth) || null,
    [allExplain, selectedForecastMonth]
  )

  const latestActualValue = summary?.latest_value
  const latestActualMonth = summary?.latest_month
  const momChange = summary?.mom_change
  const latestTrendTone = summary?.trend === "UP" ? "up" : summary?.trend === "DOWN" ? "down" : "neutral"
  const forecastDirection = normalizeDirection(activeRow?.direction, t)

  const latestSubtitle =
    momChange == null
      ? t("No monthly change available", "ไม่มีข้อมูลการเปลี่ยนแปลงรายเดือน")
      : `${t("MoM", "MoM")} ${momChange >= 0 ? "↑" : "↓"} ${Math.abs(Number(momChange)).toFixed(2)} ${t("pts", "จุด")}`

  const targetSubtitle = activeRow
    ? `${t("Target month", "เดือนเป้าหมาย")}: ${monthLabel(selectedForecastMonth, lang)}`
    : t("No forecast available", "ยังไม่มีค่าพยากรณ์")

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* <HeroMetricCard
          title={t("Latest actual", "ค่าจริงล่าสุด")}
          value={latestActualValue != null ? Number(latestActualValue).toFixed(1) : "-"}
          subtitle={`${monthLabel(latestActualMonth, lang)} • ${latestSubtitle}`}
          tone={latestTrendTone}
        /> */}
        <HeroMetricCard
          title={t("Forecast target", "เป้าหมายพยากรณ์")}
          value={activeRow?.predicted != null ? Number(activeRow.predicted).toFixed(2) : "-"}
          subtitle={targetSubtitle}
          tone={forecastDirection.tone}
          highlight
        />
        {/* <HeroMetricCard
          title={t("Model status", "สถานะโมเดล")}
          value={t("Ready", "พร้อมใช้งาน")}
          subtitle={t("XAI explanation available", "มีคำอธิบายเชิง XAI")}
          tone="neutral"
        /> */}
      </div>

      <ForecastMonthSelector
        t={t}
        selectedMonth={selectedForecastMonth}
        onSelectMonth={setSelectedForecastMonth}
        futureMonths={forecastMonths.filter((m) => allMonths.includes(m) || forecastMonths.includes(m))}
        historicalMonths={historicalMonths}
        lang={lang}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <div className="lg:col-span-2 space-y-6">
          <ReasoningPanel t={t} lang={lang} activeRow={activeRow} selectedMonth={selectedForecastMonth} />
          <ForecastChart t={t} lang={lang} series={series} selectedMonth={selectedForecastMonth} />
        </div>

        <div className="lg:col-span-1">
          <TopAspectsOnlyCard t={t} news={news} onSelectAspect={onSelectAspect} />
        </div>
      </div>
    </div>
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

  return (
    <div className="min-h-screen" style={{ background: "linear-gradient(180deg, #F4F7FC 0%, #EEF3FA 100%)" }}>
      <div className="text-white shadow-lg sticky top-0 z-10" style={{ backgroundColor: THEME.navy }}>
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center gap-4">
            <div className="flex items-center gap-3">
              <Activity className="w-8 h-8 text-white" />
              <div>
                <h1 className="text-xl font-bold">XEconomic</h1>
                <p className="text-sm text-blue-100">CCI Forecast and XAI</p>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => setLang("en")}
                className={`px-3 py-1 text-xs font-bold rounded-lg transition-all ${
                  lang === "en" ? "bg-white" : "text-white border border-white/40 hover:bg-white/10"
                }`}
                style={lang === "en" ? { color: THEME.navy } : {}}
              >
                EN
              </button>
              <button
                onClick={() => setLang("th")}
                className={`px-3 py-1 text-xs font-bold rounded-lg transition-all ${
                  lang === "th" ? "bg-white" : "text-white border border-white/40 hover:bg-white/10"
                }`}
                style={lang === "th" ? { color: THEME.navy } : {}}
              >
                ไทย
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <TopNav t={t} page={page} setPage={setPage} />

        {err ? <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 p-4 text-red-700 text-sm">{err}</div> : null}

        {page === "forecast" ? (
          <ForecastPage
            t={t}
            lang={lang}
            series={series}
            summary={summary}
            allExplain={allExplain}
            news={newsReal}
            onSelectAspect={(aspect) => {
              setSelectedAspect(aspect)
              setPage("aspectNews")
            }}
          />
        ) : null}

        {page === "aspectNews" ? (
          <AspectNewsPage t={t} lang={lang} aspect={selectedAspect} news={newsReal} onBack={() => setPage("forecast")} />
        ) : null}

        {page === "analytics" ? <AnalyticsPage t={t} lang={lang} news={newsReal} shapData={shapData} /> : null}
      </div>

      <div className="bg-white border-t mt-12" style={{ borderColor: THEME.border }}>
        <div className="max-w-7xl mx-auto px-6 py-4 text-center text-sm text-gray-600">
          © Copyright SP2025-40 XEconomics
        </div>
      </div>
    </div>
  )
}