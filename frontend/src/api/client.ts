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
};
