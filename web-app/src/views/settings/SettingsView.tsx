import { useState } from 'react'
import type { CSSProperties, ReactNode } from 'react'
import { Button } from '../../components/Button'
import { ConfidenceBadge } from '../../components/ConfidenceBadge'
import { useToast } from '../../contexts/ToastContext'

// ─── types ───────────────────────────────────────────────────────────────────

type Section = 'goals' | 'profile' | 'integrations' | 'data' | 'about'

const NAV_ITEMS: { id: Section; label: string }[] = [
  { id: 'goals',        label: 'Goals' },
  { id: 'profile',      label: 'Profile' },
  { id: 'integrations', label: 'Integrations' },
  { id: 'data',         label: 'Data' },
  { id: 'about',        label: 'About' },
]

// ─── shared style objects ────────────────────────────────────────────────────

const inputStyle: CSSProperties = {
  padding: '7px 10px',
  background: 'var(--bg-sunken)',
  border: '1px solid var(--border-soft)',
  borderRadius: 8,
  fontSize: 13,
  color: 'var(--fg1)',
  outline: 'none',
  width: '100%',
  fontFamily: 'var(--font-body)',
  boxSizing: 'border-box',
}

// ─── sub-components ──────────────────────────────────────────────────────────

function SettingsCard({
  head,
  sub,
  children,
}: {
  head: string
  sub?: string
  children: ReactNode
}) {
  return (
    <div style={{
      background: 'var(--bg-elevated)',
      border: '1px solid var(--border)',
      borderRadius: 14,
      boxShadow: 'var(--shadow-2)',
      padding: '18px 20px',
      display: 'flex',
      flexDirection: 'column',
      gap: 10,
    }}>
      <div>
        <div style={{
          fontFamily: 'var(--font-display)',
          fontSize: 20,
          fontVariationSettings: "'opsz' 28",
          fontWeight: 400,
          color: 'var(--fg1)',
          lineHeight: 1.2,
        }}>
          {head}
        </div>
        {sub && (
          <div style={{ fontSize: 12, color: 'var(--fg3)', marginTop: 4 }}>
            {sub}
          </div>
        )}
      </div>
      {children}
    </div>
  )
}

function SettingsRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '160px 1fr',
      gap: 12,
      padding: '6px 0',
      borderBottom: '1px dashed var(--border-soft)',
      alignItems: 'center',
    }}>
      <span style={{ fontSize: 12, color: 'var(--fg3)' }}>{label}</span>
      {children}
    </div>
  )
}


function IntegrationRow({
  name,
  detail,
  level,
  status,
}: {
  name: string
  detail: string
  level: 'measured' | 'estimated' | 'calculated'
  status: string
}) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr auto auto',
      gap: 12,
      alignItems: 'center',
      padding: '8px 0',
      borderBottom: '1px dashed var(--border-soft)',
    }}>
      <div>
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--fg1)' }}>{name}</div>
        <div style={{ fontSize: 11, color: 'var(--fg3)', marginTop: 2 }}>{detail}</div>
      </div>
      <ConfidenceBadge level={level}>{status}</ConfidenceBadge>
      <Button variant="ghost" disabled>Configure</Button>
    </div>
  )
}

// ─── section panels ──────────────────────────────────────────────────────────

function GoalsSection({ setToast }: { setToast: (msg: string) => void }) {
  return (
    <SettingsCard
      head="Goals are off"
      sub="Goals don't appear on Today. If you configure them, they show as an adherence chip on the Trends report only."
    >
      <SettingsRow label="Calories">
        <input type="number" placeholder="kcal" style={inputStyle} />
      </SettingsRow>
      <SettingsRow label="Protein">
        <input type="number" placeholder="g" style={inputStyle} />
      </SettingsRow>
      <SettingsRow label="Carbohydrates">
        <input type="number" placeholder="g" style={inputStyle} />
      </SettingsRow>
      <SettingsRow label="Fat">
        <input type="number" placeholder="g" style={inputStyle} />
      </SettingsRow>
      <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
        <Button variant="primary" onClick={() => setToast('Goals saved')}>Save goals</Button>
        <Button variant="secondary" disabled>Use TDEE suggestion</Button>
      </div>
      <p style={{ fontSize: 11, color: 'var(--fg3)', margin: 0 }}>
        Changing a goal versions it — past days keep their original target.
      </p>
    </SettingsCard>
  )
}

