import type { Tab } from '../App'
import { WIcon, WI } from './Icon'
import { WLogoMark } from './LogoMark'

const NAV_ITEMS: { id: Tab; label: string; icon: (typeof WI)[keyof typeof WI] }[] = [
  { id: 'today',    label: 'Today',    icon: WI.home },
  { id: 'library',  label: 'Library',  icon: WI.book },
  { id: 'reports',  label: 'Reports',  icon: WI.list },
  { id: 'settings', label: 'Settings', icon: WI.settings },
]

export function Sidebar({ active, onChange }: { active: Tab; onChange: (tab: Tab) => void }) {
  return (
    <div style={{
      width: 232,
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      borderRight: '1px solid var(--border-soft)',
      background: 'var(--bg)',
      padding: '20px 12px',
      flexShrink: 0,
    }}>
      {/* Logo + wordmark */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 24 }}>
        <WLogoMark size={28} />
        <span style={{
          fontFamily: 'var(--font-display)',
          fontStyle: 'italic',
          fontSize: 22,
          color: 'var(--fg1)',
          lineHeight: 1,
        }}>
          Porquilo
        </span>
      </div>

      {/* Nav */}
      <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {NAV_ITEMS.map(({ id, label, icon }) => {
          const isActive = active === id
          return (
            <button
              key={id}
              onClick={() => onChange(id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                width: '100%',
                padding: '9px 12px',
                borderRadius: 10,
                border: 'none',
                cursor: 'pointer',
                fontFamily: 'var(--font-body)',
                fontSize: 14,
                textAlign: 'left',
                background: isActive ? 'var(--accent-soft-bg)' : 'transparent',
                color: isActive ? 'var(--accent-soft-fg)' : 'var(--fg2)',
                fontWeight: isActive ? 600 : 500,
              }}
            >
              <WIcon d={icon} size={18} />
              {label}
            </button>
          )
        })}
      </nav>

      {/* Server status widget */}
      <div style={{ marginTop: 'auto' }}>
        <div style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          borderRadius: 10,
          padding: '10px 12px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 4 }}>
            <div style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: 'var(--porq-herb-500)',
              flexShrink: 0,
            }} />
            <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--fg1)' }}>
              porq.local
            </span>
          </div>
          <span style={{ fontSize: 12, color: 'var(--fg2)' }}>
            Your data. Your hardware.
          </span>
        </div>
      </div>
    </div>
  )
}
