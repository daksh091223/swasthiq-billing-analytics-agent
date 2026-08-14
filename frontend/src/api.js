
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, body) {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Request failed.");
  }

  return data;
}

export function analyzeBilling(rows) {
  return request("/api/analyze", rows);
}

export function generateNarrative(report) {
  return request("/api/narrative", report);
}
