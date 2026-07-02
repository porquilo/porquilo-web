import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useFoods, useAllFoods, FOODS_PAGE_SIZES } from '../../hooks/useFoods'
import type { FoodPageSize } from '../../hooks/useFoods'
import { useToast } from '../../contexts/ToastContext'
import { useMeals } from '../../hooks/useMeals'
import { useCreateEntry } from '../../hooks/useEntries'
import { Button } from '../../components/Button'
import { ConfidenceBadge } from '../../components/ConfidenceBadge'
import { WIcon, WI } from '../../components/Icon'
import { TableHeaders } from '../../components/TableHeaders'
import { Num } from '../../components/Num'
import { CreateFoodSheet } from './CreateFoodSheet'
import type { FoodResult } from '../../types/api'
import { matchesFilter } from './libraryUtils'
import { formatDate, toUtcTimestamp } from '../../utils/dates'

// ── Placeholder recipe data ────────────────────────────────────────────────

const RECIPES = [
  { id: '1', name: "Tuesday's tikka masala", portions: 6, totalG: 1240, kcalPer100: 134, source: 'Custom', made: '2 days ago' },
  { id: '2', name: 'Sunday lentil soup',     portions: 4, totalG:  890, kcalPer100: 140, source: 'Custom', made: 'last week' },
  { id: '3', name: 'Oat & banana porridge',  portions: 1, totalG:  340, kcalPer100: 113, source: 'Mealie', made: 'today' },
  { id: '4', name: 'Roast veg tray',         portions: 3, totalG:  720, kcalPer100: 91,  source: 'Custom', made: '5 days ago' },
  { id: '5', name: 'Chickpea salad bowl',    portions: 2, totalG:  580, kcalPer100: 159, source: 'Mealie', made: 'last Friday' },
]

// ── Column definitions ─────────────────────────────────────────────────────

const FOOD_COLUMNS = [
  { label: 'Name',      key: 'name' },
  { label: 'Source',    key: 'source' },
  { label: 'kcal/100g', key: 'calories' },
  { label: 'Protein',   key: 'protein' },
  { label: 'Fat',       key: 'fat' },
  { label: 'Carbs',     key: 'carbs' },
] as const

const SOURCE_MAP: Record<string, string> = {
  Custom: 'custom',
  USDA: 'usda',
  'Open Food Facts': 'open_food_facts',
}

// ── FoodRow ────────────────────────────────────────────────────────────────

const FOODS_GRID = '2fr 1fr 1fr 1fr 1fr 1fr 110px'

interface FoodRowProps {
  food: FoodResult
}

function FoodRow({ food }: FoodRowProps) {
  const kcalPer100 = Number(food.nutrients['calories_kcal'] ?? 0)
  const [qty, setQty] = useState(100)
  const { data: meals = [] } = useMeals()
  const createEntry = useCreateEntry()
  const { setToast } = useToast()

  async function handleLog() {
    const meal = meals[0]
    if (!meal) return
    const now = new Date()
    const h = String(now.getHours()).padStart(2, '0')
    const m = String(now.getMinutes()).padStart(2, '0')
    await createEntry.mutateAsync({
      food_id: food.id,
      meal_id: meal.id,
      weight_g: qty,
      eaten_at: toUtcTimestamp(formatDate(now), `${h}:${m}`),
      weight_source: 'manual',
      input_method: 'library',
    })
    setToast(`Logged — ${food.name}`)
  }

  return (
    <div
      data-testid="food-row"
      style={{
        display: 'grid',
        gridTemplateColumns: FOODS_GRID,
        gap: 12,
        alignItems: 'center',
        padding: '12px 18px',
        borderTop: '1px solid var(--border-soft)',
      }}
    >
      <div>
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--fg1)' }}>{food.name}</div>
        {food.brand && <div style={{ fontSize: 11, color: 'var(--fg3)', marginTop: 1 }}>{food.brand}</div>}
      </div>
      <div><ConfidenceBadge level="measured">{food.source}</ConfidenceBadge></div>
      <Num>{Math.round(kcalPer100)}</Num>
      <Num suffix="g">{Number(food.nutrients['protein_g'] ?? 0).toFixed(1)}</Num>
      <Num suffix="g">{Number(food.nutrients['fat_g'] ?? 0).toFixed(1)}</Num>
      <Num suffix="g">{Number(food.nutrients['carbs_g'] ?? 0).toFixed(1)}</Num>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <input
          type="number"
          value={qty}
          min={1}
          onChange={e => setQty(Math.max(1, Number(e.target.value) || 1))}
          style={{
            width: 52,
            fontFamily: 'var(--font-mono)',
            fontSize: 13,
            color: 'var(--fg1)',
            background: 'var(--bg-sunken)',
            border: '1px solid var(--border)',
            borderRadius: 6,
            padding: '4px 6px',
            outline: 'none',
          }}
        />
        <button
          onClick={() => void handleLog()}
          disabled={createEntry.isPending}
          style={{
            background: 'var(--accent)',
            color: 'var(--fg-on-accent)',
            border: 0,
            borderRadius: 6,
            padding: '5px 10px',
            fontFamily: 'var(--font-body)',
            fontSize: 12,
            fontWeight: 600,
            cursor: 'pointer',
            whiteSpace: 'nowrap',
          }}
        >
          {createEntry.isPending ? '…' : 'Log'}
        </button>
      </div>
    </div>
  )
}

