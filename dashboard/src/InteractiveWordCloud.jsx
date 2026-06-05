import React from "react"
import { getWordcloud } from "./api.js"

// Multi-colour palette — mirrors the static PNG generator so the interactive
// cloud has the same lively look. Colour per word is stable across renders
// (hash-based), so a word doesn't flicker to a different colour when the
// component re-renders on hover.
const COLOR_PALETTE = [
  "#22c55e", "#16a34a", "#15803d", "#059669",   // green shades
  "#10b981", "#34d399",                          // emerald
  "#a855f7", "#8b5cf6", "#7c3aed",               // purple
  "#f59e0b", "#d97706", "#b45309",               // amber / orange
  "#6366f1", "#4f46e5",                          // indigo
  "#06b6d4", "#0891b2",                          // cyan
]

function hashString(s) {
  let h = 0
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) - h) + s.charCodeAt(i)
    h |= 0
  }
  return Math.abs(h)
}

/**
 * Interactive word cloud — replaces the static PNG.
 * Words are sized by sentiment weight and coloured by positive/negative
 * lean; hovering a word shows article count, the pos/neg split, and a
 * few sample headlines. Data comes from GET /dashboard/wordcloud.
 */
export default function InteractiveWordCloud({ lang = "th" }) {
  const [words, setWords] = React.useState([])
  const [loading, setLoading] = React.useState(true)
  const [hover, setHover] = React.useState(null)
  const [pos, setPos] = React.useState({ x: 0, y: 0 })
  const containerRef = React.useRef(null)

  React.useEffect(() => {
    let alive = true
    getWordcloud()
      .then((r) => { if (alive) setWords(r.data || []) })
      .catch(() => { if (alive) setWords([]) })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [])

  const tr = (en, th) => (lang === "en" ? en : th)

  // Size words by article count — linear scaling for a clear big/small
  // contrast. Max capped at 56 px so a single long Thai word at top size
  // (e.g. ทองคำแท่ง) doesn't overflow the card; min 12 keeps the tail
  // readable.
  const maxCount = React.useMemo(
    () => Math.max(1, ...words.map((w) => w.count || 0)),
    [words]
  )
  const fontSize = (w) => {
    // Steeper curve (Math.pow(..., 1.5)) drops mid-tier words down faster,
    // making the most frequent words stand out dramatically more.
    // Max size increased to 100px.
    const ratio = (w.count || 0) / maxCount
    const curve = Math.pow(ratio, 1.5) 
    return 12 + curve * 88 // 12..100 px
  }

  // Render order is shuffled (Fisher–Yates) so big and small words mix
  // visually instead of cascading top-to-bottom by size. Recomputed only
  // when the data changes — hovering doesn't reshuffle.
  const shuffledWords = React.useMemo(() => {
    const arr = [...words]
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[arr[i], arr[j]] = [arr[j], arr[i]]
    }
    return arr
  }, [words])

  // colour from the multi-colour palette, deterministic per word
  const colorOf = (w) => COLOR_PALETTE[hashString(w.word) % COLOR_PALETTE.length]

  const onMove = (e) => {
    const rect = containerRef.current?.getBoundingClientRect()
    if (rect) setPos({ x: e.clientX - rect.left, y: e.clientY - rect.top })
  }

  if (loading) {
    return (
      <div className="py-10 text-center text-sm text-gray-400">
        {tr("Loading…", "กำลังโหลด…")}
      </div>
    )
  }
  if (!words.length) {
    return (
      <div className="py-10 text-center text-sm text-gray-400">
        {tr("No word data available", "ไม่มีข้อมูลคำ")}
      </div>
    )
  }

  const tooltipW = 288
  const tooltipH = 180   // approximate; just used for edge-clamping
  const containerW = containerRef.current?.offsetWidth || 0
  const containerH = containerRef.current?.offsetHeight || 0

  // Tooltip position — clamp inside the container on both axes. If the
  // cursor is near the bottom, flip the tooltip ABOVE the cursor so it
  // doesn't spill out.
  let ttLeft = Math.max(0, Math.min(pos.x + 16, containerW - tooltipW))
  let ttTop  = pos.y + 16
  if (ttTop + tooltipH > containerH) ttTop = pos.y - tooltipH - 8
  ttTop = Math.max(0, ttTop)

  return (
    <div ref={containerRef} className="relative w-full" onMouseMove={onMove}>
      <div className="flex flex-wrap items-center justify-center gap-x-3 gap-y-1 px-2 py-4">
        {shuffledWords.map((w) => (
          <span
            key={w.word}
            onMouseEnter={() => setHover(w)}
            onMouseLeave={() => setHover(null)}
            style={{
              fontSize: `${fontSize(w)}px`,
              color: colorOf(w),
              lineHeight: 1.15,
            }}
            className="cursor-default font-semibold transition-transform duration-150 hover:scale-110"
          >
            {w.word}
          </span>
        ))}
      </div>

      {hover && (
        <div
          className="pointer-events-none absolute z-50 rounded-xl border border-gray-200 bg-white p-3 shadow-xl"
          style={{ width: tooltipW, left: ttLeft, top: ttTop }}
        >
          <div className="mb-1 text-base font-bold text-gray-800">{hover.word}</div>
          <div className="mb-2 text-xs text-gray-500">
            {tr("appears in", "ปรากฏใน")}{" "}
            {(hover.count || 0).toLocaleString()} {tr("articles", "ข่าว")}
          </div>

          {hover.samples?.length > 0 && (
            <div className="border-t border-gray-100 pt-2">
              <div className="mb-1 text-[11px] font-semibold text-gray-400">
                {tr("Sample headlines", "ตัวอย่างข่าว")}
              </div>
              <ul className="space-y-1">
                {hover.samples.slice(0, 3).map((s, i) => (
                  <li key={i} className="text-[11px] leading-snug text-gray-600">
                    • {s}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
