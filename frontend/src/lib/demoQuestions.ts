// Demo questions taken verbatim from backend/synthetic_data/evaluation/questions.json.
export interface DemoQuestion {
  id: string;
  label: string;
  hint: string;
  query: string;
}

export const DEMO_QUESTIONS: DemoQuestion[] = [
  {
    id: 'Q05',
    label: 'Why did payments fail?',
    hint: 'Timeline and cause across logs, notes and spec.',
    query:
      'Why did payment requests start failing after the latest deployment? Reconstruct the timeline, identify the most likely cause, explain the evidence, and recommend the next diagnostic step.',
  },
  {
    id: 'Q06',
    label: 'Is PAY-401 an auth error?',
    hint: 'Exact error-code lookup across sources.',
    query: 'Is PAY-401 an authentication error?',
  },
  {
    id: 'Q15',
    label: 'Initial report vs evidence',
    hint: 'Handles conflicting evidence.',
    query: 'The initial report blames a credential problem. Is that still the best explanation?',
  },
  {
    id: 'Q17',
    label: 'Who approved the deploy?',
    hint: 'Unanswerable: should abstain.',
    query: 'Which person approved the payment-service 2.4.0 production deploy?',
  },
];