// ── RecipeRow ──────────────────────────────────────────────────────────────

const RECIPES_GRID = '2fr 1fr 1fr 1fr 1fr 1.2fr 110px'

interface RecipeRowData {
  id: string
  name: string
  portions: number
  totalG: number
  kcalPer100: number
  source: string
  made: string
}

function RecipeRow({ r }: { r: RecipeRowData }) {
  const { setToast } = useToast()

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: RECIPES_GRID,
      gap: 12,
      alignItems: 'center',
      padding: '12px 18px',
      borderTop: '1px solid var(--border-soft)',
    }}>
      <div style={{
        fontFamily: 'var(--font-display)',
        fontSize: 16,
        color: 'var(--fg1)',
        fontVariationSettings: "'opsz' 22",
      }}>
        {r.name}
      </div>
      <span style={{
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: '0.06em',
        textTransform: 'uppercase',
        padding: '3px 8px',
        borderRadius: 999,
        background: r.source === 'Mealie' ? 'var(--accent-soft-bg)' : 'var(--bg-sunken)',
        color: r.source === 'Mealie' ? 'var(--accent-soft-fg)' : 'var(--fg3)',
        width: 'fit-content',
        display: 'inline-block',
      }}>
        {r.source}
      </span>
      <Num>{r.portions}</Num>
      <Num suffix="g">{r.totalG}</Num>
      <Num>{r.kcalPer100}</Num>
      <div style={{ fontSize: 12, color: 'var(--fg3)' }}>{r.made}</div>
      <button
        onClick={() => setToast('Coming soon')}
        style={{
          background: 'var(--accent)',
          color: 'var(--fg-on-accent)',
          border: 0,
          borderRadius: 8,
          padding: '7px 12px',
          fontFamily: 'var(--font-body)',
          fontSize: 12,
          fontWeight: 600,
          cursor: 'pointer',
          whiteSpace: 'nowrap',
        }}
      >
        Log a portion
      </button>
    </div>
  )
}

// ── LibraryView ────────────────────────────────────────────────────────────

