'use client';

import React from 'react';
import { ChatMessage as ChatMessageType, Citation } from '../lib/types';
import { ThinkingAccordion } from './ThinkingAccordion';
import { CitationCard } from './CitationCard';
import { AlertTriangle, ShieldAlert, CheckCircle, Clock, ChevronRight, User, Cpu } from 'lucide-react';

interface ChatMessageProps {
  message: ChatMessageType;
  isStreaming?: boolean;
  onInspectCitation: (citation: Citation) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  isStreaming = false,
  onInspectCitation,
}) => {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end mb-5">
        <div className="flex items-start space-x-2.5 max-w-[85%] md:max-w-[70%] flex-row-reverse space-x-reverse">
          <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center shrink-0 shadow-md text-xs font-bold">
            <User className="w-4 h-4 text-slate-200" />
          </div>
          <div className="clay-card-sm px-4 py-3 bg-white text-slate-800 text-sm leading-relaxed border border-slate-200/60 font-medium">
            {message.content}
            {message.attachedFiles && message.attachedFiles.length > 0 && (
              <div className="mt-2 pt-2 border-t border-slate-100 flex flex-wrap gap-1.5">
                {message.attachedFiles.map((file, idx) => (
                  <span key={idx} className="text-[10px] px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 font-mono">
                    📎 {file}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  const report = message.report;

  return (
    <div className="flex justify-start mb-7">
      <div className="flex items-start space-x-3 max-w-[95%] md:max-w-[85%] w-full">
        {/* Assistant Avatar */}
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-600 to-indigo-400 text-white flex items-center justify-center shrink-0 shadow-md shadow-indigo-300/40 text-xs font-bold mt-1">
          <Cpu className="w-4 h-4 text-white" />
        </div>

        {/* Assistant Content Card */}
        <div className="clay-card p-5 bg-white w-full border border-white/80">
          {/* ChatGPT-style Thinking Accordion */}
          {(message.thinkingSteps || isStreaming) && (
            <ThinkingAccordion
              steps={message.thinkingSteps}
              durationMs={message.thinkingDurationMs}
              isStreaming={isStreaming}
            />
          )}

          {/* Test 4: Evidence-Based Abstention Box */}
          {report?.is_abstention && (
            <div className="mb-4 p-4 rounded-2xl bg-rose-50 border border-rose-200/80 text-rose-900">
              <div className="flex items-center space-x-2 text-rose-700 font-bold text-xs uppercase tracking-wider mb-1">
                <ShieldAlert className="w-4 h-4" />
                <span>Evidence-Based Abstention Triggered</span>
              </div>
              <p className="text-xs font-medium leading-relaxed text-rose-800">
                {report.abstention_reason}
              </p>
            </div>
          )}

          {/* Test 3: Conflicting Evidence Alert Box */}
          {report?.conflicting_evidence && report.conflicting_evidence.length > 0 && (
            <div className="mb-4 p-4 rounded-2xl bg-amber-50 border border-amber-200/80 text-amber-900">
              <div className="flex items-center space-x-2 text-amber-700 font-bold text-xs uppercase tracking-wider mb-1">
                <AlertTriangle className="w-4 h-4" />
                <span>Conflicting Evidence Detected</span>
              </div>
              <p className="text-xs font-medium leading-relaxed text-amber-800">
                Direct contradiction between sources: The runbook specifies an external Redis cluster, while recent architecture diagrams specify an in-memory cache.
              </p>
            </div>
          )}

          {/* Likely Root Cause / Primary Narrative */}
          {report?.likely_root_cause && (
            <div className="mb-4">
              <div className="flex items-center justify-between mb-1.5">
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Diagnosis & Primary Finding
                </h3>
                {report.confidence_score > 0 && (
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/60 font-semibold">
                    Confidence: {(report.confidence_score * 100).toFixed(0)}%
                  </span>
                )}
              </div>
              <p className="text-sm font-semibold text-slate-800 leading-relaxed bg-slate-50/70 p-3.5 rounded-xl border border-slate-100">
                {report.likely_root_cause}
              </p>
            </div>
          )}

          {/* General content if no root cause */}
          {!report?.likely_root_cause && message.content && (
            <div className="text-sm text-slate-700 leading-relaxed mb-4 whitespace-pre-wrap">
              {message.content}
            </div>
          )}

          {/* Incident Timeline (if present) */}
          {report?.timeline && report.timeline.length > 0 && (
            <div className="mb-5">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2.5 flex items-center space-x-1.5">
                <Clock className="w-3.5 h-3.5 text-indigo-500" />
                <span>Reconstructed Cross-Source Timeline</span>
              </h4>
              <div className="space-y-2 border-l-2 border-indigo-100 pl-3 ml-1.5">
                {report.timeline.map((evt, idx) => (
                  <div key={idx} className="relative text-xs">
                    <span className="absolute -left-[19px] top-1.5 w-2.5 h-2.5 rounded-full bg-indigo-500 ring-4 ring-white"></span>
                    <div className="flex items-baseline space-x-2">
                      <span className="font-mono font-bold text-indigo-700 text-[11px] shrink-0">
                        {evt.timestamp}
                      </span>
                      <span className="text-slate-700 font-medium">
                        {evt.event}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Supporting Evidence Citations (Grid) */}
          {report?.supporting_evidence && report.supporting_evidence.length > 0 && (
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Grounded Citations ({report.supporting_evidence.length} Sources)
                </h4>
                <span className="text-[10px] text-slate-400">Click to view source</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {report.supporting_evidence.map((citation, idx) => (
                  <CitationCard
                    key={idx}
                    citation={citation}
                    index={idx}
                    onInspect={onInspectCitation}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Recommended Actions */}
          {report?.recommended_actions && report.recommended_actions.length > 0 && (
            <div className="mt-4 pt-3.5 border-t border-slate-100">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                <span>Recommended Engineering Next Steps</span>
              </h4>
              <ul className="space-y-1.5">
                {report.recommended_actions.map((act, idx) => (
                  <li key={idx} className="flex items-start space-x-2 text-xs text-slate-700">
                    <ChevronRight className="w-3.5 h-3.5 text-indigo-500 shrink-0 mt-0.5" />
                    <span>{act}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
