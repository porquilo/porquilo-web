import { useEffect, useState } from 'react'
import { useFoods, useAllFoods } from '../../hooks/useFoods'
import { useToast } from '../../contexts/ToastContext'
import { Button } from '../../components/Button'
import { ConfidenceBadge } from '../../components/ConfidenceBadge'
import { WIcon, WI } from '../../components/Icon'
import { TableHeaders } from '../../components/TableHeaders'
import { Num } from '../../components/Num'
import { CreateFoodSheet } from './CreateFoodSheet'
import type { FoodResult } from '../../types/api'
import { matchesFilter } from './libraryUtils'

// ── Placeholder recipe data ────────────────────────────────────────────────

const RECIPES = [
  { id: '1', name: "Tuesday's tikka masala", portions: 6, totalG: 1240, kcalPer100: 134, source: 'Custom', made: '2 days ago' },
  { id: '2', name: 'Sunday lentil soup',     portions: 4, totalG:  890, kcalPer100: 140, source: 'Custom', made: 'last week' },
  { id: '3', name: 'Oat & banana porridge',  portions: 1, totalG:  340, kcalPer100: 113, source: 'Mealie', made: 'today' },
  { id: '4', name: 'Roast veg tray',         portions: 3, totalG:  720, kcalPer100: 91,  source: 'Custom', made: '5 days ago' },
  { id: '5', name: 'Chickpea salad bowl',    portions: 2, totalG:  580, kcalPer100: 159, source: 'Mealie', made: 'last Friday' },
]

// ── FoodRow ────────────────────────────────────────────────────────────────

const FOODS_GRID = '2fr 1fr 1fr 1fr 1fr 1fr'

interface FoodRowProps {
  food: FoodResult
}

function FoodRow({ food }: FoodRowProps) {
  const kcalPer100 = Number(food.nutrients['calories_kcal'] ?? 0)

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: FOODS_GRID,
      gap: 12,
      alignItems: 'center',
      padding: '12px 18px',
      borderTop: '1px solid var(--border-soft)',
    }}>
      <div>
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--fg1)' }}>{food.name}</div>
        {food.brand && <div style={{ fontSize: 11, color: 'var(--fg3)', marginTop: 1 }}>{food.brand}</div>}
      </div>
      <div><ConfidenceBadge level="measured">{food.source}</ConfidenceBadge></div>
      <Num>{Math.round(kcalPer100)}</Num>
      <Num suffix="g">{Number(food.nutrients['protein_g'] ?? 0).toFixed(1)}</Num>
      <Num suffix="g">{Number(food.nutrients['fat_g'] ?? 0).toFixed(1)}</Num>
      <Num suffix="g">{Number(food.nutrients['carbs_g'] ?? 0).toFixed(1)}</Num>
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
  const [tab, setTab] = useState<'foods' | 'recipes'>('foods')
  const [filter, setFilter] = useState('All')
  const [q, setQ] = useState('')
  const [sheetOpen, setSheetOpen] = useState(false)
  const [extraFoods, setExtraFoods] = useState<FoodResult[]>([])

  const { data: allFoodsData } = useAllFoods()
  const { data: searchData } = useFoods(q)

  useEffect(() => { setFilter('All') }, [tab])

  const rawFoods: FoodResult[] = q.length >= 2 ? (searchData ?? []) : (allFoodsData ?? [])

  // Prepend any foods just created this session (may not be in cache yet)
  const allFoods = [
    ...extraFoods.filter(ef => !rawFoods.some(f => f.id === ef.id)),
    ...rawFoods,
  ]

  const displayFoods = allFoods.filter(f => matchesFilter(f.source, filter))

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
              ? `Foods · ${allFoods.length}`
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
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
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
            <TableHeaders
              cols={['Name', 'Source', 'kcal/100g', 'Protein', 'Fat', 'Carbs']}
              gridTemplateColumns={FOODS_GRID}
            />
            {displayFoods.map(food => (
              <FoodRow key={food.id} food={food} />
            ))}
            {displayFoods.length === 0 && (
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

      <CreateFoodSheet
        open={sheetOpen}
        onClose={() => setSheetOpen(false)}
        onCreated={food => setExtraFoods(prev => [food, ...prev])}
      />
    </div>
  )
}