export default function LibraryView() {
  const queryClient = useQueryClient()

  const [tab, setTab]         = useState<'foods' | 'recipes'>('foods')
  const [filter, setFilter]   = useState('All')
  const [q, setQ]             = useState('')
  const [sheetOpen, setSheetOpen] = useState(false)

  // Pagination + sorting state (foods tab only)
  const [page, setPage]         = useState(1)
  const [pageSize, setPageSize] = useState<FoodPageSize>(25)
  const [sortBy, setSortBy]     = useState('name')
  const [sortDir, setSortDir]   = useState<'asc' | 'desc'>('asc')

  // Debounced search query — keeps input responsive, debounces API calls
  const [debouncedQ, setDebouncedQ] = useState(q)
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q), 350)
    return () => clearTimeout(t)
  }, [q])

  // Reset filter when switching tabs
  useEffect(() => { setFilter('All') }, [tab])

  // Reset to page 1 on any query/filter/sort/size change
  useEffect(() => { setPage(1) }, [debouncedQ, filter, sortBy, sortDir, pageSize])

  const activeSource = filter === 'All' ? undefined : SOURCE_MAP[filter]

  const allFoodsQuery = useAllFoods({ page, pageSize, sortBy, sortDir, source: activeSource })
  const searchQuery   = useFoods(debouncedQ, { page, pageSize, sortBy, sortDir, source: activeSource })
  const activeQuery   = debouncedQ.trim().length >= 2 ? searchQuery : allFoodsQuery

  const foods      = activeQuery.data?.items ?? []
  const total      = activeQuery.data?.total ?? 0
  const totalPages = Math.ceil(total / pageSize)

  const handleSort = (key: string) => {
    if (key === sortBy) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(key)
      setSortDir('asc')
    }
  }

  const foodFilters = ['All', 'Custom', 'USDA', 'Open Food Facts']
  const recipeFilters = ['All', 'Custom', 'Mealie']
  const activeFilters = tab === 'foods' ? foodFilters : recipeFilters

  const displayRecipes = RECIPES.filter(r =>
    matchesFilter(r.source, filter) &&
    r.name.toLowerCase().includes(q.toLowerCase())
  )

  return (
    <div style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      padding: '24px 32px 40px',
      overflowY: 'auto',
      minHeight: 0,
    }}>
      {/* Header */}
      <header style={{
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'space-between',
        gap: 16,
        marginBottom: 16,
        flexShrink: 0,
      }}>
        <div>
          <h1 style={{
            margin: 0,
            fontFamily: 'var(--font-display)',
            fontSize: 30,
            fontVariationSettings: "'opsz' 40",
            letterSpacing: '-0.01em',
            lineHeight: 1,
            color: 'var(--fg1)',
          }}>
            Library
          </h1>
          <div style={{ fontSize: 13, color: 'var(--fg3)', marginTop: 4 }}>
            Foods and recipes — search, edit, and log directly.
          </div>
        </div>
        <Button variant="secondary" onClick={() => tab === 'foods' && setSheetOpen(true)}>
          {tab === 'foods' ? 'Add custom food' : 'Add recipe'}
        </Button>
      </header>

      {/* Sub-tab switcher */}
      <div style={{
        display: 'flex',
        gap: 0,
        marginBottom: 14,
        background: 'var(--bg-sunken)',
        borderRadius: 10,
        padding: 3,
        width: 'fit-content',
        flexShrink: 0,
      }}>
        {(['foods', 'recipes'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              background: tab === t ? 'var(--bg-elevated)' : 'transparent',
              border: 0,
              borderRadius: 8,
              padding: '8px 18px',
              fontFamily: 'var(--font-body)',
              fontSize: 13,
              fontWeight: tab === t ? 600 : 500,
              color: tab === t ? 'var(--fg1)' : 'var(--fg3)',
              boxShadow: tab === t ? 'var(--shadow-1)' : 'none',
              cursor: 'pointer',
            }}
          >
            {t === 'foods'
              ? (total > 0 ? `Foods · ${total.toLocaleString()}` : 'Foods')
              : `Recipes · ${RECIPES.length}`}
          </button>
        ))}
      </div>

      {/* Search + filter row */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 16, alignItems: 'center', flexShrink: 0 }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          borderRadius: 10,
          padding: '8px 12px',
          flex: 1,
          boxShadow: 'var(--shadow-1)',
        }}>
          <WIcon d={WI.search} size={16} color="var(--fg3)" />
          <input
            value={q}
            onChange={e => setQ(e.target.value)}
            placeholder={tab === 'foods' ? 'banana, oat milk, …' : 'tikka masala, porridge, …'}
            style={{
              flex: 1,
              border: 0,
              background: 'transparent',
              outline: 'none',
              fontFamily: 'var(--font-body)',
              fontSize: 14,
              color: 'var(--fg1)',
            }}
          />
          {q && (
            <button
              aria-label="Clear search"
              onClick={() => setQ('')}
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--fg3)',
                padding: 0,
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <WIcon d={WI.close} size={14} />
            </button>
          )}
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
          {activeFilters.map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                background: filter === f ? 'var(--accent-soft-bg)' : 'var(--bg-elevated)',
                color: filter === f ? 'var(--accent-soft-fg)' : 'var(--fg2)',
                border: '1px solid ' + (filter === f ? 'var(--accent)' : 'var(--border)'),
                borderRadius: 999,
                padding: '6px 12px',
                fontFamily: 'var(--font-body)',
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {f}
            </button>
          ))}
          {tab === 'foods' && (
            <select
              value={pageSize}
              onChange={e => {
                setPageSize(Number(e.target.value) as FoodPageSize)
                setPage(1)
              }}
              style={{
                background: 'var(--bg-elevated)',
                color: 'var(--fg2)',
                border: '1px solid var(--border)',
                borderRadius: 999,
                padding: '6px 12px',
                fontFamily: 'var(--font-body)',
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              {FOODS_PAGE_SIZES.map(n => (
                <option key={n} value={n}>Show: {n}</option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Results table */}
      <div style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border)',
        borderRadius: 14,
        boxShadow: 'var(--shadow-2)',
        overflow: 'hidden',
      }}>
        {tab === 'foods' ? (
          <>
            {/* Sortable column headers */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: FOODS_GRID,
              gap: 12,
              padding: '10px 18px',
              background: 'var(--bg-sunken)',
              borderBottom: '1px solid var(--border-soft)',
            }}>
              {FOOD_COLUMNS.map(col => {
                const isActive = col.key === sortBy
                const indicator = isActive
                  ? (sortDir === 'asc' ? '↑' : '↓')
                  : '↕'
                return (
                  <button
                    key={col.key}
                    onClick={() => handleSort(col.key)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                      background: 'transparent',
                      border: 'none',
                      padding: 0,
                      cursor: 'pointer',
                      fontFamily: 'var(--font-body)',
                      fontSize: 10,
                      color: 'var(--fg3)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.08em',
                      fontWeight: 600,
                      textAlign: 'left',
                    }}
                  >
                    {col.label}
                    <span style={{ opacity: isActive ? 1 : 0.4 }}>{indicator}</span>
                  </button>
                )
              })}
              <div />
            </div>
            <div style={{ opacity: activeQuery.isFetching ? 0.5 : 1, transition: 'opacity 0.15s' }}>
              {foods.map(food => (
                <FoodRow key={food.id} food={food} />
              ))}
            </div>
            {total === 0 && !activeQuery.isFetching && (
              <div style={{ padding: '32px 18px', textAlign: 'center', color: 'var(--fg3)', fontSize: 13 }}>
                No foods found
              </div>
            )}
          </>
        ) : (
          <>
            <TableHeaders
              cols={['Name', 'Source', 'Portions', 'Total', 'kcal/100g', 'Last made', '']}
              gridTemplateColumns={RECIPES_GRID}
            />
            {displayRecipes.map(r => (
              <RecipeRow key={r.id} r={r} />
            ))}
            {displayRecipes.length === 0 && (
              <div style={{ padding: '32px 18px', textAlign: 'center', color: 'var(--fg3)', fontSize: 13 }}>
                No recipes found
              </div>
            )}
          </>
        )}
      </div>

      {/* Pagination controls (foods tab only) */}
      {tab === 'foods' && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginTop: 12,
          fontSize: 13,
          color: 'var(--fg3)',
          flexShrink: 0,
        }}>
          <span>
            {total === 0
              ? 'No foods found'
              : `Showing ${Math.max(1, (page - 1) * pageSize + 1)}–${Math.min(page * pageSize, total)} of ${total.toLocaleString()} foods`}
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button
              onClick={() => setPage(p => p - 1)}
              disabled={page === 1}
              style={{
                background: 'transparent',
                border: '1px solid var(--border)',
                borderRadius: 8,
                padding: '6px 12px',
                fontFamily: 'var(--font-body)',
                fontSize: 13,
                color: page === 1 ? 'var(--fg4)' : 'var(--fg2)',
                cursor: page === 1 ? 'default' : 'pointer',
              }}
            >
              ← Previous
            </button>
            <span>Page {page} of {totalPages || 1}</span>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={page >= totalPages || totalPages === 0}
              style={{
                background: 'transparent',
                border: '1px solid var(--border)',
                borderRadius: 8,
                padding: '6px 12px',
                fontFamily: 'var(--font-body)',
                fontSize: 13,
                color: (page >= totalPages || totalPages === 0) ? 'var(--fg4)' : 'var(--fg2)',
                cursor: (page >= totalPages || totalPages === 0) ? 'default' : 'pointer',
              }}
            >
              Next →
            </button>
          </div>
          <span />
        </div>
      )}

      <CreateFoodSheet
        open={sheetOpen}
        onClose={() => setSheetOpen(false)}
        onCreated={() => queryClient.invalidateQueries({ queryKey: ['foods'] })}
      />
    </div>
  )
}
