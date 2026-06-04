import { afterEach, describe, expect, it, vi } from 'vitest'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import { SkippedMealRow } from './SkippedMealRow'

afterEach(cleanup)

describe('SkippedMealRow', () => {
  it('renders the meal name', () => {
    render(<SkippedMealRow name="Lunch" onUndo={vi.fn()} />)
    expect(screen.getByText('Lunch')).toBeDefined()
  })

  it('renders the skipped label', () => {
    const { container } = render(<SkippedMealRow name="Lunch" onUndo={vi.fn()} />)
    expect(container.textContent).toContain('skipped')
  })

  it('calls onUndo when the undo button is clicked', () => {
    const onUndo = vi.fn()
    render(<SkippedMealRow name="Lunch" onUndo={onUndo} />)
    fireEvent.click(screen.getByRole('button', { name: /undo/i }))
    expect(onUndo).toHaveBeenCalledOnce()
  })
})
