import { useState } from 'react'
import { Mountain, Calendar, Dumbbell, Heart, TrendingUp, Target } from 'lucide-react'
import TodayView from './views/TodayView'
import WeekView from './views/WeekView'
import { TrainingPlanView } from './views/TrainingPlanView'
import RecoveryView from './views/RecoveryView'
import TrendsView from './views/TrendsView'
import GoalsView from './views/GoalsView'

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

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-md border-b border-border">
        <div className="max-w-2xl mx-auto px-4 py-3">
          <h1 className="text-lg font-semibold tracking-tight">
            <span className="text-accent-blue">▲</span> Ascent
          </h1>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-2xl mx-auto px-4 py-4 pb-24">
        {activeTab === 'today' && <TodayView />}
        {activeTab === 'week' && <WeekView />}
        {activeTab === 'plan' && <TrainingPlanView />}
        {activeTab === 'recovery' && <RecoveryView />}
        {activeTab === 'trends' && <TrendsView />}
        {activeTab === 'goals' && <GoalsView />}
      </main>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-bg-secondary/90 backdrop-blur-md border-t border-border">
        <div className="max-w-2xl mx-auto flex">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const active = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex flex-col items-center py-2 pt-3 gap-0.5 transition-colors ${
                  active
                    ? 'text-accent-blue'
                    : 'text-text-muted hover:text-text-secondary'
                }`}
              >
                <Icon size={18} strokeWidth={active ? 2.5 : 1.5} />
                <span className="text-[10px]">{tab.label}</span>
              </button>
            )
          })}
        </div>
      </nav>
    </div>
  )
}

export default App
