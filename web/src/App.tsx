import { useState, lazy, Suspense, useCallback } from 'react'
import { Mountain, Calendar, Dumbbell, Heart, TrendingUp, Target, RefreshCw } from 'lucide-react'
import { LoadingState } from './components/LoadingState'

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
  const handleRefresh = useCallback(() => {
    setRefreshKey((k) => k + 1)
  }, [])

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-bg-primary/90 backdrop-blur-xl border-b border-border-subtle">
        <div className="max-w-2xl mx-auto px-5 py-3.5 flex items-center justify-between">
          <h1 className="text-base font-semibold tracking-tight flex items-center gap-2">
            <span className="text-accent-green text-lg">&#9650;</span>
            <span>Ascent</span>
          </h1>
          <div className="flex items-center gap-3">
            <span className="text-[11px] text-text-muted font-medium">
              {new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
            </span>
            <button
              onClick={handleRefresh}
              className="text-text-muted hover:text-text-secondary active:rotate-180 transition-all duration-300"
              title="Refresh data"
            >
              <RefreshCw size={14} />
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-2xl mx-auto px-4 py-5 pb-28 space-y-4">
        <Suspense fallback={<LoadingState />}>
          {activeTab === 'today' && <TodayView key={refreshKey} />}
          {activeTab === 'week' && <WeekView key={refreshKey} />}
          {activeTab === 'plan' && <TrainingPlanView key={refreshKey} />}
          {activeTab === 'recovery' && <RecoveryView key={refreshKey} />}
          {activeTab === 'trends' && <TrendsView key={refreshKey} />}
          {activeTab === 'goals' && <GoalsView key={refreshKey} />}
        </Suspense>
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
                className={`flex-1 flex flex-col items-center pt-3 pb-2 gap-1 transition-all duration-200 ${
                  active
                    ? 'text-accent-green'
                    : 'text-text-muted hover:text-text-secondary active:scale-95'
                }`}
              >
                <Icon size={20} strokeWidth={active ? 2 : 1.5} />
                <span className={`text-[10px] tracking-wide ${active ? 'font-medium' : ''}`}>
                  {tab.label}
                </span>
                {active && (
                  <div className="w-1 h-1 rounded-full bg-accent-green -mt-0.5" />
                )}
              </button>
            )
          })}
        </div>
      </nav>
    </div>
  )
}

export default App
