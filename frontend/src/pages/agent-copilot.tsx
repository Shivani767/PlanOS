import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Bot, User, Send, Loader2, Sparkles, AlertTriangle, ShieldCheck, Wrench } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { usePlans, useRunAgentWorkflow } from '../hooks/useApi'
import { ExecutionCard, AssumptionChips } from '../components/agents/execution-card'
import { WORKFLOW_STAGES, stageStatus } from '../components/agents/workflow-stages'
import type { PlanWorkflowResponse, TraceEntry } from '../types'

interface ChatMessage {
  role: 'user' | 'agent'
  text: string
  runId?: string
  workflow?: PlanWorkflowResponse
  error?: string
}

const EXAMPLE_GOALS = [
  'Create a Q4 scenario where demand increases 15%, marketing increases 10%, and supplier capacity decreases 5%. Run it and tell me the margin impact.',
  'What happens to profit if demand drops 8% and we cut marketing by 12%?',
  'Test aggressive demand growth against the baseline and recommend the best option.',
]

function stageDetail(entry: TraceEntry | undefined): React.ReactNode {
  if (!entry) return undefined
  if (entry.assumptions) return <AssumptionChips assumptions={entry.assumptions} />
  if (entry.scenarios) return <p className="text-xs text-neutral-600">Variants: {entry.scenarios.join(', ')}</p>
  if (entry.recommendation !== undefined) {
    return (
      <p className="text-xs font-medium text-emerald-700">
        {entry.recommendation
          ? `Recommendation: ${entry.recommendation} (+${entry.margin_gain_pts ?? 0}pts margin)`
          : 'No option met the 2% margin bar'}
      </p>
    )
  }
  return undefined
}

