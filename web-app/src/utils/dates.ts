export function formatDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function parseDate(str: string): Date {
  const [y, m, d] = str.split('-').map(Number)
  return new Date(y, m - 1, d)
}

export function addDays(str: string, n: number): string {
  const date = parseDate(str)
  date.setDate(date.getDate() + n)
  return formatDate(date)
}

export function formatDateLabel(str: string): string {
  const date = parseDate(str)
  return new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  }).format(date)
}

/**
 * Parses a server timestamp as UTC, even when it omits a timezone designator.
 * The server emits naive (no "Z"/offset) ISO timestamps for some fields (e.g.
 * SQLite-backed columns), which `new Date(str)` would otherwise parse as local time.
 */
export function parseUtcTimestamp(isoString: string): Date {
  const hasTimezone = /Z$|[+-]\d{2}:?\d{2}$/.test(isoString)
  return new Date(hasTimezone ? isoString : `${isoString}Z`)
}
