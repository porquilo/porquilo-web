import { useEffect, useRef, useState } from 'react'
import { useFoods } from '../../hooks/useFoods'
import { useMeals } from '../../hooks/useMeals'
import { useCreateEntry } from '../../hooks/useEntries'
import { useToast } from '../../contexts/ToastContext'
import { WIcon, WI } from '../../components/Icon'
import { Button } from '../../components/Button'
import type { FoodResult, FoodVariant, Meal } from '../../types/api'

export interface QuickLogPanelProps {
  open: boolean
  onClose: () => void
  defaultMealId?: string
  selectedDate: string
}

function currentTimeHHMM(): string {
  const now = new Date()
  return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
}

function getContextualMealId(meals: Meal[], defaultMealId?: string): string {
  if (defaultMealId) return defaultMealId
  const hour = new Date().getHours()
  const find = (name: string) => meals.find(m => m.name.toLowerCase() === name)?.id
  if (hour < 11)  return find('breakfast') ?? meals[0]?.id ?? ''
  if (hour < 14)  return find('lunch')     ?? meals[0]?.id ?? ''
  if (hour >= 18) return find('dinner')    ?? meals[0]?.id ?? ''
  return find('snack') ?? meals[0]?.id ?? ''
}

// ── List view ──────────────────────────────────────────────────────────────

interface ListViewProps {
  query: string
  onQueryChange: (q: string) => void
  onSelectFood: (food: FoodResult) => void
  onClose: () => void
  searchInputRef: React.RefObject<HTMLInputElement | null>
}

function ListView({ query, onQueryChange, onSelectFood, onClose, searchInputRef }: ListViewProps) {
  const { data: results, isFetching } = useFoods(query, { page: 1, pageSize: 25, sortBy: 'name', sortDir: 'asc' })

  const showResults = query.length >= 2
  const isEmpty = showResults && !isFetching && (results?.items?.length ?? 0) === 0

  return (
    <>
      {/* Header */}
      <div style={{
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '20px 20px 16px',
        borderBottom: '1px solid var(--border-soft)',
      }}>
        <span style={{
          fontFamily: 'var(--font-display)',
          fontStyle: 'italic',
          fontSize: 20,
          fontWeight: 400,
          color: 'var(--fg1)',
          lineHeight: 1.1,
        }}>
          Quick log
        </span>
        <button
          aria-label="Close"
          onClick={onClose}
          style={{
            background: 'transparent', border: 'none', cursor: 'pointer',
            color: 'var(--fg3)', padding: 4, display: 'flex', alignItems: 'center',
            borderRadius: 6,
          }}
        >
          <WIcon d={WI.close} size={18} />
        </button>
      </div>

      {/* Search input */}
      <div style={{ flexShrink: 0, padding: '12px 20px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          background: 'var(--bg-sunken)',
          border: '1px solid var(--border)',
          borderRadius: 10,
          padding: '0 12px',
          height: 40,
        }}>
          <WIcon d={WI.search} size={16} color="var(--fg3)" />
          <input
            ref={searchInputRef}
            type="text"
            value={query}
            onChange={e => onQueryChange(e.target.value)}
            placeholder="What did you eat?"
            style={{
              flex: 1,
              border: 'none',
              background: 'transparent',
              fontFamily: 'var(--font-body)',
              fontSize: 14,
              color: 'var(--fg1)',
              outline: 'none',
            }}
          />
          {query.length > 0 && (
            <button
              onClick={() => onQueryChange('')}
              style={{
                background: 'transparent', border: 'none', cursor: 'pointer',
                color: 'var(--fg3)', padding: 0, display: 'flex', alignItems: 'center',
                fontSize: 16, lineHeight: 1,
              }}
            >
              ×
            </button>
          )}
        </div>
      </div>

      {/* Results */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {isEmpty ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: 120,
            fontSize: 13,
            color: 'var(--fg3)',
            fontStyle: 'italic',
            fontFamily: 'var(--font-display)',
          }}>
            Nothing in your library matches.
          </div>
        ) : (
          (results?.items ?? []).map(food => {
            const kcal = food.nutrients['calories_kcal'] ?? 0
            const prot = food.nutrients['protein_g'] ?? 0
            const carbs = food.nutrients['carbs_g'] ?? 0
            const fat = food.nutrients['fat_g'] ?? 0
            return (
              <button
                key={food.id}
                onClick={() => onSelectFood(food)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '10px 20px',
                  background: 'transparent',
                  border: 'none',
                  borderBottom: '1px solid var(--border-soft)',
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                    <span style={{
                      fontSize: 14, fontWeight: 600, color: 'var(--fg1)',
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}>
                      {food.name}
                    </span>
                    <span style={{ fontSize: 12, color: 'var(--fg4)', flexShrink: 0 }}>
                      {food.source}
                    </span>
                  </div>
                  <div style={{
                    fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--fg3)',
                    fontVariantNumeric: 'tabular-nums',
                  }}>
                    {Math.round(kcal)} kcal · {Math.round(prot)}g P · {Math.round(carbs)}g C · {Math.round(fat)}g F / 100g
                  </div>
                </div>
                <WIcon d={WI.chevR} size={16} color="var(--fg4)" />
              </button>
            )
          })
        )}
      </div>
    </>
  )
}

