'use client';

import React, { useState } from 'react';
import { IngestedFile, SourceType } from '../lib/types';
import { getSourceTypeLabel } from './CitationCard';
import { X, Upload, Trash2, FolderSync } from 'lucide-react';

interface UploadDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  files: IngestedFile[];
  onAddFiles: (files: File[]) => Promise<void>;
  onRemoveFile: (id: string) => void;
  onLoadSyntheticPack: () => Promise<void>;
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
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [loadingPack, setLoadingPack] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleManualUpload = async (uploadedFiles: File[]) => {
    setUploadError(null);
    setIsUploading(true);
    try {
      await onAddFiles(uploadedFiles);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Could not index the selected file.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleLoadPack = async () => {
    setUploadError(null);
    setLoadingPack(true);
    try {
      await onLoadSyntheticPack();
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Could not index the demo evidence pack.');
    } finally {
      setLoadingPack(false);
    }
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
                Indexed in MongoDB Atlas
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
              onClick={() => void handleLoadPack()}
              disabled={loadingPack || isUploading}
              className="mt-2.5 px-3 py-1.5 text-xs font-medium bg-stone-800 text-stone-50 hover:bg-stone-900 rounded-lg w-full flex items-center justify-center space-x-1.5 transition-colors cursor-pointer"
            >
              <FolderSync className="w-3.5 h-3.5" />
              <span>{loadingPack ? 'Indexing evidence pack…' : 'Load incident evidence pack'}</span>
            </button>
          </div>

          {/* Upload Area */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragActive(false);
              if (e.dataTransfer.files) void handleManualUpload(Array.from(e.dataTransfer.files));
            }}
            className={`mt-4 border border-dashed rounded-xl p-4 text-center transition-all ${
              dragActive ? 'border-stone-700 bg-[#efebe4]' : 'border-stone-300 bg-[#f3efe8]/50 hover:border-stone-400'
            }`}
          >
            <input
              type="file"
              id="file-upload"
              multiple
              accept=".pdf,.docx,.md,.html,.htm,.vtt,.txt,.json,.csv,.png,.jpg,.jpeg,.webp"
              className="hidden"
              disabled={isUploading || loadingPack}
              onChange={(e) => {
                if (e.target.files) void handleManualUpload(Array.from(e.target.files));
                e.target.value = '';
              }}
            />
            <label htmlFor="file-upload" className="cursor-pointer block">
              <Upload className="w-5 h-5 text-stone-400 mx-auto mb-1" />
              <p className="text-xs font-medium text-stone-700">
                {isUploading ? 'Uploading and indexing…' : 'Upload evidence files'}
              </p>
              <p className="text-[11px] text-stone-400 mt-0.5">PDF, DOCX, Markdown, HTML, VTT, text, JSON, CSV, PNG</p>
            </label>
          </div>
          {uploadError && (
            <p className="mt-2 text-xs text-rose-700" role="alert">{uploadError}</p>
          )}

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
