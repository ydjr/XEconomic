async function getJSON(url) {
  const res = await fetch(url);
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

export function getAllExplain() {
  return getJSON("/dashboard/explain/all");
}

export async function getAllExplainEN() {
  const res = await fetch("/dashboard/explain/all/en")
  return res.json()
}