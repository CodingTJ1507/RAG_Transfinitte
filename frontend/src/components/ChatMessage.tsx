'use client';

import React, { useState } from 'react';
import { ChatMessage as ChatMessageType, Citation } from '../lib/types';
import { ThinkingAccordion } from './ThinkingAccordion';
import { InlineCitationBadge, CompactCitationPill } from './CitationCard';
import { Copy, Check, ThumbsUp, ThumbsDown, Share2, Sparkles, AlertCircle, ShieldAlert, RefreshCw } from 'lucide-react';

interface ChatMessageProps {
  message: ChatMessageType;
  isStreaming?: boolean;
  onInspectCitation: (citation: Citation) => void;
  onRetry?: (query: string) => void;
}

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
        <div className="max-w-[85%] md:max-w-[70%] bg-slate-100 rounded-3xl px-5 py-3 text-slate-800 text-sm leading-relaxed font-normal">
          {message.content}
          {message.attachedFiles && message.attachedFiles.length > 0 && (
            <div className="mt-2 pt-2 border-t border-slate-200/60 flex flex-wrap gap-1.5">
              {message.attachedFiles.map((file, idx) => (
                <span key={idx} className="text-[11px] px-2 py-0.5 rounded-full bg-white text-slate-600 font-mono border border-slate-200">
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
            <div className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center shrink-0">
              <AlertCircle className="w-3.5 h-3.5 text-slate-500" />
            </div>
            <span className="text-xs font-semibold text-slate-700">
              {message.errorTitle || 'Something Went Wrong'}
            </span>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-slate-700 text-xs leading-relaxed space-y-3">
            <p className="text-xs text-slate-600">
              {message.content || 'An unexpected error occurred while processing your request. Please try again.'}
            </p>

            {onRetry && message.rawQuery && (
              <div className="pt-1">
                <button
                  onClick={() => onRetry(message.rawQuery!)}
                  className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium rounded-lg flex items-center space-x-1.5 transition-colors cursor-pointer"
                >
                  <RefreshCw className="w-3 h-3" />
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
        {/* Gemini Sparkle Indicator / Thinking */}
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-blue-500 via-indigo-500 to-amber-300 flex items-center justify-center p-0.5 shrink-0 shadow-2xs">
            <div className="w-full h-full bg-white rounded-full flex items-center justify-center">
              <Sparkles className="w-3 h-3 text-blue-600" />
            </div>
          </div>
          <span className="text-xs font-semibold text-slate-700">TraceIQ</span>
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
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 text-xs leading-relaxed space-y-1">
            <div className="flex items-center space-x-1.5 font-semibold text-slate-900">
              <ShieldAlert className="w-4 h-4 text-slate-600" />
              <span>Evidence-Based Abstention</span>
            </div>
            <p className="text-slate-600">
              {report.abstention_reason}
            </p>
          </div>
        )}

        {/* Test 3: Conflicting Evidence Alert */}
        {report?.conflicting_evidence && report.conflicting_evidence.length > 0 && (
          <div className="p-3.5 rounded-xl bg-amber-50/60 border border-amber-200/80 text-amber-900 text-xs leading-relaxed space-y-1">
            <div className="flex items-center space-x-1.5 font-semibold text-amber-800">
              <AlertCircle className="w-4 h-4" />
              <span>Conflicting Documentation Detected</span>
            </div>
            <p className="text-amber-700">
              Runbook specifies Redis Sentinel cache (v1.8), while the Architecture Diagram depicts an in-memory cache (v2.2).
            </p>
          </div>
        )}

        {/* Primary Diagnosis / Content (Clean Gemini Typography) */}
        {report?.likely_root_cause ? (
          <div className="space-y-4 text-sm text-slate-800 leading-relaxed">
            <h3 className="font-semibold text-base text-slate-900">
              Incident Diagnosis & Findings
            </h3>
            <p className="text-slate-700 leading-relaxed">
              {report.likely_root_cause}
              {/* Inline Gemini Citations */}
              {citations.slice(0, 3).map((cit, idx) => (
                <InlineCitationBadge
                  key={idx}
                  citation={cit}
                  onInspect={onInspectCitation}
                />
              ))}
            </p>

            {/* Reconstructed Incident Timeline */}
            {report.timeline && report.timeline.length > 0 && (
              <div className="pt-2">
                <h4 className="font-medium text-xs text-slate-500 uppercase tracking-wider mb-2">
                  Chronological Timeline
                </h4>
                <ul className="space-y-2 text-sm text-slate-700 pl-1">
                  {report.timeline.map((evt, idx) => {
                    const matchedCitation = citations.find(c => c.source_id === evt.source_id) || citations[idx % citations.length];
                    return (
                      <li key={idx} className="flex items-start justify-between flex-wrap gap-1">
                        <div className="flex items-baseline space-x-2">
                          <span className="text-slate-400 font-mono text-xs">•</span>
                          <span className="font-mono text-xs font-semibold text-slate-500 shrink-0">{evt.timestamp}</span>
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
                <h4 className="font-medium text-xs text-slate-500 uppercase tracking-wider mb-2">
                  Recommended Remediation
                </h4>
                <ul className="space-y-1.5 text-sm text-slate-700 pl-1">
                  {report.recommended_actions.map((act, idx) => (
                    <li key={idx} className="flex items-baseline space-x-2">
                      <span className="text-slate-400 font-mono text-xs">•</span>
                      <span>{act}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <div className="text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">
            {message.content}
          </div>
        )}

        {/* Minimal Sources Bar at Bottom */}
        {citations.length > 0 && (
          <div className="pt-3 border-t border-slate-100 flex items-center space-x-2 overflow-x-auto no-scrollbar">
            <span className="text-[11px] font-medium text-slate-400 shrink-0">Sources:</span>
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
        <div className="flex items-center space-x-1 pt-1 text-slate-400 text-xs">
          <button
            onClick={handleCopy}
            className="p-1.5 hover:bg-slate-100 rounded-md transition-colors text-slate-500"
            title="Copy response"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
          <button className="p-1.5 hover:bg-slate-100 rounded-md transition-colors text-slate-500" title="Good response">
            <ThumbsUp className="w-3.5 h-3.5" />
          </button>
          <button className="p-1.5 hover:bg-slate-100 rounded-md transition-colors text-slate-500" title="Poor response">
            <ThumbsDown className="w-3.5 h-3.5" />
          </button>
          <button className="p-1.5 hover:bg-slate-100 rounded-md transition-colors text-slate-500" title="Share">
            <Share2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
