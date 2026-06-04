import { useState } from 'react'

type Tab = 'today' | 'library' | 'reports' | 'settings'

function App() {
  const [tab, _setTab] = useState<Tab>('today')

  return (
    <div style={{ display: 'flex', flexDirection: 'row', height: '100%' }}>
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {tab}
      </div>
    </div>
  )
}

export default App
