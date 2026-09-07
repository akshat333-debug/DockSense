export type RiskBand = "low" | "medium" | "high" | "critical";

export type ReviewStatus =
  | "new"
  | "confirmed"
  | "false_positive"
  | "needs_investigation";

export interface RiskScore {
  score: number;
  band: RiskBand;
  confidence: number;
  components: Record<string, number>;
  weights_used: Record<string, number>;
}

export interface Incident {
  id: string;
  behaviour_id: string;
  name: string;
  video_id: string;
  session: string;
  camera: string;
  start_t: number;
  end_t: number;
  risk: RiskScore;
  explanation: string;
  sop: string[];
  clip_path: string | null;
  thumb_path: string | null;
  track_ids: number[];
  zone: string | null;
  evidence: Record<string, unknown>;
  review_status: ReviewStatus;
  review_note: string;
  created_at: string;
}

export interface IncidentListResponse {
  count: number;
  items: Incident[];
}

export interface StatsResponse {
  total: number;
  avg_risk: number;
  max_risk: number;
  avg_confidence: number;
  counts_by_behaviour: Record<string, number>;
}

export interface ChatResponse {
  answer: string;
  incident_ids: string[];
}
