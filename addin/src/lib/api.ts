import { BACKEND_URL } from "../config";

export interface EmailIn {
  from?: string;
  subject?: string;
  body: string;
}

export interface TriageResult {
  category: string;
  priority: number;
  deadline: string | null;
  suggested_folder: string;
  reasoning: string;
  confidence: number;
}

export interface TriageResponse {
  result: TriageResult;
  model_used: string;
  escalated: boolean;
}

export interface SummarizeResponse {
  summary: string;
  action_items: string[];
  model_used: string;
  escalated: boolean;
}

export interface CalendarEvent {
  subject: string;
  start: string;
  end?: string | null;
  location?: string;
  attendees?: string[];
}

export interface BriefingResponse {
  briefing_markdown: string;
  deadlines: string[];
  focus_blocks: string[];
  model_used: string;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const resp = await fetch(`${BACKEND_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Backend ${resp.status}: ${text}`);
  }
  return (await resp.json()) as T;
}

export const api = {
  triage: (email: EmailIn) => post<TriageResponse>("/triage", { email }),
  summarize: (emails: EmailIn[]) => post<SummarizeResponse>("/summarize", { emails }),
  briefing: (forDate: string, events: CalendarEvent[], flaggedSummaries: string[]) =>
    post<BriefingResponse>("/briefing", {
      for_date: forDate,
      events,
      flagged_summaries: flaggedSummaries,
    }),
};
