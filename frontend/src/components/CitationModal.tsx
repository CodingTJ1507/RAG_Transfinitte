'use client';

import React, { useState } from 'react';
import { Citation } from '../lib/types';
import { API_BASE_URL } from '../lib/api';
import { getSourceTypeLabel } from './CitationCard';
import { X, Copy, Check, ExternalLink } from 'lucide-react';

interface CitationModalProps {
  citation: Citation | null;
  onClose: () => void;
}

export const CitationModal: React.FC<CitationModalProps> = ({ citation, onClose }) => {
  const [copied, setCopied] = useState(false);
  const [opening, setOpening] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [prevCitationKey, setPrevCitationKey] = useState<string | null>(null);

  const currentCitationKey = citation ? `${citation.source_id}:${citation.chunk_id}` : null;
  if (currentCitationKey !== prevCitationKey) {
    setPrevCitationKey(currentCitationKey);
    setErrorMessage(null);
    setCopied(false);
    setOpening(false);
  }

  if (!citation) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(citation.snippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleOpenOriginal = async () => {
    if (!citation || opening) return;
    setErrorMessage(null);
    setOpening(true);

    let tab: Window | null = null;
    try {
      tab = window.open('', '_blank');
      const response = await fetch(
        `${API_BASE_URL}/api/ingest/sources/${encodeURIComponent(citation.source_id)}/original`
      );
      if (!response.ok) {
        tab?.close();
        setErrorMessage('Original file unavailable right now');
        setOpening(false);
        return;
      }
      const blob = await response.blob();
      let url = URL.createObjectURL(blob);
      const contentType = response.headers.get('content-type') || blob.type || '';
      const locator = citation.metadata?.locator as { page?: number | string } | undefined;
      const page =
        locator?.page ??
        (citation.metadata as { page?: number | string } | undefined)?.page ??
        citation.location?.match(/Page\s+(\d+)/i)?.[1];
      if (contentType.toLowerCase().includes('application/pdf') && page) {
        url += `#page=${page}`;
      }
      if (tab) {
        tab.location.href = url;
      }
    } catch {
      tab?.close();
      setErrorMessage('Original file unavailable right now');
    } finally {
      setOpening(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-2xs animate-in fade-in duration-150">
      <div 
        className="w-full max-w-lg p-6 bg-[#ffffff] rounded-2xl shadow-xl border border-[#dde4ec] max-h-[90vh] flex flex-col justify-between"
        onClick={(e) => e.stopPropagation()}
      >
        <div>
          {/* Header */}
          <div className="flex items-start justify-between pb-3 border-b border-[#dde4ec]">
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-mono text-[10px] font-semibold text-[#087f82] bg-[#09bec1]/10 px-2 py-0.5 rounded-full border border-[#09bec1]/25">
                  {getSourceTypeLabel(citation.source_type)}
                </span>
                <span className="text-xs font-mono text-slate-500">
                  {citation.location}
                </span>
              </div>
              <h3 className="text-sm font-bold text-[#162748] mt-1.5">
                {citation.title}
              </h3>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-[#162748] hover:bg-[#eaf0f6] rounded-full transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Passage Container */}
          <div className="mt-4">
            <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1.5">
              Extracted Ground-Truth Chunk
            </label>
            <div className="p-3.5 text-xs text-[#162748] leading-relaxed font-mono bg-[#f8fafc] border border-[#d4dee8] rounded-xl overflow-y-auto max-h-52 select-text">
              {citation.snippet}
            </div>
          </div>

          {/* Metadata */}
          <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
            <span>
              {citation.retrieval_score === undefined
                ? 'Retrieved evidence'
                : `Rank score: ${citation.retrieval_score.toFixed(4)}`}
            </span>
            <span className="font-mono text-[#087f82]">{citation.source_id}</span>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="mt-6 pt-3 border-t border-[#dde4ec]">
          {errorMessage && (
            <p className="text-xs text-red-600 mb-2 font-medium text-right">{errorMessage}</p>
          )}
          <div className="flex items-center justify-end space-x-2">
            <button
              onClick={handleOpenOriginal}
              disabled={opening}
              className="px-3.5 py-1.5 flex items-center space-x-1.5 text-xs font-semibold text-[#162748] bg-[#eaf0f6] hover:bg-[#dce6f0] disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors cursor-pointer border border-[#d4dee8]"
            >
              <ExternalLink className="w-3.5 h-3.5 text-[#09bec1]" />
              <span>{opening ? 'Opening...' : 'Open original'}</span>
            </button>
            <button
              onClick={handleCopy}
              className="px-3.5 py-1.5 flex items-center space-x-1.5 text-xs font-semibold text-[#162748] bg-[#eaf0f6] hover:bg-[#dce6f0] rounded-lg transition-colors cursor-pointer border border-[#d4dee8]"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-[#09bec1]" />}
              <span>{copied ? 'Copied' : 'Copy snippet'}</span>
            </button>
            <button
              onClick={onClose}
              className="px-4 py-1.5 text-xs font-semibold text-white bg-[#162748] hover:bg-[#1f3660] hover:shadow-[0_0_12px_rgba(9,190,193,0.3)] rounded-lg transition-all cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
