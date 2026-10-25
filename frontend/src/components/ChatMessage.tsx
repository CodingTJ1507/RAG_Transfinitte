'use client';
import React, { useState } from 'react';
import { ChatMessage as ChatMessageType, Citation, SupportedClaim } from '../lib/types';
import { ThinkingAccordion } from './ThinkingAccordion';
import { InlineCitationBadge, CompactCitationPill } from './CitationCard';
import { Copy, Check, ThumbsUp, ThumbsDown, Share2, Sparkles, AlertCircle, ShieldAlert, RefreshCw } from 'lucide-react';

interface ChatMessageProps {
  message: ChatMessageType;
  isStreaming?: boolean;
  onInspectCitation: (citation: Citation) => void;
  onRetry?: (query: string) => void;
}

const renderFindings = (
  claims: SupportedClaim[],
  citations: Citation[],
  onInspectCitation: (citation: Citation) => void,
) => {
  const visibleClaims = claims.filter(
    (claim) =>
      claim.classification !== 'unknown' &&
      claim.verification_status !== 'contradicted' &&
      claim.verification_status !== 'insufficient',
  );

  if (visibleClaims.length === 0) return null;

  return (
    <div className="pt-2">
      <h4 className="font-medium text-xs text-stone-500 uppercase tracking-wider mb-2">
        Findings
      </h4>
      <ul className="space-y-2 text-sm text-stone-700 pl-1">
        {visibleClaims.map((claim, idx) => {
          const isConfirmed = claim.classification === 'confirmed';
          const matchingCitations = citations.filter(
            (citation) => citation.chunk_id && claim.citation_chunk_ids.includes(citation.chunk_id),
          );
          return (
            <li key={idx} className="flex items-start space-x-2 flex-wrap gap-y-1">
              <span
                className={`text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded font-mono shrink-0 ${
                  isConfirmed
                    ? 'border border-emerald-300 bg-emerald-50 text-emerald-800'
                    : 'border border-amber-300 bg-amber-50 text-amber-800'
                }`}
              >
                {isConfirmed ? 'Confirmed' : 'Inference'}
              </span>
              <span className="leading-relaxed">{claim.claim}</span>
              {matchingCitations.map((citation) => (
                <InlineCitationBadge
                  key={citation.chunk_id ?? citation.source_id}
                  citation={citation}
                  onInspect={onInspectCitation}
                />
              ))}
              {claim.verification_status === 'not_checked' && (
                <span className="text-[11px] text-stone-400 italic">not checked</span>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
};

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  isStreaming = false,
  onInspectCitation,
  onRetry,
}) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end mb-6">
        <div className="max-w-[85%] md:max-w-[70%] bg-[#eaf0f6] border border-[#d4dee8] rounded-3xl px-5 py-3 text-[#162748] text-sm leading-relaxed font-normal shadow-2xs">
          {message.content}
          {message.attachedFiles && message.attachedFiles.length > 0 && (
            <div className="mt-2 pt-2 border-t border-[#d4dee8] flex flex-wrap gap-1.5">
              {message.attachedFiles.map((file, idx) => (
                <span key={idx} className="text-[11px] px-2 py-0.5 rounded-full bg-[#f8fafc] text-[#087f82] font-mono border border-[#09bec1]/30">
                  {file}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Handle Clean, Production-Grade User Errors (No Leaked Code / Stack Traces)
  if (message.isError) {
    return (
      <div className="flex justify-start mb-8">
        <div className="w-full max-w-3xl space-y-3">
          <div className="flex items-center space-x-2">
            <div className="w-6 h-6 rounded-full bg-rose-100 flex items-center justify-center shrink-0">
              <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
            </div>
            <span className="text-xs font-semibold text-[#162748]">
              {message.errorTitle || 'Something Went Wrong'}
            </span>
          </div>

          <div className="p-4 rounded-2xl bg-[#eef2f6] border border-[#dde4ec] text-[#162748] text-xs leading-relaxed space-y-3 shadow-2xs">
            <p className="text-xs text-slate-700">
              {message.content || 'An unexpected error occurred while processing your request. Please try again.'}
            </p>

            {onRetry && message.rawQuery && (
              <div className="pt-1">
                <button
                  onClick={() => onRetry(message.rawQuery!)}
                  className="px-3.5 py-1.5 bg-[#162748] hover:bg-[#1f3660] text-white text-xs font-medium rounded-lg flex items-center space-x-1.5 transition-colors cursor-pointer shadow-2xs"
                >
                  <RefreshCw className="w-3 h-3 text-[#09bec1]" />
                  <span>Retry</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  const report = message.report;
  const citations = report?.supporting_evidence || [];

  const handleCopy = () => {
    const textToCopy = report?.likely_root_cause || message.content;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex justify-start mb-8">
      <div className="w-full max-w-3xl space-y-4">
        {/* Concord.ai Assistant Brand Header */}
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded-lg bg-[#162748] flex items-center justify-center p-1 shrink-0 shadow-2xs border border-[#09bec1]/30">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/concord-mark.svg" alt="Concord.ai" className="w-4 h-4 object-contain" />
          </div>
          <span className="text-xs font-bold text-[#162748]">Concord.ai</span>
          <span className="text-[10px] text-slate-400 font-medium">Investigator</span>
        </div>

        {/* Minimal Thinking Process Accordion */}
        {(message.thinkingSteps || isStreaming) && (
          <ThinkingAccordion
            steps={message.thinkingSteps}
            durationMs={message.thinkingDurationMs}
            isStreaming={isStreaming}
          />
        )}

        {/* Test 4: Evidence-Based Abstention Box */}
        {report?.is_abstention && (
          <div className="p-3.5 rounded-xl bg-[#eef2f6] border border-[#dde4ec] text-[#162748] text-xs leading-relaxed space-y-1 shadow-2xs">
            <div className="flex items-center space-x-1.5 font-semibold text-[#162748]">
              <ShieldAlert className="w-4 h-4 text-[#09bec1]" />
              <span>Evidence-Based Abstention</span>
            </div>
            <p className="text-slate-700">
              {report.abstention_reason}
            </p>
          </div>
        )}

        {/* Test 3: Conflicting Evidence Alert */}
        {report?.conflicting_evidence && report.conflicting_evidence.length > 0 && (
          <div className="p-3.5 rounded-xl bg-amber-100/60 border border-amber-300/60 text-amber-950 text-xs leading-relaxed space-y-1 shadow-2xs">
            <div className="flex items-center space-x-1.5 font-semibold text-amber-900">
              <AlertCircle className="w-4 h-4" />
              <span>Conflicting Documentation Detected</span>
            </div>
            <ul className="space-y-2">
              {report.conflicting_evidence.map((citation) => (
                <li key={citation.chunk_id ?? citation.source_id} className="text-amber-900">
                  <span className="font-semibold">{citation.title} — {citation.location}: </span>
                  {citation.snippet}
                  <InlineCitationBadge citation={citation} onInspect={onInspectCitation} />
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Primary Diagnosis / Content (Clean Gemini Typography) */}
        {report?.likely_root_cause || report?.answer ? (
          <div className="space-y-4 text-sm text-stone-800 leading-relaxed">
            <h3 className="font-semibold text-base text-stone-900">
              Incident Diagnosis & Findings
            </h3>
            {report.confidence_explanation && (
              <p className="text-xs text-stone-500 -mt-2">
                {report.confidence_explanation}
              </p>
            )}
            <p className="text-stone-700 leading-relaxed">
              {report.likely_root_cause || report.answer}
              {/* Inline Gemini Citations */}
              {citations
                .filter((citation) =>
                  (report.claims ?? []).some((claim) =>
                    (claim.verification_status === 'verified' || claim.verification_status === 'not_checked')
                    && claim.citation_chunk_ids.includes(citation.chunk_id ?? ''),
                  ),
                )
                .map((cit) => (
                <InlineCitationBadge
                  key={cit.chunk_id ?? cit.source_id}
                  citation={cit}
                  onInspect={onInspectCitation}
                />
              ))}
            </p>

            {/* Findings List */}
            {!report.is_abstention && report.claims && renderFindings(report.claims, citations, onInspectCitation)}

            {/* Reconstructed Incident Timeline */}
            {report.timeline && report.timeline.length > 0 && (
              <div className="pt-2">
                <h4 className="font-medium text-xs text-stone-500 uppercase tracking-wider mb-2">
                  Chronological Timeline
                </h4>
                <ul className="space-y-2 text-sm text-stone-700 pl-1">
                  {report.timeline.map((evt, idx) => {
                    const matchedCitation = citations.find(c => c.chunk_id === evt.chunk_id)
                      ?? citations.find(c => c.source_id === evt.source_id);
                    return (
                      <li key={idx} className="flex items-start justify-between flex-wrap gap-1">
                        <div className="flex items-baseline space-x-2">
                          <span className="text-stone-400 font-mono text-xs">•</span>
                          <span className="font-mono text-xs font-semibold text-stone-500 shrink-0">{evt.timestamp}</span>
                          <span>{evt.event}</span>
                        </div>
                        {matchedCitation && (
                          <InlineCitationBadge
                            citation={matchedCitation}
                            onInspect={onInspectCitation}
                          />
                        )}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {/* Recommended Next Steps */}
            {report.recommended_actions && report.recommended_actions.length > 0 && (
              <div className="pt-2">
                <h4 className="font-medium text-xs text-stone-500 uppercase tracking-wider mb-2">
                  Recommended Remediation
                </h4>
                <ul className="space-y-1.5 text-sm text-stone-700 pl-1">
                  {report.recommended_actions.map((act, idx) => (
                    <li key={idx} className="flex items-baseline space-x-2">
                      <span className="text-stone-400 font-mono text-xs">•</span>
                      <span>{act}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Open Questions */}
            {report.uncertainties && report.uncertainties.length > 0 && (
              <div className="pt-2">
                <h4 className="font-medium text-xs text-stone-500 uppercase tracking-wider mb-2">
                  Open Questions
                </h4>
                <ul className="space-y-1.5 text-sm text-stone-700 pl-1">
                  {report.uncertainties.map((item, idx) => (
                    <li key={idx} className="flex items-baseline space-x-2">
                      <span className="text-stone-400 font-mono text-xs">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <div className="text-sm text-stone-800 leading-relaxed whitespace-pre-wrap">
            {message.content}
          </div>
        )}

        {/* Minimal Sources Bar at Bottom */}
        {citations.length > 0 && (
          <div className="pt-3 border-t border-[#ded9cf]/80 flex items-center space-x-2 overflow-x-auto no-scrollbar">
            <span className="text-[11px] font-medium text-stone-500 shrink-0">Sources:</span>
            {citations.map((citation, idx) => (
              <CompactCitationPill
                key={idx}
                citation={citation}
                index={idx}
                onInspect={onInspectCitation}
              />
            ))}
          </div>
        )}

        {/* Gemini-style Action Bar */}
        <div className="flex items-center space-x-1 pt-1 text-stone-400 text-xs">
          <button
            onClick={handleCopy}
            className="p-1.5 hover:bg-[#eae5dc] rounded-md transition-colors text-stone-500 cursor-pointer"
            title="Copy response"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
          <button className="p-1.5 hover:bg-[#eae5dc] rounded-md transition-colors text-stone-500 cursor-pointer" title="Good response">
            <ThumbsUp className="w-3.5 h-3.5" />
          </button>
          <button className="p-1.5 hover:bg-[#eae5dc] rounded-md transition-colors text-stone-500 cursor-pointer" title="Poor response">
            <ThumbsDown className="w-3.5 h-3.5" />
          </button>
          <button className="p-1.5 hover:bg-[#eae5dc] rounded-md transition-colors text-stone-500 cursor-pointer" title="Share">
            <Share2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
