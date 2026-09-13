import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { PageHeader, LoadingState, EmptyState, ErrorState } from '../components/ui/states'
import { useScenarios, usePlans, useCreateScenario, useRunScenario } from '../hooks/useApi'
import { getErrorMessage } from '../lib/api'
import { formatDateTime, getStatusColor } from '../lib/utils'
import { Plus, GitBranch, Play, Search } from 'lucide-react'
import { toast } from 'sonner'

export function ScenariosPage() {
  const [searchParams] = useSearchParams()
  const preselectedPlan = searchParams.get('plan_id')
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(!!preselectedPlan)
  const [name, setName] = useState('')
  const [desc, setDesc] = useState('')
  const [planId, setPlanId] = useState(preselectedPlan || '')
  const [demand, setDemand] = useState('15')
  const [marketing, setMarketing] = useState('10')
  const [capacity, setCapacity] = useState('-5')
  const { data, isLoading, error } = useScenarios(1, 50)
  const { data: plansData } = usePlans(1, 100)
  const createScenario = useCreateScenario()
  const runScenario = useRunScenario()

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={getErrorMessage(error)} />

  const scenarios = data?.items ?? []
  const plans = plansData?.items ?? []
  const filtered = scenarios.filter(s => s.name.toLowerCase().includes(search.toLowerCase()))

  const handleCreate = async () => {
    if (!name.trim() || !planId) return
    try {
      await createScenario.mutateAsync({
        name, base_plan_id: planId, description: desc || undefined,
        changes: {
          demand_growth: parseFloat(demand) / 100,
          marketing_budget_multiplier: 1 + parseFloat(marketing) / 100,
          supplier_capacity_multiplier: 1 + parseFloat(capacity) / 100,
        }
      })
      toast.success('Scenario created')
      setShowCreate(false); setName(''); setDesc('')
    } catch (e) { toast.error(getErrorMessage(e, 'Failed to create scenario')) }
  }

  const handleRun = async (id: string) => {
    try { await runScenario.mutateAsync(id); toast.success('Scenario queued for execution') }
    catch (e) { toast.error(getErrorMessage(e, 'Failed to run scenario')) }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Scenarios" description="What-if analysis and scenario modeling"
        actions={<Button onClick={() => setShowCreate(true)}><Plus className="mr-2 h-4 w-4" /> New Scenario</Button>} />

      {showCreate && (
        <Card>
          <CardHeader><CardTitle className="text-base">Create Scenario</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-1 block">Base Plan</label>
              <select className="w-full border rounded-md px-3 py-2 text-sm bg-background" value={planId} onChange={e => setPlanId(e.target.value)}>
                <option value="">Select a plan...</option>
                {plans.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <Input placeholder="Scenario name" value={name} onChange={e => setName(e.target.value)} />
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium mb-1 block">Demand Growth (%)</label>
                <Input type="number" value={demand} onChange={e => setDemand(e.target.value)} />
              </div>
              <div>
                <label className="text-sm font-medium mb-1 block">Marketing (%)</label>
                <Input type="number" value={marketing} onChange={e => setMarketing(e.target.value)} />
              </div>
              <div>
                <label className="text-sm font-medium mb-1 block">Capacity Change (%)</label>
                <Input type="number" value={capacity} onChange={e => setCapacity(e.target.value)} />
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleCreate} disabled={createScenario.isPending || !name.trim() || !planId}>
                {createScenario.isPending ? 'Creating...' : 'Create Scenario'}
              </Button>
              <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input className="pl-9" placeholder="Search scenarios..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState icon={<GitBranch className="h-12 w-12" />} title="No scenarios found"
          description="Create a scenario to run what-if analysis" />
      ) : (
        <div className="border rounded-lg divide-y">
          {filtered.map(scenario => (
            <div key={scenario.id} className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors">
              <Link to={`/scenarios/${scenario.id}`} className="flex-1">
                <div className="font-medium">{scenario.name}</div>
                <div className="text-sm text-muted-foreground">
                  {scenario.description || 'No description'} &middot; {formatDateTime(scenario.created_at)}
                </div>
              </Link>
              <div className="flex items-center gap-2">
                <Badge variant={getStatusColor(scenario.status)}>{scenario.status}</Badge>
                {(scenario.status === 'draft' || scenario.status === 'completed') && (
                  <Button size="sm" variant="outline" onClick={() => handleRun(scenario.id)} disabled={runScenario.isPending}>
                    <Play className="h-3 w-3 mr-1" /> Run
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

