'use client';

import React from 'react';
import { Citation } from '../lib/types';
import { getSourceIcon, getSourceBadge } from './CitationCard';
import { X, Copy, Check, FileCheck, Layers } from 'lucide-react';

interface CitationModalProps {
  citation: Citation | null;
  onClose: () => void;
}

export const CitationModal: React.FC<CitationModalProps> = ({ citation, onClose }) => {
  const [copied, setCopied] = React.useState(false);

  if (!citation) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(citation.snippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/25 backdrop-blur-xs animate-in fade-in duration-200">
      <div 
        className="clay-card w-full max-w-lg p-6 bg-white max-h-[90vh] flex flex-col justify-between animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div>
          <div className="flex items-start justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center space-x-2.5">
              <span className="p-2 rounded-xl bg-slate-100 border border-slate-200/60">
                {getSourceIcon(citation.source_type)}
              </span>
              <div>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getSourceBadge(citation.source_type)} uppercase tracking-wider`}>
                  {citation.source_type.replace('_', ' ')}
                </span>
                <h3 className="text-sm font-bold text-slate-800 mt-1">
                  {citation.title}
                </h3>
              </div>
            </div>

            <button
              onClick={onClose}
              className="clay-btn p-1.5 text-slate-400 hover:text-slate-700 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Location Badge */}
          <div className="my-3 flex items-center justify-between text-xs bg-slate-50 p-2.5 rounded-xl border border-slate-100">
            <span className="font-semibold text-slate-600">Exact Evidence Location:</span>
            <span className="font-mono text-indigo-700 font-semibold px-2 py-0.5 rounded-md bg-white border border-slate-200 shadow-2xs">
              📍 {citation.location}
            </span>
          </div>

          {/* Full Extracted Passage */}
          <div className="mt-3">
            <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1.5">
              Ground-Truth Passage (Extracted Chunk)
            </label>
            <div className="clay-inset p-3.5 text-xs text-slate-700 leading-relaxed font-mono bg-slate-50/70 border border-slate-200/60 rounded-xl overflow-y-auto max-h-52 select-text">
              {citation.snippet}
            </div>
          </div>

          {/* Metadata properties */}
          <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500">
            <span>Retrieval Confidence: <strong>{(citation.confidence * 100).toFixed(1)}%</strong></span>
            <span>Source Identifier: <code className="font-mono text-slate-600">{citation.source_id}</code></span>
          </div>
        </div>

        {/* Modal Actions */}
        <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-end space-x-2.5">
          <button
            onClick={handleCopy}
            className="clay-btn px-4 py-2 flex items-center space-x-1.5 text-xs font-semibold text-slate-700 hover:text-indigo-600 transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied snippet' : 'Copy passage'}</span>
          </button>
          <button
            onClick={onClose}
            className="clay-btn-primary px-4 py-2 text-xs font-semibold"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
