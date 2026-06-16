import { useState } from 'react'
import { Sidebar } from './components/Sidebar'
import { ToastProvider, useToast } from './contexts/ToastContext'
import { TodayView } from './views/today/TodayView'
import { QuickLogPanel } from './views/today/QuickLogPanel'
import { EditEntryPanel } from './views/today/EditEntryPanel'
import LibraryView from './views/library/LibraryView'
import ReportsView from './views/reports/ReportsView'
import SettingsView from './views/settings/SettingsView'
import { formatDate } from './utils/dates'

export type Tab = 'today' | 'library' | 'reports' | 'settings'

function Shell() {
  const [tab, setTab] = useState<Tab>('today')
  const [selectedDate, setSelectedDate] = useState<string>(() => formatDate(new Date()))
  const [logOpen, setLogOpen] = useState(false)
  const [logDefaultMealId, setLogDefaultMealId] = useState<string | undefined>()
  const [editEntryId, setEditEntryId] = useState<string | null>(null)
  const { toast } = useToast()

  function openLog(mealId?: string) {
    setLogDefaultMealId(mealId)
    setLogOpen(true)
  }

  function renderView() {
    switch (tab) {
      case 'today':    return (
        <TodayView
          onOpenLog={openLog}
          onEditEntry={setEditEntryId}
          selectedDate={selectedDate}
          onDateChange={setSelectedDate}
        />
      )
      case 'library':  return <LibraryView />
      case 'reports':  return <ReportsView />
      case 'settings': return <SettingsView />
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'row', height: '100vh', overflow: 'hidden' }}>
      <Sidebar active={tab} onChange={setTab} />
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        overflow: 'hidden',
      }}>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          {renderView()}
        </div>
        <QuickLogPanel
          open={logOpen}
          onClose={() => setLogOpen(false)}
          defaultMealId={logDefaultMealId}
          selectedDate={selectedDate}
        />
        <EditEntryPanel
          entryId={editEntryId}
          onClose={() => setEditEntryId(null)}
        />

        {toast && (
          <div style={{
            position: 'absolute',
            bottom: 24,
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'var(--fg1)',
            color: 'var(--bg-elevated)',
            padding: '12px 20px',
            borderRadius: 10,
            fontSize: 13,
            fontWeight: 500,
            boxShadow: 'var(--shadow-4)',
            zIndex: 30,
            whiteSpace: 'nowrap',
            animation: 'toastIn 180ms var(--ease-out)',
          }}>
            {toast}
          </div>
        )}
      </div>
    </div>
  )
}

function App() {
  return (
    <ToastProvider>
      <Shell />
    </ToastProvider>
  )
}

export default App
