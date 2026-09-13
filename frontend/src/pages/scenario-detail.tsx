import { useParams, Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { PageHeader, LoadingState, ErrorState } from '../components/ui/states'
import { useScenario, useRunScenario } from '../hooks/useApi'
import { getErrorMessage } from '../lib/api'
import { formatDateTime, formatCurrency, getStatusColor } from '../lib/utils'
import { ArrowLeft, Play, BarChart3 } from 'lucide-react'
import { toast } from 'sonner'

export function ScenarioDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: scenario, isLoading, error } = useScenario(id!)
  const runScenario = useRunScenario()

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={getErrorMessage(error)} />
  if (!scenario) return <ErrorState message="Scenario not found" />

  const handleRun = async () => {
    try { await runScenario.mutateAsync(scenario.id); toast.success('Scenario queued') }
    catch (e) { toast.error(getErrorMessage(e, 'Failed to run scenario')) }
  }

  const changes = scenario.changes || {}
  const results = scenario.results as Record<string, unknown> | null

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link to="/scenarios" className="hover:text-foreground flex items-center gap-1">
          <ArrowLeft className="h-4 w-4" /> Scenarios
        </Link>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{scenario.name}</h1>
          {scenario.description && <p className="text-muted-foreground mt-1">{scenario.description}</p>}
        </div>
        <div className="flex gap-2">
          <Badge variant={getStatusColor(scenario.status)} className="text-sm">{scenario.status}</Badge>
          {(scenario.status === 'draft' || scenario.status === 'completed') && (
            <Button onClick={handleRun} disabled={runScenario.isPending}>
              <Play className="mr-2 h-4 w-4" /> {runScenario.isPending ? 'Queuing...' : 'Run'}
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Created</CardTitle></CardHeader>
          <CardContent><div className="text-sm">{formatDateTime(scenario.created_at)}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Updated</CardTitle></CardHeader>
          <CardContent><div className="text-sm">{formatDateTime(scenario.updated_at)}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Base Plan</CardTitle></CardHeader>
          <CardContent><div className="text-sm font-mono">{scenario.base_plan_id?.slice(0, 8)}...</div></CardContent></Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-base flex items-center gap-2"><BarChart3 className="h-4 w-4" /> Assumptions</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(changes).length === 0 ? (
              <p className="text-sm text-muted-foreground">No assumptions defined</p>
            ) : Object.entries(changes).map(([key, value]) => (
              <div key={key} className="flex justify-between text-sm">
                <span className="text-muted-foreground capitalize">{key.replace(/_/g, ' ')}</span>
                <span className="font-medium">{typeof value === 'number' ? `${(value as number * 100).toFixed(1)}%` : String(value)}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-base">Results</CardTitle></CardHeader>
          <CardContent>
            {results ? (
              <div className="space-y-3">
                {Object.entries(results).slice(0, 6).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="text-muted-foreground capitalize">{key.replace(/_/g, ' ')}</span>
                    <span className="font-medium">{typeof value === 'number' ? formatCurrency(value) : String(value)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Run the scenario to see results</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
