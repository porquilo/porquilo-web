import type { ReactNode, ReactElement } from 'react'

export interface WIconProps {
  d: string | ReactNode
  size?: number
  stroke?: number
  color?: string
}

export function WIcon({ d, size = 18, stroke = 1.6, color }: WIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color || 'currentColor'}
      strokeWidth={stroke}
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{ flexShrink: 0 }}
    >
      {typeof d === 'string' ? <path d={d} /> : d}
    </svg>
  )
}

export const WI: Record<string, string | ReactElement> = {
  home:     <g><path d="M3 9.5L12 4l9 5.5V20H3z"/><path d="M9 20v-6h6v6"/></g>,
  book:     <g><path d="M5 5h10l4 4v10H5z"/><path d="M9 9h6M9 13h6"/></g>,
  list:     <g><path d="M4 7h16M4 12h16M4 17h12"/></g>,
  server:   <g><rect x="3" y="4" width="18" height="7" rx="2"/><rect x="3" y="13" width="18" height="7" rx="2"/><circle cx="7" cy="7.5" r="0.7" fill="currentColor"/><circle cx="7" cy="16.5" r="0.7" fill="currentColor"/></g>,
  search:   <g><circle cx="11" cy="11" r="6"/><path d="M16 16l5 5"/></g>,
  plus:     'M12 5v14M5 12h14',
  scale:    <g><path d="M5 11h14M5 11l1 9h12l1-9M9 7a3 3 0 1 1 6 0v4"/></g>,
  barcode:  <g><path d="M4 6v12M7 6v12M10 6v12M13 6v12M16 6v12M19 6v12"/></g>,
  camera:   <g><rect x="3" y="6" width="18" height="14" rx="2"/><circle cx="12" cy="13" r="3.5"/><path d="M8 6l1.5-2h5L16 6"/></g>,
  recipe:   <g><path d="M5 5h10l4 4v10H5z"/><path d="M9 9h6M9 13h6M9 17h4"/></g>,
  describe: <g><path d="M4 5h16v12H7l-3 3z"/><path d="M8 9h8M8 13h5"/></g>,
  chevL:    'M15 5l-7 7 7 7',
  chevR:    'M9 5l7 7-7 7',
  download: <g><path d="M12 4v12M7 11l5 5 5-5"/><path d="M4 20h16"/></g>,
  settings: <g><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 0 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 0 1-4 0v-.1a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 0 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 0 1 0-4h.1a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 0 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3h0a1.7 1.7 0 0 0 1-1.5V3a2 2 0 0 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 0 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8v0a1.7 1.7 0 0 0 1.5 1H21a2 2 0 0 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></g>,
  close:    'M18 6L6 18M6 6l12 12',
  back:     'M19 12H5M12 5l-7 7 7 7',
}
