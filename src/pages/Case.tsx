import { useContext, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api, useApi } from '../api'
import { AppCtx } from '../ctx'
import { CalendarRail } from '../ui/CalendarRail'
import { SealSlot } from '../ui/SealSlot'
import { Spine } from '../ui/Spine'
import { FindingSlip, NextStep } from '../ui/FindingSlip'
import { PdfViewer, type Box } from '../ui/PdfViewer'
import { GraphModal, TraceRibbon } from '../ui/Trace'
import { ClauseDrawer, WaiveModal } from '../ui/Modals'
import { NetworkMap } from '../ui/NetworkMap'
import { PlausibilityMap } from '../ui/PlausibilityMap'
import { ChainFooter } from '../ui/ChainFooter'
import { FoldStack } from '../ui/FoldStack'
import { Stamp } from '../ui/Stamp'
import { num } from '../lib/format'

type Tab = 'document' | 'delta' | 'network' | 'infra'
export function Case() {
  const { bump, say } = useContext(AppCtx); const [sp] = useSearchParams()
  const cov = useApi<any>('/applications/APP-0001/coverage'); const fd = useApi<any>('/findings'); const tl = useApi<any>('/applications/APP-0001/timeline')
  const cl = useApi<any>('/applications/APP-0001/claims'); const net = useApi<any>('/network/faculty/F-7731'); const ph = useApi<any>('/applications/APP-0001/photos'); const rules = useApi<any>('/rules')
  const [sel, setSel] = useState<string | null>(sp.get('f')); const [tab, setTab] = useState<Tab>('document')
  const [doc, setDoc] = useState({ doc: 'D-03', page: 8 }); const [waive, setWaive] = useState<string | null>(null)
  const [clause, setClause] = useState(false); const [graph, setGraph] = useState(false)
  const [trace, setTrace] = useState<string[]>([])
  const fins: any[] = fd.data?.findings ?? []
  const cur = fins.find(f => f.id === sel) ?? null
  const ordered = useMemo(() => [...fins].sort((a, b) => (a.req ?? 'Z').localeCompare(b.req ?? 'Z') || a.id.localeCompare(b.id)), [fins])

  useEffect(() => { if (!sel && ordered.length) setSel(ordered.find(f => f.id === 'F-014')?.id ?? ordered[0].id) }, [ordered, sel])
  useEffect(() => { if (cur) { const e = cur.evidence?.[0]; if (e) { setDoc({ doc: e.doc, page: e.page }); setTab('document') } api(`/findings/${cur.id}/graph`).then(g => setTrace(g.trace)).catch(() => setTrace([])) } }, [sel, fd.data])

  const act = async (action: 'accept' | 'dismiss' | 'request_info') => {
    if (!cur) return
    try { await api(`/findings/${cur.id}/decision`, { method: 'POST', json: { action } }); say(`${cur.id}: ${action.replace('_', ' ')} recorded in the audit chain`); bump() }
    catch (e: any) { say(e.message) }
  }
  const step = (d: number) => { const i = ordered.findIndex(f => f.id === sel); const n = ordered[(i + d + ordered.length) % ordered.length]; if (n) setSel(n.id) }
  useEffect(() => {
    const k = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement).closest('textarea,input') || e.metaKey || e.ctrlKey) return
      const key = e.key.toLowerCase()
      if (key === 'j') step(1); else if (key === 'k') step(-1); else if (key === 'y') act('accept'); else if (key === 'n') act('dismiss'); else if (key === 'r') act('request_info')
      else if (key === 'c') setClause(c => !c); else if (key === 'g') setGraph(g => !g)
      else if (key === 'w' && cov.data) { const r = cov.data.requirements.find((x: any) => x.id === cur?.req); if (r && cov.data.open_checks.includes(r.id)) setWaive(r.id); else if (cov.data.open_checks[0]) setWaive(cov.data.open_checks[0]) }
      else if (key === 'escape') { setClause(false); setGraph(false); setWaive(null) }
    }
    window.addEventListener('keydown', k); return () => window.removeEventListener('keydown', k)
  })
  if (!cov.data || !fd.data || !tl.data || !cl.data) return <p className="t" style={{ paddingTop: 20 }}>Opening the case file…</p>
  const ev = cur?.evidence?.[0]; const box: Box | null = ev && ev.doc === doc.doc && ev.page === doc.page ? { field: cur.claims[0], text: ev.text, box: ev.box } : null
  const rule = cur ? rules.data?.rules.find((r: any) => r.id === cur.rule_id) ?? null : null
  const mine = fins.filter(f => f.req === cur?.req)
  const submitWaiver = async (reason: string) => { await api('/applications/APP-0001/waivers', { method: 'POST', json: { check_id: waive, reason } }); say(`Waiver recorded for ${waive}`); setWaive(null); bump() }

  return (
    <main style={{ paddingTop: 12 }}>
      <div className="grid2" style={{ gridTemplateColumns: 'minmax(0,1fr) 380px', alignItems: 'start' }}>
        <div><div className="t xs up dim">Case desk · APP-0001 · version {cov.data.requirements.some((r: any) => r.reason === 'ok_after_resubmission') ? 2 : 1}</div>
          <h2 style={{ fontSize: '1.35rem', margin: '2px 0 6px' }}>Shri Vidya Institute of Engineering &amp; Technology, Pune</h2><CalendarRail tl={tl.data} /></div>
        <SealSlot cov={cov.data} onWaive={setWaive} onDone={m => { say(m); bump() }} />
      </div>
      <div className="desk">
        <div className="col-sticky"><Spine cov={cov.data} fins={fins} sel={cur?.req ?? null} onPick={(rid, d, p) => { const f = ordered.find(x => x.req === rid); if (f) setSel(f.id); else { setDoc({ doc: d, page: p }); setTab('document') } }} /></div>
        <div>
          <div className="dtabs" role="tablist">{(['document', 'delta', 'network', 'infra'] as Tab[]).map(t => <button key={t} role="tab" aria-selected={tab === t} className={tab === t ? 'on' : ''} onClick={() => setTab(t)}>{t}</button>)}</div>
          {tab === 'document' && <><PdfViewer doc={doc.doc} page={doc.page} box={box} />
            {cur && <div className="slip" style={{ marginTop: 10, borderRightStyle: 'solid' }}><div className="xs up dim t" style={{ marginBottom: 4 }}>trace</div><TraceRibbon trace={trace.length ? trace : [cur.rule_version, cur.rule_id, cur.id]} onGraph={() => setGraph(true)} /></div>}</>}
          {tab === 'delta' && <DeltaTab cl={cl.data} />}
          {tab === 'network' && net.data && <div className="slip" data-no="CROSS-INSTITUTION" style={{ marginTop: 14, borderRightStyle: 'solid' }}><NetworkMap net={net.data} /><div className="row" style={{ marginTop: 4 }}><button className="btn" onClick={() => setSel('F-017')}>open finding F-017</button><span className="xs dim">Legitimate causes exist (relieving date, data-entry lag). A human confirms.</span></div></div>}
          {tab === 'infra' && ph.data && <div className="slip" data-no="INFRASTRUCTURE EVIDENCE" style={{ marginTop: 14, borderRightStyle: 'solid' }}><PlausibilityMap ph={ph.data} /><button className="btn" onClick={() => setSel('F-024')}>open finding F-024</button></div>}
        </div>
        <div className="col-sticky stack">
          <div className="row between"><span className="t xs up dim">margin notes · {mine.length || fins.length} on this requirement</span><span className="xs dim"><kbd>J</kbd><kbd>K</kbd> move</span></div>
          {(mine.length ? mine : fins).map(f => <FindingSlip key={f.id} f={f} sel={f.id === sel} onPick={() => setSel(f.id)} />)}
          <NextStep f={cur} />
          <div className="row" style={{ flexWrap: 'wrap', gap: 6 }}>
            <button className="btn" onClick={() => act('accept')}>Accept <kbd>Y</kbd></button><button className="btn" onClick={() => act('dismiss')}>Dismiss <kbd>N</kbd></button>
            <button className="btn" onClick={() => act('request_info')}>Request info <kbd>R</kbd></button><button className="btn" onClick={() => setClause(true)}>Clause <kbd>C</kbd></button>
          </div>
          <div className="xs dim">Accept and dismiss are human acts and only clear items marked for review. A FAILED rule needs a fix or a written waiver.</div>
        </div>
      </div>
      <ChainFooter />
      <ClauseDrawer f={clause ? cur : null} rule={rule} onClose={() => setClause(false)} />
      {graph && <GraphModal trace={trace} onClose={() => setGraph(false)} />}
      {waive && <WaiveModal checkId={waive} onSubmit={submitWaiver} onClose={() => setWaive(null)} />}
    </main>
  )
}

