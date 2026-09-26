export type AgentPersona = 'PLANNER' | 'ARCHITECT' | 'CODER' | 'TEST AGENT' | 'DEBUGGER' | 'REVIEWER' | 'SYSTEM';

export type LogLevel = 'info' | 'warn' | 'error' | 'success';

export interface LogMessage {
  id: string;
  timestamp: string;
  agent: AgentPersona;
  message: string;
  level: LogLevel;
  details?: Record<string, any>;
}

export interface HardwareStatus {
  status: string;
  environment: string;
  provider: string;
  rocm_available: boolean;
  rocm_version: string | null;
  device_name: string;
  device_count: number;
  vllm_endpoint: string;
  system_memory: string;
}

export interface ReviewerPRReport {
  pr_title: string;
  pr_summary: string;
  files_changed: string[];
  test_status: string;
  risk_assessment: 'LOW' | 'MEDIUM' | 'HIGH';
  checklist: string[];
}

export interface ExecutionState {
  session_id: string;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'awaiting_governance';
  task_prompt: string;
  target_file: string;
  branch_name: string;
  current_agent: AgentPersona;
  current_cycle: number;
  max_retries: number;
  test_passed: boolean;
  test_output?: string;
  patch_diff: string;
  reviewer_report?: ReviewerPRReport;
  governance_decision?: 'approved' | 'rejected';
  governance_feedback?: string;
  start_time?: number;
  elapsed_seconds: number;
}
