'use client';

import React, { useState } from 'react';
import { ShieldCheck, Check, X, MessageSquare, AlertTriangle, ArrowRight, CornerDownRight } from 'lucide-react';
import { ExecutionState } from '../types';

interface GovernanceControlsProps {
  state: ExecutionState;
  onDecision: (decision: 'approve' | 'reject', feedback: string) => void;
  isSubmitting: boolean;
}

export const GovernanceControls: React.FC<GovernanceControlsProps> = ({
  state,
  onDecision,
  isSubmitting,
}) => {
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');

  const isAwaiting = state.status === 'awaiting_governance';
  const isApproved = state.governance_decision === 'approved';
  const isRejected = state.governance_decision === 'rejected';

  const handleApprove = () => {
    onDecision('approve', '');
  };

  const handleRejectSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onDecision('reject', feedbackText);
    setShowFeedbackModal(false);
  };

  return (
    <div className="bg-slate-900/80 backdrop-blur-md rounded-2xl border border-slate-800 p-5 shadow-xl shadow-black/20">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-5 h-5 text-indigo-400" />
          <div>
            <h3 className="text-sm font-semibold text-white tracking-wide uppercase font-mono">
              Human-in-the-Loop (HitL) Governance Gate
            </h3>
            <p className="text-xs text-slate-400">
              Zero unauthorized code lands in production without explicit engineer sign-off.
            </p>
          </div>
        </div>

        {/* Gate Status Pill */}
        <div>
          {isApproved && (
            <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
              <Check className="w-3.5 h-3.5" />
              <span>APPROVED BY OPERATOR</span>
            </span>
          )}
          {isRejected && (
            <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-950 text-rose-400 border border-rose-800">
              <X className="w-3.5 h-3.5" />
              <span>REJECTED WITH FEEDBACK</span>
            </span>
          )}
          {isAwaiting && (
            <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-950 text-amber-400 border border-amber-800 animate-pulse">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>ACTION REQUIRED: SIGN-OFF</span>
            </span>
          )}
        </div>
      </div>

      {/* Decision Buttons */}
      <div className="mt-4">
        {isAwaiting ? (
          <div className="space-y-4">
            <div className="p-3 bg-amber-950/40 border border-amber-800/60 rounded-xl text-xs text-amber-200 leading-relaxed font-mono flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <strong>Autonomous Engineering Loop Paused for Approval:</strong> All automated tests passed. Please review the patch diff and PR summary above before committing changes to Git.
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {/* Approve & Merge Button */}
              <button
                type="button"
                onClick={handleApprove}
                disabled={isSubmitting}
                id="approve-merge-btn"
                className="flex-1 flex items-center justify-center space-x-2 py-3 px-5 rounded-xl font-semibold text-xs tracking-wider uppercase bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/20 active:scale-95 transition-all cursor-pointer disabled:opacity-50"
              >
                <Check className="w-4 h-4" />
                <span>{isSubmitting ? 'Committing...' : '✓ Approve & Commit to Branch'}</span>
              </button>

              {/* Reject Button */}
              <button
                type="button"
                onClick={() => setShowFeedbackModal(true)}
                disabled={isSubmitting}
                id="reject-feedback-btn"
                className="flex-1 flex items-center justify-center space-x-2 py-3 px-5 rounded-xl font-semibold text-xs tracking-wider uppercase bg-slate-900 hover:bg-rose-950/60 text-rose-300 border border-rose-800/80 active:scale-95 transition-all cursor-pointer disabled:opacity-50"
              >
                <X className="w-4 h-4 text-rose-400" />
                <span>✗ Reject & Request Revisions</span>
              </button>
            </div>
          </div>
        ) : isApproved ? (
          <div className="p-4 bg-emerald-950/30 border border-emerald-800/60 rounded-xl text-xs text-emerald-300 font-mono flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Check className="w-4 h-4 text-emerald-400" />
              <span>Engineering patch accepted and committed to branch: <strong>{state.branch_name}</strong></span>
            </div>
          </div>
        ) : isRejected ? (
          <div className="p-4 bg-rose-950/30 border border-rose-800/60 rounded-xl text-xs text-rose-300 font-mono space-y-1">
            <div className="flex items-center space-x-2">
              <X className="w-4 h-4 text-rose-400" />
              <span>Patch rejected by human operator. Corrective feedback:</span>
            </div>
            <p className="text-slate-300 pl-6 italic">"{state.governance_feedback || 'Revision requested.'}"</p>
          </div>
        ) : (
          <div className="p-3 bg-slate-950 border border-slate-800/80 rounded-xl text-xs text-slate-500 font-mono text-center">
            Governance decision controls activate once the autonomous loop completes code generation and unit testing.
          </div>
        )}
      </div>

      {/* Reject Modal / Slide-down */}
      {showFeedbackModal && (
        <div className="mt-4 p-4 bg-slate-950 rounded-xl border border-rose-800/80 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-rose-300 font-mono flex items-center space-x-1.5">
              <MessageSquare className="w-3.5 h-3.5 text-rose-400" />
              <span>Provide Corrective Operator Guidance</span>
            </span>
            <button
              type="button"
              onClick={() => setShowFeedbackModal(false)}
              className="text-slate-500 hover:text-slate-300 text-xs"
            >
              ✕
            </button>
          </div>

          <form onSubmit={handleRejectSubmit} className="space-y-3">
            <textarea
              value={feedbackText}
              onChange={(e) => setFeedbackText(e.target.value)}
              placeholder="e.g. Please ensure you also handle negative discount percentages by raising ValueError with an explicit error code..."
              rows={2}
              className="w-full bg-slate-900 rounded-lg border border-slate-800 px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-rose-500 font-mono"
            />
            <div className="flex justify-end space-x-2">
              <button
                type="button"
                onClick={() => setShowFeedbackModal(false)}
                className="px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white shadow-md shadow-rose-600/30"
              >
                Submit Feedback & Reject
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
