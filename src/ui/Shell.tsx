import { useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { AppCtx, type Lang } from '../ctx'
import { useApi } from '../api'
import { dateTimeIST, DEMO_NOW } from '../lib/format'

const NAV: [string, string][] = [['/', 'Docket'], ['/case', 'Case desk'], ['/institution/precheck', 'Pre-check'], ['/institution/fixes', 'Fixes'], ['/rules', 'Rule lab'], ['/alerts', 'Alerts'], ['/audit', 'Audit'], ['/eval', 'Results'], ['/about', 'Method']]

export function Shell() {
  const { lang, setLang } = useContext(AppCtx)
  const [pal, setPal] = useState(false); const nav = useNavigate()
  useEffect(() => {
    const k = (e: KeyboardEvent) => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setPal(p => !p) } if (e.key === 'Escape') setPal(false) }
    window.addEventListener('keydown', k); return () => window.removeEventListener('keydown', k)
  }, [])
  return (
    <>
      <svg width="0" height="0" style={{ position: 'absolute' }} aria-hidden><defs>
        <filter id="rough"><feTurbulence type="fractalNoise" baseFrequency=".05" numOctaves="2" seed="4" result="t" /><feDisplacementMap in="SourceGraphic" in2="t" scale="2.4" /></filter>
        <marker id="a" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="var(--ink)" /></marker></defs></svg>
      <div className="binder">
        <div className="punch" aria-hidden />
        <div className="sheet">
          <header className="mast">
            <div><div className="word">SATYAPAN<span className="dv" lang="hi">सत्यापन</span></div><div className="sub">Application Integrity · Extension of Approval · AICTE · AY 2027-28</div></div>
            <div className="right"><div>{dateTimeIST(DEMO_NOW)} <span className="dim">(demo clock)</span></div>
              <div className="lang" role="group" aria-label="Language">{(['en', 'hi', 'mr'] as Lang[]).map(l => <button key={l} className={lang === l ? 'on' : ''} onClick={() => setLang(l)}>{l === 'en' ? 'EN' : l === 'hi' ? 'हिं' : 'मरा'}</button>)}</div>
              <div className="xs dim" style={{ marginTop: 4 }}>search anything <kbd>⌘K</kbd></div></div>
          </header>
          <Outlet />
        </div>
        <nav className="tabs" aria-label="Sections">{NAV.map(([to, t]) => <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => (isActive ? 'on' : '')}>{t}</NavLink>)}</nav>
      </div>
      <div className="strip">SYNTHETIC DATA · SIMULATED CONNECTORS · NORMS AND CLAUSES ILLUSTRATIVE UNTIL COPIED FROM APH 2024-27 · FLAGS ARE INDICATORS, OFFICIALS DECIDE</div>
      {pal && <Palette onClose={() => setPal(false)} go={p => { setPal(false); nav(p) }} />}
    </>
  )
}

function Palette({ onClose, go }: { onClose: () => void; go: (p: string) => void }) {
  const [q, setQ] = useState(''); const { data } = useApi<any>('/findings')
  const items = useMemo(() => [...NAV.map(([p, t]) => ({ label: `Go to ${t}`, to: p })), ...(data?.findings ?? []).map((f: any) => ({ label: `${f.id}  ${f.rule_id}  ${f.explanation.slice(0, 60)}`, to: `/case?f=${f.id}` }))]
    .filter(i => i.label.toLowerCase().includes(q.toLowerCase())).slice(0, 9), [q, data])
  return (<><div className="veil" onClick={onClose} />
    <div className="modal" role="dialog" aria-label="Command palette"><input type="text" autoFocus value={q} onChange={e => setQ(e.target.value)} placeholder="Jump to a page or a finding…" onKeyDown={e => e.key === 'Enter' && items[0] && go(items[0].to)} />
      <div style={{ marginTop: 8 }}>{items.map(i => <button key={i.label} onClick={() => go(i.to)} className="sm" style={{ display: 'block', width: '100%', textAlign: 'left', border: 'none', borderBottom: '1px dotted var(--rule)', background: 'transparent', padding: '5px 2px' }}>{i.label}</button>)}</div></div></>)
}
export const Page = ({ children }: { children: ReactNode }) => <main style={{ paddingTop: 16 }}>{children}</main>
