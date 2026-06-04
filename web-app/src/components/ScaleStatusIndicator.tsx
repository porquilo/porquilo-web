export interface ScaleStatusIndicatorProps {
  state: 'connected' | 'reading' | 'disconnected'
  label?: string
  reading?: number
}

const dotColors: Record<string, string> = {
  connected:    'var(--porq-herb-500)',
  reading:      'var(--porq-honey-500)',
  disconnected: 'var(--fg4)',
}

const defaultLabels: Record<string, string> = {
  connected:    'Scale connected',
  reading:      'Reading…',
  disconnected: 'No scale',
}

export function ScaleStatusIndicator({ state, label, reading }: ScaleStatusIndicatorProps) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 8,
      padding: '5px 10px', borderRadius: 999,
      border: '1px solid var(--border)', background: 'var(--bg-elevated)',
      fontSize: 12, fontWeight: 500, color: 'var(--fg2)',
      whiteSpace: 'nowrap',
    }}>
      <span style={{ width: 7, height: 7, borderRadius: '50%', background: dotColors[state] }} />
      <span>{label ?? defaultLabels[state]}</span>
      {reading != null && (
        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--fg1)', fontVariantNumeric: 'tabular-nums', fontWeight: 500 }}>
          {reading}<span style={{ fontSize: 10, color: 'var(--fg3)' }}>g</span>
        </span>
      )}
    </span>
  )
}
