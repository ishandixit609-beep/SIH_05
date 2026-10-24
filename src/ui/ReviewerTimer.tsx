import { useEffect, useState } from 'react'
type Run = { mode: 'with' | 'without'; secs: number; at: string }
const KEY = 'satyapan.timing.v1'
const load = (): Run[] => { try { return JSON.parse(localStorage.getItem(KEY) ?? '[]') } catch { return [] } }
const save = (r: Run[]) => { try { localStorage.setItem(KEY, JSON.stringify(r)) } catch { /* private mode: keep in memory only */ } }
const mean = (r: Run[]) => (r.length ? (r.reduce((a, b) => a + b.secs, 0) / r.length).toFixed(0) + ' s' : 'no runs')

/** User-test helper: time how long a volunteer takes to find a seeded issue, with and without the tool. */
export function ReviewerTimer() {
  const [runs, setRuns] = useState<Run[]>([]); const [mode, setMode] = useState<'with' | 'without'>('with'); const [t0, setT0] = useState<number | null>(null); const [now, setNow] = useState(0)
  useEffect(() => setRuns(load()), [])
  useEffect(() => { if (t0 === null) return; const i = setInterval(() => setNow(Date.now()), 250); return () => clearInterval(i) }, [t0])
  const stop = () => { if (t0 === null) return; const r = [...runs, { mode, secs: Math.round((Date.now() - t0) / 1000), at: new Date().toISOString().slice(0, 16) }]; setRuns(r); save(r); setT0(null) }
  const w = runs.filter(r => r.mode === 'with'), wo = runs.filter(r => r.mode === 'without')
  return (
    <div className="slip" data-no="REVIEWER TIME TEST" style={{ marginTop: 18, borderRightStyle: 'solid' }}>
      <div className="sm">Task for the volunteer: <b>find the area-per-seat problem and say which page of which document it is on.</b></div>
      <div className="row" style={{ marginTop: 8, flexWrap: 'wrap' }}>
        <label className="sm">Condition <select value={mode} onChange={e => setMode(e.target.value as 'with' | 'without')} disabled={t0 !== null}><option value="with">with SATYAPAN</option><option value="without">without (plain PDFs)</option></select></label>
        {t0 === null ? <button className="btn dark" onClick={() => { setT0(Date.now()); setNow(Date.now()) }}>Start timer</button> : <button className="btn red" onClick={stop}>Found it: stop</button>}
        {t0 !== null && <b className="t">{Math.round((now - t0) / 1000)} s</b>}
        <button className="btn" onClick={() => { setRuns([]); save([]) }}>clear</button>
      </div>
      <table className="ledger sm" style={{ marginTop: 8 }}><thead><tr><th>condition</th><th className="num">runs</th><th className="num">mean time</th></tr></thead>
        <tbody><tr><td>with SATYAPAN</td><td className="num">{w.length}</td><td className="num">{mean(w)}</td></tr><tr><td>without</td><td className="num">{wo.length}</td><td className="num">{mean(wo)}</td></tr></tbody></table>
      <div className="xs dim" style={{ marginTop: 6 }}>Stored only in this browser. With a handful of volunteers this is an indication, not a statistic.</div>
    </div>
  )
}
