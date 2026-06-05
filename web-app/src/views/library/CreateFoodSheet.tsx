import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createFood } from '../../api/foods'
import { useToast } from '../../contexts/ToastContext'
import { Button } from '../../components/Button'
import { WIcon, WI } from '../../components/Icon'
import type { FoodResult } from '../../types/api'

export interface CreateFoodSheetProps {
  open: boolean
  onClose: () => void
  onCreated: (food: FoodResult) => void
}

interface VariantRow {
  id: number
  label: string
  weight: string
  error: string
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  background: 'var(--bg-sunken)',
  border: '1px solid var(--border)',
  borderRadius: 8,
  padding: '8px 10px',
  fontFamily: 'var(--font-body)',
  fontSize: 13,
  color: 'var(--fg1)',
  outline: 'none',
  boxSizing: 'border-box',
}

const labelStyle: React.CSSProperties = {
  fontSize: 11,
  fontWeight: 600,
  color: 'var(--fg3)',
  textTransform: 'uppercase',
  letterSpacing: '0.06em',
  marginBottom: 4,
  display: 'block',
}

const errorStyle: React.CSSProperties = {
  fontSize: 11,
  color: 'var(--danger-fg, #c0392b)',
  marginTop: 4,
}

let variantIdCounter = 0

export function CreateFoodSheet({ open, onClose, onCreated }: CreateFoodSheetProps) {
  const { setToast } = useToast()
  const queryClient = useQueryClient()

  // Identity
  const [name, setName] = useState('')
  const [brand, setBrand] = useState('')
  const [barcode, setBarcode] = useState('')

  // Unit
  const [unit, setUnit] = useState<'g' | 'ml'>('g')

  // Required nutrients
  const [kcal, setKcal] = useState('')
  const [protein, setProtein] = useState('')
  const [carbs, setCarbs] = useState('')
  const [fat, setFat] = useState('')

  // Optional nutrients
  const [showMore, setShowMore] = useState(false)
  const [fiber, setFiber] = useState('')
  const [sugar, setSugar] = useState('')
  const [sodium, setSodium] = useState('')
  const [satFat, setSatFat] = useState('')

  // Variants
  const [variants, setVariants] = useState<VariantRow[]>([])

  // Errors
  const [nameError, setNameError] = useState('')
  const [kcalError, setKcalError] = useState('')
  const [apiError, setApiError] = useState('')

  const mutation = useMutation({
    mutationFn: createFood,
    onSuccess: (food) => {
      void queryClient.invalidateQueries({ queryKey: ['foods', ''] })
      const result: FoodResult = {
        id: food.id,
        name: food.name,
        brand: food.brand,
        source: food.source,
        default_unit: food.default_unit,
        nutrients: Object.fromEntries(food.nutrients.map(n => [n.nutrient_key, n.value_per_100])),
        variants: food.variants.map(v => ({ id: '', name: v.name, amount: v.amount, unit: v.unit })),
      }
      onCreated(result)
      setToast(`Added ${food.name} to your library`)
      handleClose()
    },
    onError: (err: Error) => {
      setApiError(err.message ?? 'Something went wrong')
    },
  })

  function resetForm() {
    setName(''); setBrand(''); setBarcode('')
    setUnit('g')
    setKcal(''); setProtein(''); setCarbs(''); setFat('')
    setShowMore(false)
    setFiber(''); setSugar(''); setSodium(''); setSatFat('')
    setVariants([])
    setNameError(''); setKcalError(''); setApiError('')
  }

  function handleClose() {
    onClose()
    setTimeout(resetForm, 320)
  }

  function handleSubmit() {
    let valid = true
    setNameError(''); setKcalError(''); setApiError('')

    if (!name.trim()) {
      setNameError('Name is required')
      valid = false
    }
    const kcalNum = parseFloat(kcal)
    if (!kcal || isNaN(kcalNum) || kcalNum <= 0) {
      setKcalError('Calories required')
      valid = false
    }

    const newVariants = variants.map(v => {
      const w = parseFloat(v.weight)
      if (v.label && (!v.weight || w <= 0)) {
        return { ...v, error: 'Weight must be > 0' }
      }
      return { ...v, error: '' }
    })
    setVariants(newVariants)
    if (newVariants.some(v => v.error)) valid = false

    if (!valid) return

    const nutrients = [
      { nutrient_key: 'calories_kcal', value_per_100: kcalNum },
      ...(protein ? [{ nutrient_key: 'protein_g', value_per_100: parseFloat(protein) }] : []),
      ...(carbs   ? [{ nutrient_key: 'carbs_g',   value_per_100: parseFloat(carbs) }]   : []),
      ...(fat     ? [{ nutrient_key: 'fat_g',      value_per_100: parseFloat(fat) }]     : []),
      ...(fiber   ? [{ nutrient_key: 'fiber_g',    value_per_100: parseFloat(fiber) }]   : []),
      ...(sugar   ? [{ nutrient_key: 'sugar_g',    value_per_100: parseFloat(sugar) }]   : []),
      ...(sodium  ? [{ nutrient_key: 'sodium_mg',  value_per_100: parseFloat(sodium) }]  : []),
      ...(satFat  ? [{ nutrient_key: 'saturated_fat_g', value_per_100: parseFloat(satFat) }] : []),
    ]

    mutation.mutate({
      name: name.trim(),
      brand: brand.trim() || undefined,
      barcode: barcode.trim() || undefined,
      default_unit: unit,
      nutrients,
      variants: newVariants
        .filter(v => v.label.trim() && parseFloat(v.weight) > 0)
        .map(v => ({ name: v.label.trim(), amount: parseFloat(v.weight), unit })),
    })
  }

  function addVariant() {
    setVariants(prev => [...prev, { id: ++variantIdCounter, label: '', weight: '', error: '' }])
  }

  function removeVariant(id: number) {
    setVariants(prev => prev.filter(v => v.id !== id))
  }

  function updateVariant(id: number, field: 'label' | 'weight', value: string) {
    setVariants(prev => prev.map(v => v.id === id ? { ...v, [field]: value, error: '' } : v))
  }

  return (
    <div style={{
      position: 'absolute',
      inset: 0,
      zIndex: 20,
      pointerEvents: open ? 'auto' : 'none',
    }}>
      {/* Scrim */}
      <div
        data-testid="sheet-scrim"
        onClick={handleClose}
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
            Add custom food
          </span>
          <button
            onClick={handleClose}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--fg3)',
              padding: 4,
              display: 'flex',
              alignItems: 'center',
              borderRadius: 6,
            }}
          >
            <WIcon d={WI.close} size={18} />
          </button>
        </div>

        {/* Scrollable form body */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: 20,
          display: 'flex',
          flexDirection: 'column',
          gap: 20,
        }}>
          {/* Identity */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div>
              <label style={labelStyle}>Name *</label>
              <input
                value={name}
                onChange={e => { setName(e.target.value); setNameError('') }}
                placeholder="e.g. Banana, raw"
                style={{ ...inputStyle, borderColor: nameError ? 'var(--danger-fg, #c0392b)' : undefined }}
              />
              {nameError && <div style={errorStyle}>{nameError}</div>}
            </div>
            <div>
              <label style={labelStyle}>Brand</label>
              <input
                value={brand}
                onChange={e => setBrand(e.target.value)}
                placeholder="e.g. Fage (optional)"
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Barcode</label>
              <input
                value={barcode}
                onChange={e => setBarcode(e.target.value)}
                placeholder="e.g. 5449000214911 (optional)"
                style={inputStyle}
              />
            </div>
          </div>

          {/* Default unit toggle */}
          <div>
            <label style={labelStyle}>Default unit</label>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 6,
            }}>
              {(['g', 'ml'] as const).map(u => (
                <button
                  key={u}
                  onClick={() => setUnit(u)}
                  style={{
                    padding: '9px 14px',
                    borderRadius: 8,
                    border: '1px solid',
                    fontFamily: 'var(--font-body)',
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: 'pointer',
                    background: unit === u ? 'var(--accent-soft-bg)' : 'var(--bg-sunken)',
                    color: unit === u ? 'var(--accent-soft-fg)' : 'var(--fg2)',
                    borderColor: unit === u ? 'var(--accent)' : 'var(--border)',
                  }}
                >
                  {u}
                </button>
              ))}
            </div>
          </div>

          {/* Required nutrients */}
          <div>
            <label style={{ ...labelStyle, marginBottom: 8 }}>Nutrients per 100{unit}</label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <div>
                <label style={labelStyle}>Calories (kcal) *</label>
                <input
                  value={kcal}
                  onChange={e => { setKcal(e.target.value); setKcalError('') }}
                  placeholder="0"
                  type="number"
                  min="0"
                  style={{ ...inputStyle, borderColor: kcalError ? 'var(--danger-fg, #c0392b)' : undefined }}
                />
                {kcalError && <div style={errorStyle}>{kcalError}</div>}
              </div>
              <div>
                <label style={labelStyle}>Protein (g)</label>
                <input value={protein} onChange={e => setProtein(e.target.value)} placeholder="0" type="number" min="0" style={inputStyle} />
              </div>
              <div>
                <label style={labelStyle}>Carbs (g)</label>
                <input value={carbs} onChange={e => setCarbs(e.target.value)} placeholder="0" type="number" min="0" style={inputStyle} />
              </div>
              <div>
                <label style={labelStyle}>Fat (g)</label>
                <input value={fat} onChange={e => setFat(e.target.value)} placeholder="0" type="number" min="0" style={inputStyle} />
              </div>
            </div>
          </div>

          {/* Optional nutrients */}
          <div>
            <button
              onClick={() => setShowMore(v => !v)}
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--fg3)',
                fontSize: 12,
                fontFamily: 'var(--font-body)',
                fontWeight: 600,
                padding: 0,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              <WIcon d={showMore ? WI.chevL : WI.chevR} size={14} />
              {showMore ? 'Show less' : 'Show more nutrients'}
            </button>
            {showMore && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 10 }}>
                <div>
                  <label style={labelStyle}>Fiber (g)</label>
                  <input value={fiber} onChange={e => setFiber(e.target.value)} placeholder="0" type="number" min="0" style={inputStyle} />
                </div>
                <div>
                  <label style={labelStyle}>Sugar (g)</label>
                  <input value={sugar} onChange={e => setSugar(e.target.value)} placeholder="0" type="number" min="0" style={inputStyle} />
                </div>
                <div>
                  <label style={labelStyle}>Sodium (mg)</label>
                  <input value={sodium} onChange={e => setSodium(e.target.value)} placeholder="0" type="number" min="0" style={inputStyle} />
                </div>
                <div>
                  <label style={labelStyle}>Sat. fat (g)</label>
                  <input value={satFat} onChange={e => setSatFat(e.target.value)} placeholder="0" type="number" min="0" style={inputStyle} />
                </div>
              </div>
            )}
          </div>

          {/* Variants */}
          <div>
            <label style={{ ...labelStyle, marginBottom: 8 }}>Serving variants</label>
            {variants.map(v => (
              <div key={v.id} style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <input
                    value={v.label}
                    onChange={e => updateVariant(v.id, 'label', e.target.value)}
                    placeholder="e.g. 1 cup"
                    style={inputStyle}
                  />
                </div>
                <div style={{ width: 80 }}>
                  <input
                    value={v.weight}
                    onChange={e => updateVariant(v.id, 'weight', e.target.value)}
                    placeholder={unit}
                    type="number"
                    min="0"
                    style={{ ...inputStyle, borderColor: v.error ? 'var(--danger-fg, #c0392b)' : undefined }}
                  />
                </div>
                <button
                  onClick={() => removeVariant(v.id)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    color: 'var(--fg3)',
                    padding: '8px 4px',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <WIcon d={WI.close} size={14} />
                </button>
                {v.error && <div style={errorStyle}>{v.error}</div>}
              </div>
            ))}
            <button
              onClick={addVariant}
              style={{
                background: 'transparent',
                border: '1px dashed var(--border)',
                borderRadius: 8,
                padding: '7px 12px',
                fontFamily: 'var(--font-body)',
                fontSize: 12,
                fontWeight: 600,
                color: 'var(--fg3)',
                cursor: 'pointer',
                width: '100%',
              }}
            >
              + Add variant
            </button>
          </div>

          {apiError && (
            <div style={{
              background: 'var(--danger-soft-bg, #fef2f2)',
              border: '1px solid var(--danger-soft-border, #fca5a5)',
              borderRadius: 8,
              padding: '10px 12px',
              fontSize: 12,
              color: 'var(--danger-fg, #c0392b)',
            }}>
              {apiError}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          flexShrink: 0,
          padding: '16px 20px',
          borderTop: '1px solid var(--border-soft)',
        }}>
          <Button
            variant="primary"
            onClick={handleSubmit}
            disabled={mutation.isPending}
            style={{ width: '100%', justifyContent: 'center' }}
          >
            {mutation.isPending ? 'Adding…' : 'Add to library'}
          </Button>
        </div>
      </div>
    </div>
  )
}
