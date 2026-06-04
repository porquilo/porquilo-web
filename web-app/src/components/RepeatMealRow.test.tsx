import { afterEach, describe, expect, it, vi } from 'vitest'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import { RepeatMealRow } from './RepeatMealRow'

afterEach(cleanup)

describe('RepeatMealRow', () => {
  it('renders the meal name and when label', () => {
    const { container } = render(
      <RepeatMealRow when="yesterday" name="Oat bowl" kcal={420} onDismiss={vi.fn()} />
    )
    expect(container.textContent).toContain('yesterday')
    expect(container.textContent).toContain('Oat bowl')
  })

  it('renders the kcal amount', () => {
    const { container } = render(
      <RepeatMealRow when="yesterday" name="Oat bowl" kcal={420} onDismiss={vi.fn()} />
    )
    expect(container.textContent).toContain('420 kcal')
  })

  it('calls onDismiss when the dismiss button is clicked', () => {
    const onDismiss = vi.fn()
    render(<RepeatMealRow when="yesterday" name="Oat bowl" kcal={420} onDismiss={onDismiss} />)
    fireEvent.click(screen.getByRole('button'))
    expect(onDismiss).toHaveBeenCalledOnce()
  })
})
