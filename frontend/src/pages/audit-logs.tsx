import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { EmptyState, LoadingState } from '../components/ui/states'
import { Activity } from 'lucide-react'
import { api } from '../lib/api'

interface AuditLogEntry {
  id: string
  user_email: string
  action: string
  resource: string
  resource_id: string
  status: string
  request_id: string
  created_at: string
}

export function AuditLogsPage() {
  const { data: logs, isLoading } = useQuery({
    queryKey: ['audit-logs'],
    queryFn: async () => {
      try {
        const res = await api.get<AuditLogEntry[]>('/audit-logs')
        return res.data
      } catch {
        return []
      }
    },
  })

  if (isLoading) return <LoadingState />

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Audit Logs</h1>
        <p className="mt-1 text-sm text-gray-500">
          Immutable record of all sensitive operations
        </p>
      </div>

      {!logs?.length ? (
        <EmptyState
          title="No audit logs"
          description="Audit events will appear here as actions are performed."
        />
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50 text-left text-gray-500">
                    <th className="px-4 py-3 font-medium">Time</th>
                    <th className="px-4 py-3 font-medium">User</th>
                    <th className="px-4 py-3 font-medium">Action</th>
                    <th className="px-4 py-3 font-medium">Resource</th>
                    <th className="px-4 py-3 font-medium">Request ID</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id} className="border-b last:border-0 hover:bg-gray-50">
                      <td className="px-4 py-3 text-gray-500">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3">{log.user_email}</td>
                      <td className="px-4 py-3">
                        <span className="rounded bg-gray-100 px-2 py-0.5 font-mono text-xs">
                          {log.action}
                        </span>
                      </td>
                      <td className="px-4 py-3">{log.resource}</td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-400">
                        {log.request_id}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