function ProfileSection({ setToast }: { setToast: (msg: string) => void }) {
  return (
    <SettingsCard
      head="Profile"
      sub="Body metrics, timestamped — feeds the Trends report."
    >
      <SettingsRow label="Weight">
        <input type="text" placeholder="e.g. 75 kg" style={inputStyle} />
      </SettingsRow>
      <SettingsRow label="Height">
        <input type="text" placeholder="e.g. 178 cm" style={inputStyle} />
      </SettingsRow>
      <SettingsRow label="Age">
        <input type="number" placeholder="years" style={inputStyle} />
      </SettingsRow>
      <SettingsRow label="Activity">
        <input type="text" placeholder="e.g. Moderately active" style={inputStyle} />
      </SettingsRow>
      <SettingsRow label="Units">
        <input type="text" placeholder="metric / imperial" style={inputStyle} />
      </SettingsRow>
      <div style={{ marginTop: 4 }}>
        <Button variant="primary" onClick={() => setToast('Profile saved')}>Save profile</Button>
      </div>
    </SettingsCard>
  )
}


function IntegrationsSection() {
  return (
    <SettingsCard
      head="Integrations"
      sub="Mealie, Open Food Facts, and MCP — toggleable."
    >
      <IntegrationRow
        name="Mealie"
        detail="Self-hosted recipe manager"
        level="calculated"
        status="Not connected"
      />
      <IntegrationRow
        name="Open Food Facts"
        detail="Barcode lookup, open database"
        level="calculated"
        status="Not connected"
      />
      <IntegrationRow
        name="MCP server"
        detail="Model Context Protocol bridge"
        level="calculated"
        status="Not connected"
      />
      <IntegrationRow
        name="Home Assistant"
        detail="Smart home integration"
        level="calculated"
        status="Not connected"
      />
    </SettingsCard>
  )
}

function DataSection() {
  return (
    <SettingsCard
      head="Data"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <Button variant="primary" disabled>Download SQLite snapshot</Button>
        <Button variant="secondary" disabled>Restore from snapshot</Button>
        <Button variant="secondary" disabled>Import from MyFitnessPal CSV</Button>
        <Button variant="secondary" disabled>Import from Cronometer CSV</Button>
      </div>
      <div style={{
        background: 'var(--bg-sunken)',
        borderRadius: 8,
        padding: '12px 14px',
        fontSize: 12,
        color: 'var(--fg2)',
        marginTop: 4,
      }}>
        — entries · — recipes · — MB on disk
      </div>
    </SettingsCard>
  )
}

function AboutSection() {
  const rows: [string, string][] = [
    ['App version',  '0.1.0-alpha'],
    ['License',      'AGPL-3.0'],
    ['Documentation','porq.local/docs'],
    ['Source',       'github.com/porquilo/porquilo'],
    ['Named after',  'por quilo · Brazilian pay-by-weight counters'],
  ]
  return (
    <SettingsCard head="About">
      {rows.map(([key, value]) => (
        <div
          key={key}
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'baseline',
            gap: 12,
            padding: '6px 0',
            borderBottom: '1px dashed var(--border-soft)',
          }}
        >
          <span style={{ fontSize: 12, color: 'var(--fg3)', flexShrink: 0 }}>{key}</span>
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 13,
            color: 'var(--fg1)',
            fontVariantNumeric: 'tabular-nums',
            textAlign: 'right',
          }}>
            {value}
          </span>
        </div>
      ))}
    </SettingsCard>
  )
}

// ─── main view ───────────────────────────────────────────────────────────────

export default function SettingsView() {
  const [section, setSection] = useState<Section>('goals')
  const { setToast } = useToast()

  const navBtnBase: CSSProperties = {
    fontFamily: 'var(--font-body)',
    fontSize: 14,
    borderRadius: 10,
    padding: '8px 14px',
    border: 'none',
    cursor: 'pointer',
    textAlign: 'left',
    width: '100%',
    transition: 'all 120ms var(--ease-out)',
    lineHeight: 1,
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      padding: '24px 32px 40px',
      overflowY: 'auto',
      boxSizing: 'border-box',
    }}>
      <h1 style={{
        fontFamily: 'var(--font-display)',
        fontSize: 30,
        fontVariationSettings: "'opsz' 40",
        fontWeight: 400,
        color: 'var(--fg1)',
        margin: 0,
        lineHeight: 1.2,
      }}>
        Settings
      </h1>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '200px 1fr',
        gap: 24,
        marginTop: 20,
        alignItems: 'start',
      }}>
        {/* Left nav */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {NAV_ITEMS.map(({ id, label }) => {
            const isActive = section === id
            return (
              <button
                key={id}
                onClick={() => setSection(id)}
                style={{
                  ...navBtnBase,
                  background: isActive ? 'var(--accent-soft-bg)' : 'transparent',
                  color: isActive ? 'var(--accent-soft-fg)' : 'var(--fg2)',
                  fontWeight: isActive ? 600 : 500,
                }}
              >
                {label}
              </button>
            )
          })}
        </nav>

        {/* Right content */}
        <div>
          {section === 'goals'        && <GoalsSection setToast={setToast} />}
          {section === 'profile'      && <ProfileSection setToast={setToast} />}
{section === 'integrations' && <IntegrationsSection />}
          {section === 'data'         && <DataSection />}
          {section === 'about'        && <AboutSection />}
        </div>
      </div>
    </div>
  )
}
