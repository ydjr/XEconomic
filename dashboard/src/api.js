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