// ── Detail view ────────────────────────────────────────────────────────────

interface DetailViewProps {
  food: FoodResult
  defaultMealId?: string
  selectedDate: string
  onBack: () => void
  onClose: () => void
  amountInputRef: React.RefObject<HTMLInputElement | null>
}

function DetailView({ food, defaultMealId, selectedDate, onBack, onClose, amountInputRef }: DetailViewProps) {
  const { data: meals = [], isLoading: mealsLoading } = useMeals()
  const createEntry = useCreateEntry()
  const { setToast } = useToast()

  const firstVariant = food.variants[0] ?? null
  const [selectedVariant, setSelectedVariant] = useState<FoodVariant | null>(firstVariant)
  const [qty, setQty] = useState<number>(firstVariant?.amount ?? 100)
  const [selectedMealId, setSelectedMealId] = useState<string>('')
  const [time, setTime] = useState<string>(currentTimeHHMM())
  const [error, setError] = useState<string | null>(null)
  const [isLogging, setIsLogging] = useState(false)

  // Pre-select meal once meals load
  useEffect(() => {
    if (meals.length > 0 && selectedMealId === '') {
      setSelectedMealId(getContextualMealId(meals, defaultMealId))
    }
  }, [meals, defaultMealId, selectedMealId])

  const unit = selectedVariant?.unit ?? food.default_unit

  function handleVariantSelect(v: FoodVariant) {
    setSelectedVariant(v)
    if (v.amount !== null) setQty(v.amount)
  }

  const kcal  = qty > 0 ? Math.round((food.nutrients['calories_kcal'] ?? 0) * qty / 100) : null
  const prot  = qty > 0 ? Math.round((food.nutrients['protein_g']     ?? 0) * qty / 100) : null
  const carbs = qty > 0 ? Math.round((food.nutrients['carbs_g']       ?? 0) * qty / 100) : null
  const fat   = qty > 0 ? Math.round((food.nutrients['fat_g']         ?? 0) * qty / 100) : null

  async function handleLog() {
    if (qty === 0 || !selectedMealId) return
    setError(null)
    setIsLogging(true)
    try {
      const eaten_at = `${selectedDate}T${time}:00`
      await createEntry.mutateAsync({
        food_id: food.id,
        meal_id: selectedMealId,
        weight_g: qty,
        eaten_at,
        weight_source: 'manual',
        input_method: 'quick_log',
      })
      const mealName = meals.find(m => m.id === selectedMealId)?.name ?? ''
      setToast(`Logged — ${food.name}, ${qty} ${unit}, ${kcal ?? 0} kcal · ${mealName}`)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to log entry')
    } finally {
      setIsLogging(false)
    }
  }

  const variantButtonStyle = (selected: boolean): React.CSSProperties => ({
    fontFamily: 'var(--font-body)',
    fontSize: 13,
    fontWeight: 500,
    padding: '8px 10px',
    borderRadius: 8,
    border: `1px solid ${selected ? 'var(--accent)' : 'var(--border)'}`,
    background: selected ? 'var(--accent-soft-bg)' : 'var(--bg-sunken)',
    color: selected ? 'var(--accent-soft-fg)' : 'var(--fg2)',
    cursor: 'pointer',
    textAlign: 'left' as const,
    transition: 'all 120ms var(--ease-out)',
  })

  return (
    <>
      {/* Header */}
      <div style={{
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '16px 20px',
        borderBottom: '1px solid var(--border-soft)',
      }}>
        <button
          onClick={onBack}
          style={{
            background: 'transparent', border: 'none', cursor: 'pointer',
            color: 'var(--fg2)', padding: '4px 0', display: 'flex', alignItems: 'center',
            gap: 6, fontSize: 13, fontFamily: 'var(--font-body)', fontWeight: 500,
          }}
        >
          <WIcon d={WI.back} size={16} />
          Back to results
        </button>
        <button
          onClick={onClose}
          style={{
            background: 'transparent', border: 'none', cursor: 'pointer',
            color: 'var(--fg3)', padding: 4, display: 'flex', alignItems: 'center',
            borderRadius: 6,
          }}
        >
          <WIcon d={WI.close} size={18} />
        </button>
      </div>

      {/* Scrollable body */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px 20px 32px' }}>

        {/* Food identity */}
        <div style={{ marginBottom: 20 }}>
          <div style={{
            fontFamily: 'var(--font-display)',
            fontStyle: 'italic',
            fontSize: 22,
            fontWeight: 400,
            color: 'var(--fg1)',
            lineHeight: 1.2,
            marginBottom: 4,
          }}>
            {food.name}
          </div>
          <div style={{
            fontSize: 11,
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            color: 'var(--fg4)',
            fontFamily: 'var(--font-body)',
            fontWeight: 600,
          }}>
            {food.source}
          </div>
        </div>

        {/* Serving picker */}
        {food.variants.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <div style={{
              fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em',
              color: 'var(--fg3)', fontWeight: 600, marginBottom: 8,
            }}>
              Serving
            </div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 6,
            }}>
              {food.variants.map((v, i) => {
                const isLast = i === food.variants.length - 1
                const isOddLast = isLast && food.variants.length % 2 !== 0
                return (
                  <button
                    key={v.id}
                    onClick={() => handleVariantSelect(v)}
                    style={{
                      ...variantButtonStyle(selectedVariant?.id === v.id),
                      gridColumn: isOddLast ? '1 / -1' : undefined,
                    }}
                  >
                    {v.name ?? `${v.amount ?? ''} ${v.unit}`.trim()}
                    {v.amount !== null && v.name !== null && (
                      <span style={{ color: 'var(--fg3)', marginLeft: 4, fontSize: 12 }}>
                        {v.amount} {v.unit}
                      </span>
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {/* Amount */}
        <div style={{ marginBottom: 16 }}>
          <div style={{
            fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em',
            color: 'var(--fg3)', fontWeight: 600, marginBottom: 8,
          }}>
            Amount
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <input
              ref={amountInputRef}
              type="number"
              min={0}
              step={1}
              value={qty === 0 ? '' : qty}
              onChange={e => setQty(Math.max(0, Number(e.target.value) || 0))}
              style={{
                width: 96,
                fontFamily: 'var(--font-mono)',
                fontSize: 16,
                fontWeight: 500,
                color: 'var(--fg1)',
                background: 'var(--bg-sunken)',
                border: '1px solid var(--border)',
                borderRadius: 8,
                padding: '8px 12px',
                outline: 'none',
                fontVariantNumeric: 'tabular-nums',
              }}
            />
            <span style={{ fontSize: 14, color: 'var(--fg2)', fontFamily: 'var(--font-body)' }}>
              {unit}
            </span>
          </div>
        </div>

        {/* Macro preview */}
        <div style={{ marginBottom: 20 }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: 6,
          }}>
            {([
              ['kcal', kcal],
              ['protein', prot],
              ['carbs', carbs],
              ['fat', fat],
            ] as [string, number | null][]).map(([label, val]) => (
              <div
                key={label}
                style={{
                  background: 'var(--bg-sunken)',
                  border: '1px solid var(--border-soft)',
                  borderRadius: 8,
                  padding: '10px 8px',
                  textAlign: 'center',
                }}
              >
                <div style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 16,
                  fontWeight: 500,
                  color: 'var(--fg1)',
                  fontVariantNumeric: 'tabular-nums',
                  lineHeight: 1.2,
                  marginBottom: 3,
                }}>
                  {val === null ? '—' : val}
                </div>
                <div style={{ fontSize: 10, color: 'var(--fg3)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  {label}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Meal picker */}
        {mealsLoading && meals.length === 0 && (
          <div style={{ marginBottom: 16 }}>
            <div style={{
              fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em',
              color: 'var(--fg3)', fontWeight: 600, marginBottom: 8,
            }}>
              Meal
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
              {[0, 1, 2, 3].map(i => (
                <div key={i} style={{
                  height: 36, borderRadius: 8,
                  background: 'var(--border)', opacity: 0.5,
                }} />
              ))}
            </div>
          </div>
        )}
        {meals.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <div style={{
              fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em',
              color: 'var(--fg3)', fontWeight: 600, marginBottom: 8,
            }}>
              Meal
            </div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 6,
            }}>
              {meals.map((meal, i) => {
                const isLast = i === meals.length - 1
                const isOddLast = isLast && meals.length % 2 !== 0
                return (
                  <button
                    key={meal.id}
                    onClick={() => setSelectedMealId(meal.id)}
                    style={{
                      ...variantButtonStyle(selectedMealId === meal.id),
                      gridColumn: isOddLast ? '1 / -1' : undefined,
                    }}
                  >
                    {meal.name}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {/* Time */}
        <div style={{ marginBottom: 24 }}>
          <div style={{
            fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em',
            color: 'var(--fg3)', fontWeight: 600, marginBottom: 8,
          }}>
            Time
          </div>
          <input
            type="time"
            value={time}
            onChange={e => setTime(e.target.value)}
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 14,
              color: 'var(--fg1)',
              background: 'var(--bg-sunken)',
              border: '1px solid var(--border)',
              borderRadius: 8,
              padding: '8px 12px',
              outline: 'none',
            }}
          />
        </div>

        {/* Log it */}
        <Button
          variant="primary"
          disabled={qty === 0 || isLogging}
          onClick={() => void handleLog()}
          style={{ width: '100%', justifyContent: 'center' }}
        >
          {isLogging ? 'Logging…' : 'Log it'}
        </Button>

        {error && (
          <div style={{
            marginTop: 10,
            fontSize: 13,
            color: 'var(--danger-fg)',
            fontFamily: 'var(--font-body)',
          }}>
            {error}
          </div>
        )}
      </div>
    </>
  )
}

// ── Panel shell ────────────────────────────────────────────────────────────

export function QuickLogPanel({ open, onClose, defaultMealId, selectedDate }: QuickLogPanelProps) {
  const [query, setQuery] = useState('')
  const [selectedFood, setSelectedFood] = useState<FoodResult | null>(null)
  const searchInputRef = useRef<HTMLInputElement | null>(null)
  const amountInputRef = useRef<HTMLInputElement | null>(null)

  // Auto-focus search after slide-in
  useEffect(() => {
    if (open) {
      const t = setTimeout(() => searchInputRef.current?.focus(), 240)
      return () => clearTimeout(t)
    }
  }, [open])

  // Auto-focus amount when detail view opens
  useEffect(() => {
    if (selectedFood) {
      const t = setTimeout(() => amountInputRef.current?.focus(), 50)
      return () => clearTimeout(t)
    }
  }, [selectedFood])

  // Reset state after close transition completes
  useEffect(() => {
    if (!open) {
      const t = setTimeout(() => {
        setQuery('')
        setSelectedFood(null)
      }, 260)
      return () => clearTimeout(t)
    }
  }, [open])

  return (
    <div style={{
      position: 'absolute',
      inset: 0,
      zIndex: 20,
      pointerEvents: open ? 'auto' : 'none',
    }}>
      {/* Scrim */}
      <div
        onClick={onClose}
        style={{
          position: 'absolute',
          inset: 0,
          background: 'rgba(26, 18, 11, 0.32)',
          opacity: open ? 1 : 0,
          transition: 'opacity var(--dur-slow) var(--ease-out)',
        }}
      />

      {/* Drawer */}
      <div style={{
        position: 'absolute',
        top: 0,
        right: 0,
        bottom: 0,
        width: 384,
        background: 'var(--bg-elevated)',
        borderLeft: '1px solid var(--border)',
        boxShadow: 'var(--shadow-4)',
        transform: open ? 'translateX(0)' : 'translateX(100%)',
        transition: 'transform var(--dur-slow) var(--ease-out)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}>
        {selectedFood ? (
          <DetailView
            food={selectedFood}
            defaultMealId={defaultMealId}
            selectedDate={selectedDate}
            onBack={() => setSelectedFood(null)}
            onClose={onClose}
            amountInputRef={amountInputRef}
          />
        ) : (
          <ListView
            query={query}
            onQueryChange={setQuery}
            onSelectFood={setSelectedFood}
            onClose={onClose}
            searchInputRef={searchInputRef}
          />
        )}
      </div>
    </div>
  )
}
