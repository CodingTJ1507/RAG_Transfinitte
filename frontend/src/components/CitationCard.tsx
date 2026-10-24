'use client';

import React from 'react';
import { Citation, SourceType } from '../lib/types';
import { FileText, Globe, Image as ImageIcon, Mic, Database } from 'lucide-react';

export const getSourceTypeLabel = (type: SourceType) => {
  switch (type) {
    case 'document':
      return 'DOC';
    case 'webpage':
      return 'WEB';
    case 'image':
      return 'PNG';
    case 'transcript':
      return 'AUDIO';
    case 'structured_record':
      return 'LOG';
  }
};

export const getSourceIcon = (type: SourceType) => {
  switch (type) {
    case 'document':
      return <FileText className="w-3 h-3 text-blue-500" />;
    case 'webpage':
      return <Globe className="w-3 h-3 text-cyan-600" />;
    case 'image':
      return <ImageIcon className="w-3 h-3 text-violet-500" />;
    case 'transcript':
      return <Mic className="w-3 h-3 text-amber-500" />;
    case 'structured_record':
      return <Database className="w-3 h-3 text-emerald-600" />;
  }
};

export const getSourceBadgeStyles = (type: SourceType) => {
  switch (type) {
    case 'document':
      return 'bg-blue-50 text-blue-700 border-blue-200/80 hover:bg-blue-100';
    case 'webpage':
      return 'bg-cyan-50 text-cyan-700 border-cyan-200/80 hover:bg-cyan-100';
    case 'image':
      return 'bg-violet-50 text-violet-700 border-violet-200/80 hover:bg-violet-100';
    case 'transcript':
      return 'bg-amber-50 text-amber-700 border-amber-200/80 hover:bg-amber-100';
    case 'structured_record':
      return 'bg-emerald-50 text-emerald-700 border-emerald-200/80 hover:bg-emerald-100';
  }
};

export const getSourceBadge = getSourceBadgeStyles;

/**
 * Gemini-style compact inline citation badge (e.g. [JPG], [LOG], [DOC])
 * Sits directly next to text/data without disrupting the reading flow.
 */
interface InlineCitationBadgeProps {
  citation: Citation;
  index?: number;
  onInspect: (citation: Citation) => void;
}

export const InlineCitationBadge: React.FC<InlineCitationBadgeProps> = ({ citation, index, onInspect }) => {
  const label = getSourceTypeLabel(citation.source_type);
  const badgeStyle = getSourceBadgeStyles(citation.source_type);

  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        onInspect(citation);
      }}
      title={`${citation.title} (${citation.location})\nClick to inspect snippet`}
      className={`inline-flex items-center space-x-1 px-1.5 py-0.5 mx-1 align-baseline rounded-md border text-[10px] font-mono font-bold transition-all shadow-2xs cursor-pointer select-none ${badgeStyle}`}
    >
      <span>{getSourceIcon(citation.source_type)}</span>
      <span>{label}</span>
      {index !== undefined && <span className="opacity-60 text-[9px]">#{index + 1}</span>}
    </button>
  );
};

/**
 * Minimal horizontal pill for the bottom "Sources" row (Gemini / Perplexity style)
 */
interface CompactCitationPillProps {
  citation: Citation;
  index: number;
  onInspect: (citation: Citation) => void;
}

export const CompactCitationPill: React.FC<CompactCitationPillProps> = ({ citation, index, onInspect }) => {
  const badgeStyle = getSourceBadgeStyles(citation.source_type);

  return (
    <button
      type="button"
      onClick={() => onInspect(citation)}
      className="clay-card-sm px-2.5 py-1.5 flex items-center space-x-2 text-left hover:border-indigo-300 transition-all cursor-pointer group shrink-0 bg-white"
      title={citation.snippet}
    >
      <span className="p-1 rounded-md bg-slate-50 border border-slate-200/60">
        {getSourceIcon(citation.source_type)}
      </span>
      <div className="max-w-[200px]">
        <div className="flex items-center space-x-1.5">
          <span className={`text-[9px] font-bold px-1 py-0.2 rounded border uppercase font-mono ${badgeStyle}`}>
            {getSourceTypeLabel(citation.source_type)}
          </span>
          <span className="text-[11px] font-semibold text-slate-700 truncate group-hover:text-indigo-600 transition-colors">
            {citation.title}
          </span>
        </div>
        <p className="text-[10px] text-indigo-600 font-mono truncate">
          📍 {citation.location}
        </p>
      </div>
    </button>
  );
};
