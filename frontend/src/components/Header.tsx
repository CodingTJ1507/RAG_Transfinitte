'use client';

import React from 'react';
import { FolderUp, RotateCcw, ChevronDown } from 'lucide-react';

interface HeaderProps {
  onOpenUpload: () => void;
  onResetChat: () => void;
  ingestedFileCount: number;
}

export const Header: React.FC<HeaderProps> = ({ onOpenUpload, onResetChat, ingestedFileCount }) => {
  return (
    <header className="sticky top-0 z-20 bg-[#f7f5f0]/90 backdrop-blur-xs border-b border-[#ded9cf]/80 px-4 md:px-6 py-2.5 flex items-center justify-between">
      {/* Brand & Model Selector (Gemini style) */}
      <div className="flex items-center space-x-2">
        <div className="flex items-center space-x-1.5 cursor-pointer hover:bg-[#efebe4] px-2 py-1 rounded-lg transition-colors">
          <span className="font-semibold text-stone-800 text-base">TraceIQ</span>
          <span className="text-xs text-stone-500 font-medium flex items-center">
            <span>Evidence RAG</span>
            <ChevronDown className="w-3.5 h-3.5 ml-0.5 text-stone-400" />
          </span>
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center space-x-2">
        {/* Atlas status dot */}
        <div className="hidden sm:flex items-center space-x-1.5 text-xs text-stone-600 font-medium px-2 py-1">
          <span className="w-2 h-2 rounded-full bg-emerald-600"></span>
          <span>Atlas Connected</span>
        </div>

        {/* Evidence Pack pill */}
        <button
          onClick={onOpenUpload}
          className="flex items-center space-x-1.5 text-xs text-stone-700 bg-[#eae5dc] hover:bg-[#dfd9cd] border border-stone-300/40 px-3 py-1.5 rounded-full transition-colors font-medium cursor-pointer"
        >
          <FolderUp className="w-3.5 h-3.5 text-stone-500" />
          <span>Evidence ({ingestedFileCount})</span>
        </button>

        {/* Reset */}
        <button
          onClick={onResetChat}
          className="p-1.5 text-stone-500 hover:text-stone-800 hover:bg-[#eae5dc] rounded-full transition-colors cursor-pointer"
          title="New Investigation"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
