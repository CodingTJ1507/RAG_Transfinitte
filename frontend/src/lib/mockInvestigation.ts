import { InvestigationReport, ThinkingStep } from './types';

export const MOCK_INVESTIGATIONS: Record<string, { steps: ThinkingStep[]; report: InvestigationReport }> = {
  // TEST 1: Cross-source reasoning
  'payment': {
    steps: [
      { step: 'Query Intent Extraction', detail: 'Identified incident diagnosis request regarding post-deployment payment failures.', timestamp: '0.2s' },
      { step: 'MongoDB Atlas Vector Search', detail: 'Queried collection `chunks` for semantic clusters around payment exceptions and gateway timeouts.', timestamp: '0.5s' },
      { step: 'Structured Log Ingestion Scan', detail: 'Matched 48 HTTP 500 records in `payment_service.log` starting at 10:07 AM UTC.', timestamp: '0.9s' },
      { step: 'Cross-Source Document Corroboration', detail: 'Cross-referenced v2.4.0 Release Notes with API Specification schema requirements.', timestamp: '1.4s' },
      { step: 'Transcript Dialogue Analysis', detail: 'Correlated war-room engineer remarks regarding missing idempotency header payload.', timestamp: '1.8s' },
      { step: 'Timeline Synthesis & Citation Verification', detail: 'Reconstructed 4-stage chronological incident timeline with 100% citation grounding.', timestamp: '2.2s' },
    ],
    report: {
      query: 'Why did payment failures begin after yesterday\'s deployment?',
      likely_root_cause: 'Version 2.4.0 introduced a breaking change requiring an `idempotency_key` string in request headers. Legacy client checkout services continued transmitting unkeyed payloads, triggering fatal `PAY-401` schema rejections at the payment gateway.',
      confidence_score: 0.96,
      is_abstention: false,
      timeline: [
        { timestamp: '10:02 AM', event: 'Payment Service v2.4.0 deployed to production via CI/CD pipeline.', source_type: 'structured_record', source_id: 'deploy-log-1002', severity: 'info' },
        { timestamp: '10:07 AM', event: 'First batch of HTTP 500 errors recorded in payment service logs (Error code PAY-401).', source_type: 'structured_record', source_id: 'pay-log-1007', severity: 'critical' },
        { timestamp: '10:11 AM', event: 'Grafana latency dashboard registers a 420% spike in checkout failure rate.', source_type: 'image', source_id: 'grafana-spike-img', severity: 'warning' },
        { timestamp: '10:14 AM', event: 'Incident review meeting: On-call engineer identifies configuration header mismatch.', source_type: 'transcript', source_id: 'warroom-transcript', severity: 'info' }
      ],
      supporting_evidence: [
        {
          source_id: 'deploy-log-1002',
          source_type: 'structured_record',
          title: 'Deployment History Log (deployments.json)',
          location: 'Line 142 • Event #D-240',
          snippet: '{"timestamp": "2026-10-23T10:02:14Z", "service": "payment-service", "version": "2.4.0", "status": "DEPLOY_SUCCESS", "author": "ci-runner"}',
          confidence: 0.99
        },
        {
          source_id: 'pay-log-1007',
          source_type: 'structured_record',
          title: 'Payment Microservice Log (payment_service.log)',
          location: 'Line 804 • Error Event',
          snippet: '[ERROR] 2026-10-23T10:07:02Z [PAY-401] SchemaValidationError: Header "idempotency_key" is mandatory for POST /v1/charges in v2.4.0.',
          confidence: 0.98
        },
        {
          source_id: 'release-notes-240',
          source_type: 'webpage',
          title: 'Gateway Release Notes v2.4.0 (Changelog)',
          location: 'Section: Breaking Changes • Item 2',
          snippet: 'Breaking Change: All charge requests now require a non-null "idempotency_key" header to prevent duplicate debiting under network retries.',
          confidence: 0.95
        },
        {
          source_id: 'api-spec-v1',
          source_type: 'document',
          title: 'Internal Payment API Specification',
          location: 'Page 14 • Request Headers Table',
          snippet: 'Header idempotency_key is marked Optional in v2.3.9 clients, leading to legacy services submitting payloads without this mandatory attribute.',
          confidence: 0.92
        },
        {
          source_id: 'warroom-transcript',
          source_type: 'transcript',
          title: 'Incident War-Room Call Audio Transcript',
          location: 'Timestamp 10:14:32 • Speaker: DevLead',
          snippet: '"Hey team, check the gateway logs — it looks like the frontend checkout container is not sending the new idempotency header that 2.4.0 expects."',
          confidence: 0.94
        }
      ],
      conflicting_evidence: [],
      recommended_actions: [
        'Roll back payment-service container image from v2.4.0 to v2.3.9 immediately to restore checkout availability.',
        'Apply hotfix in frontend checkout service to populate UUIDv4 idempotency keys before redeploying v2.4.0.',
        'Update staging synthetic integration tests to enforce required header validation prior to production release gating.'
      ],
      uncertainties: [
        'Whether any partial transactions were debited at third-party acquiring banks prior to error throwing.'
      ]
    }
  },

  // TEST 2: Exact technical lookup
  'pay-401': {
    steps: [
      { step: 'Exact Keyword Tokenization', detail: 'Extracted exact alphanumeric error token `PAY-401`.', timestamp: '0.1s' },
      { step: 'MongoDB Atlas Full-Text Index Query', detail: 'Bypassing pure semantic embeddings to prevent fuzzy code confusion; scanning exact text index.', timestamp: '0.4s' },
      { step: 'Version Partition Comparison', detail: 'Filtered logs across deployment versions 2.3.9 and 2.4.0.', timestamp: '0.8s' },
      { step: 'Tabular Synthesis', detail: 'Compiled exact occurrence counts and timestamps.', timestamp: '1.2s' },
    ],
    report: {
      query: 'Find every occurrence of error code PAY-401 and compare the affected versions.',
      likely_root_cause: 'Error code `PAY-401` exists exclusively in service version `2.4.0` (48 occurrences between 10:07 AM and 10:35 AM). There are 0 occurrences of `PAY-401` in version `2.3.9`.',
      confidence_score: 1.0,
      is_abstention: false,
      timeline: [
        { timestamp: '10:07 AM', event: 'First occurrence of PAY-401 logged on container node-04 (v2.4.0).', source_type: 'structured_record', source_id: 'pay-log-1007', severity: 'critical' },
        { timestamp: '10:22 AM', event: 'Peak occurrence rate: 8 errors per second logged across 3 pods.', source_type: 'structured_record', source_id: 'pay-log-1022', severity: 'critical' }
      ],
      supporting_evidence: [
        {
          source_id: 'pay-log-1007',
          source_type: 'structured_record',
          title: 'payment_service.log (Version 2.4.0)',
          location: 'Lines 804-852 • 48 Matches',
          snippet: '2026-10-23T10:07:02Z [PAY-401] SchemaValidationError: Header "idempotency_key" is mandatory (Service: payment-service:2.4.0)',
          confidence: 1.0
        },
        {
          source_id: 'pay-log-v239',
          source_type: 'structured_record',
          title: 'payment_service.log.historical (Version 2.3.9)',
          location: 'Entire File • 0 Matches',
          snippet: 'Scanned 14,200 lines for version 2.3.9. Result: 0 matches for token "PAY-401".',
          confidence: 1.0
        }
      ],
      conflicting_evidence: [],
      recommended_actions: [
        'Query Prometheus metric `rate(http_requests_total{status="500", code="PAY-401"}[5m])` for real-time validation.'
      ],
      uncertainties: []
    }
  },

  // TEST 3: Conflicting evidence
  'redis': {
    steps: [
      { step: 'Topic Extraction', detail: 'Identified architectural inquiry regarding caching tier (Redis vs In-Memory).', timestamp: '0.2s' },
      { step: 'Multi-Document Retrieval', detail: 'Retrieved Runbook v1.8 and Architecture Spec Diagram v2.2 from MongoDB Atlas.', timestamp: '0.6s' },
      { step: 'Contradiction Detection Engine', detail: 'Flagged direct conflict between Runbook specification and Architecture diagram.', timestamp: '1.1s' },
      { step: 'Temporal Metadata Audit', detail: 'Compared document update dates: Diagram updated August 2026 vs Runbook updated January 2026.', timestamp: '1.5s' },
      { step: 'Uncertainty Formulation', detail: 'Formulated non-hallucinatory response highlighting discrepancy.', timestamp: '1.9s' }
    ],
    report: {
      query: 'The runbook says the service uses Redis, but the latest architecture diagram shows an in-memory cache. Which is correct?',
      likely_root_cause: 'Direct architectural contradiction detected between Runbook v1.8 and Architecture Diagram v2.2. While the Architecture Diagram is more recent (August 2026 vs January 2026), production logs show active connection attempts to Redis cluster port 6379, indicating the transition may be incomplete.',
      confidence_score: 0.72,
      is_abstention: false,
      timeline: [
        { timestamp: 'Jan 15, 2026', event: 'Deployment Runbook v1.8 documents Redis Sentinel cluster as primary session cache.', source_type: 'document', source_id: 'runbook-v18', severity: 'info' },
        { timestamp: 'Aug 20, 2026', event: 'Architecture Diagram v2.2 revised to depict local in-memory L1/L2 cache tier.', source_type: 'image', source_id: 'arch-diagram-v22', severity: 'warning' }
      ],
      supporting_evidence: [
        {
          source_id: 'runbook-v18',
          source_type: 'document',
          title: 'Service Operations Runbook v1.8',
          location: 'Page 8 • Section 3.2: Cache Architecture',
          snippet: '"The payment service utilizes a 3-node Redis Sentinel cluster (port 6379) for distributed state and token rate-limiting."',
          confidence: 0.88
        },
        {
          source_id: 'arch-diagram-v22',
          source_type: 'image',
          title: 'System Architecture Diagram v2.2',
          location: 'Figure 4: Data Layer Overview',
          snippet: '"Diagram visual box labels Payment Service Cache as [Local In-Memory Cache (Guava/Caffeine)] with no external Redis node line drawn."',
          confidence: 0.85
        }
      ],
      conflicting_evidence: [
        {
          source_id: 'arch-vs-runbook',
          source_type: 'document',
          title: 'Conflicting Architectural Claims',
          location: 'Runbook v1.8 vs Arch Diagram v2.2',
          snippet: 'Runbook explicitly asserts external Redis cluster, whereas Architecture Diagram v2.2 claims local in-memory cache.',
          confidence: 0.95
        }
      ],
      recommended_actions: [
        'Inspect live environment variables on payment-service pods: `kubectl exec -it <pod> -- printenv | grep REDIS`.',
        'Verify whether RFC-109 (Migration from Redis to in-memory) was fully executed or stalled in testing.',
        'Update Runbook v1.8 once production state is confirmed.'
      ],
      uncertainties: [
        'Whether in-memory caching was only intended for read-heavy catalog items rather than payment idempotency tokens.'
      ]
    }
  },

  // TEST 4: Evidence-based abstention
  'secretly': {
    steps: [
      { step: 'Speculation & Attribution Check', detail: 'User query asks for personal intent, secret actions, and code author attribution.', timestamp: '0.2s' },
      { step: 'Evidence Boundary Verification', detail: 'Examined all 5 ingested evidence sets (logs, specs, release notes, war-room transcripts).', timestamp: '0.6s' },
      { step: 'Abstention Trigger Fired', detail: 'No evidence establishes personal culpability or line-level author blame. Invoking Evidence-Based Abstention.', timestamp: '0.9s' }
    ],
    report: {
      query: 'Which engineer secretly caused the outage, and what exact line of code did they change?',
      likely_root_cause: undefined,
      confidence_score: 0.0,
      is_abstention: true,
      abstention_reason: 'Evidence-Based Abstention: The available sources (system logs, release notes, architecture specifications, and incident call transcripts) do NOT identify individual engineer culpability, intent, or line-level source code diffs.',
      timeline: [],
      supporting_evidence: [],
      conflicting_evidence: [],
      recommended_actions: [
        'Do not speculate on human attribution during blameless post-mortem investigations.',
        'Examine Git repository commit history (`git log --patch`) and PR review approvals on GitHub to identify the code change.',
        'Inspect CI/CD build deployment audit trails in GitHub Actions / Jenkins to review release authorization records.'
      ],
      uncertainties: [
        'Git author metadata and commit SHA are not present in current ingested operational evidence pack.'
      ]
    }
  }
};

export function getMockInvestigation(query: string): { steps: ThinkingStep[]; report: InvestigationReport } {
  const q = query.toLowerCase();
  if (q.includes('secret') || q.includes('who caused') || q.includes('which engineer') || q.includes('blame')) {
    return MOCK_INVESTIGATIONS['secretly'];
  }
  if (q.includes('pay-401') || q.includes('401') || q.includes('occurrence') || q.includes('error code')) {
    return MOCK_INVESTIGATIONS['pay-401'];
  }
  if (q.includes('redis') || q.includes('runbook') || q.includes('cache') || q.includes('memory') || q.includes('diagram')) {
    return MOCK_INVESTIGATIONS['redis'];
  }
  // Default to payment investigation (Test 1)
  return MOCK_INVESTIGATIONS['payment'];
}
