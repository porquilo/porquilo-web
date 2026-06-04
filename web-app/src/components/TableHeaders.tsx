interface TableHeadersProps {
  cols: string[]
  gridTemplateColumns: string
}

export function TableHeaders({ cols, gridTemplateColumns }: TableHeadersProps) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns,
      gap: 12,
      padding: '10px 18px',
      background: 'var(--bg-sunken)',
      borderBottom: '1px solid var(--border-soft)',
    }}>
      {cols.map((col, i) => (
        <div key={i} style={{
          fontSize: 10,
          color: 'var(--fg3)',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          fontWeight: 600,
        }}>
          {col}
        </div>
      ))}
    </div>
  )
}
