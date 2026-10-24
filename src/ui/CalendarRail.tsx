const D = (s: string) => new Date(s + 'T00:00:00+05:30').getTime()
const fmt = (s: string) => new Date(D(s)).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'Asia/Kolkata' })

/** Academic calendar with expiry pins. A pin inside a semester gets a pulsing ring: that is the radar. */
export function CalendarRail({ tl }: { tl: any }) {
  const W = 940, H = 64, a = D('2027-01-01'), b = D('2028-06-30')
  const x = (s: string) => ((D(s) - a) / (b - a)) * (W - 20) + 10
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Academic calendar with document expiry pins" style={{ display: 'block' }}>
      <line x1="10" x2={W - 10} y1="40" y2="40" stroke="var(--ink)" strokeWidth="1" />
      {tl.semesters.map((s: any) => (
        <g key={s.name}>
          <rect x={x(s.start)} y="30" width={x(s.end) - x(s.start)} height="20" fill="var(--manila)" stroke="var(--ink)" />
          <text x={(x(s.start) + x(s.end)) / 2} y="44" textAnchor="middle" fontFamily="var(--type)" fontSize="10">{s.name}</text>
        </g>
      ))}
      <g><line x1={x(tl.today)} x2={x(tl.today)} y1="22" y2="58" stroke="var(--ink)" strokeDasharray="2 2" /><text x={x(tl.today) + 4} y="20" fontFamily="var(--type)" fontSize="10">today (demo clock) {fmt(tl.today)}</text></g>
      {tl.pins.map((p: any) => (
        <g key={p.doc}>
          {p.inside_semester && <circle cx={x(p.expires)} cy="40" r="9" fill="none" stroke="var(--warn)" strokeWidth="2"><animate attributeName="r" values="7;14;7" dur="2s" repeatCount="indefinite" /><animate attributeName="opacity" values="1;.2;1" dur="2s" repeatCount="indefinite" /></circle>}
          <path d={`M${x(p.expires)} 40 l-5 -14 h10 z`} fill={p.inside_semester ? 'var(--warn)' : 'var(--ink)'} stroke="var(--ink)" />
          <text x={x(p.expires)} y="12" textAnchor="middle" fontFamily="var(--type)" fontSize="10" fontWeight="700">{p.label} ends {fmt(p.expires)}{p.inside_semester ? ' (inside semester)' : ''}</text>
        </g>
      ))}
    </svg>
  )
}
