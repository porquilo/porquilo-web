import { useState } from 'react'
import type { ReactNode } from 'react'
import { Button } from '../../components/Button'
import { TimeRangeSelector } from '../../components/TimeRangeSelector'

// ── Constants ──────────────────────────────────────────────────────────────

const CIRC = 2 * Math.PI * 50 // ≈ 314.159

const SPARKLINE_PTS = 'M0,55 C20,50 40,60 60,45 C80,30 100,40 120,38 C140,35 160,42 180,30 C200,25 220,35 240,28 C260,22 280,32 300,28 C320,25 340,30 360,22 L400,25'

const DONUT_SEGMENTS = [
  { label: 'Weighed',    detail: '47 entries', pct: 0.65, color: 'var(--porq-herb-500)'  },
  { label: 'Calculated', detail: '18 entries', pct: 0.20, color: 'var(--porq-cocoa-500)' },
  { label: 'Estimated',  detail: '10 entries', pct: 0.15, color: 'var(--porq-honey-500)' },
]

const BUILDER_FIELDS = [
  { label: 'Metric',      value: 'Energy (kcal)' },
  { label: 'Grouped by',  value: 'Day' },
  { label: 'Time range',  value: '30 days' },
  { label: 'Chart type',  value: 'Area line' },
  { label: 'Filter',      value: 'All meals' },
  { label: 'Overlay',     value: '7-day average' },
]

// ── DonutChart ─────────────────────────────────────────────────────────────

interface DonutSegment {
  label: string
  detail: string
  pct: number
  color: string
}

function DonutChart({ segments }: { segments: DonutSegment[] }) {
  let offset = 0
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
      <div style={{ position: 'relative', width: 120, height: 120, flexShrink: 0 }}>
        <svg width={120} height={120} viewBox="0 0 120 120">
          <g transform="rotate(-90 60 60)">
            <circle
              cx={60} cy={60} r={50}
              fill="none"
              stroke="var(--bg-sunken)"
              strokeWidth={14}
              strokeDasharray={`${CIRC} ${CIRC}`}
            />
            {segments.map((s, i) => {
              const dash = s.pct * CIRC
              const off = -(offset * CIRC)
              offset += s.pct
              return (
                <circle
                  key={i}
                  cx={60} cy={60} r={50}
                  fill="none"
                  stroke={s.color}
                  strokeWidth={14}
                  strokeDasharray={`${dash} ${CIRC}`}
                  strokeDashoffset={off}
                />
              )
            })}
          </g>
        </svg>
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 22, fontWeight: 600, color: 'var(--fg1)', lineHeight: 1 }}>
            {Math.round(segments[0].pct * 100)}%
          </span>
          <span style={{ fontSize: 10, color: 'var(--fg3)', marginTop: 2 }}>weighed</span>
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {segments.map((s, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 10, height: 10, borderRadius: 2, background: s.color, flexShrink: 0 }} />
            <span style={{ fontSize: 12, color: 'var(--fg2)', flex: 1, whiteSpace: 'nowrap' }}>{s.label}</span>
            <span style={{ fontSize: 11, color: 'var(--fg3)', marginRight: 4 }}>{s.detail}</span>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--fg1)', fontFamily: 'var(--font-mono)' }}>
              {Math.round(s.pct * 100)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── SparklineChart ─────────────────────────────────────────────────────────

function SparklineChart() {
  const area = `${SPARKLINE_PTS} L400,90 L0,90 Z`
  return (
    <div style={{ width: '100%' }}>
      <svg
        viewBox="0 0 400 90"
        preserveAspectRatio="none"
        width="100%"
        height={90}
        style={{ display: 'block' }}
      >
        <line x1={0} y1={45} x2={400} y2={45} stroke="var(--border)" strokeDasharray="4 4" />
        <path d={area} fill="var(--accent)" fillOpacity={0.10} stroke="none" />
        <path d={SPARKLINE_PTS} fill="none" stroke="var(--accent)" strokeWidth={1.8} />
      </svg>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--fg3)' }}>30 days ago</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--fg3)' }}>now</span>
      </div>
    </div>
  )
}

// ── DashCard ───────────────────────────────────────────────────────────────

interface DashCardProps {
  title: string
  subtitle: string
  pinned?: boolean
  showActions?: boolean
  children: ReactNode
}

function DashCard({ title, subtitle, pinned = false, showActions = true, children }: DashCardProps) {
  return (
    <div style={{
      background: 'var(--bg-elevated)',
      border: '1px solid var(--border)',
      borderRadius: 14,
      boxShadow: 'var(--shadow-2)',
      padding: '16px 20px',
      display: 'flex',
      flexDirection: 'column',
      gap: 14,
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
        <div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontVariationSettings: "'opsz' 28", color: 'var(--fg1)', lineHeight: 1.2, whiteSpace: 'nowrap' }}>
            {title}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 12, color: 'var(--fg3)' }}>{subtitle}</span>
            {pinned && (
              <span style={{ fontSize: 10, color: 'var(--fg3)', padding: '2px 7px', background: 'var(--bg-sunken)', borderRadius: 999 }}>
                📌 pinned
              </span>
            )}
            {pinned && (
              <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.04em', color: 'var(--warning-fg)', background: 'var(--warning-bg)', padding: '2px 7px', borderRadius: 999 }}>
                Not live data
              </span>
            )}
          </div>
        </div>
        {showActions && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0 }}>
            <Button variant="ghost" disabled style={{ fontSize: 12, padding: '5px 10px' }}>Edit</Button>
            <Button variant="ghost" disabled style={{ fontSize: 12, padding: '5px 10px' }}>Open</Button>
          </div>
        )}
      </div>
      {children}
    </div>
  )
}

