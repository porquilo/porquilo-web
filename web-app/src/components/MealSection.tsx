export interface MealSectionProps {
  name: string
  kcal: number
  grams: number
}

export function MealSection({ name, kcal, grams }: MealSectionProps) {
  return (
    <div style={{
      display: 'flex', alignItems: 'baseline', justifyContent: 'space-between',
      gap: 12, padding: '4px 4px 8px',
      borderBottom: '1px solid var(--border-soft)',
    }}>
      <span style={{
        fontFamily: 'var(--font-display)', fontSize: 18,
        color: 'var(--fg1)', fontVariationSettings: "'opsz' 28",
        fontStyle: 'italic', letterSpacing: '-0.01em', lineHeight: 1,
      }}>{name}</span>
      <span style={{
        fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg3)',
        fontVariantNumeric: 'tabular-nums', letterSpacing: 0.02,
        whiteSpace: 'nowrap', flexShrink: 0,
      }}>
        <b style={{ color: 'var(--fg1)', fontWeight: 500 }}>{kcal.toLocaleString()}</b> kcal · <b style={{ color: 'var(--fg1)', fontWeight: 500 }}>{grams}</b> g
      </span>
    </div>
  )
}
