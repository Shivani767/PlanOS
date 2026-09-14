import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { PageHeader, LoadingState, EmptyState, ErrorState } from '../components/ui/states'
import { useAgentRuns } from '../hooks/useApi'
import type { AgentRun } from '../types'
import { getErrorMessage } from '../lib/api'
import { formatDateTime, getStatusColor } from '../lib/utils'
import { Bot, Search, Clock, Zap } from 'lucide-react'

export function AgentRunsPage() {
  const [search, setSearch] = useState('')
  const { data, isLoading, error } = useAgentRuns(1, 50)

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={getErrorMessage(error)} />

  const runs: AgentRun[] = data?.items ?? []
  const filtered = runs.filter(r =>
    r.status.toLowerCase().includes(search.toLowerCase()) ||
    (r.input_text ?? '').toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <PageHeader title="Agent Runs" description="Monitor and inspect agent executions" />

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input className="pl-9" placeholder="Search runs..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={<Bot className="h-12 w-12" />}
          title="No agent runs found"
          description="Agent executions will appear here"
        />
      ) : (
        <div className="border rounded-lg divide-y">
          {filtered.map((run) => (
            <Link
              key={run.id}
              to={`/agent-runs/${run.id}`}
              className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-4 min-w-0 flex-1">
                <Bot className="h-5 w-5 text-muted-foreground shrink-0" />
                <div className="min-w-0 flex-1">
                  <div className="font-medium truncate">{run.input_text ?? "Run"}</div>
                  <div className="flex items-center gap-3 text-sm text-muted-foreground mt-0.5">
                    <span className="capitalize">
                      {(run.agent_type ?? "agent").replace(/_/g, " ")}
                    </span>
                    <span>&middot;</span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" /> {formatDateTime(run.created_at)}
                    </span>
                    {run.duration_ms != null && (
                      <>
                        <span>&middot;</span>
                        <span className="flex items-center gap-1">
                          <Zap className="h-3 w-3" /> {run.duration_ms}ms
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {run.total_tokens > 0 && (
                  <span className="text-xs text-muted-foreground">{run.total_tokens} tok</span>
                )}
                <Badge variant={getStatusColor(run.status)}>{run.status}</Badge>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
