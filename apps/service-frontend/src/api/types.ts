export type TaskStatus =
  | "draft"
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled"
  | "review_required";

export interface ApiError {
  code: string;
  message: string;
  field_errors?: Record<string, string>;
  details?: Record<string, unknown>;
  status?: number;
}

export interface HubSession {
  hubUserId: string;
  hubUserName?: string;
  role?: string;
  loginUrl?: string;
}

export type HubSessionSource = "hub" | "local_fallback" | "missing";

export interface TaskSummary {
  id: string;
  job_no: string;
  scenario_key: string;
  title: string;
  status: TaskStatus;
  current_attempt_no: number;
  error_code?: string | null;
  error_message?: string | null;
  result_summary?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface TaskAttempt {
  id: string;
  attempt_no: number;
  workflow_stage: string;
  provider_name: string;
  provider_model: string;
  status: string;
  retryable: boolean;
  error_code?: string | null;
  error_message?: string | null;
  latency_ms?: number | null;
  input_tokens?: number | null;
  output_tokens?: number | null;
  external_request_id?: string | null;
  started_at: string;
  finished_at?: string | null;
}

export interface TaskResult {
  id: string;
  version_no: number;
  result_type: string;
  structured_payload: Record<string, unknown>;
  preview_text?: string | null;
  quality_status: string;
  review_comment?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskArtifact {
  id: string;
  artifact_role: string;
  storage_type: string;
  uri: string;
  mime_type?: string | null;
  size_bytes?: number | null;
  checksum?: string | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface TaskDetail extends TaskSummary {
  input_payload: Record<string, unknown>;
  normalized_payload: Record<string, unknown>;
  submitted_by_hub_user_id: string;
  submitted_by_name?: string | null;
  source_channel?: string | null;
  retryable: boolean;
  max_retries?: number | null;
  last_success_result?: TaskResult | null;
  attempts: TaskAttempt[];
  results: TaskResult[];
  artifacts: TaskArtifact[];
}

export interface AiProfile {
  id: string;
  profile_key: string;
  profile_name: string;
  scenario_key: string;
  is_default: boolean;
  is_active: boolean;
  provider_name: string;
  model_name: string;
  system_prompt?: string | null;
  prompt_template?: string | null;
  temperature: number;
  max_tokens: number;
  timeout_ms: number;
  max_retries: number;
  concurrency_limit: number;
  created_at: string;
  updated_at: string;
}

export interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  service: string;
  version: string;
  instance_id: string;
  uptime_sec: number;
  checks: Record<string, { status: string; detail: string }>;
  metrics: Record<string, number>;
  timestamp: string;
  registration: Record<string, unknown>;
}
