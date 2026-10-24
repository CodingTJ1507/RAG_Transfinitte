'use client';

import React, { useState } from 'react';
import { IngestedFile, SourceType } from '../lib/types';
import { getSourceTypeLabel } from './CitationCard';
import { X, Upload, Plus, Trash2, FolderSync, CheckCircle2 } from 'lucide-react';

interface UploadDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  files: IngestedFile[];
  onAddFiles: (newFiles: IngestedFile[]) => void;
  onRemoveFile: (id: string) => void;
  onLoadSyntheticPack: () => void;
}

export const UploadDrawer: React.FC<UploadDrawerProps> = ({
  isOpen,
  onClose,
  files,
  onAddFiles,
  onRemoveFile,
  onLoadSyntheticPack
}) => {
  const [selectedType, setSelectedType] = useState<SourceType | 'all'>('all');
  const [dragActive, setDragActive] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleManualUpload = (uploaded: File[]) => {
    const newItems: IngestedFile[] = uploaded.map((f, i) => {
      let type: SourceType = 'document';
      if (f.name.endsWith('.json') || f.name.endsWith('.csv') || f.name.endsWith('.log')) type = 'structured_record';
      else if (f.name.endsWith('.png') || f.name.endsWith('.jpg')) type = 'image';
      else if (f.name.endsWith('.html')) type = 'webpage';
      else if (f.name.includes('transcript')) type = 'transcript';

      return {
        id: `upload-${Date.now()}-${i}`,
        name: f.name,
        source_type: type,
        size: `${(f.size / 1024).toFixed(1)} KB`,
        uploadedAt: 'Just now',
        status: 'indexed',
        chunkCount: Math.max(3, Math.floor(f.size / 400))
      };
    });
    onAddFiles(newItems);
  };

  const filteredFiles = selectedType === 'all' 
    ? files 
    : files.filter(f => f.source_type === selectedType);

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/25 backdrop-blur-2xs animate-in fade-in duration-150">
      <div 
        className="w-full max-w-md bg-white border-l border-slate-200 h-full flex flex-col justify-between p-6 overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div>
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <h2 className="text-base font-semibold text-slate-900">
                Evidence Collection
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Indexed in MongoDB Atlas Vector Search
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-full transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Quick Demo Pack Loader */}
          <div className="mt-4 p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <h4 className="text-xs font-semibold text-slate-800">
              Demo Incident Evidence Pack
            </h4>
            <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
              Load the 5 benchmark evidence files for the payment failure incident.
            </p>
            <button
              onClick={onLoadSyntheticPack}
              className="mt-2.5 px-3 py-1.5 text-xs font-medium bg-slate-900 text-white hover:bg-slate-800 rounded-lg w-full flex items-center justify-center space-x-1.5 transition-colors"
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
              dragActive ? 'border-blue-500 bg-blue-50/40' : 'border-slate-200 hover:border-slate-300'
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
              <Upload className="w-5 h-5 text-slate-400 mx-auto mb-1" />
              <p className="text-xs font-medium text-slate-700">Upload evidence files</p>
              <p className="text-[11px] text-slate-400 mt-0.5">PDF, HTML, PNG, Transcripts, JSON</p>
            </label>
          </div>

          {/* Category Filter Chips */}
          <div className="mt-4 flex flex-wrap gap-1.5">
            {(['all', 'document', 'webpage', 'image', 'transcript', 'structured_record'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setSelectedType(t)}
                className={`text-[11px] font-medium px-2.5 py-1 rounded-full border transition-colors ${
                  selectedType === t
                    ? 'bg-slate-900 text-white border-slate-900'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
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
                className="p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 flex items-center justify-between group transition-colors"
              >
                <div className="min-w-0">
                  <div className="flex items-center space-x-1.5">
                    <span className="font-mono text-[9px] font-semibold text-slate-500 bg-slate-100 px-1 py-0.2 rounded border border-slate-200">
                      {getSourceTypeLabel(file.source_type)}
                    </span>
                    <p className="text-xs font-medium text-slate-800 truncate">
                      {file.name}
                    </p>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-0.5 pl-6">
                    {file.chunkCount} chunks • {file.size}
                  </p>
                </div>

                <button
                  onClick={() => onRemoveFile(file.id)}
                  className="p-1 text-slate-300 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Remove"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom */}
        <div className="pt-4 border-t border-slate-100 mt-4">
          <button
            onClick={onClose}
            className="w-full py-2 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
