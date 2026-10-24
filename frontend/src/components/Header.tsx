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
    <header className="sticky top-0 z-20 bg-[#f8fafc]/90 backdrop-blur-xs border-b border-[#dde4ec] px-4 md:px-6 py-2.5 flex items-center justify-between">
      {/* Brand Logo & Tagline */}
      <div className="flex items-center space-x-2">
        <div className="flex items-center space-x-2 cursor-pointer hover:opacity-90 py-1 transition-opacity">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/concord-logo.svg"
            alt="Concord.ai"
            className="h-6 md:h-7 w-auto object-contain"
          />
          <span className="text-[10px] font-semibold tracking-wide text-[#087f82] bg-[#09bec1]/10 border border-[#09bec1]/25 px-2 py-0.5 rounded-full hidden sm:inline-block">
            Evidence RAG
          </span>
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center space-x-2">
        {/* Atlas status dot */}
        <div className="hidden sm:flex items-center space-x-1.5 text-xs text-slate-600 font-medium px-2 py-1">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Atlas Connected</span>
        </div>

        {/* Evidence Pack pill */}
        <button
          onClick={onOpenUpload}
          className="flex items-center space-x-1.5 text-xs text-[#162748] bg-[#eaf0f6] hover:bg-[#dce6f0] border border-[#d4dee8] hover:border-[#09bec1]/40 px-3 py-1.5 rounded-full transition-all font-medium cursor-pointer shadow-2xs"
        >
          <FolderUp className="w-3.5 h-3.5 text-[#09bec1]" />
          <span>Evidence ({ingestedFileCount})</span>
        </button>

        {/* Reset */}
        <button
          onClick={onResetChat}
          className="p-1.5 text-slate-500 hover:text-[#162748] hover:bg-[#eaf0f6] rounded-full transition-colors cursor-pointer"
          title="New Investigation"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
