import { Link } from 'react-router-dom'
import { useApi } from '../api'
import { FoldStack } from '../ui/FoldStack'
import { Stamp } from '../ui/Stamp'
import { BundleCard } from '../ui/DiffBundle'
import { Donut, Legend, CoverageBars, Scatter, type Part } from '../ui/Charts'
import { PhotoEvidence } from '../ui/PhotoEvidence'
import { Workflow, type Step } from '../ui/Workflow'
import { useContext, useEffect, useState } from 'react'
import { AppCtx } from '../ctx'
import { num } from '../lib/format'

export function Inbox() {
  const { lang } = useContext(AppCtx)
  const s = useApi<any>('/applications/APP-0001/summary'); const c = useApi<any>('/applications/APP-0001/claims'); const f = useApi<any>('/findings'); const a = useApi<any>('/alerts')
  const cov = useApi<any>('/applications/APP-0001/coverage'); const ph = useApi<any>('/applications/APP-0001/photos')
  const [peers, setPeers] = useState<any[]>([]); const [pick, setPick] = useState<number | null>(null)
  useEffect(() => { fetch('/fixtures/peers.json').then(r => r.json()).then(setPeers).catch(() => setPeers([])) }, [])
  if (!s.data || !c.data || !f.data) return <p className="t" style={{ paddingTop: 20 }}>Opening the docket…</p>
  const fins: any[] = f.data.findings.filter((x: any) => !x.resolved)
  const unexplained = c.data.claims.filter((x: any) => x.bucket === 'CHANGED_NO_EXPLANATION')
  const red = fins.filter(x => x.state === 'FAILED'), amber = fins.filter(x => x.state !== 'FAILED' && !x.decision)
  const counts = c.data.counts; const total = Object.values(counts).reduce((x: number, y: any) => x + y, 0) as number
  const parts: Part[] = [{ label: 'Unchanged, carried forward', value: counts.UNCHANGED, color: 'var(--acc)' }, { label: 'Changed, with evidence', value: counts.CHANGED_WITH_EVIDENCE, color: 'var(--rules)' },
    { label: 'Changed, no explanation', value: counts.CHANGED_NO_EXPLANATION, color: 'var(--stamp)' }, { label: 'New', value: counts.NEW, color: 'var(--warn)' }]
  const val = (k: string) => c.data.claims.find((x: any) => x.key === k)?.value as number | undefined
  const meI = val('intake.total'), meF = val('faculty.count')
  const pts = peers.map(p => ({ x: p.claims['intake.total'], y: p.claims['faculty.count'] })).filter(p => p.x && p.y)
  const reqs: any[] = cov.data?.requirements ?? []
  const steps: Step[] = [
    { n: 1, who: 'human', title: 'Institution uploads', big: `${reqs.length} requirements`, line: 'documents uploaded and dry-run checked before submission' },
    { n: 2, who: 'ai', title: 'AI reads the PDFs', big: `${total} claims`, line: 'values lifted from the page; page and box are saved as proof' },
    { n: 3, who: 'rules', title: 'Delta engine', big: `${counts.UNCHANGED} skipped`, line: `${total - counts.UNCHANGED} changed or new are re-checked, a sample of the rest is re-verified` },
    { n: 4, who: 'rules', title: 'Rules decide', big: `${red.length} failed`, line: `${amber.length} more need a human read. The AI never decides pass or fail` },
    { n: 5, who: 'human', title: 'Officer acts', big: `${s.data.open_checks.length} open`, line: 'accept, dismiss, request info, or waive in writing' },
    { n: 6, who: 'rules', title: 'Seal and audit', big: s.data.open_checks.length ? '409 until clear' : 'Ready', line: 'Approve is blocked by the server; every act joins a hash chain' },
  ]
  return (
    <main style={{ paddingTop: 4 }}>
      <div className="pagehead">
        <div><div className="t xs up dim">Docket · reviewer queue</div><h1>{s.data.institution.name}</h1>
          <div className="t sm dim">{s.data.id} · {s.data.category} · {s.data.cycle} · version {s.data.version} · {s.data.institution.state}</div></div>
        <Link to="/case" className="btn dark" style={{ textDecoration: 'none', padding: '10px 20px' }}>Open the case desk →</Link>
      </div>
      <Workflow steps={steps} />
      <div className="kpis" style={{ marginTop: 14 }}>
        <div className="kpi"><div className="l">Claims in this file</div><div className="v">{total}</div><div className="xs dim">{counts.UNCHANGED} carried forward, {total - counts.UNCHANGED} need a look</div></div>
        <div className="kpi red"><div className="l">Rules failed</div><div className="v" style={{ color: 'var(--stamp)' }}>{red.length + unexplained.length}</div><div className="xs dim">red queue, officer must act</div></div>
        <div className="kpi amber"><div className="l">Awaiting a human</div><div className="v">{amber.length}</div><div className="xs dim">{s.data.open_checks.length} required checks open · {a.data?.alerts.length ?? 0} alerts</div></div>
        <div className="kpi green"><div className="l">Anomaly vs peers</div><div className="v">{s.data.anomaly.flag ? 'Flagged' : 'Normal'}</div><div className="xs dim">largest deviation: {s.data.anomaly.top_feature.replace(/_/g, ' ')}</div></div>
      </div>
      <div className="charts" style={{ marginTop: 14 }}>
        <div className="card"><h4>Delta tally · {total} claims</h4><div className="donutrow"><Donut parts={parts} center={String(total)} sub="claims" /><Legend parts={parts} /></div></div>
        <div className="card"><h4>Proof coverage by requirement</h4><CoverageBars reqs={cov.data?.requirements ?? []} /></div>
        <div className="card"><h4>Faculty against intake, peers in the same state</h4>
          {meI && meF && pts.length > 2 ? <Scatter pts={pts} me={{ x: meI, y: meF, label: 'this application' }} xl="total intake (seats)" yl="faculty count" /> : <p className="xs dim">Peer data not loaded.</p>}
          <div className="xs dim">{s.data.anomaly.wording}.</div></div>
      </div>
      <div className="grid2" style={{ marginTop: 14, alignItems: 'start' }}>
        <div>
          <FoldStack claims={c.data.claims} sample={c.data.sample} />
          <div className="card" style={{ marginTop: 14 }}><table className="ledger"><thead><tr><th>Delta tally · 80 claims</th><th className="num">n</th><th>what happens</th></tr></thead><tbody>
            <tr><td className="t">UNCHANGED</td><td className="num">{counts.UNCHANGED}</td><td className="sm">folded, sampled, expiry re-tested</td></tr>
            <tr><td className="t">CHANGED, WITH EVIDENCE</td><td className="num">{counts.CHANGED_WITH_EVIDENCE}</td><td className="sm">checked against the supporting document</td></tr>
            <tr><td className="t" style={{ color: 'var(--stamp)' }}>CHANGED, NO EXPLANATION</td><td className="num"><b>{counts.CHANGED_NO_EXPLANATION}</b></td><td className="sm">red queue: needs the officer</td></tr>
            <tr><td className="t">NEW</td><td className="num">{counts.NEW}</td><td className="sm">full scrutiny, nothing to compare</td></tr></tbody></table></div>
          {ph.data && <div className="card" style={{ marginTop: 14 }}><h4>Photo evidence <Link to="/case" className="xs t" style={{ fontWeight: 400 }}>map and details →</Link></h4><PhotoEvidence ph={ph.data} sel={pick} onSel={setPick} /></div>}
        </div>
        <div className="stack">
          <div className="slip ink human" data-no="CASE STATE">
            <div className="row between"><span style={{ fontSize: '1.15rem', fontWeight: 700 }}>{s.data.overall === 'READY_FOR_DECISION' ? 'Ready for decision' : 'Review incomplete'}</span><Stamp state={s.data.overall === 'READY_FOR_DECISION' ? 'PASSED' : 'MANUAL_REVIEW'} big /></div>
            <div className="t sm" style={{ marginTop: 6 }}>{s.data.open_checks.length} required checks open · {s.data.findings_open} findings awaiting a human · {a.data?.alerts.length ?? 0} alerts</div>
            <div className="xs dim" style={{ marginTop: 6 }}>Anomaly model (precomputed, offline): {s.data.anomaly.wording}. Largest deviation: <b className="t">{s.data.anomaly.top_feature.replace(/_/g, ' ')}</b>.</div>
          </div>
          <div className="slip ink rules" data-no="RED QUEUE">
            <div className="who rules">rules failed · {red.length + unexplained.length}</div>
            {red.map(x => <Link key={x.id} to={`/case?f=${x.id}`} className="row between sm" style={{ textDecoration: 'none', padding: '6px 0', borderBottom: '1px solid var(--rule)' }}><span><b className="t">{x.id}</b> {x.explanation.slice(0, 70)}…</span><Stamp state="FAILED" /></Link>)}
            {unexplained.map((x: any) => <div key={x.key} className="row between sm" style={{ padding: '6px 0', borderBottom: '1px solid var(--rule)' }}><span className="t">{x.key}: {num(x.prev)} → {num(x.value)}</span><span className="xs dim">no declared change</span></div>)}
          </div>
          <div className="slip ink human" data-no="AMBER QUEUE">
            <div className="who human">needs a human read · {amber.length}</div>
            {amber.slice(0, 7).map(x => <Link key={x.id} to={`/case?f=${x.id}`} className="row between sm" style={{ textDecoration: 'none', padding: '5px 0', borderBottom: '1px solid var(--rule)' }}><span><b className="t">{x.id}</b> {x.rule_id.replace(/_/g, ' ').toLowerCase()}</span><Stamp state={x.state} /></Link>)}
          </div>
        </div>
      </div>
      {f.data.bundles.map((b: any) => <BundleCard key={b.id} b={b} fins={f.data.findings} lang={lang} />)}
    </main>
  )
}
