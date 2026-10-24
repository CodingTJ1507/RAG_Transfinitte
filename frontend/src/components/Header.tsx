'use client';

import React from 'react';
import { ShieldCheck, Database, FolderUp, RotateCcw, Sparkles } from 'lucide-react';

interface HeaderProps {
  onOpenUpload: () => void;
  onResetChat: () => void;
  ingestedFileCount: number;
}

export const Header: React.FC<HeaderProps> = ({ onOpenUpload, onResetChat, ingestedFileCount }) => {
  return (
    <header className="sticky top-0 z-20 backdrop-blur-md bg-[#f4f6fa]/85 border-b border-white/60 px-4 md:px-8 py-3.5 flex items-center justify-between transition-all">
      {/* Brand Identity */}
      <div className="flex items-center space-x-3.5">
        <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-500 to-indigo-400 flex items-center justify-center shadow-md shadow-indigo-300/40 text-white font-bold text-lg">
          🔍
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-lg font-bold tracking-tight text-slate-800">TraceIQ</h1>
            <span className="text-[11px] font-semibold tracking-wide uppercase px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/60 shadow-xs">
              Evidence Investigator
            </span>
          </div>
          <p className="text-xs text-slate-500 font-medium">Multimodal RAG with Grounded Citations</p>
        </div>
      </div>

      {/* Action Controls */}
      <div className="flex items-center space-x-2.5">
        {/* MongoDB Connection Status Indicator */}
        <div className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-full clay-card-sm text-xs font-medium text-slate-600">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <Database className="w-3.5 h-3.5 text-slate-500" />
          <span>MongoDB Atlas: Connected</span>
        </div>

        {/* Upload / Evidence Drawer Toggle */}
        <button
          onClick={onOpenUpload}
          className="clay-btn px-3.5 py-1.5 flex items-center space-x-2 text-xs font-semibold text-slate-700 hover:text-indigo-600 transition-colors"
          title="Upload or Inspect Evidence"
        >
          <FolderUp className="w-3.5 h-3.5 text-indigo-500" />
          <span>Evidence Pack</span>
          <span className="px-1.5 py-0.2 rounded-full bg-slate-100 text-[11px] font-bold text-slate-600">
            {ingestedFileCount}
          </span>
        </button>

        {/* Reset Chat */}
        <button
          onClick={onResetChat}
          className="clay-btn p-2 text-slate-500 hover:text-slate-800 transition-colors"
          title="Reset Investigation"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>
    </header>
  );
};
