const BASE_URL = import.meta.env.VITE_API_URL || "";

async function getJSON(url) {
  const res = await fetch(`${BASE_URL}${url}`);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${url} failed: ${res.status} ${text}`);
  }
  return await res.json();
}

export function getSummary() {
  return getJSON("/dashboard/summary");
}

export function getLatestExplain() {
  return getJSON("/dashboard/explain/latest");
}

export function getTimeSeries(limit = 500) {
  return getJSON(`/dashboard/timeseries?limit=${limit}`);
}

export function getNews(limit = 2000) {
  return getJSON(`/dashboard/news?limit=${limit}`);
}

export async function getShap() {
  return getJSON(`/dashboard/shap`);
}

export async function getShapAll() {
  return getJSON(`/dashboard/shap/all`);
}

export function getWordcloud(limit = 120) {
  return getJSON(`/dashboard/wordcloud?limit=${limit}`);
}

export function getAllExplain() {
  return getJSON("/dashboard/explain/all");
}

export async function getAllExplainEN() {
  const res = await fetch(`${BASE_URL}/dashboard/explain/all/en`)
  return res.json()
}