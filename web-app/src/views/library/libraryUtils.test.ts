import { describe, expect, it } from 'vitest'
import { matchesFilter } from './libraryUtils'

describe('matchesFilter', () => {
  describe('"All" filter', () => {
    it('passes any source', () => {
      expect(matchesFilter('custom', 'All')).toBe(true)
      expect(matchesFilter('usda', 'All')).toBe(true)
      expect(matchesFilter('openfoodfacts', 'All')).toBe(true)
      expect(matchesFilter('mealie', 'All')).toBe(true)
      expect(matchesFilter('whatever', 'All')).toBe(true)
    })
  })

  describe('"Custom" filter', () => {
    it('passes exact "custom" source (case-insensitive)', () => {
      expect(matchesFilter('custom', 'Custom')).toBe(true)
      expect(matchesFilter('CUSTOM', 'Custom')).toBe(true)
    })

    it('rejects sources that merely contain "custom"', () => {
      expect(matchesFilter('custom_extended', 'Custom')).toBe(false)
    })

    it('rejects other sources', () => {
      expect(matchesFilter('usda', 'Custom')).toBe(false)
      expect(matchesFilter('mealie', 'Custom')).toBe(false)
    })
  })

  describe('"USDA" filter', () => {
    it('passes sources containing "usda"', () => {
      expect(matchesFilter('usda', 'USDA')).toBe(true)
      expect(matchesFilter('USDA_SR', 'USDA')).toBe(true)
      expect(matchesFilter('usda_branded', 'USDA')).toBe(true)
    })

    it('rejects sources without "usda"', () => {
      expect(matchesFilter('custom', 'USDA')).toBe(false)
      expect(matchesFilter('openfoodfacts', 'USDA')).toBe(false)
    })
  })

  describe('"Open Food Facts" filter', () => {
    it('passes "openfoodfacts" key', () => {
      expect(matchesFilter('openfoodfacts', 'Open Food Facts')).toBe(true)
      expect(matchesFilter('OPENFOODFACTS', 'Open Food Facts')).toBe(true)
    })

    it('passes sources containing the spaced form', () => {
      expect(matchesFilter('open food facts', 'Open Food Facts')).toBe(true)
    })

    it('rejects other sources', () => {
      expect(matchesFilter('custom', 'Open Food Facts')).toBe(false)
      expect(matchesFilter('usda', 'Open Food Facts')).toBe(false)
    })
  })

  describe('"Mealie" filter', () => {
    it('passes exact "mealie" source (case-insensitive)', () => {
      expect(matchesFilter('mealie', 'Mealie')).toBe(true)
      expect(matchesFilter('MEALIE', 'Mealie')).toBe(true)
    })

    it('rejects other sources', () => {
      expect(matchesFilter('custom', 'Mealie')).toBe(false)
    })
  })

  describe('unknown filter', () => {
    it('defaults to passing everything through', () => {
      expect(matchesFilter('custom', 'SomeFutureFilter')).toBe(true)
    })
  })
})
