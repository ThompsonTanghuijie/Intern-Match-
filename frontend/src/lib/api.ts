export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type HealthResponse = {
  status: string;
  app: string;
};

export type TrendPoint = {
  label: string;
  count: number;
};

export type TrendsResponse = {
  total_jobs: number;
  active_jobs: number;
  by_job_type: TrendPoint[];
  by_source: TrendPoint[];
  by_day_seen: TrendPoint[];
  top_locations: TrendPoint[];
  top_skills: TrendPoint[];
  application_status: TrendPoint[];
};

export type Job = {
  id: number;
  source_id: number;
  company: string;
  title: string;
  location: string | null;
  job_type: string | null;
  season: string | null;
  apply_url: string | null;
  source_url: string;
  raw_text: string | null;
  skills_json: string | null;
  status: string;
  is_active: boolean;
  content_hash: string;
  first_seen_at: string;
  last_seen_at: string;
};

export type JobListResponse = {
  total: number;
  items: Job[];
};

export type Source = {
  id: number;
  name: string;
  url: string;
  source_type: string;
  enabled: boolean;
  last_status: string | null;
  last_crawled_at: string | null;
};

export type CrawlRun = {
  id: number;
  source_id: number | null;
  status: string;
  started_at: string;
  finished_at: string | null;
  jobs_found: number;
  jobs_created: number;
  jobs_updated: number;
  message: string | null;
};

export type MatchRequest = {
  name: string;
  skills: string[];
  target_locations: string[];
  target_directions: string[];
  remote_preference: string | null;
  blacklist_keywords: string[];
  min_score: number;
  limit: number;
};

export type MatchItem = {
  job: Job;
  score: number;
  reasons: string[];
};

export type MatchResponse = {
  items: MatchItem[];
};

export type UserProfileCreate = {
  name: string;
  skills: string[];
  target_locations: string[];
  target_directions: string[];
  remote_preference: string | null;
  blacklist_keywords: string[];
};

export type UserProfileRead = UserProfileCreate & {
  id: number;
};

export type UserJobUpsert = {
  profile_name: string;
  is_favorite: boolean;
  application_status: "saved" | "interested" | "applied" | "interview" | "offer" | "rejected" | "archived";
  notes: string | null;
  applied_at: string | null;
};

export type UserJobRead = {
  id: number;
  user_id: number;
  job_id: number;
  is_favorite: boolean;
  application_status: string;
  notes: string | null;
  applied_at: string | null;
  created_at: string;
  updated_at: string;
  job: Job;
};

type QueryValue = string | number | boolean | null | undefined;

function buildUrl(path: string, params?: Record<string, QueryValue>) {
  const url = new URL(path, API_BASE_URL);
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });
  return url.toString();
}

async function request<T>(path: string, init?: RequestInit, params?: Record<string, QueryValue>): Promise<T> {
  const response = await fetch(buildUrl(path, params), {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers
    },
    ...init
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getTrends(limit = 10) {
  return request<TrendsResponse>("/analytics/trends", undefined, { limit });
}

export function getHealth() {
  return request<HealthResponse>("/health");
}

export function getJobs(params: {
  skip?: number;
  limit?: number;
  q?: string;
  location?: string;
  job_type?: string;
}) {
  return request<JobListResponse>("/jobs", undefined, params);
}

export function getJob(jobId: number) {
  return request<Job>(`/jobs/${jobId}`);
}

export function getSources() {
  return request<Source[]>("/sources");
}

export function runCrawl(force = true) {
  return request<CrawlRun[]>("/crawl/run", { method: "POST" }, { force });
}

export function getMatches(payload: MatchRequest) {
  return request<MatchResponse>("/match", { method: "POST", body: JSON.stringify(payload) });
}
