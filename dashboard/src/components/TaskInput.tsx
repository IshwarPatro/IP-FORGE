'use client';

import React, { useState } from 'react';
import { Play, Sparkles, Sliders, FileCode, CheckCircle, RotateCcw } from 'lucide-react';

interface TaskInputProps {
  onLaunchTask: (prompt: string, repoDir: string, targetFile: string, maxRetries: number) => void;
  onReset: () => void;
  isRunning: boolean;
}

const PRESETS = [
  {
    title: 'Fix Discount Bug',
    prompt: 'Fix calculate_discount in app/utils.py so it correctly validates discount percentages between 0 and 100, rounds to 2 decimal places, and prevents ValueError.',
    repoDir: 'tests/dummy_repo',
    file: 'app/utils.py',
    tag: 'Bugfix & Test',
  },
  {
    title: 'Add Pagination to Catalog',
    prompt: 'Implement page and page_size query parameters in app/routes.py to paginate the product catalog response with total page metadata.',
    repoDir: 'tests/dummy_repo',
    file: 'app/routes.py',
    tag: 'Feature',
  },
  {
    title: 'Inventory Bounds Check',
    prompt: 'Enforce strict bounds checking in app/services.py to guarantee stock balance cannot drop below zero during order checkout.',
    repoDir: 'tests/dummy_repo',
    file: 'app/services.py',
    tag: 'Robustness',
  },
];

export const TaskInput: React.FC<TaskInputProps> = ({
  onLaunchTask,
  onReset,
  isRunning,
}) => {
  const [prompt, setPrompt] = useState(PRESETS[0].prompt);
  const [repoDir, setRepoDir] = useState(PRESETS[0].repoDir);
  const [targetFile, setTargetFile] = useState(PRESETS[0].file);
  const [maxRetries, setMaxRetries] = useState(3);

  const handleSelectPreset = (p: typeof PRESETS[0]) => {
    setPrompt(p.prompt);
    setRepoDir(p.repoDir);
    setTargetFile(p.file);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isRunning) return;
    onLaunchTask(prompt, repoDir, targetFile, maxRetries);
  };

  return (
    <div className="bg-slate-900/80 backdrop-blur-md rounded-2xl border border-slate-800 p-5 shadow-xl shadow-black/20">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-white tracking-wide uppercase font-mono">
            Autonomous Task Dispatcher
          </h2>
        </div>

        {/* Preset Pills */}
        <div className="flex items-center space-x-2 overflow-x-auto pb-1 sm:pb-0">
          <span className="text-[11px] text-slate-500 font-mono hidden sm:inline">Presets:</span>
          {PRESETS.map((preset) => (
            <button
              key={preset.title}
              type="button"
              onClick={() => handleSelectPreset(preset)}
              disabled={isRunning}
              className={`text-[11px] font-medium px-2.5 py-1 rounded-md transition-all cursor-pointer border ${
                targetFile === preset.file && prompt === preset.prompt
                  ? 'bg-cyan-950 text-cyan-300 border-cyan-700/80 shadow-sm shadow-cyan-900/50'
                  : 'bg-slate-950 text-slate-400 hover:text-slate-200 border-slate-800 hover:border-slate-700'
              }`}
            >
              {preset.title}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Main Prompt Textarea */}
        <div className="relative">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isRunning}
            id="task-prompt-input"
            rows={3}
            placeholder="Describe the software engineering task, bug to fix, or architectural feature..."
            className="w-full bg-slate-950 rounded-xl border border-slate-800 px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 font-mono transition-colors resize-none"
          />
        </div>

        {/* Controls Row */}
        <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-center">
          {/* Repo Directory (Real Project Path) */}
          <div className="sm:col-span-4 flex items-center space-x-2 bg-slate-950 px-3 py-2 rounded-xl border border-slate-800">
            <span className="text-xs text-slate-500 font-mono shrink-0">Repo:</span>
            <input
              type="text"
              id="repo-dir-input"
              value={repoDir}
              onChange={(e) => setRepoDir(e.target.value)}
              disabled={isRunning}
              placeholder="e.g. tests/dummy_repo or /path/to/project"
              className="w-full bg-transparent text-xs text-slate-200 font-mono focus:outline-none"
              title="Target repository folder to index and execute on (supports real repositories)"
            />
          </div>

          {/* Target File */}
          <div className="sm:col-span-3 flex items-center space-x-2 bg-slate-950 px-3 py-2 rounded-xl border border-slate-800">
            <FileCode className="w-4 h-4 text-slate-400 shrink-0" />
            <span className="text-xs text-slate-500 font-mono shrink-0">File:</span>
            <input
              type="text"
              id="target-file-input"
              value={targetFile}
              onChange={(e) => setTargetFile(e.target.value)}
              disabled={isRunning}
              placeholder="e.g. app/utils.py"
              className="w-full bg-transparent text-xs text-slate-200 font-mono focus:outline-none"
            />
          </div>

          {/* Max Retries Slider */}
          <div className="sm:col-span-2 flex items-center justify-between bg-slate-950 px-3 py-2 rounded-xl border border-slate-800">
            <div className="flex items-center space-x-1 text-xs text-slate-400">
              <Sliders className="w-3.5 h-3.5 text-cyan-400" />
              <span>Cycles:</span>
            </div>
            <div className="flex items-center space-x-1">
              {[1, 2, 3].map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => setMaxRetries(val)}
                  disabled={isRunning}
                  className={`w-5 h-5 rounded text-[11px] font-mono font-semibold transition-colors cursor-pointer ${
                    maxRetries === val
                      ? 'bg-cyan-500 text-slate-950'
                      : 'bg-slate-900 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {val}
                </button>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="sm:col-span-3 flex items-center space-x-2">
            <button
              type="submit"
              disabled={isRunning || !prompt.trim()}
              id="launch-agent-btn"
              className={`w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl font-medium text-xs tracking-wider uppercase transition-all duration-200 cursor-pointer shadow-lg ${
                isRunning
                  ? 'bg-cyan-950 text-cyan-400 border border-cyan-800 cursor-not-allowed'
                  : 'bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white shadow-cyan-500/25 active:scale-95'
              }`}
            >
              <Play className={`w-3.5 h-3.5 ${isRunning ? 'animate-spin' : ''}`} />
              <span>{isRunning ? 'Orchestrating...' : 'Launch Loop'}</span>
            </button>

            <button
              type="button"
              onClick={onReset}
              disabled={isRunning}
              title="Reset task workspace"
              className="p-2.5 rounded-xl border border-slate-800 bg-slate-950 text-slate-400 hover:text-slate-200 hover:border-slate-700 transition-colors cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
