import Papa from "papaparse"

function toSignedSentiment(score, impactType) {
  const s = Number(score)
  if (!Number.isFinite(s)) return 0
  const centered = (s - 0.5) * 2
  if (impactType === "Negative") return -Math.abs(centered)
  if (impactType === "Positive") return Math.abs(centered)
  return centered
}

function impactToNumber(impactType) {
  if (impactType === "Positive") return 1
  if (impactType === "Negative") return -1
  return 0
}

function inferSourceFromUrl(url) {
  const u = String(url || "")
  if (u.includes("thairath.co.th")) return "Thairath"
  try {
    return new URL(u).hostname.replace("www.", "")
  } catch {
    return ""
  }
}

function mapNewsRow(r) {
  let dateRaw = String(r.published_at || r.date || "");
  let date = dateRaw.slice(0, 10);
  if (dateRaw.includes("/")) {
    const parts = dateRaw.split(" ")[0].split("/");
    if (parts.length === 3 && parts[2].length === 4) {
      date = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
    }
  }

  const impactType = String(r.impact_type || r.impactType || "Neutral").trim()
  const effectType = String(r.effect_type || r.effectType || "").trim()
  const aspect = String(r.Aspect || r.aspect || "Other").trim()
  const raw = Number(r.sentiment_score ?? r.rawSentiment)
  const rawSentiment = Number.isFinite(raw) ? raw : 0

  return {
    id: r.article_id || r.id || "",
    date,
    title: r.headline || r.title || "",
    url: r.url || "",
    aspect,
    tag: r.section || r.tag || "",
    source: inferSourceFromUrl(r.url) || r.agency || r.source || "",
    agency: r.agency || "",
    sentiment: toSignedSentiment(rawSentiment, impactType),
    impact: impactToNumber(impactType),
    impactType,
    effectType,
    rawSentiment,
    summary: r.summary || "",
  }
}

async function loadFromBackend() {
  const res = await fetch("/dashboard/news?limit=20000")
  if (!res.ok) throw new Error("โหลดข่าวจาก backend ไม่สำเร็จ")
  const json = await res.json()
  return (json.data || []).map(mapNewsRow).filter((x) => x.date && x.title)
}

export async function getNewsSentimentFromCSV() {
  const res = await fetch("./data/2017-2026.csv")
  if (!res.ok) {
    return loadFromBackend()
  }

  const text = await res.text()

  if (text.trim().startsWith("<!doctype html") || text.includes('<div id="root"></div>')) {
    return loadFromBackend()
  }

  const parsed = Papa.parse(text, { header: true, skipEmptyLines: true })
  return (parsed.data || []).map(mapNewsRow).filter((x) => x.date && x.title)
}

export async function getAgencyVolumeFromCSV(newsRows) {
  const monthMap = {}

  newsRows.forEach((n) => {
    const month = n.date?.slice(0, 7)
    const agency = n.agency || n.source || "Unknown"
    if (!month) return

    if (!monthMap[month]) monthMap[month] = {}
    monthMap[month][agency] = (monthMap[month][agency] || 0) + 1
  })

  const result = []
  Object.entries(monthMap).forEach(([month, agencies]) => {
    Object.entries(agencies).forEach(([agency, count]) => {
      result.push({ month, agency, count })
    })
  })

  return result
}