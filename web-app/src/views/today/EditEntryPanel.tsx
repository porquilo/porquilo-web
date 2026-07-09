import { useEffect, useState } from 'react'
import { useEntry, useUpdateEntry, useDeleteEntry } from '../../hooks/useEntries'
import { useMeals } from '../../hooks/useMeals'
import { formatDate, parseUtcTimestamp, toUtcTimestamp } from '../../utils/dates'
import type { UpdateEntryRequest } from '../../types/api'

interface EditEntryPanelProps {
  entryId: string | null
  onClose: () => void
}

const MACRO_KEYS = ['calories_kcal', 'protein_g', 'carbs_g', 'fat_g'] as const
const MACRO_LABELS: Record<string, string> = {
  calories_kcal: 'kcal',
  protein_g: 'protein',
  carbs_g: 'carbs',
  fat_g: 'fat',
}

function formatLocalTime(isoStr: string): string {
  const d = parseUtcTimestamp(isoStr)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

export function EditEntryPanel({ entryId, onClose }: EditEntryPanelProps) {
  const open = entryId !== null

  const [view, setView] = useState<'edit' | 'confirm-delete'>('edit')
  const [weight, setWeight] = useState('')
  const [weightSource, setWeightSource] = useState('')
  const [mealId, setMealId] = useState('')
  const [eatenAt, setEatenAt] = useState('')
  const [saveError, setSaveError] = useState<string | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const { data: entry, isLoading } = useEntry(entryId)
  const { data: meals } = useMeals()
  const updateEntry = useUpdateEntry()
  const deleteEntry = useDeleteEntry()

  // Populate fields when entry loads
  useEffect(() => {
    if (!entry) return
    setWeight(String(Number(entry.weight_g)))
    setWeightSource(entry.weight_source)
    setMealId(entry.meal_id)
    setEatenAt(formatLocalTime(entry.eaten_at))
    setSaveError(null)
    setDeleteError(null)
  }, [entry])

  // Reset view state after close transition completes
  useEffect(() => {
    if (!open) {
      const t = setTimeout(() => {
        setView('edit')
        setSaveError(null)
        setDeleteError(null)
      }, 260)
      return () => clearTimeout(t)
    }
  }, [open])

  const currentWeight = parseFloat(weight) || 0
  const entryWeight = entry ? Number(entry.weight_g) : 0
  const ratio = entryWeight > 0 ? currentWeight / entryWeight : 0

  function handleSave() {
    if (!entry || currentWeight === 0) return
    setSaveError(null)

    const patch: UpdateEntryRequest = {}

    const newWeightG = currentWeight
    if (newWeightG !== entryWeight) patch.weight_g = newWeightG
    if (weightSource !== entry.weight_source) patch.weight_source = weightSource
    if (mealId !== entry.meal_id) patch.meal_id = mealId

    const datePart = formatDate(parseUtcTimestamp(entry.eaten_at))
    const newEatenAt = toUtcTimestamp(datePart, eatenAt)
    const origTime = formatLocalTime(entry.eaten_at)
    if (eatenAt !== origTime) patch.eaten_at = newEatenAt

    updateEntry.mutate(
      { id: entry.id, patch },
      {
        onSuccess: onClose,
        onError: (err) => setSaveError(err.message),
      },
    )
  }

  function handleConfirmDelete() {
    if (!entryId) return
    setDeleteError(null)
    deleteEntry.mutate(entryId, {
      onSuccess: onClose,
      onError: (err) => setDeleteError(err.message),
    })
  }

  const labelStyle: React.CSSProperties = {
    fontSize: 11,
    fontWeight: 600,
    color: 'var(--fg3)',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    marginBottom: 4,
  }

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '8px 10px',
    border: '1px solid var(--border)',
    borderRadius: 8,
    background: 'var(--bg)',
    color: 'var(--fg1)',
    fontSize: 14,
    fontFamily: 'var(--font-body)',
    boxSizing: 'border-box',
  }

  const fieldStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
  }

  return (
    <div
      aria-hidden={!open}
      style={{
        position: 'absolute',
        inset: 0,
        zIndex: 20,
        pointerEvents: open ? 'auto' : 'none',
      }}
    >
      {/* Scrim */}
      <div
        data-testid="edit-entry-scrim"
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
      <div
        data-testid="edit-entry-drawer"
        data-state={open ? 'open' : 'closed'}
        style={{
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
        }}
      >
        {/* Header */}
        <div style={{
          padding: '20px 20px 16px',
          borderBottom: '1px solid var(--border-soft)',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h2 style={{
              fontFamily: 'var(--font-display)',
              fontStyle: 'italic',
              fontSize: 22,
              fontWeight: 400,
              color: 'var(--fg1)',
              margin: 0,
              lineHeight: 1.1,
            }}>
              {isLoading ? 'Loading…' : (entry?.food_name ?? '')}
            </h2>
            <button
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--fg3)',
                fontSize: 20,
                lineHeight: 1,
                padding: '4px 6px',
                borderRadius: 6,
                display: 'flex',
                alignItems: 'center',
              }}
              aria-label="Close"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 20 }}>
          {isLoading ? (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: 'var(--fg3)',
              fontSize: 14,
            }}>
              Loading…
            </div>
          ) : !entry ? null : view === 'edit' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Weight */}
              <div style={fieldStyle}>
                <label style={labelStyle}>Weight</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <input
                    type="number"
                    min="0"
                    step="any"
                    value={weight}
                    onChange={(e) => setWeight(e.target.value)}
                    style={{ ...inputStyle, width: 120 }}
                  />
                  <span style={{ fontSize: 13, color: 'var(--fg3)' }}>g</span>
                </div>
              </div>

              {/* Weight source */}
              <div style={fieldStyle}>
                <label style={labelStyle}>Weight source</label>
                <select
                  value={weightSource}
                  onChange={(e) => setWeightSource(e.target.value)}
                  style={inputStyle}
                >
                  <option value="scale">Scale</option>
                  <option value="recipe_derived">Recipe derived</option>
                  <option value="manual">Manual</option>
                  <option value="quick_search">Quick log (search)</option>
                  <option value="quick_barcode">Quick log (barcode)</option>
                  <option value="ai_describe">AI (describe)</option>
                  <option value="ai_photo">AI (photo)</option>
                </select>
              </div>

              {/* Meal */}
              <div style={fieldStyle}>
                <label style={labelStyle}>Meal</label>
                <select
                  value={mealId}
                  onChange={(e) => setMealId(e.target.value)}
                  style={inputStyle}
                >
                  {(meals ?? []).map((m) => (
                    <option key={m.id} value={m.id}>{m.name}</option>
                  ))}
                </select>
              </div>

              {/* Time */}
              <div style={fieldStyle}>
                <label style={labelStyle}>Time</label>
                <input
                  type="time"
                  value={eatenAt}
                  onChange={(e) => setEatenAt(e.target.value)}
                  style={{ ...inputStyle, width: 140 }}
                />
              </div>

              {/* Macro preview */}
              <div style={{
                background: 'var(--bg)',
                border: '1px solid var(--border-soft)',
                borderRadius: 10,
                padding: '12px 14px',
              }}>
                <div style={{ ...labelStyle, marginBottom: 10 }}>Nutrients</div>
                <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                  {MACRO_KEYS.map((key) => {
                    const raw = entry?.nutrients[key]?.value
                    const scaled = raw !== undefined && currentWeight > 0
                      ? Math.round(Number(raw) * ratio)
                      : null
                    return (
                      <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        <span style={{ fontSize: 10, color: 'var(--fg3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          {MACRO_LABELS[key]}
                        </span>
                        <span style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: 15,
                          fontVariantNumeric: 'tabular-nums',
                          color: 'var(--fg1)',
                        }}>
                          {scaled !== null ? scaled : '—'}
                          {scaled !== null && key !== 'calories_kcal' && (
                            <span style={{ fontSize: 11, color: 'var(--fg3)' }}> g</span>
                          )}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>

              {saveError && (
                <div style={{
                  fontSize: 13,
                  color: 'var(--color-error, #c0392b)',
                  background: 'var(--color-error-bg, #fdf0ee)',
                  border: '1px solid var(--color-error-border, #e8b4ae)',
                  borderRadius: 8,
                  padding: '8px 12px',
                }}>
                  {saveError}
                </div>
              )}
            </div>
          ) : (
            /* Confirm delete view */
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <p style={{ fontSize: 14, color: 'var(--fg1)', margin: 0, lineHeight: 1.5 }}>
                Delete this entry? This cannot be undone.
              </p>
              {deleteError && (
                <div style={{
                  fontSize: 13,
                  color: 'var(--color-error, #c0392b)',
                  background: 'var(--color-error-bg, #fdf0ee)',
                  border: '1px solid var(--color-error-border, #e8b4ae)',
                  borderRadius: 8,
                  padding: '8px 12px',
                }}>
                  {deleteError}
                </div>
              )}
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  onClick={() => setView('edit')}
                  style={{
                    flex: 1,
                    padding: '10px 16px',
                    border: '1px solid var(--border)',
                    borderRadius: 8,
                    background: 'transparent',
                    color: 'var(--fg1)',
                    fontSize: 14,
                    fontFamily: 'var(--font-body)',
                    cursor: 'pointer',
                    fontWeight: 500,
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmDelete}
                  disabled={deleteEntry.isPending}
                  style={{
                    flex: 1,
                    padding: '10px 16px',
                    border: 'none',
                    borderRadius: 8,
                    background: 'var(--color-error, #c0392b)',
                    color: '#fff',
                    fontSize: 14,
                    fontFamily: 'var(--font-body)',
                    cursor: deleteEntry.isPending ? 'not-allowed' : 'pointer',
                    fontWeight: 500,
                    opacity: deleteEntry.isPending ? 0.7 : 1,
                  }}
                >
                  {deleteEntry.isPending ? 'Deleting…' : 'Confirm delete'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer — only shown in edit view */}
        {!isLoading && entry && view === 'edit' && (
          <div style={{
            padding: '14px 20px',
            borderTop: '1px solid var(--border-soft)',
            flexShrink: 0,
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}>
            <button
              onClick={handleSave}
              disabled={currentWeight === 0 || updateEntry.isPending}
              style={{
                width: '100%',
                padding: '11px 16px',
                border: 'none',
                borderRadius: 9,
                background: 'var(--color-accent, var(--fg1))',
                color: '#fff',
                fontSize: 14,
                fontFamily: 'var(--font-body)',
                fontWeight: 600,
                cursor: currentWeight === 0 || updateEntry.isPending ? 'not-allowed' : 'pointer',
                opacity: currentWeight === 0 || updateEntry.isPending ? 0.5 : 1,
              }}
            >
              {updateEntry.isPending ? 'Saving…' : 'Save'}
            </button>
            <button
              onClick={() => { setView('confirm-delete'); setDeleteError(null) }}
              style={{
                width: '100%',
                padding: '9px 16px',
                border: '1px solid var(--border)',
                borderRadius: 9,
                background: 'transparent',
                color: 'var(--fg3)',
                fontSize: 13,
                fontFamily: 'var(--font-body)',
                fontWeight: 500,
                cursor: 'pointer',
              }}
            >
              Delete entry
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
