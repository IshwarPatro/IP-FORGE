'use client';

import React from 'react';
import { GitBranch, Clock, Repeat, CheckCircle, AlertTriangle, Cpu, ShieldAlert, Check } from 'lucide-react';
import { ExecutionState } from '../types';

interface MetricsBarProps {
  state: ExecutionState;
}

export const MetricsBar: React.FC<MetricsBarProps> = ({ state }) => {
  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainingSecs = (secs % 60).toFixed(1);
    return `${mins.toString().padStart(2, '0')}:${remainingSecs.padStart(4, '0')}`;
  };

  const getStatusBadge = () => {
    switch (state.status) {
      case 'running':
        return (
          <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-cyan-950/80 text-cyan-400 border border-cyan-700/60 animate-pulse">
            <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
            <span>AUTONOMOUS LOOP ACTIVE</span>
          </span>
        );
      case 'awaiting_governance':
        return (
          <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-400 border border-amber-700/60 animate-bounce">
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>AWAITING GOVERNANCE SIGN-OFF</span>
          </span>
        );
      case 'completed':
        return (
          <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-700/60">
            <Check className="w-3.5 h-3.5" />
            <span>APPROVED & COMMITTED</span>
          </span>
        );
      case 'failed':
        return (
          <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-950/80 text-rose-400 border border-rose-700/60">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>LOOP EXHAUSTED</span>
          </span>
        );
      default:
        return (
          <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-900 text-slate-400 border border-slate-800">
            <span className="w-2 h-2 rounded-full bg-slate-500"></span>
            <span>STANDBY</span>
          </span>
        );
    }
  };

  return (
    <div className="w-full bg-slate-900/60 backdrop-blur border-b border-slate-800/80 px-4 sm:px-6 lg:px-8 py-3">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
        {/* Status Indicator */}
        <div className="flex items-center space-x-3">
          {getStatusBadge()}
          {state.branch_name && (
            <div className="flex items-center space-x-1.5 text-xs font-mono text-slate-300 bg-slate-950 px-2.5 py-1 rounded-md border border-slate-800">
              <GitBranch className="w-3.5 h-3.5 text-indigo-400" />
              <span>{state.branch_name}</span>
            </div>
          )}
        </div>

        {/* Telemetry Stats Pills */}
        <div className="flex items-center space-x-4 sm:space-x-6 text-xs font-medium">
          {/* Active Agent */}
          <div className="flex items-center space-x-2">
            <span className="text-slate-500">Current Agent:</span>
            <span className="font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800/50">
              [{state.current_agent}]
            </span>
          </div>

          {/* Self-Healing Cycle */}
          <div className="flex items-center space-x-2">
            <Repeat className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-slate-500">Self-Healing Cycle:</span>
            <span className="text-white font-mono font-semibold">
              {state.current_cycle} / {state.max_retries}
            </span>
          </div>

          {/* Test Status */}
          <div className="flex items-center space-x-2">
            {state.test_passed ? (
              <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            )}
            <span className="text-slate-500">Tests:</span>
            <span
              className={`font-semibold ${
                state.test_passed ? 'text-emerald-400' : 'text-amber-400'
              }`}
            >
              {state.test_passed ? 'PASSED (100%)' : state.status === 'idle' ? 'Pending' : 'Failing (Auto-Healing)'}
            </span>
          </div>

          {/* Elapsed Timer */}
          <div className="flex items-center space-x-2">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-500">Elapsed:</span>
            <span className="font-mono text-white">
              {formatTime(state.elapsed_seconds)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
