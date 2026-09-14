import { CheckCircle2, XCircle, Loader2, Circle } from 'lucide-react'
import { Badge } from '../ui/badge'

export type StageStatus = 'done' | 'running' | 'waiting' | 'error'

/** One agent lifecycle stage card in the execution pipeline. */
export function ExecutionCard({
  label,
  description,
  status,
  detail,
}: {
  label: string
  description: string
  status: StageStatus
  detail?: React.ReactNode
}) {
  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-3">
      <div className="flex items-start gap-3">
        <div className="mt-0.5">
          {status === 'done' && <CheckCircle2 className="h-4 w-4 text-emerald-600" aria-label="completed" />}
          {status === 'running' && <Loader2 className="h-4 w-4 animate-spin text-blue-600" aria-label="running" />}
          {status === 'error' && <XCircle className="h-4 w-4 text-red-600" aria-label="failed" />}
          {status === 'waiting' && <Circle className="h-4 w-4 text-neutral-300" aria-label="waiting" />}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-neutral-900">{label}</span>
            {status === 'done' && <Badge variant="success">Done</Badge>}
            {status === 'running' && <Badge variant="info">Running</Badge>}
            {status === 'error' && <Badge variant="destructive">Failed</Badge>}
            {status === 'waiting' && <Badge variant="secondary">Waiting</Badge>}
          </div>
          <p className="mt-0.5 text-xs text-neutral-500">{description}</p>
          {detail && <div className="mt-2">{detail}</div>}
        </div>
      </div>
    </div>
  )
}

/** Compact assumption chips (e.g. demand_growth=+15%). */
export function AssumptionChips({ assumptions }: { assumptions: Record<string, number> }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {Object.entries(assumptions).map(([key, value]) => (
        <span
          key={key}
          className="inline-flex items-center gap-1 rounded bg-neutral-100 px-2 py-0.5 text-xs font-mono text-neutral-700"
        >
          {key}={value > 0 ? `+${(value * 100).toFixed(0)}%` : `${(value * 100).toFixed(0)}%`}
        </span>
      ))}
    </div>
  )
}
