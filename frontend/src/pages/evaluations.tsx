import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { EmptyState, LoadingState } from '../components/ui/states'
import { TrendingUp, CheckCircle, Shield, Clock } from 'lucide-react'

interface EvalMetric {
  agent: string
  success_rate: number
  tool_accuracy: number
  policy_violations: number
  p95_latency: number
  total_runs: number
}

const demoMetrics: EvalMetric[] = [
  { agent: 'Planner Agent', success_rate: 94.8, tool_accuracy: 96.2, policy_violations: 0, p95_latency: 2.4, total_runs: 156 },
  { agent: 'Finance Agent', success_rate: 92.1, tool_accuracy: 94.5, policy_violations: 0.3, p95_latency: 3.1, total_runs: 98 },
  { agent: 'Workforce Agent', success_rate: 89.5, tool_accuracy: 91.8, policy_violations: 0.1, p95_latency: 2.8, total_runs: 72 },
  { agent: 'Analyst Agent', success_rate: 96.2, tool_accuracy: 97.1, policy_violations: 0, p95_latency: 1.9, total_runs: 134 },
]

export function EvaluationsPage() {
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['evaluations'],
    queryFn: async () => demoMetrics,
  })

  if (isLoading) return <LoadingState />

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Evaluations</h1>
        <p className="mt-1 text-sm text-gray-500">
          Agent performance metrics from evaluation framework experiments
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard title="Avg Success Rate" value="93.2%" icon={TrendingUp} color="text-green-600" />
        <MetricCard title="Avg Tool Accuracy" value="94.9%" icon={CheckCircle} color="text-blue-600" />
        <MetricCard title="Policy Violations" value="0.1%" icon={Shield} color="text-yellow-600" />
        <MetricCard title="P95 Latency" value="2.5s" icon={Clock} color="text-purple-600" />
      </div>

      {!metrics?.length ? (
        <EmptyState
          title="No evaluation data"
          description="Evaluation metrics will appear here after running the evaluation framework."
        />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Agent Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500">
                    <th className="pb-3 font-medium">Agent</th>
                    <th className="pb-3 font-medium text-right">Success Rate</th>
                    <th className="pb-3 font-medium text-right">Tool Accuracy</th>
                    <th className="pb-3 font-medium text-right">Violations</th>
                    <th className="pb-3 font-medium text-right">P95 Latency</th>
                    <th className="pb-3 font-medium text-right">Total Runs</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.map((m) => (
                    <tr key={m.agent} className="border-b last:border-0">
                      <td className="py-3 font-medium">{m.agent}</td>
                      <td className="py-3 text-right">{m.success_rate}%</td>
                      <td className="py-3 text-right">{m.tool_accuracy}%</td>
                      <td className="py-3 text-right">{m.policy_violations}%</td>
                      <td className="py-3 text-right">{m.p95_latency}s</td>
                      <td className="py-3 text-right">{m.total_runs}</td>
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

function MetricCard({ title, value, icon: Icon, color }: { title: string; value: string; icon: React.ElementType; color: string }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-4">
        <div className={`rounded-lg bg-gray-50 p-2 ${color}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-xl font-semibold">{value}</p>
        </div>
      </CardContent>
    </Card>
  )
}
