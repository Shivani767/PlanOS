import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import { AppLayout } from './components/layout/app-layout'
import { LoginPage } from './pages/login'
import { LoadingState } from './components/ui/states'
import { DashboardPage } from './pages/dashboard'
import { PlansPage } from './pages/plans'
import { PlanDetailPage } from './pages/plan-detail'
import { ScenariosPage } from './pages/scenarios'
import { ScenarioDetailPage } from './pages/scenario-detail'
import { AgentRunsPage } from './pages/agent-runs'
import { AgentRunDetailPage } from './pages/agent-run-detail'
import { ApprovalsPage } from './pages/approvals'
import { EvaluationsPage } from './pages/evaluations'
import { ImportsPage } from './pages/imports'
import { AuditLogsPage } from './pages/audit-logs'
import { SettingsPage } from './pages/settings'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  if (isLoading) return <LoadingState />
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) return <LoadingState />

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={
        <ProtectedRoute>
          <AppLayout>
            <Routes>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/plans" element={<PlansPage />} />
              <Route path="/plans/:id" element={<PlanDetailPage />} />
              <Route path="/scenarios" element={<ScenariosPage />} />
              <Route path="/scenarios/:id" element={<ScenarioDetailPage />} />
              <Route path="/agent-runs" element={<AgentRunsPage />} />
              <Route path="/agent-runs/:id" element={<AgentRunDetailPage />} />
              <Route path="/approvals" element={<ApprovalsPage />} />
              <Route path="/evaluations" element={<EvaluationsPage />} />
              <Route path="/imports" element={<ImportsPage />} />
              <Route path="/audit-logs" element={<AuditLogsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </AppLayout>
        </ProtectedRoute>
      } />
    </Routes>
  )
}
