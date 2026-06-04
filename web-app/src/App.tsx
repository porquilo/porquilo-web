import { useState } from 'react'
import { Sidebar } from './components/Sidebar'
import { ToastProvider, useToast } from './contexts/ToastContext'
import { TodayView } from './views/today/TodayView'
import LibraryView from './views/library/LibraryView'
import ReportsView from './views/reports/ReportsView'
import SettingsView from './views/settings/SettingsView'

export type Tab = 'today' | 'library' | 'reports' | 'settings'

function Shell() {
  const [tab, setTab] = useState<Tab>('today')
  const { toast } = useToast()

  function renderView() {
    switch (tab) {
      case 'today':    return <TodayView onOpenLog={(mealId) => console.log('open log', mealId)} />
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
