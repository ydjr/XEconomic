import Papa from "papaparse"

/**
 * โหลดข้อมูลข่าวจากไฟล์ CSV จริง (public/data/2017-2026.csv)
 * แปลงให้อยู่ในรูปแบบเดียวกับที่ระบบเดิมใช้อยู่ (news row objects)
 */

function toSignedSentiment(score, impactType) {
  const s = Number(score)
  if (!Number.isFinite(s)) return 0
  const centered = (s - 0.5) * 2 // [-1,1]
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
    const host = new URL(u).hostname.replace("www.", "")
    return host
  } catch {
    return ""
  }
}

/**
 * โหลด CSV ข่าวจาก static file แล้ว return เป็น array ของ news objects
 * คอลัมน์ใน CSV: source_file, agency, article_id, section, subtype,
 *   published_at, headline, content, summary, url,
 *   sentiment_score, Aspect, effect_type, impact_type
 */
export async function getNewsSentimentFromCSV() {
  const res = await fetch("./data/2017-2026.csv")
  if (!res.ok) throw new Error("โหลดไฟล์ 2017-2026.csv ไม่สำเร็จ")

  const text = await res.text()
  const parsed = Papa.parse(text, { header: true, skipEmptyLines: true })

  return (parsed.data || [])
    .map((r) => {
      const date = r.published_at ? String(r.published_at).slice(0, 10) : ""
      const impactType = r.impact_type || "Neutral"
      const sentiment = toSignedSentiment(r.sentiment_score, impactType)

      return {
        id: r.article_id || "",
        date,
        title: r.headline || "",
        url: r.url || "",
        aspect: r.Aspect || "Other",
        tag: r.section || "",
        source: inferSourceFromUrl(r.url) || r.agency || "",
        agency: r.agency || "",
        sentiment,
        impact: impactToNumber(impactType),
        impactType,
        effectType: r.effect_type || "",
        rawSentiment: Number(r.sentiment_score),
        summary: r.summary || "",
      }
    })
    .filter((x) => x.date && x.title)
}

/**
 * คำนวณ agency volume by month จากข้อมูล CSV (แทนที่ Supabase RPC)
 * return ในรูปแบบเดียวกับ get_news_volume_by_agency_month
 */
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
