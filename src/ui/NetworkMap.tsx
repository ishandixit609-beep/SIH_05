/** Two institutions joined through a hashed faculty token. Wording is always 'possible overlap, needs confirmation'. */
export function NetworkMap({ net }: { net: any }) {
  const [a, b] = net.nodes; const [ea, eb] = net.edges
  const range = (e: any) => `${e.from} to ${e.to ?? 'present'} · ${e.kind.replace('_', '-')}`
  return (
    <svg viewBox="0 0 860 300" width="100%" role="img" aria-label="Faculty overlap between two institutions">
      {[[0, a, ea], [600, b, eb]].map(([x, n, e]: any) => (
        <g key={n.id} transform={`translate(${x + 10} 90)`}>
          <rect width="240" height="110" fill="var(--paper-hi)" stroke="var(--ink)" strokeWidth="1.5" /><rect x="5" y="5" width="230" height="100" fill="none" stroke="var(--ink)" strokeDasharray="2 3" />
          <text x="14" y="30" fontFamily="var(--serif)" fontWeight="700" fontSize="13">{n.name.split(',')[0]}</text>
          <text x="14" y="48" fontFamily="var(--type)" fontSize="11">{n.name.split(',')[1]?.trim() ?? ''}</text>
          <text x="14" y="76" fontFamily="var(--type)" fontSize="10">{n.id}</text><text x="14" y="94" fontFamily="var(--type)" fontSize="10">{range(e)}</text>
        </g>
      ))}
      <line x1="250" y1="145" x2="360" y2="145" stroke="var(--ink)" strokeWidth="2" /><line x1="500" y1="145" x2="610" y2="145" stroke="var(--ink)" strokeWidth="2" />
      <g transform="translate(360 105)"><path d="M0 40 L20 0 H120 L140 40 L120 80 H20 Z" fill="var(--manila)" stroke="var(--ink)" strokeWidth="1.5" />
        <text x="70" y="30" textAnchor="middle" fontFamily="var(--type)" fontSize="10">faculty token</text><text x="70" y="48" textAnchor="middle" fontFamily="var(--type)" fontWeight="700" fontSize="14">{net.label}</text>
        <text x="70" y="66" textAnchor="middle" fontFamily="var(--type)" fontSize="8" fill="var(--ink-2)">{net.token}</text></g>
      <text x="430" y="40" textAnchor="middle" fontFamily="var(--serif)" fontStyle="italic" fontSize="15">possible overlap, needs confirmation</text>
      <text x="430" y="58" textAnchor="middle" fontFamily="var(--type)" fontSize="11">both full-time from {net.overlaps[0]?.overlap_from}</text>
      <text x="430" y="250" textAnchor="middle" fontFamily="var(--type)" fontSize="10" fill="var(--ink-2)">HMAC-SHA256 token. The raw faculty ID is never stored. Part-time and visiting posts are not flagged.</text>
    </svg>
  )
}
