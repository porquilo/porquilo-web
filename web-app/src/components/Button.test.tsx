import { afterEach, describe, expect, it, vi } from 'vitest'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import { Button } from './Button'

afterEach(cleanup)

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Save</Button>)
    expect(screen.getByRole('button', { name: 'Save' })).toBeDefined()
  })

  it('defaults to type="button"', () => {
    render(<Button>Go</Button>)
    expect(screen.getByRole('button', { name: 'Go' }).getAttribute('type')).toBe('button')
  })

  it('sets type="submit" when specified', () => {
    render(<Button type="submit">Submit</Button>)
    expect(screen.getByRole('button', { name: 'Submit' }).getAttribute('type')).toBe('submit')
  })

  it('calls onClick when clicked', () => {
    const handler = vi.fn()
    render(<Button onClick={handler}>Click me</Button>)
    fireEvent.click(screen.getByRole('button', { name: 'Click me' }))
    expect(handler).toHaveBeenCalledOnce()
  })

  it('does not fire onClick when disabled', () => {
    const handler = vi.fn()
    render(<Button onClick={handler} disabled>Click me</Button>)
    fireEvent.click(screen.getByRole('button', { name: 'Click me' }))
    expect(handler).not.toHaveBeenCalled()
  })

  it('applies opacity 0.45 when disabled', () => {
    render(<Button disabled>Save</Button>)
    const btn = screen.getByRole('button', { name: 'Save' }) as HTMLButtonElement
    expect(btn.getAttribute('style')).toContain('opacity: 0.45')
  })

  it('applies cursor not-allowed when disabled', () => {
    render(<Button disabled>Save</Button>)
    const btn = screen.getByRole('button', { name: 'Save' }) as HTMLButtonElement
    expect(btn.getAttribute('style')).toContain('cursor: not-allowed')
  })

  it.each(['primary', 'secondary', 'ghost'] as const)('renders %s variant without crashing', (variant) => {
    render(<Button variant={variant}>Label</Button>)
    expect(screen.getByRole('button', { name: 'Label' })).toBeDefined()
  })
})
