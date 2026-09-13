import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { EmptyState, LoadingState } from '../components/ui/states'
import { Upload, CheckCircle, XCircle, FileText } from 'lucide-react'
import { api } from '../lib/api'

interface ImportJob {
  id: string
  file_name: string
  status: string
  records_received: number
  records_valid: number
  records_invalid: number
  created_at: string
}

export function ImportsPage() {
  const [dragActive, setDragActive] = useState(false)
  const queryClient = useQueryClient()

  const { data: imports, isLoading } = useQuery({
    queryKey: ['imports'],
    queryFn: async () => {
      try {
        const res = await api.get<ImportJob[]>('/imports')
        return res.data
      } catch {
        return []
      }
    },
  })

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      await api.post('/imports', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['imports'] })
    },
  })

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    const file = e.dataTransfer.files[0]
    if (file) uploadMutation.mutate(file)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) uploadMutation.mutate(file)
  }

  if (isLoading) return <LoadingState />

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Imports</h1>
          <p className="mt-1 text-sm text-gray-500">
            Bulk CSV ingestion for planning data
          </p>
        </div>
      </div>

      <Card>
        <CardContent className="p-6">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragActive(true) }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${
              dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
            }`}
          >
            <Upload className="h-8 w-8 text-gray-400" />
            <p className="mt-2 text-sm text-gray-600">
              Drag and drop a CSV file here, or
            </p>
            <label className="mt-2 cursor-pointer text-sm font-medium text-blue-600 hover:text-blue-500">
              browse to upload
              <input type="file" className="hidden" accept=".csv" onChange={handleFileSelect} />
            </label>
            {uploadMutation.isPending && (
              <p className="mt-2 text-sm text-gray-500">Uploading...</p>
            )}
          </div>
        </CardContent>
      </Card>

      {!imports?.length ? (
        <EmptyState
          title="No imports yet"
          description="Upload a CSV file to start importing planning data."
        />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Import History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500">
                    <th className="pb-3 font-medium">File</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium text-right">Records</th>
                    <th className="pb-3 font-medium text-right">Valid</th>
                    <th className="pb-3 font-medium text-right">Invalid</th>
                    <th className="pb-3 font-medium">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {imports.map((imp) => (
                    <tr key={imp.id} className="border-b last:border-0">
                      <td className="py-3">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-gray-400" />
                          {imp.file_name}
                        </div>
                      </td>
                      <td className="py-3">
                        <StatusBadge status={imp.status} />
                      </td>
                      <td className="py-3 text-right">{imp.records_received.toLocaleString()}</td>
                      <td className="py-3 text-right text-green-600">{imp.records_valid.toLocaleString()}</td>
                      <td className="py-3 text-right text-red-600">{imp.records_invalid.toLocaleString()}</td>
                      <td className="py-3 text-gray-500">{new Date(imp.created_at).toLocaleDateString()}</td>
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

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    completed: 'bg-green-100 text-green-700',
    processing: 'bg-blue-100 text-blue-700',
    failed: 'bg-red-100 text-red-700',
    queued: 'bg-gray-100 text-gray-700',
  }
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${colors[status] || colors.queued}`}>
      {status === 'completed' && <CheckCircle className="h-3 w-3" />}
      {status === 'failed' && <XCircle className="h-3 w-3" />}
      {status}
    </span>
  )
}
