import { Card, CardContent } from '../components/ui/card'
import { PageHeader, EmptyState } from '../components/ui/states'
import { CheckCircle2, XCircle, Clock } from 'lucide-react'

export function ApprovalsPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Approvals" description="Review and manage approval requests" />
      <EmptyState icon={<CheckCircle2 className="h-12 w-12" />} title="No pending approvals"
        description="Approval requests will appear here when agents need authorization" />
    </div>
  )
}
