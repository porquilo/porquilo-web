import { formatDate, parseDate, addDays } from '../../utils/dates'

export interface WeekStripProps {
  selectedDate: string
  onSelectDate: (date: string) => void
}

const DAY_LABELS = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']

function getMondayOfWeek(str: string): string {
  const date = parseDate(str)
  const dow = date.getDay() // 0=Sun, 1=Mon, ...
  const offset = dow === 0 ? -6 : 1 - dow
  const monday = new Date(date)
  monday.setDate(date.getDate() + offset)
  return formatDate(monday)
}

export function WeekStrip({ selectedDate, onSelectDate }: WeekStripProps) {
  const today = formatDate(new Date())
  const monday = getMondayOfWeek(selectedDate)

  return (
    <div style={{
      background: 'var(--bg-elevated)',
      border: '1px solid var(--border)',
      borderRadius: 12,
      boxShadow: 'var(--shadow-1)',
      padding: '12px 16px',
      display: 'grid',
      gridTemplateColumns: 'repeat(7, 1fr)',
      gap: 4,
    }}>
      {DAY_LABELS.map((label, i) => {
        const cellDate = addDays(monday, i)
        const isSelected = cellDate === selectedDate
        const isPast = cellDate < today
        const isFuture = cellDate > today

        let labelColor: string
        let numberColor: string
        let underlineColor: string
        let underlineOpacity: number

        if (isSelected) {
          labelColor = 'var(--accent)'
          numberColor = 'var(--accent)'
          underlineColor = 'var(--accent)'
          underlineOpacity = 1
        } else if (isPast) {
          labelColor = 'var(--fg3)'
          numberColor = 'var(--fg2)'
          underlineColor = 'var(--border)'
          underlineOpacity = 1
        } else {
          labelColor = 'var(--fg4)'
          numberColor = 'var(--fg4)'
          underlineColor = 'transparent'
          underlineOpacity = 0
        }

        const dayNum = parseDate(cellDate).getDate()

        return (
          <button
            key={cellDate}
            onClick={() => onSelectDate(cellDate)}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 4,
              padding: '8px 4px',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              borderRadius: 8,
            }}
          >
            <span style={{
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: '0.1em',
              color: labelColor,
              fontFamily: 'var(--font-body)',
            }}>
              {label}
            </span>
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 17,
              color: numberColor,
              lineHeight: 1,
              fontVariantNumeric: 'tabular-nums',
            }}>
              {dayNum}
            </span>
            <span style={{
              display: 'block',
              width: '55%',
              height: 3,
              borderRadius: 2,
              background: underlineColor,
              opacity: underlineOpacity,
            }} />
          </button>
        )
      })}
    </div>
  )
}
