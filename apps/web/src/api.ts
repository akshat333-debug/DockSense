import type { ChatResponse, Incident, IncidentListResponse, ReviewStatus, StatsResponse } from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export function clipUrl(path: string): string {
  const clean = path.replace(/\\/g, "/").split("/").pop();
  return `${API_URL}/clips/${encodeURIComponent(clean ?? path)}`;
}

export async function fetchIncidents(params: URLSearchParams = new URLSearchParams()): Promise<Incident[]> {
  if (!params.has("limit")) {
    params.set("limit", "100");
  }
  const data = await request<IncidentListResponse>(`/incidents?${params.toString()}`);
  return data.items;
}

export async function fetchStats(): Promise<StatsResponse> {
  return request<StatsResponse>("/stats");
}

export async function updateReview(
  id: string,
  review_status: ReviewStatus,
  review_note: string,
): Promise<Incident> {
  return request<Incident>(`/incidents/${encodeURIComponent(id)}/review`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ review_status, review_note }),
  });
}

export async function askQuestion(question: string): Promise<ChatResponse> {
  return request<ChatResponse>("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Request failed with ${res.status}`);
  }
  return res.json() as Promise<T>;
}
