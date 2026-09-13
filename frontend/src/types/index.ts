export interface User {
  id: string
  email: string
  full_name: string
  role: 'ADMIN' | 'PLANNER' | 'ANALYST' | 'VIEWER'
  organization_id: string
  organization_name?: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
  organization_slug: string
}

export interface Organization {
  id: string
  name: string
  slug: string
  created_at: string
}

export interface Plan {
  id: string
  organization_id: string
  name: string
  description: string | null
  status: string
  current_version: number
  created_by: string | null
  created_at: string
  updated_at: string
}

export interface PlanVersion {
  id: string
  plan_id: string
  version: number
  data: Record<string, unknown>
  created_by: string | null
  created_at: string
}

export interface CreatePlanRequest {
  name: string
  description?: string
}

export interface UpdatePlanRequest {
  name?: string
  description?: string
  expected_version: number
}

export interface ScenarioChanges {
  demand_growth?: number
  marketing_budget_multiplier?: number
  supplier_capacity_multiplier?: number
  cost_change?: number
  headcount_change?: number
}

export interface Scenario {
  id: string
  organization_id: string
  base_plan_id: string
  name: string
  description: string | null
  changes: ScenarioChanges
  status: string
  results: Record<string, unknown> | null
  created_by: string | null
  created_at: string
  updated_at: string
}

export interface CreateScenarioRequest {
  name: string
  base_plan_id: string
  description?: string
  changes: ScenarioChanges
}

export interface AgentRun {
  id: string
  organization_id: string
  agent_type: string
  status: string
  input: string
  output: string | null
  duration_ms: number | null
  tokens_used: number | null
  error: string | null
  created_at: string
  completed_at: string | null
}

export interface AgentStep {
  id: string
  run_id: string
  step_number: number
  agent_type: string
  action: string
  input: Record<string, unknown>
  output: Record<string, unknown>
  duration_ms: number
  created_at: string
}

export interface ApprovalRequest {
  id: string
  organization_id: string
  title: string
  description: string | null
  requested_by: string
  requested_action: string
  resource_type: string
  resource_id: string
  status: string
  changes: Record<string, unknown>
  policy_reason: string | null
  reviewed_by: string | null
  created_at: string
  reviewed_at: string | null
}

export interface AuditLog {
  id: string
  organization_id: string
  user_id: string | null
  action: string
  resource_type: string
  resource_id: string | null
  old_value: Record<string, unknown> | null
  new_value: Record<string, unknown> | null
  request_id: string | null
  trace_id: string | null
  created_at: string
}

export interface ImportJob {
  id: string
  organization_id: string
  filename: string
  status: string
  records_received: number
  records_valid: number
  records_invalid: number
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export interface EvaluationRun {
  id: string
  agent_type: string
  status: string
  total_cases: number
  passed: number
  failed: number
  avg_latency_ms: number
  created_at: string
}

export interface DashboardMetrics {
  total_plans: number
  active_scenarios: number
  agent_runs: number
  pending_approvals: number
}
