// Mirrors FRONTEND_SPEC.md §2 — the frozen API contract. SINGLE source of truth.
// Additive optional fields only, never renames.

export interface BiasFlag {
  phrase: string;
  why: string;
  suggestion: string;
}

export interface SectionEvidence {
  name: string;
  similarity: number;
}

export interface Evidence {
  sections: SectionEvidence[];
  highlight: string;
}

/** One object per JD requirement: the best matching resume line + its score. */
export interface RequirementEvidence {
  requirement: string;
  skill: string;
  line: string;
  section: string;
  similarity: number; // 0–1
}

export type Band = 'strong' | 'medium' | 'weak';

export interface Candidate {
  rank: number;
  name: string;
  file: string;
  overall_score: number;
  keyword_score: number;
  semantic_score: number;
  matched_skills: string[];
  partial_skills: string[];
  missing_skills: string[];
  evidence: Evidence;
  explanation: string | null;
  // v2 additive — always present from the live backend
  band: Band;
  parse_warning: string | null;
  skill_evidence: Record<string, string>;
  requirement_evidence: RequirementEvidence[];
}

export interface JdInfo {
  title: string | null;
  company: string | null;
  required_skills: string[];
  nice_skills: string[];
}

export interface Duplicate {
  name: string;
  file: string;
  kept_file: string;
  email: string;
}

export interface Meta {
  resumes_processed: number;
  duplicates_removed: number;
  duplicates: Duplicate[];
  elapsed_ms: number;
  engine: string;
}

export interface Analysis {
  jd: JdInfo;
  ranking: Candidate[];
  bias_flags: BiasFlag[];
  meta: Meta;
}

export interface ChatResponse {
  answer: string;
}
