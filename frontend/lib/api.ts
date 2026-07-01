// Typed client for the ClaimPilot API.

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ---- Types (mirror the backend Pydantic schemas) ----
export interface Candidate {
  property_id: string;
  source_state: string;
  holder_name: string;
  owner_name: string;
  owner_last_address: string | null;
  amount_cents: number;
  property_type: string;
  owner_deceased: boolean;
  confidence: number;
  is_match: boolean;
  match_reasons: string[];
  score_breakdown: Record<string, number | null>;
}

export interface DataQualitySummary {
  total_records: number;
  missing_address: number;
  missing_address_pct: number;
  missing_reported_date: number;
  invalid_amount: number;
  duplicate_groups: number;
  duplicate_records: number;
  duplicates_merged: number;
}

export interface PropertySearchResponse {
  candidate_count: number;
  blocking_count: number;
  candidates: Candidate[];
  data_quality_summary: DataQualitySummary;
}

export interface RequiredItem {
  label: string;
  why: string;
  requirement: "required" | "conditional";
  satisfied_by_uploaded_doc: boolean;
  source_rule_chunk_id: string | null;
  status: "grounded" | "needs_human_review";
  origin: "deterministic" | "llm";
}

export interface Citation {
  chunk_id: string;
  doc_id: string;
  state: string;
  score: number;
  text: string;
}

export interface TraceSummary {
  steps: { step: string; detail: string }[];
  retrieval_hits: number;
  tokens: number;
  cost_cents: number;
}

export interface ClaimResponse {
  claim_id: string;
  claimant_id: string;
  property_id: string;
  state: string;
  status: string;
  needs_human_review: boolean;
  required_items: RequiredItem[];
  citations: Citation[];
  draft_letter: string;
  trace: TraceSummary;
}

export interface ClaimPreviewResponse {
  state: string;
  needs_human_review: boolean;
  required_items: RequiredItem[];
  citations: Citation[];
  draft_letter: string;
  trace: TraceSummary;
}

export interface ExtractedDoc {
  doc_type: string;
  name: string | null;
  dob: string | null;
  address: string | null;
  doc_number_last4: string | null;
  issue_date: string | null;
  expiry_date: string | null;
  field_confidence: Record<string, number>;
}

export interface DocumentUploadResponse {
  claim_id: string;
  status: string;
  extracted: ExtractedDoc;
  mismatches: string[];
  needs_human_review: boolean;
  satisfied_labels: string[];
  required_items: RequiredItem[];
}

export interface Claimant {
  id: string;
  full_name: string;
  prior_names: string[];
  addresses: string[];
  is_business: boolean;
}

export interface StateRules {
  state: string;
  title: string;
  version: string;
  body_md: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body.slice(0, 300)}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  createClaimant: (body: {
    full_name: string;
    prior_names: string[];
    addresses: string[];
    is_business: boolean;
  }) => request<Claimant>("/claimants", { method: "POST", body: JSON.stringify(body) }),

  searchProperties: (body: {
    name: string;
    prior_names: string[];
    addresses: string[];
  }) =>
    request<PropertySearchResponse>("/properties/search", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  createClaim: (claimant_id: string, property_id: string) =>
    request<ClaimResponse>("/claims", {
      method: "POST",
      body: JSON.stringify({ claimant_id, property_id }),
    }),

  getClaim: (id: string) => request<ClaimResponse>(`/claims/${id}`),

  getClaimant: (id: string) => request<Claimant>(`/claimants/${id}`),

  uploadDocument: (id: string, body: { raw_text: string; doc_type_hint: string }) =>
    request<DocumentUploadResponse>(`/claims/${id}/documents`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  previewClaim: (body: {
    state: string;
    amount_cents: number;
    owner_deceased: boolean;
    is_business: boolean;
    name?: string;
  }) =>
    request<ClaimPreviewResponse>("/claims/preview", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getStateRules: (state: string) => request<StateRules>(`/states/${state}/rules`),
};

export function money(cents: number): string {
  return `$${(cents / 100).toLocaleString("en-US", { minimumFractionDigits: 2 })}`;
}
