import { useContext, useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { AppCtx, type Lang } from '../ctx'
import { useApi } from '../api'
import { dateTimeIST, DEMO_NOW } from '../lib/format'

const NAV: [string, string][] = [['/', 'Docket'], ['/case', 'Case desk'], ['/institution/precheck', 'Pre-check'], ['/institution/fixes', 'Fixes'], ['/rules', 'Rule lab'], ['/alerts', 'Alerts'], ['/audit', 'Audit'], ['/eval', 'Results'], ['/about', 'Method']]

export function Shell() {
  const { lang, setLang } = useContext(AppCtx)
  const [pal, setPal] = useState(false); const nav = useNavigate(); const loc = useLocation()
  const [theme, setTheme] = useState<'light' | 'dark'>(() => (document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'))
  const navRef = useRef<HTMLElement>(null); const [ind, setInd] = useState({ x: 0, w: 0 })

  useEffect(() => { document.documentElement.dataset.theme = theme; try { localStorage.setItem('satyapan-theme', theme) } catch { /* private mode */ } }, [theme])
  useEffect(() => {
    const k = (e: KeyboardEvent) => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setPal(p => !p) } if (e.key === 'Escape') setPal(false) }
    window.addEventListener('keydown', k); return () => window.removeEventListener('keydown', k)
  }, [])
  // Sliding pill under the active link. Re-measured on route change, resize and when web fonts finish loading.
  useLayoutEffect(() => {
    const measure = () => {
      const n = navRef.current; const a = n?.querySelector<HTMLElement>('a.on'); if (!n || !a) return
      setInd({ x: a.offsetLeft, w: a.offsetWidth })
      if (a.offsetLeft < n.scrollLeft || a.offsetLeft + a.offsetWidth > n.scrollLeft + n.clientWidth) n.scrollLeft = Math.max(0, a.offsetLeft - 24)
    }
    measure(); window.addEventListener('resize', measure); (document as any).fonts?.ready?.then(measure)
    return () => window.removeEventListener('resize', measure)
  }, [loc.pathname, lang])

  return (
    <>
      <svg width="0" height="0" style={{ position: 'absolute' }} aria-hidden><defs>
        <filter id="rough"><feTurbulence type="fractalNoise" baseFrequency=".05" numOctaves="2" seed="4" result="t" /><feDisplacementMap in="SourceGraphic" in2="t" scale="2.4" /></filter>
        <marker id="a" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="var(--ink)" /></marker></defs></svg>
      <div className="frame">
        <header className="top">
          <div className="brand"><span className="word">SATYAPAN</span><span className="dv" lang="hi">सत्यापन</span></div>
          <nav className="pill" aria-label="Sections" ref={navRef}>
            <span className="ind" aria-hidden style={{ transform: `translateX(${ind.x}px)`, width: ind.w, opacity: ind.w ? 1 : 0 }} />
            {NAV.map(([to, t]) => <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => (isActive ? 'on' : '')}>{t}</NavLink>)}
          </nav>
          <div className="tools">
            <div className="lang" role="group" aria-label="Language">{(['en', 'hi', 'mr'] as Lang[]).map(l => <button key={l} className={lang === l ? 'on' : ''} onClick={() => setLang(l)}>{l === 'en' ? 'EN' : l === 'hi' ? 'हिं' : 'मरा'}</button>)}</div>
            <button className="themebtn" onClick={() => setTheme(t => (t === 'dark' ? 'light' : 'dark'))} aria-label="Toggle light or dark theme" title="Toggle theme">{theme === 'dark' ? 'Dark' : 'Light'}</button>
            <span className="hint">search <kbd>⌘K</kbd></span>
          </div>
        </header>
        <div className="sheet">
          <div className="meta"><span>Application Integrity · Extension of Approval · AICTE · AY 2027-28</span><span>{dateTimeIST(DEMO_NOW)} <span className="dim">(demo clock)</span></span></div>
          <Outlet />
        </div>
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
      <div style={{ marginTop: 8 }}>{items.map(i => <button key={i.label} onClick={() => go(i.to)} className="sm" style={{ display: 'block', width: '100%', textAlign: 'left', border: 'none', borderBottom: '1px solid var(--rule)', background: 'transparent', padding: '7px 2px' }}>{i.label}</button>)}</div></div></>)
}
export const Page = ({ children }: { children: ReactNode }) => <main style={{ paddingTop: 16 }}>{children}</main>