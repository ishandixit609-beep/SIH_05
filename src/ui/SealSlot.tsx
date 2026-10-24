import { useState } from 'react'
import { api } from '../api'

/** The officer's decision area. The seal is withheld while any required check is open and unwaived.
    Approve stays pressable on purpose: the guard (server side) answers with HTTP 409 and the list. */
export function SealSlot({ cov, onWaive, onDone }: { cov: any; onWaive: (id: string) => void; onDone: (m: string) => void }) {
  const [err, setErr] = useState<{ msg: string; open: string[] } | null>(null)
  const open: string[] = cov.open_checks, ready = open.length === 0
  const send = async (action: string) => {
    setErr(null)
    try { await api(`/applications/APP-0001/decision`, { method: 'POST', json: { action } }); onDone(`Decision recorded: ${action.replace('_', ' ')} (officer act)`) }
    catch (e: any) { setErr({ msg: e.message, open: e.body?.open_checks ?? [] }) }
  }
  return (
    <section aria-label="Officer decision" className="slip ink human" data-no="ACTIONS">
      <div className="seal">
        <div className={`ring ${ready ? 'ready' : ''}`}>{ready ? <>READY<br />FOR<br />DECISION</> : <>SEAL<br />WITHHELD</>}</div>
        <div>
          <div style={{ fontSize: '1.05rem', fontWeight: 700 }}>{ready ? 'Ready for decision' : `Seal withheld: ${open.length} open check${open.length > 1 ? 's' : ''}`}</div>
          <div className="t xs dim">{ready ? 'Every required check is passed or has a written waiver.' : open.join('  ')}</div>
        </div>
      </div>
      {!ready && <div style={{ marginTop: 8 }}>{cov.requirements.filter((r: any) => open.includes(r.id)).map((r: any) => (
        <div key={r.id} className="row between sm" style={{ borderTop: '1px dotted var(--rule)', padding: '2px 0' }}><span><b className="t">{r.id}</b> {r.title}</span><button className="btn" style={{ padding: '0 6px' }} onClick={() => onWaive(r.id)}>waive <kbd>W</kbd></button></div>))}</div>}
      <div className="stack" style={{ marginTop: 12 }}>
        <button className="act ok" onClick={() => send('approve')}>Approve (officer decision)</button>
        <button className="act info" onClick={() => send('request_info')}>Request info</button>
        <button className="act no" onClick={() => send('reject')}>Reject</button>
      </div>
      {err && <div role="alert" className="err" style={{ marginTop: 8 }}>HTTP 409. {err.msg}<br />Open: {err.open.join(', ')}</div>}
    </section>
  )
}