function DeltaTab({ cl }: { cl: any }) {
  const rows = cl.claims.filter((c: any) => c.bucket !== 'UNCHANGED')
  const tag: Record<string, string> = { NEW: 'NEW', CHANGED_WITH_EVIDENCE: 'CHANGED · EVIDENCE', CHANGED_NO_EXPLANATION: 'CHANGED · NO EXPLANATION' }
  return (
    <div style={{ marginTop: 14 }}>
      <FoldStack claims={cl.claims} sample={cl.sample} />
      <table className="ledger sm"><thead><tr><th>claim</th><th className="num">last verified</th><th className="num">this version</th><th>bucket</th></tr></thead><tbody>
        {rows.map((c: any) => <tr key={c.key}><td className="t">{c.key}</td><td className="num dim">{c.prev == null ? '—' : typeof c.prev === 'number' ? num(c.prev) : c.prev}</td><td className="num"><b>{typeof c.value === 'number' ? num(c.value) : c.value}</b></td>
          <td className="t xs" style={{ color: c.bucket === 'CHANGED_NO_EXPLANATION' ? 'var(--stamp)' : undefined, fontWeight: c.bucket === 'CHANGED_NO_EXPLANATION' ? 700 : 400 }}>{tag[c.bucket]}</td></tr>)}</tbody></table>
    </div>
  )
}
