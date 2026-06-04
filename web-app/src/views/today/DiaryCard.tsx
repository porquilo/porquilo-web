import type { DiaryDay, DiaryMeal, DiaryEntry } from '../../types/api'
import { ConfidenceBadge } from '../../components/ConfidenceBadge'
import { Button } from '../../components/Button'
import { useSkipMeal, useUnskipMeal } from '../../hooks/useEntries'
import { useMeals } from '../../hooks/useMeals'

export interface DiaryCardProps {
  day: DiaryDay | undefined
  isLoading: boolean
  onAddFood: (mealId: string) => void
  selectedDate: string
}

function formatEntryTime(isoStr: string): string {
  const d = new Date(isoStr)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function entryKcal(entry: DiaryEntry): number {
  return entry.nutrients['energy_kcal']?.value ?? 0
}

function SkeletonMeal() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ width: 100, height: 18, borderRadius: 4, background: 'var(--border)' }} />
        <div style={{ width: 60, height: 14, borderRadius: 4, background: 'var(--border)' }} />
      </div>
      {[0, 1].map(i => (
        <div key={i} style={{ display: 'grid', gridTemplateColumns: '52px 1fr 60px 52px', gap: 12, alignItems: 'center' }}>
          <div style={{ height: 12, borderRadius: 4, background: 'var(--border)' }} />
          <div style={{ height: 14, borderRadius: 4, background: 'var(--border)' }} />
          <div style={{ height: 13, borderRadius: 4, background: 'var(--border)' }} />
          <div style={{ height: 13, borderRadius: 4, background: 'var(--border)' }} />
        </div>
      ))}
    </div>
  )
}

interface MealSectionProps {
  mealId: string
  mealName: string
  isSkipped: boolean
  entries: DiaryEntry[]
  selectedDate: string
  onAddFood: (mealId: string) => void
  onSkip: (mealId: string) => void
  onUnskip: (mealId: string) => void
}

