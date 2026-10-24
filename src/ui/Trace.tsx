/** One clickable line: rule version > clause > page > field > finding > action. */
export function TraceRibbon({ trace, onGraph }: { trace: string[]; onGraph: () => void }) {
  return (
    <div className="ribbon" aria-label="Evidence trace">
      {trace.map((t, i) => <span key={i} className="row" style={{ gap: 4 }}>{i > 0 && <span className="sep">›</span>}<button>{t}</button></span>)}
      <button onClick={onGraph} style={{ marginLeft: 6, background: 'var(--ink)', color: 'var(--paper-hi)' }}>graph (G)</button>
    </div>
  )
}

import { useApi } from '../api'

export function GraphModal({ trace, finding, onClose }: { trace: string[]; finding?: any; onClose: () => void }) {
  const audit = useApi<any[]>('/audit')
  const rows = (audit.data ?? []).filter(r => r.event?.payload?.finding && r.event.payload.finding === finding?.id)
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
        <div className="slip ink human" data-no="REVIEWER AUDIT TRAIL" style={{ borderRightStyle: 'solid', marginBottom: 10 }}>
          <div className="xs">Rule version applied: <b className="t">{finding?.rule_version ?? 'n/a'}</b> · rule <b className="t">{finding?.rule_id ?? 'n/a'}</b></div>
          {rows.length === 0 ? <div className="xs dim">No reviewer act recorded on this finding yet. Press Y, N or R on the case desk to record one.</div>
            : <table className="ledger xs"><tbody>{rows.map(r => <tr key={r.seq}><td className="num">{r.seq}</td><td className="t">{r.event.actor}</td><td className="t">{r.event.event}</td><td className="t">{r.hash.slice(0, 10)}</td></tr>)}</tbody></table>}
        </div>
        <button className="btn" onClick={onClose}>Close (Esc)</button>
      </div>
    </>
  )
}
