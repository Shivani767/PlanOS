import { useParams, Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { PageHeader, LoadingState, ErrorState } from '../components/ui/states'
import { usePlan } from '../hooks/useApi'
import { getErrorMessage } from '../lib/api'
import { formatDateTime, formatCurrency, getStatusColor } from '../lib/utils'
import { ArrowLeft, GitBranch, History } from 'lucide-react'

export function PlanDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: plan, isLoading, error } = usePlan(id!)

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={getErrorMessage(error)} />
  if (!plan) return <ErrorState message="Plan not found" />

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link to="/plans" className="hover:text-foreground flex items-center gap-1">
          <ArrowLeft className="h-4 w-4" /> Plans
        </Link>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{plan.name}</h1>
          {plan.description && <p className="text-muted-foreground mt-1">{plan.description}</p>}
        </div>
        <div className="flex gap-2">
          <Link to={`/scenarios?plan_id=${plan.id}`}>
            <Button><GitBranch className="mr-2 h-4 w-4" /> New Scenario</Button>
          </Link>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Version</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{plan.current_version}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Status</CardTitle></CardHeader>
          <CardContent><Badge variant={getStatusColor(plan.status)}>{plan.status}</Badge></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Created</CardTitle></CardHeader>
          <CardContent><div className="text-sm">{formatDateTime(plan.created_at)}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Updated</CardTitle></CardHeader>
          <CardContent><div className="text-sm">{formatDateTime(plan.updated_at)}</div></CardContent></Card>
      </div>
    </div>
  )
}
