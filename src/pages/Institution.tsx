import { useContext, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, useApi } from '../api'
import { AppCtx } from '../ctx'
import { DiffRibbon, LETTER } from '../ui/DiffBundle'
import { NumberBadge } from '../ui/NumberBadge'
import { FixNote } from '../ui/FixNote'

const GAPS: Record<string, string> = { R05: 'Fire NOC ends 30 Sep 2027, inside the odd semester. Upload the renewed NOC or the renewal receipt.', R10: 'Three of six photos carry no location data. Upload geo-tagged photographs.' }

export function Precheck() {
  const { say } = useContext(AppCtx); const cov = useApi<any>('/applications/APP-0001/coverage')
  const [n, setN] = useState(0); const [fixed, setFixed] = useState<string[]>([]); const [stage, setStage] = useState<any>(null)
  useEffect(() => { if (n > 0 && n < 14) { const t = setTimeout(() => setN(n + 1), 170); return () => clearTimeout(t) } }, [n])
  useEffect(() => { if (!stage || stage.done) return; const t = setInterval(async () => setStage(await api('/applications/APP-0001/events')), 500); return () => clearInterval(t) }, [stage])
  const reqs: any[] = cov.data?.requirements ?? []
  const submit = async () => { await api('/applications', { method: 'POST' }); setStage(await api('/applications/APP-0001/events')) }
  return (
    <main style={{ paddingTop: 18 }}>
      <div className="t xs up dim">Institution desk · pre-submission check</div><h1 style={{ fontSize: '1.8rem' }}>Check your file before it becomes an official submission</h1>
      <p className="sm dim" style={{ maxWidth: 680 }}>The dry-run reads your documents and tests only the missing and expired rules. It creates no deficiency record. Fix what it finds, then submit.</p>
      <div className="grid2" style={{ marginTop: 14 }}>
        <div className="drop"><div style={{ fontFamily: 'var(--serif)', fontSize: '1.15rem' }}>Drop your documents here</div><div className="xs dim" style={{ margin: '4px 0 10px' }}>PDF, JPG or PNG · English, हिन्दी or मराठी</div>
          <button className="btn dark" onClick={() => { setN(1); say('8 sample documents loaded (synthetic)') }}>Load the 8 sample documents</button></div>
        <div className="slip" data-no="CHECKLIST · EoA with intake change" style={{ borderRightStyle: 'solid' }}>
          {reqs.map((r, i) => <div key={r.id} className="sm" style={{ padding: '2px 0' }}><span className={`tick ${i < n ? (GAPS[r.id] && !fixed.includes(r.id) ? 'gap' : 'on') : ''}`}>{i < n ? (GAPS[r.id] && !fixed.includes(r.id) ? '!' : '✓') : ''}</span><span className="t xs">{r.id}</span> {r.title}</div>)}
        </div>
      </div>
      {n >= 14 && <div className="stack" style={{ marginTop: 16 }}>
        <h3>Two gaps found by the dry-run</h3>
        {Object.entries(GAPS).map(([id, t]) => <div key={id} className="slip ink rules" data-no={id} style={{ borderRightStyle: 'solid' }}><div className="row between"><span className="sm">{t}</span>
          <button className="btn" disabled={fixed.includes(id)} onClick={() => setFixed([...fixed, id])}>{fixed.includes(id) ? 'fixed' : 'upload fix'}</button></div></div>)}
        <button className="btn dark" onClick={submit} disabled={!!stage}>Submit application</button>
      </div>}
      {stage && <div style={{ marginTop: 18 }}><div className="stage">{stage.stages.map((s: string, i: number) => <div key={s} className={i < stage.completed ? 'done' : i === stage.completed ? 'now' : ''}>{i + 1}<br />{s}</div>)}</div>
        {stage.done && <p className="sm"><Link to="/">Application read, checked and graded. Open the reviewer docket →</Link></p>}</div>}
    </main>
  )
}

export function Fixes() {
  const { lang, bump, say } = useContext(AppCtx); const f = useApi<any>('/findings'); const [diff, setDiff] = useState<any>(null)
  const fins: any[] = f.data?.findings ?? []; const res = (id: string) => fins.find(x => x.id === id)?.resolved
  const upload = async () => { setDiff(await api('/applications/APP-0001/resubmit', { method: 'POST' })); say('Version 2 received. Only dependent checks re-ran.'); bump() }
  const items = [['F-011', 'Upload one certified trust registration certificate that matches your AICTE record.', false], ['F-014', 'Upload the corrected architect-certified area statement.', true], ['F-016', 'Upload the renewed Fire NOC (current one ends 30 Sep 2027).', false]] as const
  return (
    <main style={{ paddingTop: 18 }}>
      <div className="t xs up dim">Institution desk · requests from the officer</div><h1 style={{ fontSize: '1.8rem' }}>What we need from you</h1>
      <p className="sm dim" style={{ maxWidth: 680 }}>Three findings about the trust name share one cause, so you receive one request. Use the language switch at the top right to read it in हिन्दी or मराठी.</p>
      <div className="slip ink ai" data-no="MESSAGE FROM THE REVIEWER" style={{ marginTop: 14, borderRightStyle: 'solid' }}><span className="who ai">drafted by AI, numbers checked, sent by the officer</span><div style={{ marginTop: 6 }}>{LETTER[lang]}</div><NumberBadge text={LETTER[lang]} fins={fins} /></div>
      <div className="stack" style={{ marginTop: 16 }}>{items.map(([id, t, canUpload]) => (
        <div key={id} className="slip" data-no={id} style={{ borderRightStyle: 'solid' }}><div className="row between"><span>{t}<FixNote f={fins.find(x => x.id === id)} resolved={!!res(id)} /></span>
          {res(id) ? <span className="stamp PASSED">resolved</span> : canUpload ? <button className="btn dark" onClick={upload}>Upload corrected area statement</button> : <span className="xs dim">upload slot (demo: not wired)</span>}</div></div>))}</div>
      {diff && <div style={{ marginTop: 18 }}><DiffRibbon diff={diff} /></div>}
    </main>
  )
}
