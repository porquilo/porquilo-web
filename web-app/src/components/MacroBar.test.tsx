import { afterEach, describe, expect, it } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { MacroBar } from './MacroBar'

afterEach(cleanup)

describe('MacroBar', () => {
  it('renders without crashing when all values are zero', () => {
    expect(() =>
      render(<MacroBar kcal={0} protein={0} carbs={0} fat={0} />)
    ).not.toThrow()
  })

  it('displays no NaN text when all values are zero', () => {
    const { container } = render(<MacroBar kcal={0} protein={0} carbs={0} fat={0} />)
    expect(container.textContent).not.toContain('NaN')
  })

  it('renders the kcal figure', () => {
    render(<MacroBar kcal={2100} protein={160} carbs={200} fat={70} />)
    expect(screen.getByText('2,100')).toBeDefined()
  })

  it('shows estimated tilde and note when anyEstimated is true', () => {
    render(<MacroBar kcal={1800} protein={100} carbs={150} fat={60} anyEstimated />)
    expect(screen.getByText('~')).toBeDefined()
    expect(screen.getByText('some entries estimated')).toBeDefined()
  })

  it('does not show tilde when anyEstimated is false', () => {
    render(<MacroBar kcal={1800} protein={100} carbs={150} fat={60} anyEstimated={false} />)
    expect(screen.queryByText('~')).toBeNull()
  })

  it('renders macro labels', () => {
    const { container } = render(<MacroBar kcal={1800} protein={100} carbs={150} fat={60} />)
    expect(container.textContent).toContain('Protein')
    expect(container.textContent).toContain('Carbs')
    expect(container.textContent).toContain('Fat')
  })
})
