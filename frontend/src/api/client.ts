const BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface Position {
  id: number;
  title: string;
  department: string;
  jd_text: string;
  core_competencies: string;
  preferences: string;
  status: string;
  created_at: string;
  updated_at: string;
  candidate_count: number;
}

export interface Candidate {
  id: number;
  position_id: number;
  codename: string;
  resume_file_path: string;
  structured_info: string;
  created_at: string;
  has_match: boolean;
  resume_sanitized_text?: string;
}

export interface MatchScore {
  id: number;
  candidate_id: number;
  experience_score: number;
  experience_note: string;
  industry_score: number;
  industry_note: string;
  competency_score: number;
  competency_note: string;
  potential_score: number;
  potential_note: string;
  overall_score: number;
  recommendation: string;
  highlights: string;
  risks: string;
  questions: string;
  created_at: string;
}

export interface QuestionItem {
  question: string;
  purpose: string;
  good_answer_elements: string[];
  red_flags: string[];
}

export interface QuestionSet {
  opening: QuestionItem[];
  experience_verification: QuestionItem[];
  competency: QuestionItem[];
  risk_probing: QuestionItem[];
  culture_fit: QuestionItem[];
}

export interface Interview {
  id: number;
  position_id: number;
  candidate_id: number;
  status: string;
  questions_json: string;
  started_at: string | null;
  ended_at: string | null;
  duration_seconds: number;
  created_at: string;
  candidate_codename: string;
  position_title: string;
  has_summary: boolean;
}

export interface TranscriptEntry {
  id: number;
  speaker: string;
  sanitized_text: string;
  timestamp: number;
  duration: number;
}

export interface InterviewSummary {
  id: number;
  interview_id: number;
  candidate_overview: string;
  expression_score: number;
  case_richness_score: number;
  depth_score: number;
  self_awareness_score: number;
  enthusiasm_score: number;
  overall_score: number;
  highlights: string;
  concerns: string;
  jd_alignment: string;
  recommendation: string;
  recommendation_reason: string;
  next_steps: string;
  pdf_path: string;
  created_at: string;
}

export interface WsTranscript {
  type: "transcript";
  speaker: string;
  text: string;
  timestamp: number;
}

export interface WsAnalysis {
  type: "analysis";
  current_question_index: number;
  elements_checked: string[];
  follow_up_suggestions: string[];
  instant_rating: string;
  instant_comment: string;
}

export type WsMessage =
  | WsTranscript
  | WsAnalysis
  | { type: "error"; message: string }
  | { type: "question_switched"; current_question_index: number };

export const api = {
  positions: {
    list: () => request<Position[]>("/positions"),
    get: (id: number) => request<Position>(`/positions/${id}`),
    create: (data: Partial<Position>) =>
      request<Position>("/positions", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (id: number, data: Partial<Position>) =>
      request<Position>(`/positions/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    delete: (id: number) =>
      request<void>(`/positions/${id}`, { method: "DELETE" }),
  },
  candidates: {
    list: (positionId: number) =>
      request<Candidate[]>(`/candidates?position_id=${positionId}`),
    get: (id: number) => request<Candidate>(`/candidates/${id}`),
    upload: async (positionId: number, file: File): Promise<Candidate> => {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(
        `${BASE}/candidates/upload?position_id=${positionId}`,
        { method: "POST", body: formData }
      );
      if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
      return res.json();
    },
  },
  matches: {
    get: (candidateId: number) =>
      request<MatchScore>(`/matches/${candidateId}`),
    score: (candidateId: number) =>
      request<MatchScore>(`/matches/${candidateId}/score`, { method: "POST" }),
    generateQuestions: (candidateId: number) =>
      request<QuestionSet>(`/matches/${candidateId}/questions`, {
        method: "POST",
      }),
  },
  interviews: {
    list: (candidateId?: number, positionId?: number) => {
      const params = new URLSearchParams();
      if (candidateId) params.set("candidate_id", String(candidateId));
      if (positionId) params.set("position_id", String(positionId));
      return request<Interview[]>(`/interviews?${params}`);
    },
    get: (id: number) => request<Interview>(`/interviews/${id}`),
    create: (data: {
      position_id: number;
      candidate_id: number;
      questions_json?: string;
    }) =>
      request<Interview>("/interviews", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    start: (id: number) =>
      request<Interview>(`/interviews/${id}/start`, { method: "POST" }),
    end: (id: number) =>
      request<Interview>(`/interviews/${id}/end`, { method: "POST" }),
    createSession: (id: number) =>
      request<{ status: string }>(`/interviews/${id}/session`, {
        method: "POST",
      }),
    stopSession: (id: number) =>
      request<{ status: string }>(`/interviews/${id}/session/stop`, {
        method: "POST",
      }),
    getTranscripts: (id: number) =>
      request<TranscriptEntry[]>(`/interviews/${id}/transcripts`),
  },
  summaries: {
    get: (interviewId: number) =>
      request<InterviewSummary>(`/summaries/${interviewId}`),
    generate: (interviewId: number) =>
      request<InterviewSummary>(`/summaries/${interviewId}/generate`, {
        method: "POST",
      }),
    exportPdf: (interviewId: number) =>
      `${BASE}/summaries/${interviewId}/pdf`,
  },
};
