import { useDiary } from '../../hooks/useDiary'
import { Button } from '../../components/Button'
import { WIcon, WI } from '../../components/Icon'
import { addDays, formatDateLabel } from '../../utils/dates'
import { WeekStrip } from './WeekStrip'
import { SummaryCard } from './SummaryCard'
import { DiaryCard } from './DiaryCard'

export interface TodayViewProps {
  onOpenLog: (mealId?: string) => void
  onEditEntry: (entryId: string) => void
  selectedDate: string
  onDateChange: (d: string) => void
}

export function TodayView({ onOpenLog, onEditEntry, selectedDate, onDateChange }: TodayViewProps) {
  const { data: day, isLoading } = useDiary(selectedDate)

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
    }}>
      {/* Sticky header */}
      <div style={{
        flexShrink: 0,
        padding: '28px 32px 0',
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        background: 'var(--bg)',
      }}>
        {/* Date nav row */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <button
              data-testid="prev-day"
              onClick={() => onDateChange(addDays(selectedDate, -1))}
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--fg2)',
                padding: 4,
                display: 'flex',
                alignItems: 'center',
                borderRadius: 6,
              }}
            >
              <WIcon d={WI.chevL} size={20} />
            </button>

            <h1 style={{
              fontFamily: 'var(--font-display)',
              fontStyle: 'italic',
              fontSize: 28,
              fontWeight: 400,
              color: 'var(--fg1)',
              margin: 0,
              lineHeight: 1.1,
            }}>
              {formatDateLabel(selectedDate)}
            </h1>

            <button
              data-testid="next-day"
              onClick={() => onDateChange(addDays(selectedDate, 1))}
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--fg2)',
                padding: 4,
                display: 'flex',
                alignItems: 'center',
                borderRadius: 6,
              }}
            >
              <WIcon d={WI.chevR} size={20} />
            </button>
          </div>

          <Button variant="primary" onClick={() => onOpenLog()}>
            Log food
          </Button>
        </div>

        <WeekStrip selectedDate={selectedDate} onSelectDate={onDateChange} />
        <SummaryCard day={day} isLoading={isLoading} />

        {/* Bottom padding for header */}
        <div style={{ height: 4 }} />
      </div>

      {/* Scrollable body */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '20px 32px 48px',
      }}>
        <DiaryCard
          day={day}
          isLoading={isLoading}
          onAddFood={(mealId) => onOpenLog(mealId)}
          onEditEntry={onEditEntry}
          selectedDate={selectedDate}
        />
      </div>
    </div>
  )
}
