import { Link } from 'react-router-dom'
import { useApi } from '../api'
import { FoldStack } from '../ui/FoldStack'
import { Stamp } from '../ui/Stamp'
import { BundleCard } from '../ui/DiffBundle'
import { useContext } from 'react'
import { AppCtx } from '../ctx'
import { num } from '../lib/format'

export function Inbox() {
  const { lang } = useContext(AppCtx)
  const s = useApi<any>('/applications/APP-0001/summary'); const c = useApi<any>('/applications/APP-0001/claims'); const f = useApi<any>('/findings'); const a = useApi<any>('/alerts')
  if (!s.data || !c.data || !f.data) return <p className="t" style={{ paddingTop: 20 }}>Opening the docket…</p>
  const fins: any[] = f.data.findings.filter((x: any) => !x.resolved)
  const unexplained = c.data.claims.filter((x: any) => x.bucket === 'CHANGED_NO_EXPLANATION')
  const red = fins.filter(x => x.state === 'FAILED'), amber = fins.filter(x => x.state !== 'FAILED' && !x.decision)
  const counts = c.data.counts
  return (
    <main style={{ paddingTop: 18 }}>
      <div className="row between" style={{ alignItems: 'flex-end' }}>
        <div><div className="t xs up dim">Docket · reviewer queue</div><h1 style={{ fontSize: '1.9rem' }}>{s.data.institution.name}</h1>
          <div className="t sm dim">{s.data.id} · {s.data.category} · {s.data.cycle} · version {s.data.version} · {s.data.institution.state}</div></div>
        <Link to="/case" className="btn dark" style={{ textDecoration: 'none' }}>Open the case desk →</Link>
      </div>
      <hr className="rule" />
      <div className="grid2" style={{ marginTop: 14 }}>
        <div>
          <FoldStack claims={c.data.claims} sample={c.data.sample} />
          <table className="ledger" style={{ marginTop: 14 }}><thead><tr><th>Delta tally · 80 claims</th><th className="num">n</th><th>what happens</th></tr></thead><tbody>
            <tr><td className="t">UNCHANGED</td><td className="num">{counts.UNCHANGED}</td><td className="sm">folded, sampled, expiry re-tested</td></tr>
            <tr><td className="t">CHANGED, WITH EVIDENCE</td><td className="num">{counts.CHANGED_WITH_EVIDENCE}</td><td className="sm">checked against the supporting document</td></tr>
            <tr><td className="t" style={{ color: 'var(--stamp)' }}>CHANGED, NO EXPLANATION</td><td className="num"><b>{counts.CHANGED_NO_EXPLANATION}</b></td><td className="sm">red queue: needs the officer</td></tr>
            <tr><td className="t">NEW</td><td className="num">{counts.NEW}</td><td className="sm">full scrutiny, nothing to compare</td></tr></tbody></table>
        </div>
        <div className="stack">
          <div className="slip ink human" data-no="CASE STATE" style={{ borderRightStyle: 'solid' }}>
            <div className="row between"><span style={{ fontFamily: 'var(--serif)', fontSize: '1.15rem', fontWeight: 700 }}>{s.data.overall === 'READY_FOR_DECISION' ? 'Ready for decision' : 'Review incomplete'}</span><Stamp state={s.data.overall === 'READY_FOR_DECISION' ? 'PASSED' : 'MANUAL_REVIEW'} big /></div>
            <div className="t sm" style={{ marginTop: 6 }}>{s.data.open_checks.length} required checks open · {s.data.findings_open} findings awaiting a human · {a.data?.alerts.length ?? 0} alerts</div>
            <div className="xs dim" style={{ marginTop: 6 }}>Anomaly model (precomputed, offline): {s.data.anomaly.wording}. Largest deviation: <b className="t">{s.data.anomaly.top_feature.replace(/_/g, ' ')}</b>.</div>
          </div>
          <div className="slip ink rules" data-no="RED QUEUE" style={{ borderRightStyle: 'solid' }}>
            <div className="who rules">rules failed · {red.length + unexplained.length}</div>
            {red.map(x => <Link key={x.id} to={`/case?f=${x.id}`} className="row between sm" style={{ textDecoration: 'none', padding: '4px 0', borderBottom: '1px dotted var(--rule)' }}><span><b className="t">{x.id}</b> {x.explanation.slice(0, 70)}…</span><Stamp state="FAILED" /></Link>)}
            {unexplained.map((x: any) => <div key={x.key} className="row between sm" style={{ padding: '4px 0', borderBottom: '1px dotted var(--rule)' }}><span className="t">{x.key}: {num(x.prev)} → {num(x.value)}</span><span className="xs dim">no declared change</span></div>)}
          </div>
          <div className="slip ink human" data-no="AMBER QUEUE" style={{ borderRightStyle: 'solid' }}>
            <div className="who human">needs a human read · {amber.length}</div>
            {amber.slice(0, 7).map(x => <Link key={x.id} to={`/case?f=${x.id}`} className="row between sm" style={{ textDecoration: 'none', padding: '3px 0', borderBottom: '1px dotted var(--rule)' }}><span><b className="t">{x.id}</b> {x.rule_id.replace(/_/g, ' ').toLowerCase()}</span><Stamp state={x.state} /></Link>)}
          </div>
        </div>
      </div>
      {f.data.bundles.map((b: any) => <BundleCard key={b.id} b={b} fins={f.data.findings} lang={lang} />)}
    </main>
  )
}
