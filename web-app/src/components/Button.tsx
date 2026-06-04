import type { CSSProperties, ReactNode } from 'react'
import { WIcon } from './Icon'

export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost'
  onClick?: () => void
  leftIcon?: string | ReactNode
  disabled?: boolean
  type?: 'button' | 'submit'
  style?: CSSProperties
  children?: ReactNode
}

const base: CSSProperties = {
  fontFamily: 'var(--font-body)', fontSize: 14, fontWeight: 600,
  borderRadius: 10, padding: '9px 14px', border: '1px solid transparent',
  cursor: 'pointer', lineHeight: 1, display: 'inline-flex',
  alignItems: 'center', gap: 8,
  transition: 'all 120ms var(--ease-out)',
  whiteSpace: 'nowrap',
}

const variants: Record<string, CSSProperties> = {
  primary:   { background: 'var(--accent)', color: 'var(--fg-on-accent)' },
  secondary: { background: 'var(--bg-elevated)', color: 'var(--fg1)', borderColor: 'var(--border)' },
  ghost:     { background: 'transparent', color: 'var(--fg1)' },
}

const disabledStyles: CSSProperties = {
  opacity: 0.45, cursor: 'not-allowed', pointerEvents: 'none',
}

export function Button({
  variant = 'primary',
  onClick,
  leftIcon,
  disabled,
  type = 'button',
  style = {},
  children,
}: ButtonProps) {
  return (
    <button
      type={type}
      onClick={disabled ? undefined : onClick}
      style={{ ...base, ...variants[variant], ...(disabled ? disabledStyles : {}), ...style }}
    >
      {leftIcon != null ? <WIcon d={leftIcon} size={16} /> : null}
      {children}
    </button>
  )
}
