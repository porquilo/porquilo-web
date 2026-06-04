import { afterEach, beforeAll, afterAll, describe, expect, it, vi } from 'vitest'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import { WeekStrip } from './WeekStrip'

afterEach(cleanup)

// Fix "today" to 2025-06-04 (Wednesday) for colour-state tests
beforeAll(() => vi.useFakeTimers({ now: new Date(2025, 5, 4) }))
afterAll(() => vi.useRealTimers())

describe('WeekStrip', () => {
  it('renders 7 day cells', () => {
    render(<WeekStrip selectedDate="2025-06-04" onSelectDate={() => {}} />)
    const buttons = screen.getAllByRole('button')
    expect(buttons).toHaveLength(7)
  })

  it('renders Mon–Sun labels for the correct week', () => {
    render(<WeekStrip selectedDate="2025-06-04" onSelectDate={() => {}} />)
    ;['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'].forEach(label => {
      expect(screen.getByText(label)).toBeDefined()
    })
  })

  it('shows day numbers 2–8 for a week containing Wednesday June 4', () => {
    render(<WeekStrip selectedDate="2025-06-04" onSelectDate={() => {}} />)
    // Week: Mon 2 Jun – Sun 8 Jun
    ;['2', '3', '4', '5', '6', '7', '8'].forEach(n => {
      expect(screen.getByText(n)).toBeDefined()
    })
  })

  it('handles Sunday as part of the same Mon–Sun week (not start of next)', () => {
    // Sun 2026-06-07 should land in the week Mon Jun 1 – Sun Jun 7
    render(<WeekStrip selectedDate="2026-06-07" onSelectDate={() => {}} />)
    expect(screen.getByText('1')).toBeDefined()  // Mon Jun 1
    expect(screen.getByText('7')).toBeDefined()  // Sun Jun 7
  })

  it('calls onSelectDate with the correct YYYY-MM-DD string when a cell is clicked', () => {
    const handler = vi.fn()
    render(<WeekStrip selectedDate="2025-06-04" onSelectDate={handler} />)
    // Click WED (3rd button, index 2) — should be 2025-06-04 (Wed Jun 4)
    const buttons = screen.getAllByRole('button')
    fireEvent.click(buttons[2])
    expect(handler).toHaveBeenCalledWith('2025-06-04')
  })

  it('calls onSelectDate with Monday date when MON cell is clicked', () => {
    const handler = vi.fn()
    render(<WeekStrip selectedDate="2025-06-04" onSelectDate={handler} />)
    fireEvent.click(screen.getAllByRole('button')[0])
    expect(handler).toHaveBeenCalledWith('2025-06-02')
  })

  it('highlights selected cell with accent color', () => {
    // today=Wed Jun 4, selectedDate=Wed Jun 4 → index 2 is the selected cell
    render(<WeekStrip selectedDate="2025-06-04" onSelectDate={() => {}} />)
    const wedButton = screen.getAllByRole('button')[2]
    expect(wedButton.querySelector('span')?.getAttribute('style')).toContain('var(--accent)')
  })

  it('applies faded color to future cells', () => {
    // today=Wed Jun 4, THU Jun 5 (index 3) is future
    render(<WeekStrip selectedDate="2025-06-04" onSelectDate={() => {}} />)
    const thuButton = screen.getAllByRole('button')[3]
    expect(thuButton.querySelector('span')?.getAttribute('style')).toContain('var(--fg4)')
  })
})
