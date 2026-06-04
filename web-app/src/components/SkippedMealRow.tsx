export interface SkippedMealRowProps {
  name: string
  onUndo: () => void
}

export function SkippedMealRow({ name, onUndo }: SkippedMealRowProps) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      gap: 14, padding: '12px 16px',
      border: '1px dashed var(--border-strong)',
      borderRadius: 12, background: 'transparent',
    }}>
      <span>
        <span style={{ fontFamily: 'var(--font-display)', fontSize: 17, color: 'var(--fg2)', fontVariationSettings: "'opsz' 22", fontStyle: 'italic', opacity: 0.7 }}>{name}</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg3)', textTransform: 'uppercase', letterSpacing: 0.06, marginLeft: 10 }}>— skipped</span>
      </span>
      <button
        type="button"
        onClick={onUndo}
        style={{ background: 'transparent', border: 0, padding: '4px 8px', color: 'var(--fg3)', cursor: 'pointer', fontSize: 11, borderRadius: 6, fontFamily: 'var(--font-body)' }}
      >undo</button>
    </div>
  )
}