function MessageList({
  messages,
  isPending,
  onPickExample,
}: {
  messages: ChatMessage[]
  isPending: boolean
  onPickExample: (goal: string) => void
}) {
  if (messages.length === 0 && !isPending) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
        <div className="rounded-full bg-violet-50 p-4">
          <Bot className="h-8 w-8 text-violet-600" aria-hidden />
        </div>
        <div>
          <p className="font-medium text-neutral-900">What would you like to plan?</p>
          <p className="mt-1 max-w-md text-sm text-neutral-500">
            Describe a goal in natural language. The agent workflow parses your request, checks
            permissions, runs deterministic calculations, and recommends the best scenario.
          </p>
        </div>
        <div className="grid w-full max-w-lg gap-2">
          {EXAMPLE_GOALS.map((goal) => (
            <button
              key={goal}
              type="button"
              onClick={() => onPickExample(goal)}
              className="rounded-lg border border-neutral-200 bg-neutral-50 p-3 text-left text-sm text-neutral-700 transition hover:border-violet-300 hover:bg-violet-50"
            >
              {goal}
            </button>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {messages.map((msg, i) => (
        <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
          {msg.role === 'agent' && (
            <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-violet-100">
              <Bot className="h-4 w-4 text-violet-700" aria-hidden />
            </div>
          )}
          <div
            className={`max-w-[80%] rounded-lg px-4 py-3 text-sm ${
              msg.role === 'user'
                ? 'bg-violet-600 text-white'
                : msg.error
                  ? 'border border-red-200 bg-red-50 text-red-800'
                  : 'border border-neutral-200 bg-white text-neutral-800'
            }`}
          >
            {msg.error ? (
              <div className="flex items-start gap-2">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
                <div>
                  <p className="font-medium">{msg.text}</p>
                  <p className="mt-1 text-xs">{msg.error}</p>
                </div>
              </div>
            ) : (
              <p className="whitespace-pre-wrap">{msg.text}</p>
            )}
            {msg.runId && (
              <Link
                to={`/agent-runs/${msg.runId}`}
                className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-violet-700 hover:underline"
              >
                View execution trace →
              </Link>
            )}
          </div>
          {msg.role === 'user' && (
            <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-neutral-200">
              <User className="h-4 w-4 text-neutral-600" aria-hidden />
            </div>
          )}
        </div>
      ))}

      {isPending && (
        <div className="flex gap-3">
          <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-violet-100">
            <Bot className="h-4 w-4 animate-pulse text-violet-700" aria-hidden />
          </div>
          <div className="rounded-lg border border-neutral-200 bg-white px-4 py-3">
            <div className="flex items-center gap-2 text-sm text-neutral-500">
              <Loader2 className="h-4 w-4 animate-spin text-violet-600" aria-hidden />
              Agent workflow executing…
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function PipelinePanel({
  latestWorkflow,
  isPending,
}: {
  latestWorkflow?: PlanWorkflowResponse
  isPending: boolean
}) {
  return (
    <Card className="lg:col-span-2">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <ShieldCheck className="h-4 w-4 text-neutral-500" aria-hidden />
          Execution Pipeline
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {latestWorkflow
          ? WORKFLOW_STAGES.map(({ stage, label, description }) => {
              const entry = latestWorkflow.trace.find((t) => t.agent === stage)
              return (
                <ExecutionCard
                  key={stage}
                  label={label}
                  description={description}
                  status={stageStatus(stage, latestWorkflow.trace, isPending)}
                  detail={stageDetail(entry)}
                />
              )
            })
          : WORKFLOW_STAGES.map(({ stage, label, description }) => (
              <ExecutionCard
                key={stage}
                label={label}
                description={description}
                status={isPending && stage === 'planner' ? 'running' : 'waiting'}
              />
            ))}
        <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3">
          <p className="flex items-start gap-2 text-xs text-neutral-500">
            <Wrench className="mt-0.5 h-3 w-3 shrink-0" aria-hidden />
            Every agent action passes through the tool registry and policy engine before execution.
            Calculations are deterministic — the agent never computes numbers itself.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

export default function AgentCopilot() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [activeRunId, setActiveRunId] = useState<string | undefined>()
  const { data: plans, isLoading: plansLoading } = usePlans(1, 50)
  const workflowMutation = useRunAgentWorkflow()

  const selectedPlanId =
    plans && plans.items.length > 0
      ? (plans.items.find((p) => p.status === 'active') ?? plans.items[0]).id
      : ''
  const canSubmit = input.trim().length > 0 && !!selectedPlanId && !workflowMutation.isPending
  const latestWorkflow = [...messages].reverse().find((m) => m.workflow)?.workflow

  function handleSend(text?: string) {
    const goal = (text ?? input).trim()
    if (!goal || !selectedPlanId || workflowMutation.isPending) return
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', text: goal }])
    workflowMutation.mutate(
      { plan_id: selectedPlanId, goal },
      {
        onSuccess: (workflow) => {
          setActiveRunId(workflow.run_id)
          setMessages((prev) => [
            ...prev,
            {
              role: 'agent',
              text: workflow.output ?? 'Workflow completed.',
              runId: workflow.run_id,
              workflow,
            },
          ])
        },
        onError: (err) => {
          setMessages((prev) => [
            ...prev,
            {
              role: 'agent',
              text: 'The agent run failed.',
              error: err instanceof Error ? err.message : 'Unknown error',
            },
          ])
        },
      },
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold text-neutral-900">
            <Sparkles className="h-6 w-6 text-violet-600" aria-hidden />
            Planning Copilot
          </h1>
          <p className="mt-1 text-sm text-neutral-500">
            Agents propose, the policy engine decides, the deterministic engine calculates.
          </p>
        </div>
        {plans && plans.items.length > 0 && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-neutral-500">Target plan:</span>
            <span className="rounded-md border border-neutral-200 bg-neutral-50 px-2 py-1 font-medium text-neutral-800">
              {plans.items.find((p) => p.id === selectedPlanId)?.name}
            </span>
          </div>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardContent className="flex h-[600px] flex-col p-0">
            <div className="flex-1 overflow-y-auto p-4">
              <MessageList
                messages={messages}
                isPending={workflowMutation.isPending}
                onPickExample={handleSend}
              />
            </div>
            <div className="border-t border-neutral-200 p-3">
              <form
                className="flex gap-2"
                onSubmit={(e) => {
                  e.preventDefault()
                  handleSend()
                }}
              >
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Describe a planning goal…"
                  aria-label="Planning goal"
                  disabled={workflowMutation.isPending || !selectedPlanId}
                />
                <Button type="submit" disabled={!canSubmit} aria-label="Send message">
                  {workflowMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                  ) : (
                    <Send className="h-4 w-4" aria-hidden />
                  )}
                </Button>
              </form>
              {!selectedPlanId && !plansLoading && (
                <p className="mt-2 text-xs text-amber-600">
                  Create a plan first — the agent needs a plan to operate on.
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        <PipelinePanel latestWorkflow={latestWorkflow} isPending={workflowMutation.isPending} />
      </div>

      {activeRunId && (
        <Link
          to={`/agent-runs/${activeRunId}`}
          className="block rounded-lg border border-violet-200 bg-violet-50 p-3 text-center text-sm font-medium text-violet-700 transition hover:bg-violet-100"
        >
          Open full execution trace for the latest run →
        </Link>
      )}
    </div>
  )
}



