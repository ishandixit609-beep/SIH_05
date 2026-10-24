/** One clickable line: rule version > clause > page > field > finding > action. */
export function TraceRibbon({ trace, onGraph }: { trace: string[]; onGraph: () => void }) {
  return (
    <div className="ribbon" aria-label="Evidence trace">
      {trace.map((t, i) => <span key={i} className="row" style={{ gap: 4 }}>{i > 0 && <span className="sep">›</span>}<button>{t}</button></span>)}
      <button onClick={onGraph} style={{ marginLeft: 6, background: 'var(--ink)', color: 'var(--paper-hi)' }}>graph (G)</button>
    </div>
  )
}

export function GraphModal({ trace, onClose }: { trace: string[]; onClose: () => void }) {
  const kinds = ['rule version', 'rule', 'document page', 'claim', 'finding', 'next step']
  return (
    <>
      <div className="veil" onClick={onClose} />
      <div className="modal" role="dialog" aria-label="Evidence graph">
        <h3>Evidence graph</h3>
        <p className="xs dim">Every step written to the audit chain. Read top to bottom.</p>
        <svg viewBox={`0 0 460 ${trace.length * 54 + 10}`} width="100%">
          {trace.map((t, i) => (
            <g key={i} transform={`translate(30 ${i * 54 + 8})`}>
              {i > 0 && <line x1="200" x2="200" y1="-14" y2="0" stroke="var(--ink)" markerEnd="url(#a)" />}
              <rect width="400" height="34" fill="var(--paper)" stroke="var(--ink)" />
              <text x="10" y="21" fontFamily="var(--type)" fontSize="12" fontWeight="700">{t}</text>
              <text x="390" y="21" textAnchor="end" fontFamily="var(--type)" fontSize="9" fill="var(--ink-2)">{kinds[Math.min(i, kinds.length - 1)]}</text>
            </g>
          ))}
        </svg>
        <button className="btn" onClick={onClose}>Close (Esc)</button>
      </div>
    </>
  )
}
