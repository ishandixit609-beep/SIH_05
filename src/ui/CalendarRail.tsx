const D = (s: string) => new Date(s + 'T00:00:00+05:30').getTime()
const fmt = (s: string) => new Date(D(s)).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'Asia/Kolkata' })

/** Academic calendar with expiry pins. A pin inside a semester gets a pulsing ring: that is the radar. */
export function CalendarRail({ tl }: { tl: any }) {
  const W = 940, H = 84, a = D('2027-01-01'), b = D('2028-06-30')
  const x = (s: string) => ((D(s) - a) / (b - a)) * (W - 20) + 10
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Academic calendar with document expiry pins" style={{ display: 'block' }}>
      <line x1="10" x2={W - 10} y1="52" y2="52" stroke="var(--ink)" strokeWidth="1" />
      {tl.semesters.map((s: any) => (
        <g key={s.name}>
          <rect x={x(s.start)} y="40" width={x(s.end) - x(s.start)} height="24" fill="var(--manila)" stroke="var(--ink)" />
          <text x={(x(s.start) + x(s.end)) / 2} y="55" textAnchor="middle" fontFamily="var(--type)" fontSize="14">{s.name}</text>
        </g>
      ))}
      <g><line x1={x(tl.today)} x2={x(tl.today)} y1="30" y2="72" stroke="var(--ink)" strokeDasharray="2 2" /><text x={x(tl.today) + 4} y="26" fontFamily="var(--type)" fontSize="14">today (demo clock) {fmt(tl.today)}</text></g>
      {tl.pins.map((p: any) => (
        <g key={p.doc}>
          {p.inside_semester && <circle cx={x(p.expires)} cy="52" r="9" fill="none" stroke="var(--warn)" strokeWidth="2"><animate attributeName="r" values="7;14;7" dur="2s" repeatCount="indefinite" /><animate attributeName="opacity" values="1;.2;1" dur="2s" repeatCount="indefinite" /></circle>}
          <path d={`M${x(p.expires)} 52 l-6 -16 h12 z`} fill={p.inside_semester ? 'var(--warn)' : 'var(--ink)'} stroke="var(--ink)" />
          <text x={x(p.expires)} y="16" textAnchor="middle" fontFamily="var(--type)" fontSize="14" fontWeight="700">{p.label} ends {fmt(p.expires)}{p.inside_semester ? ' (inside semester)' : ''}</text>
        </g>
      ))}
    </svg>
  )
}