// ── Dashboard ──────────────────────────────────────────────────────────────

function DashboardArea() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
      <DashCard title="How you logged" subtitle="Confidence breakdown" pinned>
        <DonutChart segments={DONUT_SEGMENTS} />
      </DashCard>

      <DashCard title="Daily kcal" subtitle="30-day trend · 7-day avg" pinned>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 4 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 32, fontWeight: 500, color: 'var(--fg1)', lineHeight: 1 }}>
            1,847
          </span>
          <span style={{ fontSize: 12, color: 'var(--fg3)' }}>avg kcal</span>
          <span style={{ fontSize: 12, color: 'var(--porq-herb-700)', marginLeft: 4 }}>−3% vs prior 30d</span>
        </div>
        <SparklineChart />
      </DashCard>
    </div>
  )
}

// ── Report Library ─────────────────────────────────────────────────────────

function LibraryArea() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
      <DashCard title="Confidence breakdown" subtitle="Built-in report" showActions={false}>
        <p style={{ margin: '0 0 12px', fontSize: 13, color: 'var(--fg2)', lineHeight: 1.5 }}>
          See how often you weighed, calculated, or estimated — and track improvement over time.
        </p>
        <DonutChart segments={DONUT_SEGMENTS} />
        <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
          <Button variant="primary" disabled>Open</Button>
          <Button variant="secondary" disabled>Duplicate to customize</Button>
        </div>
      </DashCard>

      <DashCard title="Trends" subtitle="Built-in report" showActions={false}>
        <p style={{ margin: '0 0 12px', fontSize: 13, color: 'var(--fg2)', lineHeight: 1.5 }}>
          Daily kcal, protein, or any macro over any time range.
        </p>
        <SparklineChart />
        <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
          <Button variant="primary" disabled>Open</Button>
          <Button variant="secondary" disabled>Duplicate to customize</Button>
        </div>
      </DashCard>
    </div>
  )
}

// ── Builder ────────────────────────────────────────────────────────────────

function BuilderArea() {
  return (
    <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
      <div style={{
        width: 260,
        flexShrink: 0,
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border)',
        borderRadius: 14,
        padding: '16px 18px',
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
      }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--fg1)' }}>Configure report</div>
        {BUILDER_FIELDS.map(f => (
          <div key={f.label} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--fg3)' }}>
              {f.label}
            </span>
            <div style={{
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border)',
              borderRadius: 8,
              padding: '8px 12px',
              fontSize: 13,
              color: 'var(--fg1)',
              cursor: 'pointer',
            }}>
              {f.value}
            </div>
          </div>
        ))}
        <Button variant="primary" disabled style={{ width: '100%', marginTop: 4 }}>Save report</Button>
        <p style={{ margin: 0, fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg3)', lineHeight: 1.5 }}>
          Reports are stored as JSON in your account.
        </p>
      </div>

      <div style={{
        flex: 1,
        background: 'var(--bg)',
        border: '2px dashed var(--border-strong)',
        borderRadius: 10,
        minHeight: 280,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
      }}>
        <span style={{
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: 'var(--fg3)',
          marginBottom: 16,
        }}>
          Live preview
        </span>
        <div style={{ width: '100%' }}>
          <SparklineChart />
        </div>
      </div>
    </div>
  )
}

// ── ReportsView ────────────────────────────────────────────────────────────

type Area = 'dashboard' | 'library' | 'builder'

const AREAS: { id: Area; label: string }[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'library',   label: 'Report library' },
  { id: 'builder',   label: 'Builder' },
]

export default function ReportsView() {
  const [area, setArea] = useState<Area>('dashboard')
  const [range, setRange] = useState('30d')

  return (
    <div style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      padding: '24px 32px 40px',
      overflowY: 'auto',
      minHeight: 0,
    }}>
      <header style={{
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'space-between',
        gap: 16,
        marginBottom: 16,
        flexShrink: 0,
      }}>
        <div>
          <h1 style={{
            margin: 0,
            fontFamily: 'var(--font-display)',
            fontSize: 30,
            fontVariationSettings: "'opsz' 40",
            letterSpacing: '-0.01em',
            lineHeight: 1,
            color: 'var(--fg1)',
          }}>
            Reports
          </h1>
          <div style={{ fontSize: 13, color: 'var(--fg3)', marginTop: 4 }}>
            Two built-ins to start; build more in the canvas.
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
          <TimeRangeSelector range={range} onChange={setRange} />
          <Button variant="primary" disabled>New report</Button>
        </div>
      </header>

      <div style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 2,
        background: 'var(--bg-sunken)',
        borderRadius: 10,
        padding: 3,
        marginBottom: 20,
        alignSelf: 'flex-start',
      }}>
        {AREAS.map(a => (
          <button
            key={a.id}
            type="button"
            onClick={() => setArea(a.id)}
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: 13,
              fontWeight: 600,
              lineHeight: 1,
              borderRadius: 8,
              padding: '7px 16px',
              border: 'none',
              cursor: 'pointer',
              transition: 'all 120ms var(--ease-out)',
              background: area === a.id ? 'var(--bg-elevated)' : 'transparent',
              boxShadow: area === a.id ? 'var(--shadow-1)' : 'none',
              color: area === a.id ? 'var(--fg1)' : 'var(--fg2)',
            }}
          >
            {a.label}
          </button>
        ))}
      </div>

      {area === 'dashboard' && <DashboardArea />}
      {area === 'library'   && <LibraryArea />}
      {area === 'builder'   && <BuilderArea />}
    </div>
  )
}
