import type { DiaryDay, DiaryMeal, DiaryEntry } from '../../types/api'
import { ConfidenceBadge } from '../../components/ConfidenceBadge'
import { useSkipMeal, useUnskipMeal } from '../../hooks/useEntries'
import { useMeals } from '../../hooks/useMeals'

export interface DiaryCardProps {
  day: DiaryDay | undefined
  isLoading: boolean
  onAddFood: (mealId: string) => void
  onEditEntry?: (entryId: string) => void
  selectedDate: string
}

function formatEntryTime(isoStr: string): string {
  const d = new Date(isoStr)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function entryKcal(entry: DiaryEntry): number {
  return Number(entry.nutrients['calories_kcal']?.value) || 0
}

const dashedButtonStyle: React.CSSProperties = {
  background: 'transparent',
  border: '1px dashed var(--border-strong)',
  padding: '7px 12px',
  borderRadius: 8,
  fontFamily: 'var(--font-body)',
  fontSize: 12,
  fontWeight: 500,
  color: 'var(--fg2)',
  cursor: 'pointer',
}

function SkeletonSection({ isFirst }: { isFirst: boolean }) {
  return (
    <div style={{
      padding: '14px 18px',
      borderTop: isFirst ? 0 : '1px solid var(--border-soft)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: 8, borderBottom: '1px solid var(--border-soft)', marginBottom: 2 }}>
        <div style={{ width: 90, height: 18, borderRadius: 4, background: 'var(--border)' }} />
        <div style={{ width: 80, height: 12, borderRadius: 4, background: 'var(--border)' }} />
      </div>
      {[0, 1].map(i => (
        <div key={i} style={{ display: 'grid', gridTemplateColumns: '60px 1fr auto auto', gap: 16, alignItems: 'center', padding: '10px 0', borderBottom: i === 1 ? 0 : '1px dashed var(--border-soft)' }}>
          <div style={{ height: 13, borderRadius: 4, background: 'var(--border)' }} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ height: 14, borderRadius: 4, background: 'var(--border)' }} />
            <div style={{ width: 70, height: 18, borderRadius: 99, background: 'var(--border)' }} />
          </div>
          <div style={{ width: 52, height: 14, borderRadius: 4, background: 'var(--border)' }} />
          <div style={{ width: 52, height: 14, borderRadius: 4, background: 'var(--border)' }} />
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
  isFirst: boolean
  onAddFood: (mealId: string) => void
  onEditEntry?: (entryId: string) => void
  onSkip: (mealId: string) => void
  onUnskip: (mealId: string) => void
}

function MealSection({ mealId, mealName, isSkipped, entries, isFirst, onAddFood, onEditEntry, onSkip, onUnskip }: MealSectionProps) {
  const isEmpty = entries.length === 0

  const sectionStyle: React.CSSProperties = {
    padding: '14px 18px',
    borderTop: isFirst ? 0 : '1px solid var(--border-soft)',
  }

  const nameStyle: React.CSSProperties = {
    fontFamily: 'var(--font-display)',
    fontStyle: 'italic',
    fontSize: 17,
    color: 'var(--fg3)',
    lineHeight: 1,
  }

  if (isSkipped) {
    return (
      <div
        style={{ ...sectionStyle, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 14 }}
        data-testid={`meal-section-${mealName.toLowerCase()}`}
      >
        <span style={nameStyle}>{mealName}</span>
        <button style={dashedButtonStyle} onClick={() => onUnskip(mealId)}>
          Eating after all
        </button>
      </div>
    )
  }

  if (isEmpty) {
    return (
      <div
        style={{ ...sectionStyle, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 14 }}
        data-testid={`meal-section-${mealName.toLowerCase()}`}
      >
        <span style={nameStyle}>{mealName}</span>
        <div style={{ display: 'flex', gap: 6 }}>
          <button style={dashedButtonStyle} onClick={() => onAddFood(mealId)}>
            + Add food
          </button>
          <button style={dashedButtonStyle} onClick={() => onSkip(mealId)}>
            Not eating
          </button>
        </div>
      </div>
    )
  }

  const mealKcalTotal = entries.reduce((sum, e) => sum + entryKcal(e), 0)
  const mealGTotal = entries.reduce((sum, e) => sum + (Number(e.weight_g) || 0), 0)
  const hasEstimated = entries.some(e => e.weight_confidence === 'estimated')

  return (
    <div style={sectionStyle} data-testid={`meal-section-${mealName.toLowerCase()}`}>
      {/* Meal header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'baseline',
        gap: 12,
        padding: '4px 4px 8px',
        borderBottom: '1px solid var(--border-soft)',
      }}>
        <span style={{
          fontFamily: 'var(--font-display)',
          fontStyle: 'italic',
          fontSize: 18,
          color: 'var(--fg1)',
          letterSpacing: '-0.01em',
          lineHeight: 1,
        }}>
          {mealName}
        </span>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: 'var(--fg3)',
          fontVariantNumeric: 'tabular-nums',
          whiteSpace: 'nowrap',
          flexShrink: 0,
        }}>
          {hasEstimated && <span style={{ color: 'var(--confidence-estimated-fg)' }}>~</span>}
          <b style={{ color: 'var(--fg1)', fontWeight: 500 }}>{Math.round(mealKcalTotal).toLocaleString()}</b>
          {' kcal · '}
          <b style={{ color: 'var(--fg1)', fontWeight: 500 }}>{Math.round(mealGTotal)}</b>
          {' g'}
        </span>
      </div>

      {/* Entry rows */}
      {entries.map((entry, i) => {
        const isEstimated = entry.weight_confidence === 'estimated'
        const isMeasured = entry.weight_confidence === 'measured'
        const isLast = i === entries.length - 1
        const nameColor = isEstimated ? 'var(--confidence-estimated-fg)' : 'var(--fg1)'
        const nameFontStyle = isEstimated ? 'italic' : 'normal'
        const nameFontWeight = isMeasured ? 600 : 400
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
            role="button"
            tabIndex={0}
            onClick={() => onEditEntry?.(entry.id)}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onEditEntry?.(entry.id) }}
            style={{
              display: 'grid',
              gridTemplateColumns: '60px 1fr auto auto auto',
              columnGap: 24,
              rowGap: 0,
              alignItems: 'center',
              padding: '10px 0',
              borderBottom: isLast ? 0 : '1px dashed var(--border-soft)',
              cursor: onEditEntry ? 'pointer' : undefined,
              outline: 'none',
            }}
          >
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 13,
              color: 'var(--fg3)',
              fontVariantNumeric: 'tabular-nums',
            }}>
              {formatEntryTime(entry.eaten_at)}
            </span>

            {/* dot + name only — no truncation */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
              <span style={{
                width: 7,
                height: 7,
                borderRadius: '50%',
                background: dotColor,
                flexShrink: 0,
              }} />
              <span style={{
                fontSize: 14,
                fontWeight: nameFontWeight,
                color: nameColor,
                fontStyle: nameFontStyle,
              }}>
                {entry.food_name}
              </span>
            </div>

            {/* badge in its own column so it aligns across rows */}
            <div>
              <ConfidenceBadge level={entry.weight_confidence}>
                {entry.input_method}
              </ConfidenceBadge>
            </div>

            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 14,
              color: isEstimated ? 'var(--confidence-estimated-fg)' : 'var(--fg1)',
              fontVariantNumeric: 'tabular-nums',
              minWidth: 60,
              textAlign: 'right',
              whiteSpace: 'nowrap',
            }}>
              {isEstimated && '~'}{Math.round(weightVal)}{' '}
              <span style={{ color: 'var(--fg3)', fontSize: 11 }}>g</span>
            </div>

            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 14,
              color: isEstimated ? 'var(--confidence-estimated-fg)' : 'var(--fg1)',
              fontVariantNumeric: 'tabular-nums',
              minWidth: 70,
              textAlign: 'right',
              whiteSpace: 'nowrap',
            }}>
              {isEstimated && '~'}{Math.round(kcalVal)}{' '}
              <span style={{ color: 'var(--fg3)', fontSize: 11 }}>kcal</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export function DiaryCard({ day, isLoading, onAddFood, onEditEntry, selectedDate }: DiaryCardProps) {
  const skipMeal = useSkipMeal()
  const unskipMeal = useUnskipMeal()
  const { data: meals } = useMeals()

  const handleSkip = (mealId: string) => skipMeal.mutate({ date: selectedDate, mealId })
  const handleUnskip = (mealId: string) => unskipMeal.mutate({ date: selectedDate, mealId })

  const cardStyle: React.CSSProperties = {
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 14,
    boxShadow: 'var(--shadow-2)',
    overflow: 'hidden',
  }

  if (isLoading) {
    return (
      <div style={cardStyle}>
        {[0, 1, 2, 3].map(i => <SkeletonSection key={i} isFirst={i === 0} />)}
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
    <div style={cardStyle} data-testid="diary-card">
      {diaryMeals.map((meal, i) => (
        <MealSection
          key={meal.meal_id}
          mealId={meal.meal_id}
          mealName={meal.meal_name}
          isSkipped={meal.is_skipped}
          entries={meal.entries}
          isFirst={i === 0}
          onAddFood={onAddFood}
          onEditEntry={onEditEntry}
          onSkip={handleSkip}
          onUnskip={handleUnskip}
        />
      ))}
    </div>
  )
}
