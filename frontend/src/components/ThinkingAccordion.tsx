'use client';

import React, { useState } from 'react';
import { Sparkles, ChevronDown, ChevronRight, CheckCircle2, Clock } from 'lucide-react';
import { ThinkingStep } from '../lib/types';

interface ThinkingAccordionProps {
  steps?: ThinkingStep[];
  durationMs?: number;
  isStreaming?: boolean;
}

export const ThinkingAccordion: React.FC<ThinkingAccordionProps> = ({
  steps = [],
  durationMs = 1800,
  isStreaming = false,
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(isStreaming);

  const seconds = (durationMs / 1000).toFixed(1);

  return (
    <div className="mb-3.5">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="clay-card-sm px-3.5 py-2 flex items-center justify-between w-full text-left text-xs font-semibold text-slate-700 hover:text-indigo-600 transition-all cursor-pointer group"
      >
        <div className="flex items-center space-x-2">
          {isStreaming ? (
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-indigo-600"></span>
            </span>
          ) : (
            <Sparkles className="w-3.5 h-3.5 text-indigo-500 transition-transform group-hover:rotate-12" />
          )}

          <span className="font-medium text-slate-600">
            {isStreaming ? 'Investigating multi-source evidence...' : `Investigated for ${seconds}s`}
          </span>
        </div>

        <div className="flex items-center space-x-1.5 text-slate-400 group-hover:text-slate-600 text-[11px]">
          <span>{isOpen ? 'Hide reasoning' : 'Show steps'}</span>
          {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        </div>
      </button>

      {isOpen && (
        <div className="mt-2 pl-3.5 pr-2 py-2 border-l-2 border-indigo-200 space-y-2.5 text-xs animate-in fade-in slide-in-from-top-1 duration-200">
          {steps.length > 0 ? (
            steps.map((step, idx) => (
              <div key={idx} className="flex items-start space-x-2.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 mt-0.5 shrink-0" />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-700">{step.step}</span>
                    <span className="text-[10px] text-slate-400 font-mono">{step.timestamp}</span>
                  </div>
                  <p className="text-slate-500 text-[11px] mt-0.5 leading-relaxed">{step.detail}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-slate-400 text-[11px] italic">
              {isStreaming ? 'Querying vector index and parsing structured logs...' : 'Reasoning synthesized.'}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
