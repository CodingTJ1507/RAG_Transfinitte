'use client';

import React, { useState } from 'react';
import { IngestedFile, SourceType } from '../lib/types';
import { getSourceTypeLabel } from './CitationCard';
import { X, Upload, Trash2, FolderSync } from 'lucide-react';

interface UploadDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  files: IngestedFile[];
  onAddFiles: (files: IngestedFile[]) => void;
  onRemoveFile: (id: string) => void;
  onLoadSyntheticPack: () => void;
}

export const UploadDrawer: React.FC<UploadDrawerProps> = ({
  isOpen,
  onClose,
  files,
  onAddFiles,
  onRemoveFile,
  onLoadSyntheticPack,
}) => {
  const [selectedType, setSelectedType] = useState<SourceType | 'all'>('all');
  const [dragActive, setDragActive] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleManualUpload = (uploadedFiles: File[]) => {
    const newItems: IngestedFile[] = uploadedFiles.map((file, idx) => {
      let type: SourceType = 'document';
      const ext = file.name.split('.').pop()?.toLowerCase();
      if (ext === 'html' || ext === 'htm') type = 'webpage';
      else if (['png', 'jpg', 'jpeg', 'webp'].includes(ext || '')) type = 'image';
      else if (file.name.includes('transcript') || ext === 'wav' || ext === 'mp3') type = 'transcript';
      else if (['json', 'csv', 'log'].includes(ext || '')) type = 'structured_record';

      return {
        id: `manual-${Date.now()}-${idx}`,
        name: file.name,
        source_type: type,
        size: `${(file.size / 1024).toFixed(1)} KB`,
        uploadedAt: 'Just now',
        status: 'indexed',
        chunkCount: Math.max(1, Math.floor(file.size / 600))
      };
    });
    onAddFiles(newItems);
  };

  const filteredFiles = selectedType === 'all' 
    ? files 
    : files.filter(f => f.source_type === selectedType);

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-stone-900/25 backdrop-blur-2xs animate-in fade-in duration-150">
      <div 
        className="w-full max-w-md bg-[#faf8f5] border-l border-stone-300 h-full flex flex-col justify-between p-6 overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div>
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-stone-200">
            <div>
              <h2 className="text-base font-semibold text-stone-900">
                Evidence Collection
              </h2>
              <p className="text-xs text-stone-500 mt-0.5">
                Indexed in MongoDB Atlas Vector Search
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 text-stone-400 hover:text-stone-700 hover:bg-[#eae5dc] rounded-full transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Quick Demo Pack Loader */}
          <div className="mt-4 p-3.5 rounded-xl bg-[#f0ede6] border border-stone-300/80 shadow-2xs">
            <h4 className="text-xs font-semibold text-stone-800">
              Demo Incident Evidence Pack
            </h4>
            <p className="text-xs text-stone-600 mt-0.5 leading-relaxed">
              Load the 5 benchmark evidence files for the payment failure incident.
            </p>
            <button
              onClick={onLoadSyntheticPack}
              className="mt-2.5 px-3 py-1.5 text-xs font-medium bg-stone-800 text-stone-50 hover:bg-stone-900 rounded-lg w-full flex items-center justify-center space-x-1.5 transition-colors cursor-pointer"
            >
              <FolderSync className="w-3.5 h-3.5" />
              <span>Load 5 Source Files</span>
            </button>
          </div>

          {/* Upload Area */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragActive(false);
              if (e.dataTransfer.files) handleManualUpload(Array.from(e.dataTransfer.files));
            }}
            className={`mt-4 border border-dashed rounded-xl p-4 text-center transition-all ${
              dragActive ? 'border-stone-700 bg-[#efebe4]' : 'border-stone-300 bg-[#f3efe8]/50 hover:border-stone-400'
            }`}
          >
            <input
              type="file"
              id="file-upload"
              multiple
              className="hidden"
              onChange={(e) => e.target.files && handleManualUpload(Array.from(e.target.files))}
            />
            <label htmlFor="file-upload" className="cursor-pointer block">
              <Upload className="w-5 h-5 text-stone-400 mx-auto mb-1" />
              <p className="text-xs font-medium text-stone-700">Upload evidence files</p>
              <p className="text-[11px] text-stone-400 mt-0.5">PDF, HTML, PNG, Transcripts, JSON</p>
            </label>
          </div>

          {/* Category Filter Chips */}
          <div className="mt-4 flex flex-wrap gap-1.5">
            {(['all', 'document', 'webpage', 'image', 'transcript', 'structured_record'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setSelectedType(t)}
                className={`text-[11px] font-medium px-2.5 py-1 rounded-full border transition-colors cursor-pointer ${
                  selectedType === t
                    ? 'bg-stone-800 text-stone-50 border-stone-800'
                    : 'bg-[#eae5dc] text-stone-700 border-stone-300 hover:bg-[#dfd9ce]'
                }`}
              >
                {t === 'all' ? 'All' : t.replace('_', ' ')}
              </button>
            ))}
          </div>

          {/* Ingested File List */}
          <div className="mt-3 space-y-1.5 max-h-72 overflow-y-auto pr-1">
            {filteredFiles.map((file) => (
              <div
                key={file.id}
                className="p-2.5 rounded-lg border border-stone-200/80 hover:bg-[#f0ede6] flex items-center justify-between group transition-colors shadow-2xs"
              >
                <div className="min-w-0">
                  <div className="flex items-center space-x-1.5">
                    <span className="font-mono text-[9px] font-semibold text-stone-600 bg-[#f7f5f0] px-1 py-0.2 rounded border border-stone-300">
                      {getSourceTypeLabel(file.source_type)}
                    </span>
                    <p className="text-xs font-medium text-stone-800 truncate">
                      {file.name}
                    </p>
                  </div>
                  <p className="text-[10px] text-stone-500 mt-0.5 pl-6">
                    {file.chunkCount} chunks • {file.size}
                  </p>
                </div>

                <button
                  onClick={() => onRemoveFile(file.id)}
                  className="p-1 text-stone-400 hover:text-rose-600 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                  title="Remove"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom */}
        <div className="pt-4 border-t border-stone-200 mt-4">
          <button
            onClick={onClose}
            className="w-full py-2 text-xs font-medium text-stone-700 bg-[#eae5dc] hover:bg-[#dfd9ce] rounded-lg transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
