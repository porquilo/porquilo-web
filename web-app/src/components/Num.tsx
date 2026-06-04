import type { ReactNode } from 'react'

interface NumProps {
  children: ReactNode
  suffix?: string
}

export function Num({ children, suffix }: NumProps) {
  return (
    <div style={{
      fontFamily: 'var(--font-mono)',
      fontSize: 13,
      color: 'var(--fg1)',
      fontVariantNumeric: 'tabular-nums',
    }}>
      {children}
      {suffix && <span style={{ color: 'var(--fg3)', fontSize: 11, marginLeft: 3 }}>{suffix}</span>}
    </div>
  )
}
