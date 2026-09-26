'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Filter, ArrowDownCircle, Trash2, Cpu, CheckCircle2, AlertTriangle, Bug } from 'lucide-react';
import { LogMessage, AgentPersona } from '../types';

interface AgentActivityStreamProps {
  logs: LogMessage[];
  isRunning: boolean;
  onClearLogs: () => void;
}

const AGENT_COLORS: Record<AgentPersona, { bg: string; text: string; border: string }> = {
  PLANNER: { bg: 'bg-indigo-950/80', text: 'text-indigo-400', border: 'border-indigo-800/60' },
  ARCHITECT: { bg: 'bg-cyan-950/80', text: 'text-cyan-400', border: 'border-cyan-800/60' },
  CODER: { bg: 'bg-blue-950/80', text: 'text-blue-400', border: 'border-blue-800/60' },
  'TEST AGENT': { bg: 'bg-emerald-950/80', text: 'text-emerald-400', border: 'border-emerald-800/60' },
  DEBUGGER: { bg: 'bg-rose-950/80', text: 'text-rose-400', border: 'border-rose-800/60' },
  REVIEWER: { bg: 'bg-purple-950/80', text: 'text-purple-400', border: 'border-purple-800/60' },
  SYSTEM: { bg: 'bg-slate-900', text: 'text-slate-400', border: 'border-slate-800' },
};

export const AgentActivityStream: React.FC<AgentActivityStreamProps> = ({
  logs,
  isRunning,
  onClearLogs,
}) => {
  const [filter, setFilter] = useState<string>('ALL');
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const filteredLogs = logs.filter((log) => {
    if (filter === 'ALL') return true;
    return log.agent === filter;
  });

  return (
    <div className="bg-slate-900/80 backdrop-blur-md rounded-2xl border border-slate-800 flex flex-col h-[520px] shadow-xl shadow-black/20 overflow-hidden">
      {/* Terminal Title Bar */}
      <div className="bg-slate-950/90 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-mono font-bold tracking-wider text-slate-200 uppercase">
            Agent Reasoning & MCP Tool Execution Telemetry
          </span>
          {isRunning && (
            <span className="flex items-center space-x-1 text-[11px] text-cyan-400 font-mono animate-pulse">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
              <span>STREAMING</span>
            </span>
          )}
        </div>

        {/* Controls */}
        <div className="flex items-center space-x-2">
          {/* Agent Filter Dropdown */}
          <div className="flex items-center space-x-1 bg-slate-900 px-2 py-1 rounded-lg border border-slate-800 text-xs">
            <Filter className="w-3 h-3 text-slate-400" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="bg-transparent text-[11px] text-slate-300 font-mono focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Agents</option>
              <option value="PLANNER">Planner</option>
              <option value="CODER">Coder</option>
              <option value="TEST AGENT">Tester</option>
              <option value="DEBUGGER">Debugger</option>
              <option value="REVIEWER">Reviewer</option>
              <option value="SYSTEM">System</option>
            </select>
          </div>

          {/* Auto Scroll Toggle */}
          <button
            type="button"
            onClick={() => setAutoScroll(!autoScroll)}
            className={`p-1 rounded-md text-xs transition-colors cursor-pointer border ${
              autoScroll
                ? 'bg-cyan-950 text-cyan-400 border-cyan-800'
                : 'bg-slate-900 text-slate-500 border-slate-800'
            }`}
            title={autoScroll ? 'Auto-scroll ON' : 'Auto-scroll OFF'}
          >
            <ArrowDownCircle className="w-3.5 h-3.5" />
          </button>

          {/* Clear Logs */}
          <button
            type="button"
            onClick={onClearLogs}
            className="p-1 rounded-md text-slate-500 hover:text-slate-300 bg-slate-900 hover:bg-slate-800 border border-slate-800 transition-colors cursor-pointer"
            title="Clear Activity Stream"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Terminal Output Area */}
      <div
        ref={scrollRef}
        className="flex-1 p-4 overflow-y-auto space-y-2 font-mono text-xs bg-slate-950/60 select-text"
      >
        {filteredLogs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-2">
            <Cpu className="w-8 h-8 opacity-30 text-cyan-400" />
            <p className="text-xs font-mono">Agent reasoning telemetry idle. Launch a task above.</p>
          </div>
        ) : (
          filteredLogs.map((log) => {
            const agentStyle = AGENT_COLORS[log.agent] || AGENT_COLORS.SYSTEM;
            return (
              <div
                key={log.id}
                className="flex items-start space-x-2.5 p-2 rounded-lg hover:bg-slate-900/50 transition-colors border border-transparent hover:border-slate-800/40"
              >
                <span className="text-[10px] text-slate-500 font-mono shrink-0 select-none pt-0.5">
                  {log.timestamp}
                </span>

                <span
                  className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold shrink-0 border ${agentStyle.bg} ${agentStyle.text} ${agentStyle.border}`}
                >
                  {log.agent}
                </span>

                <div className="flex-1 text-slate-200 leading-relaxed break-words whitespace-pre-wrap">
                  {log.message}
                  {log.details && (
                    <div className="mt-1.5 p-2 rounded bg-slate-950 border border-slate-800/70 text-[11px] text-slate-400">
                      {JSON.stringify(log.details, null, 2)}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}

        {isRunning && (
          <div className="flex items-center space-x-2 text-cyan-400 pt-2 animate-pulse text-[11px]">
            <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
            <span>Agent reasoning and self-healing verification cycle active...</span>
          </div>
        )}
      </div>
    </div>
  );
};
