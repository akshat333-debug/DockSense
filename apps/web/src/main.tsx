import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertTriangle,
  ArrowDownUp,
  Bot,
  Check,
  CircleGauge,
  Clock3,
  Filter,
  MessageSquareText,
  PackageSearch,
  Play,
  RefreshCw,
  ShieldAlert,
  X,
} from "lucide-react";
import { askQuestion, clipUrl, fetchIncidents, fetchStats, updateReview } from "./api";
import type { ChatResponse, Incident, ReviewStatus, RiskBand, StatsResponse } from "./types";
import "./styles.css";

type SortKey = "risk" | "time" | "confidence";
type FilterBand = "all" | RiskBand;

const REVIEW_OPTIONS: { value: ReviewStatus; label: string }[] = [
  { value: "new", label: "New" },
  { value: "needs_investigation", label: "Investigate" },
  { value: "confirmed", label: "Confirmed" },
  { value: "false_positive", label: "False positive" },
];

function App() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("risk");
  const [band, setBand] = useState<FilterBand>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [chatQuestion, setChatQuestion] = useState("show high risk incidents");
  const [chat, setChat] = useState<ChatResponse | null>(null);
  const [reviewNote, setReviewNote] = useState("");

  useEffect(() => {
    void load();
  }, []);

  const visible = useMemo(() => {
    const filtered = band === "all" ? incidents : incidents.filter((incident) => incident.risk.band === band);
    return [...filtered].sort((a, b) => {
      if (sortKey === "time") return a.start_t - b.start_t;
      if (sortKey === "confidence") return b.risk.confidence - a.risk.confidence;
      return b.risk.score - a.risk.score;
    });
  }, [band, incidents, sortKey]);

  const selected = incidents.find((incident) => incident.id === selectedId) ?? visible[0] ?? null;

  useEffect(() => {
    setReviewNote(selected?.review_note ?? "");
  }, [selected?.id]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [items, nextStats] = await Promise.all([fetchIncidents(), fetchStats()]);
      setIncidents(items);
      setStats(nextStats);
      setSelectedId((current) => current ?? items[0]?.id ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load incidents");
    } finally {
      setLoading(false);
    }
  }

  async function submitReview(status: ReviewStatus) {
    if (!selected) return;
    const updated = await updateReview(selected.id, status, reviewNote);
    setIncidents((rows) => rows.map((row) => (row.id === updated.id ? updated : row)));
    setSelectedId(updated.id);
  }

  async function submitChat() {
    const response = await askQuestion(chatQuestion);
    setChat(response);
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">DockSense operations</p>
          <h1>Incident Review Console</h1>
        </div>
        <button className="icon-button labeled" onClick={load} title="Refresh incidents">
          <RefreshCw size={18} />
          Refresh
        </button>
      </header>

      <section className="stats-strip" aria-label="Incident statistics">
        <Stat icon={<PackageSearch size={18} />} label="Incidents" value={stats?.total ?? 0} />
        <Stat icon={<CircleGauge size={18} />} label="Average Risk" value={formatNumber(stats?.avg_risk)} />
        <Stat icon={<ShieldAlert size={18} />} label="Max Risk" value={formatNumber(stats?.max_risk)} />
        <Stat icon={<Check size={18} />} label="Avg Confidence" value={formatPercent(stats?.avg_confidence)} />
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="workspace">
        <div className="queue-pane">
          <div className="toolbar">
            <div className="segmented" aria-label="Risk band filter">
              {(["all", "critical", "high", "medium", "low"] as FilterBand[]).map((item) => (
                <button key={item} className={band === item ? "active" : ""} onClick={() => setBand(item)}>
                  {item.replace("_", " ")}
                </button>
              ))}
            </div>
            <label className="select-label">
              <Filter size={16} />
              <select value={sortKey} onChange={(event) => setSortKey(event.target.value as SortKey)}>
                <option value="risk">Risk</option>
                <option value="time">Time</option>
                <option value="confidence">Confidence</option>
              </select>
            </label>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Incident</th>
                  <th>Event</th>
                  <th>
                    <span className="th-icon">
                      Risk <ArrowDownUp size={13} />
                    </span>
                  </th>
                  <th>Confidence</th>
                  <th>Time</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={6} className="empty">Loading incidents</td>
                  </tr>
                ) : visible.length ? (
                  visible.map((incident) => (
                    <tr
                      key={incident.id}
                      className={selected?.id === incident.id ? "selected" : ""}
                      onClick={() => setSelectedId(incident.id)}
                    >
                      <td className="mono">{incident.id}</td>
                      <td>{labelize(incident.name)}</td>
                      <td>
                        <span className={`band ${incident.risk.band}`}>{incident.risk.band}</span>
                        <strong>{incident.risk.score.toFixed(0)}</strong>
                      </td>
                      <td>{formatPercent(incident.risk.confidence)}</td>
                      <td>{incident.start_t.toFixed(1)}s</td>
                      <td>{labelize(incident.review_status)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="empty">No matching incidents were found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <aside className="detail-pane">
          {selected ? (
            <>
              <div className="detail-head">
                <div>
                  <p className="eyebrow">{selected.behaviour_id}</p>
                  <h2>{selected.id}</h2>
                </div>
                <span className={`band large ${selected.risk.band}`}>{selected.risk.band}</span>
              </div>

              <div className="clip-box">
                {selected.clip_path ? (
                  <video controls src={clipUrl(selected.clip_path)} />
                ) : (
                  <div className="clip-empty">
                    <Play size={22} />
                    <span>No clip attached</span>
                  </div>
                )}
              </div>

              <div className="metric-grid">
                <Metric label="Risk" value={`${selected.risk.score.toFixed(1)}/100`} />
                <Metric label="Confidence" value={formatPercent(selected.risk.confidence)} />
                <Metric label="Start" value={`${selected.start_t.toFixed(2)}s`} />
                <Metric label="Zone" value={selected.zone ?? "unknown"} />
              </div>

              <section className="detail-section">
                <h3>
                  <AlertTriangle size={16} />
                  Evidence
                </h3>
                <p>{selected.explanation}</p>
                <dl className="evidence-list">
                  {Object.entries(selected.evidence).map(([key, value]) => (
                    <div key={key}>
                      <dt>{labelize(key)}</dt>
                      <dd>{String(value)}</dd>
                    </div>
                  ))}
                </dl>
              </section>

              <section className="detail-section">
                <h3>
                  <Clock3 size={16} />
                  SOP
                </h3>
                {selected.sop.map((item) => (
                  <p key={item}>{item}</p>
                ))}
              </section>

              <section className="review-section">
                <textarea
                  value={reviewNote}
                  onChange={(event) => setReviewNote(event.target.value)}
                  placeholder="Review note"
                />
                <div className="review-actions">
                  {REVIEW_OPTIONS.map((option) => (
                    <button key={option.value} onClick={() => void submitReview(option.value)}>
                      {option.value === "false_positive" ? <X size={15} /> : <Check size={15} />}
                      {option.label}
                    </button>
                  ))}
                </div>
              </section>
            </>
          ) : (
            <div className="empty side">No incident selected</div>
          )}
        </aside>
      </section>

      <section className="chat-panel">
        <div className="chat-title">
          <Bot size={18} />
          <h2>Assistant</h2>
        </div>
        <div className="chat-input">
          <MessageSquareText size={18} />
          <input value={chatQuestion} onChange={(event) => setChatQuestion(event.target.value)} />
          <button onClick={() => void submitChat()}>Ask</button>
        </div>
        {chat ? <pre>{chat.answer}</pre> : null}
      </section>
    </main>
  );
}

function Stat({ icon, label, value }: { icon: React.ReactNode; label: string; value: string | number }) {
  return (
    <div className="stat">
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatNumber(value?: number): string {
  return typeof value === "number" ? value.toFixed(1) : "0.0";
}

function formatPercent(value?: number): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "0%";
}

function labelize(value: string): string {
  return value.replace(/_/g, " ");
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
