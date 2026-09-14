import type { TraceEntry } from '../../types'
import type { StageStatus } from './execution-card'

/** Ordered agent lifecycle stages of the flagship workflow. */
export const WORKFLOW_STAGES: { stage: string; label: string; description: string }[] = [
  { stage: 'planner', label: 'Planning Agent', description: 'Parsed goal into structured assumptions' },
  { stage: 'analyst', label: 'Analyst Agent', description: 'Fetched deterministic baseline metrics' },
  { stage: 'executor', label: 'Executor Agent', description: 'Created and ran scenario variants' },
  { stage: 'reviewer', label: 'Reviewer Agent', description: 'Selected best option and proposed approval' },
]

/** Derive a stage's status from the persisted trace (real backend state, not animation). */
export function stageStatus(
  stage: string,
  trace: TraceEntry[],
  isRunning: boolean,
): StageStatus {
  if (trace.some((t) => t.agent === stage)) return 'done'
  const nextIndex = trace.length
  const stageIndex = WORKFLOW_STAGES.findIndex((s) => s.stage === stage)
  if (isRunning && stageIndex === nextIndex) return 'running'
  return 'waiting'
}