function MealSection({ mealId, mealName, isSkipped, entries, selectedDate, onAddFood, onSkip, onUnskip }: MealSectionProps) {
  const isEmpty = entries.length === 0

  const dashedButtonStyle: React.CSSProperties = {
    border: '1.5px dashed var(--border)',
    background: 'transparent',
    color: 'var(--fg3)',
    fontSize: 12,
    fontFamily: 'var(--font-body)',
    fontWeight: 500,
    padding: '6px 14px',
    borderRadius: 8,
    cursor: 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
  }

  if (isSkipped) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <span style={{
          fontFamily: 'var(--font-display)',
          fontStyle: 'italic',
          fontSize: 16,
          color: 'var(--fg3)',
        }}>
          {mealName}
        </span>
        <div>
          <button style={dashedButtonStyle} onClick={() => onUnskip(mealId)}>
            Eating after all
          </button>
        </div>
      </div>
    )
  }

  if (isEmpty) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <span style={{
          fontFamily: 'var(--font-display)',
          fontStyle: 'italic',
          fontSize: 16,
          color: 'var(--fg3)',
        }}>
          {mealName}
        </span>
        <div style={{ display: 'flex', gap: 8 }}>
          <button style={dashedButtonStyle} onClick={() => onAddFood(mealId)}>
            Add food
          </button>
          <button style={dashedButtonStyle} onClick={() => onSkip(mealId)}>
            Not eating
          </button>
        </div>
      </div>
    )
  }

  const mealKcalTotal = entries.reduce((sum, e) => sum + entryKcal(e), 0)
  const mealGTotal = entries.reduce((sum, e) => sum + (e.weight_g ?? 0), 0)
  const hasEstimated = entries.some(e => e.weight_confidence === 'estimated')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {/* Meal header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'baseline',
        marginBottom: 6,
      }}>
        <span style={{
          fontFamily: 'var(--font-display)',
          fontStyle: 'italic',
          fontSize: 18,
          color: 'var(--fg1)',
        }}>
          {mealName}
        </span>
        <div style={{
          display: 'flex',
          gap: 12,
          fontFamily: 'var(--font-mono)',
          fontSize: 13,
          color: 'var(--fg2)',
          fontVariantNumeric: 'tabular-nums',
        }}>
          <span>
            {hasEstimated && <span style={{ color: 'var(--confidence-estimated-fg)' }}>~</span>}
            {Math.round(mealKcalTotal)} kcal
          </span>
          <span>{Math.round(mealGTotal)} g</span>
        </div>
      </div>

      {/* Entry rows */}
      {entries.map(entry => {
        const isEstimated = entry.weight_confidence === 'estimated'
        const isMeasured = entry.weight_confidence === 'measured'
        const nameColor = isEstimated ? 'var(--confidence-estimated-fg)' : 'var(--fg1)'
        const nameFontStyle = isEstimated ? 'italic' : 'normal'
        const nameFontWeight = isMeasured ? 700 : 400
        const dotColor = isEstimated
          ? 'var(--confidence-estimated-dot)'
          : isMeasured
            ? 'var(--confidence-measured-dot)'
            : 'var(--confidence-calculated-dot)'
        const kcalVal = entryKcal(entry)
        const weightVal = entry.weight_g ?? 0

        return (
          <div
            key={entry.id}
            style={{
              display: 'grid',
              gridTemplateColumns: '52px 1fr auto auto',
              gap: 12,
              alignItems: 'center',
              padding: '5px 0',
              borderTop: '1px solid var(--border-soft)',
            }}
          >
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              color: 'var(--fg3)',
              fontVariantNumeric: 'tabular-nums',
            }}>
              {formatEntryTime(entry.eaten_at)}
            </span>

            <div style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
              <span style={{
                width: 7,
                height: 7,
                borderRadius: '50%',
                background: dotColor,
                flexShrink: 0,
              }} />
              <span style={{
                fontSize: 13,
                color: nameColor,
                fontStyle: nameFontStyle,
                fontWeight: nameFontWeight,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}>
                {entry.food_name}
              </span>
              <ConfidenceBadge level={entry.weight_confidence}>
                {entry.input_method}
              </ConfidenceBadge>
            </div>

            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 13,
              color: isEstimated ? 'var(--confidence-estimated-fg)' : 'var(--fg2)',
              fontVariantNumeric: 'tabular-nums',
              textAlign: 'right',
              whiteSpace: 'nowrap',
            }}>
              {isEstimated && '~'}{Math.round(weightVal)} g
            </span>

            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 13,
              color: isEstimated ? 'var(--confidence-estimated-fg)' : 'var(--fg2)',
              fontVariantNumeric: 'tabular-nums',
              textAlign: 'right',
              whiteSpace: 'nowrap',
            }}>
              {isEstimated && '~'}{Math.round(kcalVal)}
            </span>
          </div>
        )
      })}
    </div>
  )
}

export function DiaryCard({ day, isLoading, onAddFood, selectedDate }: DiaryCardProps) {
  const skipMeal = useSkipMeal()
  const unskipMeal = useUnskipMeal()
  const { data: meals } = useMeals()

  const handleSkip = (mealId: string) => {
    skipMeal.mutate({ date: selectedDate, mealId })
  }
  const handleUnskip = (mealId: string) => {
    unskipMeal.mutate({ date: selectedDate, mealId })
  }

  if (isLoading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
        {[0, 1, 2, 3].map(i => <SkeletonMeal key={i} />)}
      </div>
    )
  }

  let diaryMeals: DiaryMeal[]

  if (day) {
    diaryMeals = day.meals
  } else {
    diaryMeals = (meals ?? []).map(m => ({
      meal_id: m.id,
      meal_name: m.name,
      is_skipped: false,
      entries: [],
      meal_totals: {},
    }))
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {diaryMeals.map(meal => (
        <MealSection
          key={meal.meal_id}
          mealId={meal.meal_id}
          mealName={meal.meal_name}
          isSkipped={meal.is_skipped}
          entries={meal.entries}
          selectedDate={selectedDate}
          onAddFood={onAddFood}
          onSkip={handleSkip}
          onUnskip={handleUnskip}
        />
      ))}
    </div>
  )
}
