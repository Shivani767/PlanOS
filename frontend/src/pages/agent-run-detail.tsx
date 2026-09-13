import { useParams, Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { PageHeader, LoadingState, ErrorState } from '../components/ui/states'
import { useAgentRun } from '../hooks/useApi'
import { getErrorMessage } from '../lib/api'
import { formatDateTime, formatCurrency, getStatusColor } from '../lib/utils'
import { ArrowLeft, Bot, Clock, Zap, AlertCircle } from 'lucide-react'

export function AgentRunDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: run, isLoading, error } = useAgentRun(id!)

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={getErrorMessage(error)} />
  if (!run) return <ErrorState message="Run not found" />

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link to="/agent-runs" className="hover:text-foreground flex items-center gap-1">
          <ArrowLeft className="h-4 w-4" /> Agent Runs
        </Link>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{run.input}</h1>
          <div className="flex items-center gap-3 mt-1 text-sm text-muted-foreground">
            <span className="capitalize">{run.agent_type.replace(/_/g, ' ')}</span>
            <span>&middot;</span>
            <span>{formatDateTime(run.created_at)}</span>
            <span>&middot;</span>
            <span className="font-mono">{run.id.slice(0, 8)}</span>
          </div>
        </div>
        <Badge variant={getStatusColor(run.status)} className="text-sm">{run.status}</Badge>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2"><Clock className="h-4 w-4" /> Duration</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{run.duration_ms ? `${run.duration_ms}ms` : '-'}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2"><Zap className="h-4 w-4" /> Tokens</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{run.tokens_used ?? '-'}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2"><Bot className="h-4 w-4" /> Agent</CardTitle></CardHeader>
          <CardContent><div className="text-sm font-medium capitalize">{run.agent_type.replace(/_/g, ' ')}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Completed</CardTitle></CardHeader>
          <CardContent><div className="text-sm">{run.completed_at ? formatDateTime(run.completed_at) : '-'}</div></CardContent></Card>
      </div>

      {run.error && (
        <Card className="border-destructive">
          <CardHeader><CardTitle className="text-base text-destructive flex items-center gap-2"><AlertCircle className="h-4 w-4" /> Error</CardTitle></CardHeader>
          <CardContent><p className="text-sm text-destructive">{run.error}</p></CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle className="text-base">Output</CardTitle></CardHeader>
        <CardContent>
          {run.output ? (
            <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto whitespace-pre-wrap">{run.output}</pre>
          ) : (
            <p className="text-sm text-muted-foreground">No output available</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
