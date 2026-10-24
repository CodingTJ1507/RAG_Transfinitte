'use client';

import React from 'react';
import { Citation, SourceType } from '../lib/types';

export const getSourceTypeLabel = (type: SourceType): string => {
  switch (type) {
    case 'document':
      return 'DOC';
    case 'webpage':
      return 'WEB';
    case 'image':
      return 'JPG';
    case 'transcript':
      return 'AUDIO';
    case 'structured_record':
      return 'LOG';
  }
};

/**
 * Gemini-identical subtle inline source badge (e.g. JPG, LOG, DOC)
 * In calm warm stone tone
 */
interface InlineCitationBadgeProps {
  citation: Citation;
  onInspect: (citation: Citation) => void;
}

export const InlineCitationBadge: React.FC<InlineCitationBadgeProps> = ({ citation, onInspect }) => {
  const label = getSourceTypeLabel(citation.source_type);

  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        onInspect(citation);
      }}
      title={`${citation.title} • ${citation.location}\nClick to inspect source passage`}
      className="gemini-source-badge"
    >
      {label}
    </button>
  );
};

/**
 * Minimalist source chip for bottom references list
 */
interface CompactCitationPillProps {
  citation: Citation;
  index: number;
  onInspect: (citation: Citation) => void;
}

export const CompactCitationPill: React.FC<CompactCitationPillProps> = ({ citation, onInspect }) => {
  const label = getSourceTypeLabel(citation.source_type);

  return (
    <button
      type="button"
      onClick={() => onInspect(citation)}
      className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-[#eae5dc] hover:bg-[#ded9ce] text-stone-700 text-xs transition-colors cursor-pointer shrink-0 border border-stone-300/60 shadow-2xs"
      title={citation.snippet}
    >
      <span className="font-mono text-[10px] font-semibold text-stone-600 bg-[#f7f5f0] px-1 py-0.2 rounded border border-stone-300/70">
        {label}
      </span>
      <span className="font-medium text-xs truncate max-w-[150px]">
        {citation.title}
      </span>
      <span className="text-[10px] text-stone-500 font-mono">
        {citation.location}
      </span>
    </button>
  );
};

export const getSourceBadge = () => 'bg-[#eae5dc] text-stone-700 border-stone-300';
export const getSourceIcon = () => null;
