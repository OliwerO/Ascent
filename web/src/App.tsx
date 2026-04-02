import { useState, lazy, Suspense, useCallback, Component } from 'react'
import type { ReactNode, ErrorInfo } from 'react'
import { Mountain, Calendar, Dumbbell, Heart, TrendingUp, Target, RefreshCw, Watch } from 'lucide-react'
import { LoadingState } from './components/LoadingState'

class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null }
  static getDerivedStateFromError(error: Error) { return { error } }
  componentDidCatch(error: Error, info: ErrorInfo) { console.error('App crash:', error, info) }
  render() {
    if (this.state.error) {
      return (
        <div className="p-6 text-center">
          <div className="text-accent-red text-lg font-semibold mb-2">Something went wrong</div>
          <div className="text-text-muted text-sm mb-4 font-mono bg-bg-card rounded-2xl p-3 text-left overflow-auto max-h-40">
            {this.state.error.message}
          </div>
          <button onClick={() => { this.setState({ error: null }); window.location.reload() }}
            className="text-accent-green text-sm underline">Reload</button>
        </div>
      )
    }
    return this.props.children
  }
}

const TodayView = lazy(() => import('./views/TodayView'))
const WeekView = lazy(() => import('./views/WeekView'))
const TrainingPlanView = lazy(() => import('./views/TrainingPlanView'))
const RecoveryView = lazy(() => import('./views/RecoveryView'))
const TrendsView = lazy(() => import('./views/TrendsView'))
const GoalsView = lazy(() => import('./views/GoalsView'))

const tabs = [
  { id: 'today', label: 'Today', icon: Mountain },
  { id: 'week', label: 'Week', icon: Calendar },
  { id: 'plan', label: 'Plan', icon: Dumbbell },
  { id: 'recovery', label: 'Recovery', icon: Heart },
  { id: 'trends', label: 'Trends', icon: TrendingUp },
  { id: 'goals', label: 'Goals', icon: Target },
] as const

type TabId = (typeof tabs)[number]['id']

function App() {
  const [activeTab, setActiveTab] = useState<TabId>('today')
  const [refreshKey, setRefreshKey] = useState(0)
  const [syncing, setSyncing] = useState(false)
  const [syncMsg, setSyncMsg] = useState<string | null>(null)
  const handleRefresh = useCallback(() => {
    setRefreshKey((k) => k + 1)
  }, [])
  const handleSync = useCallback(async () => {
    setSyncing(true)
    setSyncMsg(null)
    try {
      const resp = await fetch('/api/garmin-sync-trigger', { method: 'POST' })
      const data = await resp.json()
      setSyncMsg(data.ok ? 'Sync queued — data arrives in ~5 min' : (data.error || 'Failed'))
      setTimeout(() => setSyncMsg(null), 5000)
    } catch {
      setSyncMsg('Sync request failed')
      setTimeout(() => setSyncMsg(null), 5000)
    } finally {
      setSyncing(false)
    }
  }, [])

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-bg-primary/90 backdrop-blur-xl border-b border-border-subtle pt-[env(safe-area-inset-top)]">
        <div className="max-w-2xl mx-auto px-5 py-3 flex items-center justify-between">
          <h1 className="text-[15px] font-semibold tracking-tight flex items-center gap-2">
            <span className="text-accent-green text-lg">&#9650;</span>
            <span className="text-text-primary">Ascent</span>
          </h1>
          <div className="flex items-center gap-4">
            <span className="text-[12px] text-text-muted font-medium">
              {new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
            </span>
            <button
              onClick={handleSync}
              disabled={syncing}
              className="text-text-muted hover:text-accent-green disabled:opacity-50 transition-all p-1"
              title="Sync Garmin data now"
            >
              <Watch size={15} className={syncing ? 'animate-pulse' : ''} />
            </button>
            <button
              onClick={handleRefresh}
              className="text-text-muted hover:text-text-secondary active:rotate-180 transition-all duration-300 p-1"
              title="Refresh data"
            >
              <RefreshCw size={15} />
            </button>
          </div>
        </div>
        {syncMsg && (
          <div className="max-w-2xl mx-auto px-5 pb-2">
            <div className={`text-[12px] px-3 py-1.5 rounded-xl ${
              syncMsg.includes('queued') ? 'bg-accent-green/10 text-accent-green' : 'bg-accent-red/10 text-accent-red'
            }`}>
              {syncMsg}
            </div>
          </div>
        )}
      </header>

      {/* Content */}
      <main className="max-w-2xl mx-auto px-4 py-4 pb-28 space-y-3">
        <ErrorBoundary>
          <Suspense fallback={<LoadingState />}>
            {activeTab === 'today' && <TodayView key={refreshKey} />}
            {activeTab === 'week' && <WeekView key={refreshKey} />}
            {activeTab === 'plan' && <TrainingPlanView key={refreshKey} />}
            {activeTab === 'recovery' && <RecoveryView key={refreshKey} />}
            {activeTab === 'trends' && <TrendsView key={refreshKey} />}
            {activeTab === 'goals' && <GoalsView key={refreshKey} />}
          </Suspense>
        </ErrorBoundary>
      </main>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-bg-primary/95 backdrop-blur-xl border-t border-border-subtle">
        <div className="max-w-2xl mx-auto flex pb-[env(safe-area-inset-bottom)]">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const active = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex flex-col items-center pt-2.5 pb-1.5 gap-0.5 transition-all duration-200 min-h-[48px] ${
                  active
                    ? 'text-accent-green'
                    : 'text-text-muted hover:text-text-secondary active:scale-95'
                }`}
              >
                <Icon size={20} strokeWidth={active ? 2 : 1.5} />
                <span className={`text-[10px] tracking-wide ${active ? 'font-semibold' : 'font-medium'}`}>
                  {tab.label}
                </span>
              </button>
            )
          })}
        </div>
      </nav>
    </div>
  )
}

export default App
