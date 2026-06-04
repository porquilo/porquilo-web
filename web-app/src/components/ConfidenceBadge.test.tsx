import { afterEach, describe, expect, it } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { ConfidenceBadge } from './ConfidenceBadge'

afterEach(cleanup)

describe('ConfidenceBadge', () => {
  it('renders children', () => {
    render(<ConfidenceBadge level="measured">Measured</ConfidenceBadge>)
    expect(screen.getByText('Measured')).toBeDefined()
  })

  it('defaults to measured when no level is given', () => {
    const { container } = render(<ConfidenceBadge>label</ConfidenceBadge>)
    expect((container.firstChild as HTMLElement).getAttribute('style')).toContain('var(--confidence-measured-bg)')
  })

  it.each([
    ['measured',   '--confidence-measured-bg'],
    ['estimated',  '--confidence-estimated-bg'],
    ['calculated', '--confidence-calculated-bg'],
  ] as const)('%s level uses the correct background token', (level, token) => {
    const { container } = render(<ConfidenceBadge level={level}>x</ConfidenceBadge>)
    expect((container.firstChild as HTMLElement).getAttribute('style')).toContain(`var(${token})`)
  })

  it('maps legacy alias high → measured', () => {
    const { container } = render(
      // @ts-expect-error testing legacy alias passthrough
      <ConfidenceBadge level="high">x</ConfidenceBadge>
    )
    expect((container.firstChild as HTMLElement).getAttribute('style')).toContain('var(--confidence-measured-bg)')
  })

  it('maps legacy alias med → estimated', () => {
    const { container } = render(
      // @ts-expect-error testing legacy alias passthrough
      <ConfidenceBadge level="med">x</ConfidenceBadge>
    )
    expect((container.firstChild as HTMLElement).getAttribute('style')).toContain('var(--confidence-estimated-bg)')
  })

  it('maps legacy alias low → calculated', () => {
    const { container } = render(
      // @ts-expect-error testing legacy alias passthrough
      <ConfidenceBadge level="low">x</ConfidenceBadge>
    )
    expect((container.firstChild as HTMLElement).getAttribute('style')).toContain('var(--confidence-calculated-bg)')
  })
})
