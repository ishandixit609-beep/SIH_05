/** Evidence ladder: three rising steps for rung 1-3 (rung 0 = all empty), dashed outline on the rung the requirement needs, red bar on conflict. */
export function Ladder({ rung, need, conflict }: { rung: number; need?: number; conflict?: boolean }) {
  const label = conflict ? 'Sources disagree' : ['Declared only', 'Document read', 'Matches record', 'Issuer verified'][rung]
  return (
    <span role="img" aria-label={`Evidence rung ${rung} of 3: ${label}`} title={`${label}${need ? ` (needs rung ${need})` : ''}`}>
      <span className="ladder">{[1, 2, 3].map(i => <i key={i} className={`${i <= rung ? 'on' : ''} ${need === i ? 'need' : ''}`} />)}{conflict && <b />}</span>
      <span className="t xs dim"> R{rung}</span>
    </span>
  )
}
