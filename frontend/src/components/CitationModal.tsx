'use client';

import React, { useState } from 'react';
import { Citation } from '../lib/types';
import { getSourceTypeLabel } from './CitationCard';
import { X, Copy, Check } from 'lucide-react';

interface CitationModalProps {
  citation: Citation | null;
  onClose: () => void;
}

export const CitationModal: React.FC<CitationModalProps> = ({ citation, onClose }) => {
  const [copied, setCopied] = useState(false);

  if (!citation) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(citation.snippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/30 backdrop-blur-2xs animate-in fade-in duration-150">
      <div 
        className="w-full max-w-lg p-6 bg-white rounded-2xl shadow-xl border border-slate-200 max-h-[90vh] flex flex-col justify-between"
        onClick={(e) => e.stopPropagation()}
      >
        <div>
          {/* Header */}
          <div className="flex items-start justify-between pb-3 border-b border-slate-100">
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-mono text-[10px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full border border-slate-200">
                  {getSourceTypeLabel(citation.source_type)}
                </span>
                <span className="text-xs font-mono text-slate-500">
                  {citation.location}
                </span>
              </div>
              <h3 className="text-sm font-semibold text-slate-900 mt-1">
                {citation.title}
              </h3>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-full transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Passage Container */}
          <div className="mt-4">
            <label className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block mb-1.5">
              Extracted Ground-Truth Chunk
            </label>
            <div className="p-3.5 text-xs text-slate-700 leading-relaxed font-mono bg-slate-50 border border-slate-200 rounded-xl overflow-y-auto max-h-52 select-text">
              {citation.snippet}
            </div>
          </div>

          {/* Metadata */}
          <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
            <span>Confidence: {(citation.confidence * 100).toFixed(0)}%</span>
            <span className="font-mono">{citation.source_id}</span>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="mt-6 pt-3 border-t border-slate-100 flex items-center justify-end space-x-2">
          <button
            onClick={handleCopy}
            className="px-3.5 py-1.5 flex items-center space-x-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy snippet'}</span>
          </button>
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-medium text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
