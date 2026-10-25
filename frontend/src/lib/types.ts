export type SourceType = 'document' | 'webpage' | 'image' | 'transcript' | 'structured_record';

export interface Citation {
  source_id: string;
  chunk_id?: string;
  source_type: SourceType;
  title: string;
  location: string; // e.g. "Page 3", "Timestamp 10:14", "Line 42"
  snippet: string;
  retrieval_score?: number;
  metadata?: Record<string, unknown>;
}

export interface SupportedClaim {
  claim: string;
  classification: 'confirmed' | 'inference' | 'unknown';
  citation_chunk_ids: string[];
  explanation?: string;
  verification_status: 'verified' | 'contradicted' | 'insufficient' | 'not_checked';
}

export interface TimelineEvent {
  timestamp: string;
  event: string;
  source_type: SourceType;
  source_id: string;
  chunk_id?: string;
  classification?: string;
  severity?: 'info' | 'warning' | 'critical';
}

export interface InvestigationReport {
  query: string;
  answer: string;
  timeline: TimelineEvent[];
  claims: SupportedClaim[];
  likely_root_cause?: string;
  confidence_score: number;
  confidence_explanation?: string;
  is_abstention: boolean;
  abstention_reason?: string;
  supporting_evidence: Citation[];
  conflicting_evidence: Citation[];
  recommended_actions: string[];
  uncertainties: string[];
}

export interface ThinkingStep {
  step: string;
  detail: string;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  thinkingSteps?: ThinkingStep[];
  thinkingDurationMs?: number;
  report?: InvestigationReport;
  attachedFiles?: string[];
  isError?: boolean;
  errorTitle?: string;
  rawQuery?: string;
}

export interface IngestedFile {
  id: string;
  name: string;
  source_type: SourceType;
  size: string;
  uploadedAt: string;
  status: 'indexed' | 'processing' | 'error';
  chunkCount: number;
}

export interface EvaluationCaseResult {
  question_id: string;
  category: string;
  expected_source_ids: string[];
  retrieved_source_ids: string[];
  recall_at_k: number;
  precision_at_k: number;
  ndcg_at_k: number;
  reciprocal_rank: number;
  hit: boolean;
  abstention_expected: boolean;
  abstained: boolean | null;
  citations_valid: boolean | null;
  faithfulness: number | null;
  answer_evaluated: boolean;
  passed: boolean;
  failure_reasons: string[];
}

export interface EvaluationReport {
  status: string;
  cases_run: number;
  aggregate: {
    mean_recall_at_k?: number;
    mean_reciprocal_rank?: number;
    hit_rate?: number;
    mean_precision_at_k?: number;
    mean_ndcg_at_k?: number;
    pass_rate?: number;
    mean_faithfulness?: number;
    [key: string]: number | undefined;
  };
  results: EvaluationCaseResult[];
}

export interface IncidentSummary {
  incident_id: string;
  source_count: number;
}


