'use client';

import React, { useState } from 'react';
import { GitCompare, Copy, Check, FileDiff, Plus, Minus } from 'lucide-react';

interface DiffViewerProps {
  diff: string;
  targetFile: string;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ diff, targetFile }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!diff) return;
    navigator.clipboard.writeText(diff);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lines = diff ? diff.split('\n') : [];
  const additions = lines.filter((l) => l.startsWith('+') && !l.startsWith('+++')).length;
  const deletions = lines.filter((l) => l.startsWith('-') && !l.startsWith('---')).length;

  return (
    <div className="bg-slate-900/80 backdrop-blur-md rounded-2xl border border-slate-800 flex flex-col h-[520px] shadow-xl shadow-black/20 overflow-hidden">
      {/* Diff Header */}
      <div className="bg-slate-950/90 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <GitCompare className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-mono font-bold tracking-wider text-slate-200 uppercase">
            Unified Git Patch Inspection
          </span>
          {targetFile && (
            <span className="text-xs font-mono text-cyan-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
              {targetFile}
            </span>
          )}
        </div>

        {/* Stats and Copy */}
        <div className="flex items-center space-x-3">
          {diff && (
            <div className="flex items-center space-x-2 text-xs font-mono">
              <span className="flex items-center text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                <Plus className="w-3 h-3 mr-0.5" /> {additions}
              </span>
              <span className="flex items-center text-rose-400 bg-rose-950/60 px-2 py-0.5 rounded border border-rose-800/40">
                <Minus className="w-3 h-3 mr-0.5" /> {deletions}
              </span>
            </div>
          )}

          <button
            type="button"
            onClick={handleCopy}
            disabled={!diff}
            className="flex items-center space-x-1 px-2.5 py-1 rounded-md text-xs font-mono transition-colors cursor-pointer border bg-slate-900 hover:bg-slate-800 text-slate-300 border-slate-800 disabled:opacity-40 disabled:cursor-not-allowed"
            title="Copy diff to clipboard"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-slate-400" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Diff Content */}
      <div className="flex-1 p-3 overflow-y-auto font-mono text-xs bg-slate-950/60 select-text">
        {!diff ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-2">
            <FileDiff className="w-8 h-8 opacity-30 text-emerald-400" />
            <p className="text-xs font-mono">No patch generated yet. Waiting for CoderAgent execution.</p>
          </div>
        ) : (
          <div className="space-y-0.5">
            {lines.map((line, idx) => {
              const isAdd = line.startsWith('+') && !line.startsWith('+++');
              const isDel = line.startsWith('-') && !line.startsWith('---');
              const isHunk = line.startsWith('@@');

              let rowBg = 'hover:bg-slate-900/30 text-slate-300';
              if (isAdd) rowBg = 'bg-emerald-950/40 text-emerald-300 border-l-2 border-emerald-500';
              if (isDel) rowBg = 'bg-rose-950/40 text-rose-300 border-l-2 border-rose-500';
              if (isHunk) rowBg = 'bg-indigo-950/30 text-indigo-300 border-l-2 border-indigo-500 font-bold';

              return (
                <div
                  key={idx}
                  className={`flex items-start px-2 py-0.5 rounded-sm text-[11px] leading-relaxed transition-colors ${rowBg}`}
                >
                  <span className="w-8 text-[10px] text-slate-600 select-none shrink-0 text-right pr-2">
                    {idx + 1}
                  </span>
                  <span className="flex-1 whitespace-pre-wrap break-all">{line}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
