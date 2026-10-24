'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
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
    <div className="mb-3 text-xs">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center space-x-1.5 text-slate-500 hover:text-slate-800 transition-colors py-1 cursor-pointer font-medium"
      >
        {isStreaming ? (
          <span className="inline-block w-2 h-2 rounded-full bg-blue-500 animate-pulse mr-1"></span>
        ) : null}
        <span>{isStreaming ? 'Thinking...' : `Thinking Process (${seconds}s)`}</span>
        {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
      </button>

      {isOpen && (
        <div className="mt-1.5 pl-3 border-l border-slate-200 space-y-1.5 text-xs text-slate-600">
          {steps.length > 0 ? (
            steps.map((step, idx) => (
              <div key={idx} className="flex items-baseline space-x-2">
                <span className="text-[10px] text-slate-400 font-mono shrink-0">{step.timestamp}</span>
                <span className="font-medium text-slate-700">{step.step}:</span>
                <span className="text-slate-500 text-[11px]">{step.detail}</span>
              </div>
            ))
          ) : (
            <div className="text-slate-400 italic">Searching knowledge sources and analyzing logs...</div>
          )}
        </div>
      )}
    </div>
  );
};
