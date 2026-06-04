import { describe, expect, it } from 'vitest'
import { formatDate, parseDate, addDays, formatDateLabel } from './dates'

describe('formatDate', () => {
  it('formats a date as YYYY-MM-DD', () => {
    expect(formatDate(new Date(2025, 5, 4))).toBe('2025-06-04')
  })

  it('zero-pads single-digit month and day', () => {
    expect(formatDate(new Date(2025, 0, 9))).toBe('2025-01-09')
  })

  it('handles year boundary (Dec 31)', () => {
    expect(formatDate(new Date(2025, 11, 31))).toBe('2025-12-31')
  })
})

describe('parseDate', () => {
  it('returns local midnight for a YYYY-MM-DD string', () => {
    const d = parseDate('2025-06-04')
    expect(d.getFullYear()).toBe(2025)
    expect(d.getMonth()).toBe(5)
    expect(d.getDate()).toBe(4)
    expect(d.getHours()).toBe(0)
    expect(d.getMinutes()).toBe(0)
  })

  it('roundtrips with formatDate', () => {
    const str = '2024-02-29' // leap day
    expect(formatDate(parseDate(str))).toBe(str)
  })
})

describe('addDays', () => {
  it('adds positive days', () => {
    expect(addDays('2025-06-04', 1)).toBe('2025-06-05')
  })

  it('subtracts days with negative n', () => {
    expect(addDays('2025-06-04', -1)).toBe('2025-06-03')
  })

  it('crosses month boundary', () => {
    expect(addDays('2025-05-31', 1)).toBe('2025-06-01')
  })

  it('crosses year boundary', () => {
    expect(addDays('2025-12-31', 1)).toBe('2026-01-01')
  })

  it('handles n=0', () => {
    expect(addDays('2025-06-04', 0)).toBe('2025-06-04')
  })
})

describe('formatDateLabel', () => {
  it('formats as "Weekday, Month Day"', () => {
    expect(formatDateLabel('2025-06-04')).toBe('Wednesday, June 4')
  })

  it('does not zero-pad the day', () => {
    expect(formatDateLabel('2025-06-01')).toBe('Sunday, June 1')
  })

  it('works for a different month', () => {
    expect(formatDateLabel('2025-01-15')).toBe('Wednesday, January 15')
  })
})
