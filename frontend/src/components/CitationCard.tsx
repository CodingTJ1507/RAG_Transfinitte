'use client';

import React from 'react';
import { Citation, SourceType } from '../lib/types';
import { FileText, Globe, Image as ImageIcon, Mic, Database, ExternalLink } from 'lucide-react';

interface CitationCardProps {
  citation: Citation;
  index: number;
  onInspect: (citation: Citation) => void;
}

export const getSourceIcon = (type: SourceType) => {
  switch (type) {
    case 'document':
      return <FileText className="w-3.5 h-3.5 text-blue-500" />;
    case 'webpage':
      return <Globe className="w-3.5 h-3.5 text-cyan-600" />;
    case 'image':
      return <ImageIcon className="w-3.5 h-3.5 text-violet-500" />;
    case 'transcript':
      return <Mic className="w-3.5 h-3.5 text-amber-500" />;
    case 'structured_record':
      return <Database className="w-3.5 h-3.5 text-emerald-600" />;
  }
};

export const getSourceBadge = (type: SourceType) => {
  switch (type) {
    case 'document':
      return 'bg-blue-50 text-blue-700 border-blue-200/60';
    case 'webpage':
      return 'bg-cyan-50 text-cyan-700 border-cyan-200/60';
    case 'image':
      return 'bg-violet-50 text-violet-700 border-violet-200/60';
    case 'transcript':
      return 'bg-amber-50 text-amber-700 border-amber-200/60';
    case 'structured_record':
      return 'bg-emerald-50 text-emerald-700 border-emerald-200/60';
  }
};

export const CitationCard: React.FC<CitationCardProps> = ({ citation, index, onInspect }) => {
  return (
    <div
      onClick={() => onInspect(citation)}
      className="clay-card-sm p-3 hover:translate-y-[-1px] transition-all cursor-pointer border border-white/70 hover:border-indigo-300 group flex flex-col justify-between"
    >
      <div>
        {/* Source Header */}
        <div className="flex items-center justify-between mb-1.5">
          <div className="flex items-center space-x-1.5">
            <span className="p-1 rounded-lg bg-slate-50 border border-slate-200/60 shadow-xs">
              {getSourceIcon(citation.source_type)}
            </span>
            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-md border ${getSourceBadge(citation.source_type)} uppercase tracking-wider`}>
              {citation.source_type.replace('_', ' ')}
            </span>
          </div>

          <span className="text-[10px] font-mono font-medium text-slate-400 group-hover:text-indigo-600 transition-colors flex items-center space-x-0.5">
            <span>#{index + 1}</span>
            <ExternalLink className="w-2.5 h-2.5 opacity-0 group-hover:opacity-100 transition-opacity" />
          </span>
        </div>

        {/* Title */}
        <h4 className="text-xs font-bold text-slate-800 line-clamp-1 group-hover:text-indigo-700 transition-colors">
          {citation.title}
        </h4>

        {/* Location Tag */}
        <div className="text-[11px] font-medium text-indigo-600 mt-0.5 font-mono">
          📍 {citation.location}
        </div>

        {/* Snippet preview */}
        <p className="text-[11px] text-slate-500 line-clamp-2 mt-1.5 leading-relaxed italic">
          "{citation.snippet}"
        </p>
      </div>

      <div className="mt-2.5 pt-1.5 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
        <span>Confidence: {(citation.confidence * 100).toFixed(0)}%</span>
        <span className="text-indigo-600 font-medium group-hover:underline">Inspect passage →</span>
      </div>
    </div>
  );
};
