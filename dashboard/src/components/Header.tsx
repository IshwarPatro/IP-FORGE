'use client';

import React from 'react';
import { Cpu, Server, ShieldCheck, Zap, RefreshCw, Terminal, CheckCircle2 } from 'lucide-react';
import { HardwareStatus } from '../types';

interface HeaderProps {
  hardware: HardwareStatus | null;
  onToggleProvider: (provider: 'amd_cloud' | 'local_m4') => void;
  isBackendConnected: boolean;
  isToggling: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  hardware,
  onToggleProvider,
  isBackendConnected,
  isToggling,
}) => {
  const isAmd = hardware?.provider === 'amd_cloud';

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Left: Branding & Tagline */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-indigo-500 to-rose-500 p-[1.5px] shadow-lg shadow-cyan-500/20">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <Zap className="w-5 h-5 text-cyan-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg tracking-wider bg-gradient-to-r from-white via-slate-200 to-cyan-400 bg-clip-text text-transparent font-mono">
                IP FORGE
              </span>
              <span className="text-[10px] uppercase font-semibold tracking-widest px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
                v1.0.0-ROCm
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Federated Orchestrator for Reliable Generation & Engineering
            </p>
          </div>
        </div>

        {/* Middle: Lead Architect & Live Status */}
        <div className="hidden md:flex items-center space-x-4">
          <div className="flex items-center space-x-2 px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Lead Architect:</span>
            <strong className="text-white font-medium">Ishwar Patro</strong>
          </div>

          <div className="flex items-center space-x-2 px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs">
            <span
              className={`w-2 h-2 rounded-full ${
                isBackendConnected
                  ? 'bg-emerald-400 shadow-sm shadow-emerald-400 animate-pulse'
                  : 'bg-amber-400 shadow-sm shadow-amber-400'
              }`}
            />
            <span className="text-slate-300 font-mono text-[11px]">
              {isBackendConnected ? 'API: localhost:8000 (LIVE)' : 'API: Simulated Mode'}
            </span>
          </div>
        </div>

        {/* Right: Hardware Telemetry & Provider Toggle */}
        <div className="flex items-center space-x-3">
          <div className="hidden lg:flex flex-col text-right">
            <div className="flex items-center justify-end space-x-1 text-xs font-medium text-slate-200">
              {isAmd ? (
                <>
                  <Server className="w-3.5 h-3.5 text-rose-400 mr-1" />
                  <span className="text-rose-300">AMD Instinct MI300X</span>
                </>
              ) : (
                <>
                  <Cpu className="w-3.5 h-3.5 text-cyan-400 mr-1" />
                  <span className="text-cyan-300">Apple Silicon M4</span>
                </>
              )}
            </div>
            <span className="text-[10px] text-slate-500 font-mono">
              {isAmd ? 'ROCm 6.2 · 8x MI300X (192GB)' : '10-Core CPU · Neural Engine'}
            </span>
          </div>

          {/* Toggle Button */}
          <button
            onClick={() => onToggleProvider(isAmd ? 'local_m4' : 'amd_cloud')}
            disabled={isToggling}
            id="provider-toggle-btn"
            className="flex items-center space-x-2 px-3.5 py-1.5 rounded-lg border text-xs font-semibold transition-all duration-200 cursor-pointer shadow-sm hover:shadow-cyan-500/10 active:scale-95 bg-slate-900 hover:bg-slate-800 border-slate-700 text-slate-200"
            title="Toggle between AMD ROCm Cloud & Local M4 Orchestration"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${isToggling ? 'animate-spin' : ''}`} />
            <span>Switch to {isAmd ? 'Apple M4' : 'AMD Cloud'}</span>
          </button>
        </div>
      </div>
    </header>
  );
};
