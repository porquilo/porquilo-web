export interface MacroBarProps {
  kcal: number
  protein: number
  carbs: number
  fat: number
  anyEstimated?: boolean
}

export function MacroBar({ kcal, protein, carbs, fat, anyEstimated }: MacroBarProps) {
  const pKcal = protein * 4
  const cKcal = carbs * 4
  const fKcal = fat * 9
  const total = pKcal + cKcal + fKcal || 1

  return (
    <div style={{
      background: 'var(--bg-elevated)', border: '1px solid var(--border)',
      borderRadius: 14, boxShadow: 'var(--shadow-2)',
      padding: '16px 20px',
      display: 'flex', flexDirection: 'column', gap: 14,
    }}>
      <div style={{
        fontSize: 11, color: 'var(--fg3)', textTransform: 'uppercase',
        letterSpacing: 0.08, fontWeight: 600,
      }}>Today, eaten</div>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
          {anyEstimated && (
            <span style={{ color: 'var(--confidence-estimated-fg)', fontFamily: 'var(--font-mono)', fontSize: 40, fontWeight: 500, letterSpacing: '-0.02em' }}>~</span>
          )}
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: 48, fontWeight: 500,
            color: anyEstimated ? 'var(--confidence-estimated-fg)' : 'var(--fg1)',
            letterSpacing: '-0.025em', fontVariantNumeric: 'tabular-nums', lineHeight: 1,
          }}>{kcal.toLocaleString()}</span>
          <span style={{ fontSize: 16, color: 'var(--fg3)' }}>kcal</span>
        </div>
        {anyEstimated && (
          <span style={{ fontSize: 12, color: 'var(--confidence-estimated-fg)', fontStyle: 'italic' }}>
            some entries estimated
          </span>
        )}
      </div>
      <div style={{ display: 'flex', height: 10, borderRadius: 5, overflow: 'hidden', background: 'var(--bg-sunken)' }}>
        <div style={{ flex: pKcal / total, background: 'var(--porq-herb-500)' }} />
        <div style={{ flex: cKcal / total, background: 'var(--porq-honey-500)' }} />
        <div style={{ flex: fKcal / total, background: 'var(--porq-clay-500)' }} />
      </div>
      <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap' }}>
        {([
          ['var(--porq-herb-500)',  'Protein', protein],
          ['var(--porq-honey-500)', 'Carbs',   carbs],
          ['var(--porq-clay-500)',  'Fat',      fat],
        ] as [string, string, number][]).map(([c, l, v]) => (
          <span key={l} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--fg2)' }}>
            <span style={{ width: 8, height: 8, borderRadius: 2, background: c }} />
            {l}{' '}<span style={{ fontFamily: 'var(--font-mono)', color: 'var(--fg1)', fontVariantNumeric: 'tabular-nums', fontWeight: 500 }}>{v}g</span>
          </span>
        ))}
      </div>
    </div>
  )
}
