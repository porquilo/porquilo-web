export interface TimeRangeSelectorProps {
  range: string
  onChange: (r: string) => void
}

const OPTIONS = ['7d', '30d', '90d', 'Custom']

export function TimeRangeSelector({ range, onChange }: TimeRangeSelectorProps) {
  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 2,
      background: 'var(--bg-elevated)',
      border: '1px solid var(--border)',
      borderRadius: 10,
      boxShadow: 'var(--shadow-1)',
      padding: 3,
    }}>
      {OPTIONS.map(opt => (
        <button
          key={opt}
          type="button"
          onClick={() => onChange(opt)}
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: 13,
            fontWeight: 600,
            lineHeight: 1,
            borderRadius: 8,
            padding: '6px 12px',
            border: 'none',
            cursor: 'pointer',
            transition: 'all 120ms var(--ease-out)',
            background: range === opt ? 'var(--accent-soft-bg)' : 'transparent',
            color: range === opt ? 'var(--accent-soft-fg)' : 'var(--fg2)',
          }}
        >
          {opt}
        </button>
      ))}
    </div>
  )
}
