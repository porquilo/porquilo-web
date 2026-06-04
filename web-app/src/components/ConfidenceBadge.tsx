import type { ReactNode } from 'react'

export interface ConfidenceBadgeProps {
  level?: 'measured' | 'estimated' | 'calculated'
  children?: ReactNode
}

const aliasMap: Record<string, string> = {
  high: 'measured',
  med: 'estimated',
  low: 'calculated',
}

export function ConfidenceBadge({ level = 'measured', children }: ConfidenceBadgeProps) {
  const lvl = aliasMap[level] ?? level
  const base = `var(--confidence-${lvl}`
  const p = { bg: `${base}-bg)`, fg: `${base}-fg)`, dot: `${base}-dot)` }
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      background: p.bg, color: p.fg,
      padding: '3px 9px', borderRadius: 999,
      fontFamily: 'var(--font-body)', fontSize: 11, fontWeight: 600,
      letterSpacing: 0.02, lineHeight: 1,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: p.dot }} />
      {children}
    </span>
  )
}
