import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { PageHeader, LoadingState, EmptyState, ErrorState } from '../components/ui/states'
import { usePlans, useCreatePlan } from '../hooks/useApi'
import { getErrorMessage } from '../lib/api'
import { formatDateTime, getStatusColor } from '../lib/utils'
import { Plus, FolderKanban, Search, MoreHorizontal } from 'lucide-react'
import { toast } from 'sonner'

export function PlansPage() {
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const { data, isLoading, error } = usePlans(1, 50)
  const createPlan = useCreatePlan()

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={getErrorMessage(error)} />
  const plans = data?.items ?? []
  const filtered = plans.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase())
  )

  const handleCreate = async () => {
    if (!newName.trim()) return
    try {
      await createPlan.mutateAsync({ name: newName, description: newDesc || undefined })
      toast.success('Plan created')
      setShowCreate(false); setNewName(''); setNewDesc('')
    } catch (e) { toast.error(getErrorMessage(e, 'Failed to create plan')) }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Plans" description="Manage your planning models"
        actions={<Button onClick={() => setShowCreate(true)}><Plus className="mr-2 h-4 w-4" /> New Plan</Button>} />

      {showCreate && (
        <Card>
          <CardHeader><CardTitle className="text-base">Create New Plan</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Input placeholder="Plan name" value={newName} onChange={e => setNewName(e.target.value)} />
            <Input placeholder="Description (optional)" value={newDesc} onChange={e => setNewDesc(e.target.value)} />
            <div className="flex gap-2">
              <Button onClick={handleCreate} disabled={createPlan.isPending || !newName.trim()}>
                {createPlan.isPending ? 'Creating...' : 'Create'}
              </Button>
              <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input className="pl-9" placeholder="Search plans..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <div className="text-sm text-muted-foreground">{filtered.length} plans</div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState icon={<FolderKanban className="h-12 w-12" />} title="No plans found"
          description={search ? 'Try adjusting your search' : 'Create your first plan to get started'} />
      ) : (
        <div className="border rounded-lg divide-y">
          {filtered.map(plan => (
            <Link key={plan.id} to={`/plans/${plan.id}`} className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors">
              <div className="flex items-center gap-4">
                <FolderKanban className="h-5 w-5 text-muted-foreground" />
                <div>
                  <div className="font-medium">{plan.name}</div>
                  <div className="text-sm text-muted-foreground">
                    v{plan.current_version} &middot; Updated {formatDateTime(plan.updated_at)}
                  </div>
                </div>
              </div>
              <Badge variant={getStatusColor(plan.status)}>{plan.status}</Badge>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
