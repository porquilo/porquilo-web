export interface WLogoMarkProps {
  size?: number
}

export function WLogoMark({ size = 28 }: WLogoMarkProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64">
      <circle cx="32" cy="32" r="26" fill="none" stroke="var(--fg1)" strokeWidth="2.5" />
      <circle cx="32" cy="32" r="20" fill="none" stroke="var(--fg1)" strokeWidth="1" strokeDasharray="1 3" opacity="0.4" />
      <circle cx="32" cy="32" r="2" fill="var(--fg1)" />
      <line x1="32" y1="32" x2="36.5" y2="9.5" stroke="var(--accent)" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="32" y1="3" x2="32" y2="7" stroke="var(--fg1)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}
