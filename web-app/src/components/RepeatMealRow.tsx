import { WIcon } from './Icon'

export interface RepeatMealRowProps {
  when: string
  name: string
  kcal: number
  onDismiss: () => void
}

const repeatIcon = (
  <g>
    <path d="M21 12a9 9 0 0 1-15.5 6.3L3 16" />
    <path d="M3 12a9 9 0 0 1 15.5-6.3L21 8" />
    <path d="M21 4v4h-4M3 20v-4h4" />
  </g>
)

export function RepeatMealRow({ when, name, kcal, onDismiss }: RepeatMealRowProps) {
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: 'auto 1fr auto auto',
      gap: 12, alignItems: 'center',
      padding: '11px 16px',
      background: 'var(--accent-soft-bg)',
      border: '1px solid var(--porq-clay-100)',
      borderRadius: 12, cursor: 'pointer',
    }}>
      <div style={{ color: 'var(--accent)' }}>
        <WIcon d={repeatIcon} size={16} />
      </div>
      <div style={{ fontSize: 14, color: 'var(--fg1)' }}>
        <span style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic', color: 'var(--accent-soft-fg)' }}>Just like {when}?</span>
        {' — '}
        <span style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic' }}>{name}</span>
      </div>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--fg2)', fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap' }}>{kcal} kcal</span>
      <button
        type="button"
        onClick={onDismiss}
        style={{ background: 'transparent', border: 0, padding: 4, color: 'var(--fg3)', cursor: 'pointer', borderRadius: 6, display: 'flex' }}
      >
        <WIcon d="M18 6L6 18M6 6l12 12" size={14} />
      </button>
    </div>
  )
}
