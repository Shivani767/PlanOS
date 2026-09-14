import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import type {
  AgentRun,
  AgentToolInfo,
  PlanWorkflowRequest,
  PlanWorkflowResponse,
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export interface ApiError {
  code: string
  message: string
  request_id?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail: ApiError }>) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export function getErrorMessage(error: unknown, fallback = 'An error occurred'): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (detail?.message) return detail.message
    if (typeof detail === 'string') return detail
    if (error.response?.status === 409) return 'Conflict: Resource was modified by another user.'
    if (error.response?.status === 403) return 'You do not have permission to perform this action.'
    if (error.response?.status === 404) return 'Resource not found.'
    if (error.response?.status === 422) return 'Validation error. Please check your input.'
    if (error.response?.status === 429) return 'Too many requests. Please try again later.'
    if (error.response?.status === 500) return 'Server error. Please try again later.'
    if (error.code === 'ERR_NETWORK') return 'Network error. Please check your connection.'
  }
  return fallback
}


export const agentsApi = {
  /** List agent runs (newest first). */
  listRuns: async (limit = 20, offset = 0): Promise<AgentRun[]> => {
    const { data } = await api.get<AgentRun[]>('/agents/runs', { params: { limit, offset } })
    return data
  },

  /** Get a single agent run (includes persisted steps). */
  getRun: async (runId: string): Promise<AgentRun> => {
    const { data } = await api.get<AgentRun>(`/agents/runs/${runId}`)
    return data
  },

  /** Get full execution trace for a run. */
  getTrace: async (runId: string): Promise<Record<string, unknown>> => {
    const { data } = await api.get(`/agents/runs/${runId}/trace`)
    return data
  },

  /** Run the flagship planning workflow (planner → analyst → executor → reviewer). */
  runWorkflow: async (request: PlanWorkflowRequest): Promise<PlanWorkflowResponse> => {
    const { data } = await api.post<PlanWorkflowResponse>('/agents/plan', request)
    return data
  },

  /** List tools visible to the caller's role. */
  listTools: async (): Promise<AgentToolInfo[]> => {
    const { data } = await api.get<AgentToolInfo[]>('/agents/tools')
    return data
  },
}
