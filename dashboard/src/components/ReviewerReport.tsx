'use client';

import React from 'react';
import { FileCheck, ShieldAlert, CheckSquare, GitPullRequest, AlertCircle, Sparkles } from 'lucide-react';
import { ReviewerPRReport } from '../types';

interface ReviewerReportProps {
  report: ReviewerPRReport | undefined;
  testPassed: boolean;
}

export const ReviewerReport: React.FC<ReviewerReportProps> = ({ report, testPassed }) => {
  if (!report) {
    return (
      <div className="bg-slate-900/80 backdrop-blur-md rounded-2xl border border-slate-800 p-5 shadow-xl shadow-black/20 flex flex-col items-center justify-center min-h-[220px] text-slate-500 text-center">
        <GitPullRequest className="w-8 h-8 opacity-30 text-purple-400 mb-2" />
        <h3 className="text-sm font-semibold text-slate-400 font-mono">
          Reviewer Pull Request Card Pending
        </h3>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          ReviewerAgent will generate an automated Pull Request description, verification checklist, and risk rating upon successful test completion.
        </p>
      </div>
    );
  }

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case 'LOW':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
            LOW RISK
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-950 text-amber-400 border border-amber-800">
            MEDIUM RISK
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-950 text-rose-400 border border-rose-800">
            HIGH RISK
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900/80 backdrop-blur-md rounded-2xl border border-slate-800 p-5 shadow-xl shadow-black/20">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <GitPullRequest className="w-4 h-4 text-purple-400" />
          <h3 className="text-sm font-semibold text-white tracking-wide uppercase font-mono">
            Automated PR Review & Governance Package
          </h3>
        </div>
        <div className="flex items-center space-x-2">
          {getRiskBadge(report.risk_assessment)}
          <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-indigo-950 text-indigo-300 border border-indigo-800">
            {testPassed ? 'TESTS VERIFIED' : 'TESTS INCOMPLETE'}
          </span>
        </div>
      </div>

      {/* PR Content */}
      <div className="mt-4 space-y-3 font-mono">
        <div>
          <span className="text-[11px] text-slate-500 uppercase tracking-wider">PR Title:</span>
          <p className="text-sm font-semibold text-white mt-0.5">{report.pr_title}</p>
        </div>

        <div>
          <span className="text-[11px] text-slate-500 uppercase tracking-wider">Summary:</span>
          <p className="text-xs text-slate-300 mt-0.5 leading-relaxed bg-slate-950 p-2.5 rounded-lg border border-slate-800/80">
            {report.pr_summary}
          </p>
        </div>

        {/* Verification Checklist */}
        <div>
          <span className="text-[11px] text-slate-500 uppercase tracking-wider">
            Verification & Quality Checklist:
          </span>
          <div className="mt-1 space-y-1.5 bg-slate-950 p-3 rounded-lg border border-slate-800/80">
            {report.checklist && report.checklist.length > 0 ? (
              report.checklist.map((item, idx) => (
                <div key={idx} className="flex items-center space-x-2 text-xs text-slate-300">
                  <CheckSquare className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>{item}</span>
                </div>
              ))
            ) : (
              <div className="text-xs text-slate-500">Checklist criteria satisfied.</div>
            )}
          </div>
        </div>

        {/* Files Modified */}
        {report.files_changed && report.files_changed.length > 0 && (
          <div className="flex items-center space-x-2 text-xs text-slate-400 pt-1">
            <span>Files Modified:</span>
            {report.files_changed.map((file, i) => (
              <span key={i} className="px-2 py-0.5 rounded bg-slate-950 text-cyan-400 border border-slate-800">
                {file}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
