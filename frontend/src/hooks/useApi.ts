import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, getErrorMessage, type PaginatedResponse } from '../lib/api'
import type {
  Plan,
  Scenario,
  AgentRun,
  AgentToolInfo,
  ApprovalRequest,
  AuditLog,
  ImportJob,
  PlanWorkflowResponse,
} from '../types'

// Plans
export function usePlans(page = 1, size = 20) {
  return useQuery({
    queryKey: ['plans', page, size],
    queryFn: async () => {
      const res = await api.get<PaginatedResponse<Plan>>('/plans', { params: { page, size } })
      return res.data
    },
  })
}

export function usePlan(id: string) {
  return useQuery({
    queryKey: ['plan', id],
    queryFn: async () => {
      const res = await api.get<Plan>(`/plans/${id}`)
      return res.data
    },
    enabled: !!id,
  })
}

export function useCreatePlan() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (data: { name: string; description?: string }) => {
      const res = await api.post<Plan>('/plans', data)
      return res.data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['plans'] }),
  })
}

export function useUpdatePlan() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: { name?: string; description?: string; expected_version: number } }) => {
      const res = await api.patch<Plan>(`/plans/${id}`, data)
      return res.data
    },
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ['plans'] })
      qc.invalidateQueries({ queryKey: ['plan', id] })
    },
  })
}

// Scenarios
export function useScenarios(page = 1, size = 20) {
  return useQuery({
    queryKey: ['scenarios', page, size],
    queryFn: async () => {
      const res = await api.get<PaginatedResponse<Scenario>>('/scenarios', { params: { page, size } })
      return res.data
    },
  })
}

export function useScenario(id: string) {
  return useQuery({
    queryKey: ['scenario', id],
    queryFn: async () => {
      const res = await api.get<Scenario>(`/scenarios/${id}`)
      return res.data
    },
    enabled: !!id,
  })
}

export function useCreateScenario() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (data: { name: string; base_plan_id: string; description?: string; changes: Record<string, number> }) => {
      const res = await api.post<Scenario>('/scenarios', data)
      return res.data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['scenarios'] }),
  })
}

export function useRunScenario() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api.post<{ job_id: string; status: string }>(`/scenarios/${id}/run`)
      return res.data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['scenarios'] }),
  })
}

// Agent Runs
export function useAgentRuns(page = 1, size = 20) {
  const limit = size;
  const offset = (page - 1) * size;
  return useQuery({
    queryKey: ['agent-runs', limit, offset],
    queryFn: async () => {
      const res = await api.get<AgentRun[]>('/agents/runs', { params: { limit, offset } });
      return { items: res.data, total: res.data.length, page, page_size: size };
    },
  })
}

export function useAgentRun(id: string) {
  return useQuery({
    queryKey: ['agent-run', id],
    queryFn: async () => {
      const res = await api.get<AgentRun>(`/agents/runs/${id}`)
      return res.data
    },
    enabled: !!id,
  })
}

export function useAgentTools() {
  return useQuery({
    queryKey: ['agent-tools'],
    queryFn: async () => {
      const res = await api.get<AgentToolInfo[]>('/agents/tools')
      return res.data
    },
  })
}

export function useAgentTrace(runId: string) {
  return useQuery({
    queryKey: ['agent-trace', runId],
    queryFn: async () => {
      const res = await api.get<Record<string, unknown>>(`/agents/runs/${runId}/trace`)
      return res.data
    },
    enabled: !!runId,
  })
}

// Agent workflow (planner → analyst → executor → reviewer)
export function useRunAgentWorkflow() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (data: { plan_id: string; goal: string }) => {
      const res = await api.post<PlanWorkflowResponse>('/agents/plan', data)
      return res.data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['agent-runs'] })
      qc.invalidateQueries({ queryKey: ['scenarios'] })
      qc.invalidateQueries({ queryKey: ['audit-logs'] })
    },
  })
}


// Approvals
export function useApprovals(page = 1, size = 20) {
  return useQuery({
    queryKey: ['approvals', page, size],
    queryFn: async () => {
      const res = await api.get<PaginatedResponse<ApprovalRequest>>('/approvals', { params: { page, size } })
      return res.data
    },
  })
}

export function useAuditLogs(page = 1, size = 50) {
  return useQuery({
    queryKey: ['audit-logs', page, size],
    queryFn: async () => {
      const res = await api.get<PaginatedResponse<AuditLog>>('/audit-logs', { params: { page, size } })
      return res.data
    },
  })
}

export function useImports(page = 1, size = 20) {
  return useQuery({
    queryKey: ['imports', page, size],
    queryFn: async () => {
      const res = await api.get<PaginatedResponse<ImportJob>>('/imports', { params: { page, size } })
      return res.data
    },
  })
}
