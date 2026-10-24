'use client';

import React from 'react';
import { Database, FolderUp, RotateCcw, ChevronDown, Sparkles } from 'lucide-react';

interface HeaderProps {
  onOpenUpload: () => void;
  onResetChat: () => void;
  ingestedFileCount: number;
}

export const Header: React.FC<HeaderProps> = ({ onOpenUpload, onResetChat, ingestedFileCount }) => {
  return (
    <header className="sticky top-0 z-20 bg-white/95 backdrop-blur-xs border-b border-slate-100 px-4 md:px-6 py-2.5 flex items-center justify-between">
      {/* Brand & Model Selector (Gemini style) */}
      <div className="flex items-center space-x-2">
        <div className="flex items-center space-x-1.5 cursor-pointer hover:bg-slate-50 px-2 py-1 rounded-lg transition-colors">
          <span className="font-semibold text-slate-800 text-base">TraceIQ</span>
          <span className="text-xs text-slate-400 font-medium flex items-center">
            <span>Evidence RAG</span>
            <ChevronDown className="w-3.5 h-3.5 ml-0.5 text-slate-400" />
          </span>
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center space-x-2">
        {/* Atlas status dot */}
        <div className="hidden sm:flex items-center space-x-1.5 text-xs text-slate-500 font-medium px-2 py-1">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span>Atlas Connected</span>
        </div>

        {/* Evidence Pack pill */}
        <button
          onClick={onOpenUpload}
          className="flex items-center space-x-1.5 text-xs text-slate-700 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-full transition-colors font-medium"
        >
          <FolderUp className="w-3.5 h-3.5 text-slate-500" />
          <span>Evidence ({ingestedFileCount})</span>
        </button>

        {/* Reset */}
        <button
          onClick={onResetChat}
          className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-full transition-colors"
          title="New Investigation"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
