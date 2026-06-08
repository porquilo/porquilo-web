import { useEffect, useState } from 'react'
import type { CSSProperties, ReactNode } from 'react'
import { Button } from '../../components/Button'
import { ConfidenceBadge } from '../../components/ConfidenceBadge'
import { useToast } from '../../contexts/ToastContext'
import { getSettings, putSetting } from '../../api/settings'
import type { SettingRead } from '../../api/settings'
import { startOffSync, getOffSyncStatus } from '../../api/sync'
import type { OffSyncStatus } from '../../api/sync'
import { ApiError } from '../../api/client'

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


const helperStyle: CSSProperties = { fontSize: 11, color: 'var(--fg3)', marginTop: 4 }

function IntegrationGroup({
  name,
  badge,
  helper,
  children,
  onSave,
}: {
  name: string
  badge: ReactNode
  helper: string
  children: ReactNode
  onSave: () => Promise<void>
}) {
  const [saving, setSaving] = useState(false)
  async function handleSave() {
    setSaving(true)
    try {
      await onSave()
    } finally {
      setSaving(false)
    }
  }
  return (
    <div style={{
      padding: '12px 0',
      borderBottom: '1px dashed var(--border-soft)',
      display: 'flex',
      flexDirection: 'column',
      gap: 8,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--fg1)' }}>{name}</span>
        {badge}
      </div>
      {children}
      <div style={helperStyle}>{helper}</div>
      <div>
        <Button variant="primary" onClick={() => void handleSave()} disabled={saving}>
          {saving ? 'Saving…' : 'Save'}
        </Button>
      </div>
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


function IntegrationsSection({ setToast }: { setToast: (msg: string) => void }) {
  const [vals, setVals] = useState<Record<string, string>>({})

  useEffect(() => {
    getSettings()
      .then((rows: SettingRead[]) => {
        const map: Record<string, string> = {}
        for (const r of rows) {
          // Never pre-populate password fields
          if (r.key === 'off_password' || r.key === 'mealie_api_key') continue
          if (r.value !== null) map[r.key] = r.value
        }
        setVals(map)
      })
      .catch(() => {/* silently ignore load errors */})
  }, [])

  function field(key: string) {
    return {
      value: vals[key] ?? '',
      onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
        setVals(prev => ({ ...prev, [key]: e.target.value })),
    }
  }

  async function save(keys: string[]) {
    try {
      await Promise.all(
        keys.map(k => putSetting(k, vals[k]?.trim() || null))
      )
      setToast('Saved')
    } catch (err) {
      setToast(err instanceof Error ? err.message : 'Save failed')
    }
  }

  const usdaConfigured = Boolean(vals['usda_api_key']?.trim())
  const offAuthenticated = Boolean(vals['off_username']?.trim())
  const mealieConnected = Boolean(vals['mealie_url']?.trim())

  return (
    <SettingsCard
      head="Integrations"
      sub="Configure external services — credentials are stored locally."
    >
      {/* USDA FoodData Central */}
      <IntegrationGroup
        name="USDA FoodData Central"
        badge={
          <ConfidenceBadge level={usdaConfigured ? 'measured' : 'estimated'}>
            {usdaConfigured ? 'configured' : 'demo key'}
          </ConfidenceBadge>
        }
        helper="Free key at api.nal.usda.gov — demo key is rate-limited to ~3 req/min"
        onSave={() => save(['usda_api_key'])}
      >
        <SettingsRow label="API key">
          <input type="text" placeholder="DEMO_KEY" style={inputStyle} {...field('usda_api_key')} />
        </SettingsRow>
      </IntegrationGroup>

      {/* Open Food Facts */}
      <IntegrationGroup
        name="Open Food Facts"
        badge={
          <ConfidenceBadge level={offAuthenticated ? 'measured' : 'calculated'}>
            {offAuthenticated ? 'authenticated' : 'anonymous'}
          </ConfidenceBadge>
        }
        helper="Optional — anonymous contributions work without an account"
        onSave={() => save(['off_username', 'off_password'])}
      >
        <SettingsRow label="Username">
          <input type="text" placeholder="username" style={inputStyle} {...field('off_username')} />
        </SettingsRow>
        <SettingsRow label="Password">
          <input
            type="password"
            placeholder="••••••••"
            style={inputStyle}
            value={vals['off_password'] ?? ''}
            onChange={e => setVals(prev => ({ ...prev, off_password: e.target.value }))}
          />
        </SettingsRow>
      </IntegrationGroup>

      {/* Mealie */}
      <IntegrationGroup
        name="Mealie"
        badge={
          <ConfidenceBadge level={mealieConnected ? 'measured' : 'calculated'}>
            {mealieConnected ? 'connected' : 'not configured'}
          </ConfidenceBadge>
        }
        helper="Your Mealie base URL, e.g. http://mealie.local"
        onSave={() => save(['mealie_url', 'mealie_api_key'])}
      >
        <SettingsRow label="Instance URL">
          <input type="text" placeholder="http://mealie.local" style={inputStyle} {...field('mealie_url')} />
        </SettingsRow>
        <SettingsRow label="API key">
          <input
            type="password"
            placeholder="••••••••"
            style={inputStyle}
            value={vals['mealie_api_key'] ?? ''}
            onChange={e => setVals(prev => ({ ...prev, mealie_api_key: e.target.value }))}
          />
        </SettingsRow>
      </IntegrationGroup>

      {/* MCP server */}
      <div style={{ padding: '12px 0', display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--fg1)' }}>MCP server</span>
        <ConfidenceBadge level="measured">active</ConfidenceBadge>
      </div>
    </SettingsCard>
  )
}

function Spinner() {
  return (
    <>
      <style>{`@keyframes pq-spin{to{transform:rotate(360deg)}}`}</style>
      <span style={{
        display: 'inline-block',
        width: 12,
        height: 12,
        border: '2px solid currentColor',
        borderTopColor: 'transparent',
        borderRadius: '50%',
        animation: 'pq-spin 0.7s linear infinite',
        flexShrink: 0,
      }} />
    </>
  )
}

function DataSection({ setToast }: { setToast: (msg: string) => void }) {
  const [syncStatus, setSyncStatus] = useState<OffSyncStatus | null>(null)

  useEffect(() => {
    void getOffSyncStatus().then(setSyncStatus).catch(() => {})
  }, [])

  useEffect(() => {
    if (syncStatus?.status !== 'queued' && syncStatus?.status !== 'running') return
    const id = setInterval(() => {
      void getOffSyncStatus().then(setSyncStatus).catch(() => {})
    }, 10_000)
    return () => clearInterval(id)
  }, [syncStatus?.status])

  const importing = syncStatus?.status === 'queued' || syncStatus?.status === 'running'

  async function handleImport() {
    try {
      await startOffSync()
      setSyncStatus(s => ({
        status: 'queued',
        last_synced_at: s?.last_synced_at ?? null,
        error: null,
        sync_progress: null,
        sync_total: null,
      }))
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setToast('Import already running')
      }
    }
  }

  function statusLine() {
    const st = syncStatus?.status ?? null
    if (st === null) {
      return 'No food database downloaded — text search uses USDA only'
    }
    if (st === 'queued' || st === 'running') {
      const total = syncStatus?.sync_total ?? 0
      if (total > 0) {
        const progress = syncStatus?.sync_progress ?? 0
        const pct = Math.min(100, Math.round((progress / total) * 100))
        return `Importing Open Food Facts… ${progress.toLocaleString()} / ${total.toLocaleString()} products (${pct}%)`
      }
      return 'Importing Open Food Facts… this may take 15–90 minutes'
    }
    if (st === 'succeeded' && syncStatus?.last_synced_at) {
      const d = new Date(syncStatus.last_synced_at)
      const formatted = d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
      return `Last imported ${formatted}`
    }
    if (st === 'failed') {
      return null // rendered separately with amber colour
    }
    return null
  }

  const line = statusLine()
  const failed = syncStatus?.status === 'failed'
  const determinate = importing && (syncStatus?.sync_total ?? 0) > 0 && syncStatus?.status === 'running'
  const fillWidth = determinate
    ? Math.min(100, Math.round(((syncStatus?.sync_progress ?? 0) / (syncStatus?.sync_total ?? 1)) * 100)) + '%'
    : '30%'

  return (
    <SettingsCard head="Data">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <Button
          variant="primary"
          disabled={importing}
          leftIcon={importing ? <Spinner /> : undefined}
          onClick={() => void handleImport()}
        >
          Download food database
        </Button>
        {importing && (
          <>
            <style>{`@keyframes offImportIndeterminate{0%{transform:translateX(-100%)}100%{transform:translateX(430%)}}`}</style>
            <div style={{ width: '100%', height: 4, background: 'var(--bg-sunken)', borderRadius: 2, overflow: 'hidden', marginTop: 8 }}>
              <div style={{
                height: '100%',
                background: 'var(--accent)',
                borderRadius: 2,
                width: fillWidth,
                ...(determinate
                  ? { transition: 'width 0.6s var(--ease-out)' }
                  : { animation: 'offImportIndeterminate 1.4s ease-in-out infinite' }
                ),
              }} />
            </div>
          </>
        )}
        {line && (
          <div style={{ fontSize: 12, color: 'var(--fg3)', paddingLeft: 2 }}>{line}</div>
        )}
        {failed && (
          <div style={{ fontSize: 12, color: 'var(--amber, #f59e0b)', paddingLeft: 2 }}>
            Last import failed — {syncStatus?.error ?? 'unknown error'}
          </div>
        )}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 4 }}>
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
{section === 'integrations' && <IntegrationsSection setToast={setToast} />}
          {section === 'data'         && <DataSection setToast={setToast} />}
          {section === 'about'        && <AboutSection />}
        </div>
      </div>
    </div>
  )
}
