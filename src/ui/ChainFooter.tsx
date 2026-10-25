import { useState } from 'react'
import { api, useApi } from '../api'
import { useContext } from 'react'
import { AppCtx } from '../ctx'

export function ChainFooter() {
  const { bump } = useContext(AppCtx)
  const { data } = useApi<any>('/audit/verify')
  const [fresh, setFresh] = useState<any>(null)
  const v = fresh ?? data
  const verify = async () => setFresh(await api('/audit/verify'))
  const tamper = async () => { await api('/audit/_tamper', { method: 'POST' }); setFresh(null); bump() }
  const repair = async () => { await api('/audit/_repair', { method: 'POST' }); setFresh(null); bump() }
  if (!v) return null
  return (
    <div className="slip dbl row between" style={{ marginTop: 18, borderRightStyle: 'solid', flexWrap: 'wrap' }}>
      <span className="t sm">{v.intact ? <><b style={{ color: 'var(--ok)' }}>Audit chain intact</b> · {v.entries} entries · head {v.head.slice(0, 12)}…</> : <b style={{ color: 'var(--stamp)' }}>CHAIN BROKEN at entry {v.first_broken_seq}: a stored record no longer matches its hash</b>}</span>
      <span className="row"><button className="btn" onClick={verify}>Verify</button><button className="btn red" onClick={tamper} title="Demo only: edits one stored record">Tamper (demo)</button>{!v.intact && <button className="btn" onClick={repair}>Reset (demo)</button>}</span>
    </div>
  )
}
