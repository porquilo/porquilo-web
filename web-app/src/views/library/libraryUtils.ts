/**
 * Returns true if a food's source matches the active filter chip.
 * 'All' always passes. Other chips do a case-insensitive substring match
 * against the source key returned by the API.
 */
export function matchesFilter(source: string, filter: string): boolean {
  if (filter === 'All') return true
  const s = source.toLowerCase()
  if (filter === 'Custom') return s === 'custom'
  if (filter === 'USDA') return s.includes('usda')
  if (filter === 'Open Food Facts') return s.includes('openfoodfacts') || s.includes('open food facts')
  if (filter === 'Mealie') return s === 'mealie'
  return true
}
