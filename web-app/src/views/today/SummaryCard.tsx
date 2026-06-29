import type { DiaryDay, DiaryEntry } from '../../types/api'
import { parseUtcTimestamp } from '../../utils/dates'

export interface SummaryCardProps {
  day: DiaryDay | undefined
  isLoading: boolean
}

function getAllEntries(day: DiaryDay): DiaryEntry[] {
  return day.meals.flatMap(m => m.entries)
}

function formatTime(isoStr: string): string {
  const d = parseUtcTimestamp(isoStr)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function Skeleton({ width, height, style = {} }: { width: number | string; height: number; style?: React.CSSProperties }) {
  return (
    <div style={{
      width,
      height,
      borderRadius: 4,
      background: 'var(--border)',
      ...style,
    }} />
  )
}

export function SummaryCard({ day, isLoading }: SummaryCardProps) {
  if (isLoading) {
    return (
      <div style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border)',
        borderRadius: 12,
        boxShadow: 'var(--shadow-1)',
        display: 'flex',
        flexDirection: 'row',
        padding: '20px 24px',
        gap: 24,
        minHeight: 140,
      }}>
        <div style={{ flex: 1.2, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <Skeleton width={120} height={52} />
          <Skeleton width={160} height={14} />
          <Skeleton width="100%" height={8} />
          <div style={{ display: 'flex', gap: 16 }}>
            <Skeleton width={80} height={14} />
            <Skeleton width={80} height={14} />
            <Skeleton width={80} height={14} />
          </div>
        </div>
        <div style={{ width: 1, background: 'var(--border)', flexShrink: 0 }} />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <Skeleton width={100} height={11} />
          <div style={{ display: 'flex', gap: 12 }}>
            <Skeleton width={60} height={32} />
            <Skeleton width={60} height={32} />
            <Skeleton width={60} height={32} />
          </div>
          <Skeleton width={100} height={11} />
          <Skeleton width="100%" height={5} />
          <div style={{ display: 'flex', gap: 12 }}>
            <Skeleton width={60} height={14} />
            <Skeleton width={60} height={14} />
            <Skeleton width={60} height={14} />
          </div>
        </div>
      </div>
    )
  }

  const kcal = Number(day?.day_totals['calories_kcal']) || 0
  const protein = Number(day?.day_totals['protein_g']) || 0
  const carbs = Number(day?.day_totals['carbs_g']) || 0
  const fat = Number(day?.day_totals['fat_g']) || 0
  const isEstimated = day?.has_estimated_entries ?? false

  const allEntries = day ? getAllEntries(day) : []
  const totalEntries = allEntries.length
  const estimatedCount = allEntries.filter(e => e.weight_confidence === 'estimated').length
  const measuredCount = allEntries.filter(e => e.weight_confidence === 'measured').length
  const calculatedCount = allEntries.filter(e => e.weight_confidence === 'calculated').length
  const totalWeightG = allEntries.reduce((sum, e) => sum + (Number(e.weight_g) || 0), 0)

  const lastEntry = allEntries.length > 0
    ? allEntries.reduce((latest, e) => e.eaten_at > latest.eaten_at ? e : latest)
    : null
  const lastLogged = lastEntry ? formatTime(lastEntry.eaten_at) : '—'

  const pKcal = protein * 4
  const cKcal = carbs * 4
  const fKcal = fat * 9
  const macroTotal = pKcal + cKcal + fKcal || 1

  const totalConfidence = (measuredCount + calculatedCount + estimatedCount) || 1

  const entryCountLabel = estimatedCount > 0
    ? `${totalEntries} entries, ${estimatedCount} estimated`
    : `${totalEntries} entries`

  const kcalColor = isEstimated ? 'var(--confidence-estimated-fg)' : 'var(--fg1)'

  const sectionLabelStyle: React.CSSProperties = {
    fontSize: 11,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.08em',
    color: 'var(--fg3)',
    fontWeight: 600,
    fontFamily: 'var(--font-body)',
  }

  return (
    <div style={{
      background: 'var(--bg-elevated)',
      border: '1px solid var(--border)',
      borderRadius: 12,
      boxShadow: 'var(--shadow-1)',
      display: 'flex',
      flexDirection: 'row',
      overflow: 'hidden',
    }}>
      {/* LEFT: Kcal + macros */}
      <div style={{
        flex: 1.2,
        padding: '20px 24px',
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
      }}>
        {/* Kcal */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
          {isEstimated && (
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 36,
              fontWeight: 500,
              color: 'var(--confidence-estimated-fg)',
              lineHeight: 1,
            }}>~</span>
          )}
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 52,
            fontWeight: 500,
            color: kcalColor,
            lineHeight: 1,
            fontVariantNumeric: 'tabular-nums',
            letterSpacing: '-0.02em',
          }}>
            {Math.round(kcal).toLocaleString()}
          </span>
          <span style={{ fontSize: 14, color: 'var(--fg3)', marginLeft: 4 }}>kcal</span>
        </div>

        {/* Entry count */}
        <div style={{
          fontSize: 13,
          fontStyle: 'italic',
          fontFamily: 'var(--font-display)',
          color: 'var(--fg3)',
        }}>
          {entryCountLabel}
        </div>

        {/* Macro proportion bar */}
        <div style={{
          display: 'flex',
          height: 8,
          borderRadius: 4,
          overflow: 'hidden',
          background: 'var(--bg-sunken)',
        }}>
          <div style={{ flex: pKcal / macroTotal, background: 'var(--porq-herb-500)' }} />
          <div style={{ flex: cKcal / macroTotal, background: 'var(--porq-honey-500)' }} />
          <div style={{ flex: fKcal / macroTotal, background: 'var(--porq-clay-500)' }} />
        </div>

        {/* Macro gram labels */}
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          {([
            ['var(--porq-herb-500)', protein, 'protein'],
            ['var(--porq-honey-500)', carbs, 'carbs'],
            ['var(--porq-clay-500)', fat, 'fat'],
          ] as [string, number, string][]).map(([color, value, name]) => (
            <span key={name} style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 5,
              fontSize: 12,
              color: 'var(--fg2)',
              fontFamily: 'var(--font-body)',
            }}>
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: color, flexShrink: 0 }} />
              <span style={{ fontFamily: 'var(--font-mono)', fontVariantNumeric: 'tabular-nums' }}>
                {Math.round(value)}g
              </span>
              {' '}{name}
            </span>
          ))}
        </div>
      </div>

      {/* Divider */}
      <div style={{ width: 1, background: 'var(--border)', flexShrink: 0 }} />

      {/* RIGHT: Day at a glance */}
      <div style={{
        flex: 1,
        padding: '20px 24px',
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
      }}>
        <div style={sectionLabelStyle}>Day at a glance</div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
          {[
            ['Total weight', totalWeightG > 0 ? `${Math.round(totalWeightG)} g` : '— g'],
            ['Entries', String(totalEntries)],
            ['Last logged', lastLogged],
          ].map(([label, value]) => (
            <div key={label} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <div style={{ fontSize: 10, color: 'var(--fg4)', fontFamily: 'var(--font-body)' }}>{label}</div>
              <div style={{
                fontSize: 15,
                fontFamily: 'var(--font-mono)',
                fontVariantNumeric: 'tabular-nums',
                color: 'var(--fg1)',
                fontWeight: 500,
              }}>{value}</div>
            </div>
          ))}
        </div>

        <div style={sectionLabelStyle}>How you knew</div>

        {/* Confidence proportion bar */}
        <div style={{
          display: 'flex',
          height: 5,
          borderRadius: 4,
          overflow: 'hidden',
          background: 'var(--bg-sunken)',
        }}>
          <div style={{ flex: measuredCount / totalConfidence, background: 'var(--confidence-measured-dot)' }} />
          <div style={{ flex: calculatedCount / totalConfidence, background: 'var(--confidence-calculated-dot)' }} />
          <div style={{ flex: estimatedCount / totalConfidence, background: 'var(--confidence-estimated-dot)' }} />
        </div>

        {/* Confidence counts */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
          {([
            ['var(--confidence-measured-dot)', measuredCount, 'Measured'],
            ['var(--confidence-calculated-dot)', calculatedCount, 'Calculated'],
            ['var(--confidence-estimated-dot)', estimatedCount, 'Estimated'],
          ] as [string, number, string][]).map(([color, count, label]) => (
            <div key={label} style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
              opacity: count === 0 ? 0.3 : 1,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 7, height: 7, borderRadius: '50%', background: color, flexShrink: 0 }} />
                <span style={{ fontSize: 10, color: 'var(--fg4)', fontFamily: 'var(--font-body)' }}>{label}</span>
              </div>
              <div style={{
                fontSize: 15,
                fontFamily: 'var(--font-mono)',
                fontVariantNumeric: 'tabular-nums',
                color: 'var(--fg1)',
                fontWeight: 500,
              }}>{count}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
