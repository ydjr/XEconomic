import Papa from "papaparse"

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
  if (u.includes("thaipbs.or.th")) return "Thai PBS"
  try {
    const host = new URL(u).hostname.replace("www.", "")
    return host
  } catch {
    return ""
  }
}

// export async function getNewsSentimentFromCSV() {
    
//   const res = await fetch("./data/news_sentiment_summary_all.csv")
//   if (!res.ok) throw new Error("โหลดไฟล์ news_sentiment_summary_all.csv ไม่สำเร็จ (เช็ค data)")

//   const text = await res.text()
//   const parsed = Papa.parse(text, { header: true, skipEmptyLines: true })

//   return (parsed.data || [])
//     .map((r) => {
//       const date = r.published_at ? String(r.published_at).slice(0, 10) : ""
//       const impactType = r.impact_type || "Neutral"
//       const sentiment = toSignedSentiment(r.sentiment_score, impactType)

//       return {
//         id: r.id,
//         date,
//         title: r.headline || "",
//         url: r.url || "",
//         aspect: r.aspects || "Other",
//         tag: r.category || "",
//         source: inferSourceFromUrl(r.url) || r.subtype || "",
//         sentiment,
//         impact: impactToNumber(impactType), 
//         impactType,
//         effectType: r.effect_type || "",
//         rawSentiment: Number(r.sentiment_score),
//       }
//     })
//     .filter((x) => x.date && x.title)
// }
