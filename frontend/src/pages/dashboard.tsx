import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { PageHeader, LoadingState, EmptyState } from '../components/ui/states'
import { usePlans, useScenarios, useAgentRuns } from '../hooks/useApi'
import { formatDateTime, getStatusColor } from '../lib/utils'
import { FolderKanban, GitBranch, Bot, Plus, TrendingUp } from 'lucide-react'

export function DashboardPage() {
  const { data: plansData, isLoading: plansLoading } = usePlans(1, 100)
  const { data: scenariosData, isLoading: scenariosLoading } = useScenarios(1, 100)
  const { data: runsData, isLoading: runsLoading } = useAgentRuns(1, 10)
  const isLoading = plansLoading || scenariosLoading || runsLoading
  if (isLoading) return <LoadingState />
  const plans = plansData?.items ?? []
  const scenarios = scenariosData?.items ?? []
  const recentRuns = runsData?.items ?? []
  return (
    <div className="space-y-6">
      <PageHeader title="Dashboard" description="Overview of your planning workspace"
        actions={<Link to="/plans"><Button><Plus className="mr-2 h-4 w-4" /> New Plan</Button></Link>} />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard to="/plans" title="Total Plans" value={plans.length} extra={`${plans.filter(p => p.status === 'active').length} active`} icon={FolderKanban} />
        <StatCard to="/scenarios" title="Scenarios" value={scenarios.length} extra={`${scenarios.filter(s => s.status === 'completed').length} completed`} icon={GitBranch} />
        <StatCard to="/agent-runs" title="Agent Runs" value={runsData?.total ?? 0} extra={`${recentRuns.filter(r => r.status === 'running').length} running`} icon={Bot} />
        <StatCard to="/approvals" title="Pending Approvals" value={0} extra="No action needed" icon={TrendingUp} />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Recent Scenarios</CardTitle></CardHeader>
          <CardContent>
            {scenarios.length === 0 ? <EmptyState title="No scenarios" description="Create your first scenario" /> : (
              <div className="space-y-3">{scenarios.slice(0, 5).map(s => (
                <Link key={s.id} to={`/scenarios/${s.id}`} className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted/50">
                  <div><div className="font-medium text-sm">{s.name}</div><div className="text-xs text-muted-foreground">{formatDateTime(s.created_at)}</div></div>
                  <Badge variant={getStatusColor(s.status)}>{s.status}</Badge>
                </Link>
              ))}</div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Recent Agent Runs</CardTitle></CardHeader>
          <CardContent>
            {recentRuns.length === 0 ? <EmptyState title="No agent runs" description="Runs will appear here" /> : (
              <div className="space-y-3">{recentRuns.map(r => (
                <Link key={r.id} to={`/agent-runs/${r.id}`} className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted/50">
                  <div><div className="font-medium text-sm">{r.input?.substring(0, 50) || 'Run'}...</div><div className="text-xs text-muted-foreground">{formatDateTime(r.created_at)}</div></div>
                  <Badge variant={getStatusColor(r.status)}>{r.status}</Badge>
                </Link>
              ))}</div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function StatCard({ to, title, value, extra, icon: Icon }: { to: string; title: string; value: number; extra: string; icon: React.ElementType }) {
  return (
    <Link to={to}>
      <Card className="transition-shadow hover:shadow-md">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
          <Icon className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{value}</div>
          <p className="text-xs text-muted-foreground">{extra}</p>
        </CardContent>
      </Card>
    </Link>
  )
}
