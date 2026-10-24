'use client';

import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Plus, Mic } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (query: string, attachedFiles?: string[]) => void;
  isLoading: boolean;
  onOpenUpload: () => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading,
  onOpenUpload,
}) => {
  const [input, setInput] = useState<string>('');
  const [attachedFiles, setAttachedFiles] = useState<string[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const quickScenarios = [
    {
      label: 'Payment failure root cause',
      query: "Why did payment failures begin after yesterday's deployment?"
    },
    {
      label: 'Find error code PAY-401',
      query: 'Find every occurrence of error code PAY-401 and compare the affected versions.'
    },
    {
      label: 'Redis vs In-memory conflict',
      query: 'The runbook says the service uses Redis, but the latest architecture diagram shows an in-memory cache. Which is correct?'
    },
    {
      label: 'Outage code blame audit',
      query: 'Which engineer secretly caused the outage, and what exact line of code did they change?'
    }
  ];

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim(), attachedFiles);
    setInput('');
    setAttachedFiles([]);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="sticky bottom-0 z-10 p-3 md:p-5 bg-gradient-to-t from-[#f7f5f0] via-[#f7f5f0]/95 to-transparent">
      <div className="max-w-3xl mx-auto space-y-2.5">
        {/* Minimal Chips for Tests */}
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 no-scrollbar text-xs">
          {quickScenarios.map((scenario, idx) => (
            <button
              key={idx}
              onClick={() => onSendMessage(scenario.query)}
              disabled={isLoading}
              className="px-3 py-1.5 rounded-full bg-[#eae5dc] hover:bg-[#dfd9cd] text-stone-700 border border-stone-300/40 text-xs transition-colors shrink-0 disabled:opacity-50 font-normal cursor-pointer"
            >
              {scenario.label}
            </button>
          ))}
        </div>

        {/* Gemini-Style Rounded Capsule Input */}
        <div className="gemini-input-pill flex items-center px-3 py-2 shadow-2xs">
          {/* Plus / Attach Evidence Button */}
          <button
            type="button"
            onClick={onOpenUpload}
            className="p-2 text-stone-500 hover:text-stone-800 hover:bg-[#ded9cf]/70 rounded-full transition-colors shrink-0 cursor-pointer"
            title="Add evidence files"
          >
            <Plus className="w-4 h-4" />
          </button>

          {/* Text Area */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask TraceIQ..."
            rows={1}
            disabled={isLoading}
            className="flex-1 bg-transparent border-0 resize-none outline-hidden px-2.5 py-1 text-sm text-stone-800 placeholder-stone-400 font-normal max-h-32 leading-relaxed"
          />

          {/* Right Action Icons */}
          <div className="flex items-center space-x-1 shrink-0">
            <button
              type="button"
              className="p-2 text-stone-400 hover:text-stone-700 rounded-full transition-colors cursor-pointer"
              title="Voice query"
            >
              <Mic className="w-4 h-4" />
            </button>

            {/* Circular Send Arrow */}
            <button
              type="button"
              onClick={() => handleSubmit()}
              disabled={!input.trim() || isLoading}
              className={`w-8 h-8 rounded-full flex items-center justify-center transition-all cursor-pointer ${
                input.trim() && !isLoading
                  ? 'bg-stone-800 text-stone-50 hover:bg-stone-900'
                  : 'bg-[#ded9cf] text-stone-400 cursor-not-allowed'
              }`}
            >
              <ArrowUp className="w-4 h-4" />
            </button>
          </div>
        </div>

        <p className="text-[11px] text-center text-stone-400 font-normal">
          TraceIQ is evidence-grounded and cites all verified sources.
        </p>
      </div>
    </div>
  );
};
