export type SourceType = 'document' | 'webpage' | 'image' | 'transcript' | 'structured_record';

export interface Citation {
  source_id: string;
  source_type: SourceType;
  title: string;
  location: string; // e.g. "Page 3", "Timestamp 10:14", "Line 42"
  snippet: string;
  confidence: number;
  metadata?: Record<string, any>;
}

export interface TimelineEvent {
  timestamp: string;
  event: string;
  source_type: SourceType;
  source_id: string;
  severity?: 'info' | 'warning' | 'critical';
}

export interface InvestigationReport {
  query: string;
  timeline: TimelineEvent[];
  likely_root_cause?: string;
  confidence_score: number;
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
