import { useEffect, useState } from 'react'
import { api, useApi } from '../api'
import { Stamp } from '../ui/Stamp'
import { ChainFooter } from '../ui/ChainFooter'

export function RuleLab() {
  const rules = useApi<any>('/rules')
  const [v, setV] = useState(4.0); const [res, setRes] = useState<any>(null); const [rp2, setRp] = useState<any>(null)
  useEffect(() => { const t = setTimeout(() => api('/rules/simulate', { method: 'POST', json: { rule_id: 'AREA_PER_SEAT', param: 'min_sqm_per_seat', value: v } }).then(setRes), 60); return () => clearTimeout(t) }, [v])
  return (
    <main style={{ paddingTop: 18 }}>
      <div className="t xs up dim">Rule lab · versioned rules are data</div><h1 style={{ fontSize: '1.8rem' }}>Preview a rule change before it is issued</h1>
      <div className="slip ink rules" data-no="RULE DIAL · AREA_PER_SEAT" style={{ marginTop: 16, borderRightStyle: 'solid' }}>
        <div className="row between"><span>Minimum built-up area per seat</span><b className="t" style={{ fontSize: '1.6rem' }}>{v.toFixed(1)} sq m</b></div>
        <input type="range" min="2" max="7" step="0.1" value={v} onChange={e => setV(+e.target.value)} style={{ width: '100%', accentColor: 'var(--ink)' }} aria-label="Minimum area per seat" />
        <div className="row between xs t dim"><span>2.0</span><span>current rule 4.0 (illustrative)</span><span>7.0</span></div>
        {res && <div style={{ marginTop: 10 }}><span style={{ fontFamily: 'var(--serif)', fontSize: '1.4rem' }}>{res.count} of {res.total}</span> <span className="sm">peer institutions would change status. Nothing is applied.</span>
          <div className="t xs dim" style={{ marginTop: 4 }}>{res.first10.join('  ') || 'no change at this value'}</div></div>}
      </div>
      <div className="grid2" style={{ marginTop: 18 }}>
        <div className="slip" data-no="REPLAY · F-014" style={{ borderRightStyle: 'solid' }}>
          <button className="btn" onClick={async () => setRp(await api('/replay', { method: 'POST' }))}>Replay under rule v1.1 (illustrative)</button>
          {rp2 && <table className="ledger sm" style={{ marginTop: 8 }}><thead><tr><th>rule version</th><th className="num">min sq m / seat</th><th>result</th></tr></thead><tbody>
            <tr><td className="t">{rp2.v1.version}</td><td className="num">{rp2.v1.param.toFixed(1)}</td><td><Stamp state={rp2.v1.state} /></td></tr><tr><td className="t">{rp2.v1_1.version}</td><td className="num">{rp2.v1_1.param.toFixed(1)}</td><td><Stamp state={rp2.v1_1.state} /></td></tr></tbody></table>}
          <div className="xs dim" style={{ marginTop: 6 }}>Replay re-runs the stored case under another rule version. The stored decision is untouched.</div></div>
        <div className="slip" data-no="RULES IN eoa_v1" style={{ borderRightStyle: 'solid' }}>{rules.data?.rules.map((r: any) => <div key={r.id} className="row between sm" style={{ padding: '3px 0', borderBottom: '1px dotted var(--rule)' }}><span className="t">{r.id}</span><span className="xs dim">{r.severity} · rung {r.required_rung} · {r.clause.doc} ref {r.clause.ref}</span></div>)}</div>
      </div>
    </main>
  )
}

export function Alerts() {
  const a = useApi<any>('/alerts')
  const lab: Record<string, string> = { expiry_inside_semester: 'Document expires inside the semester', source_unavailable: 'Issuer source unavailable', anomaly_raised: 'Unusual compared with peers', bundle_awaiting_institution: 'Bundle awaiting institution response' }
  return (
    <main style={{ paddingTop: 18 }}><div className="t xs up dim">Alert centre</div><h1 style={{ fontSize: '1.8rem' }}>Alerts</h1>
      <table className="ledger" style={{ marginTop: 14 }}><thead><tr><th>no.</th><th>alert</th><th>owner</th><th className="num">due</th><th>ref</th><th>status</th></tr></thead><tbody>
        {a.data?.alerts.map((x: any) => <tr key={x.id}><td className="t">{x.id}</td><td>{lab[x.kind] ?? x.kind}</td><td className="t xs">{x.owner_role}</td><td className="num">{x.due}</td><td className="t">{x.ref}</td><td className="t xs up">{x.status}</td></tr>)}</tbody></table></main>)
}

export function AuditPage() {
  const l = useApi<any[]>('/audit')
  return (
    <main style={{ paddingTop: 18 }}><div className="t xs up dim">Audit · hash chain</div><h1 style={{ fontSize: '1.8rem' }}>Every act, in order, sealed to the one before it</h1>
      <table className="ledger sm" style={{ marginTop: 14 }}><thead><tr><th className="num">seq</th><th>actor</th><th>event</th><th>hash (first 16)</th></tr></thead><tbody>
        {l.data?.map(e => <tr key={e.seq}><td className="num">{e.seq}</td><td className="t">{e.event.actor}</td><td className="t">{e.event.event}</td><td className="t xs">{e.hash.slice(0, 16)}</td></tr>)}</tbody></table>
      <ChainFooter /></main>)
}

export function Results() {
  const r = useApi<any>('/eval/summary')
  if (!r.data) return <p className="t" style={{ paddingTop: 20 }}>Counting…</p>
  return (
    <main style={{ paddingTop: 18 }}><div className="t xs up dim">Measured results · computed from ground_truth.json when this page loads</div><h1 style={{ fontSize: '1.8rem' }}>What the system found, against what was planted</h1>
      <div className="row" style={{ gap: 30, margin: '16px 0' }}>
        <div><div style={{ font: '700 3rem var(--serif)' }}>{r.data.found}<span className="dim" style={{ fontSize: '1.6rem' }}> / {r.data.planted}</span></div><div className="xs t dim">planted issues found</div></div>
        <div><div style={{ font: '700 3rem var(--serif)' }}>{r.data.false_positives}</div><div className="xs t dim">valid-but-unusual documents wrongly failed</div></div></div>
      <table className="ledger sm"><thead><tr><th>id</th><th>planted problem</th><th>finding</th><th>result</th></tr></thead><tbody>
        {r.data.rows.map((p: any) => <tr key={p.id}><td className="t">{p.id}</td><td>{p.what}</td><td className="t">{p.expect_finding}</td><td><Stamp state={p.found ? 'PASSED' : 'FAILED'} /></td></tr>)}</tbody></table>
      <p className="xs dim" style={{ maxWidth: 660, marginTop: 12 }}>Synthetic results show that the workflow is correct. They are not a claim about accuracy on real institutions.</p></main>)
}
