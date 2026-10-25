import { useContext, useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { AppCtx, type Lang } from '../ctx'
import { useApi } from '../api'
import { dateTimeIST, DEMO_NOW } from '../lib/format'
import { getUser, setUser, type User } from '../lib/session'

// The main demo story stays on four pages. The rest live under "More" so a judge is never lost.
const PRIMARY: [string, string][] = [['/', 'Docket'], ['/case', 'Case desk'], ['/institution/precheck', 'Pre-check'], ['/institution/fixes', 'Fixes']]
const MORE: [string, string][] = [['/rules', 'Rule lab'], ['/alerts', 'Alerts'], ['/audit', 'Audit'], ['/eval', 'Results'], ['/about', 'Method']]
const NAV = [...PRIMARY, ...MORE]

export function Shell() {
  const { lang, setLang } = useContext(AppCtx)
  const [pal, setPal] = useState(false); const nav = useNavigate(); const loc = useLocation()
  const [more, setMore] = useState(false); const [acct, setAcct] = useState(false); const [user, setU] = useState<User | null>(() => getUser())
  const [theme, setTheme] = useState<'light' | 'dark'>(() => (document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'))
  const navRef = useRef<HTMLElement>(null); const [ind, setInd] = useState({ x: 0, w: 0 })
  const inMore = MORE.some(([p]) => loc.pathname.startsWith(p))

  useEffect(() => { document.documentElement.dataset.theme = theme; try { localStorage.setItem('satyapan-theme', theme) } catch { /* private mode */ } }, [theme])
  useEffect(() => { setMore(false); setAcct(false) }, [loc.pathname])
  useEffect(() => {
    const k = (e: KeyboardEvent) => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setPal(p => !p) } if (e.key === 'Escape') { setPal(false); setMore(false); setAcct(false) } }
    window.addEventListener('keydown', k); return () => window.removeEventListener('keydown', k)
  }, [])
  // Sliding white pill under the active link. Re-measured on route change, resize and when web fonts finish loading.
  useLayoutEffect(() => {
    const measure = () => {
      const n = navRef.current; const a = n?.querySelector<HTMLElement>('a.on'); if (!n || !a) { setInd(i => ({ ...i, w: 0 })); return }
      setInd({ x: a.offsetLeft, w: a.offsetWidth })
      if (a.offsetLeft < n.scrollLeft || a.offsetLeft + a.offsetWidth > n.scrollLeft + n.clientWidth) n.scrollLeft = Math.max(0, a.offsetLeft - 24)
    }
    measure(); window.addEventListener('resize', measure); (document as any).fonts?.ready?.then(measure)
    return () => window.removeEventListener('resize', measure)
  }, [loc.pathname, lang])

  return (
    <>
      <svg width="0" height="0" style={{ position: 'absolute' }} aria-hidden><defs>
        <marker id="a" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="var(--ink)" /></marker></defs></svg>
      <header className="top"><div className="topin">
        <Link to="/" className="brand" aria-label="SATYAPAN home"><span className="word">SATYAPAN</span><span className="dv" lang="hi">सत्यापन</span></Link>
        <div className="navwrap">
          <nav className="pill" aria-label="Sections" ref={navRef}>
            <span className="ind" aria-hidden style={{ transform: `translateX(${ind.x}px)`, width: ind.w, opacity: ind.w ? 1 : 0 }} />
            {PRIMARY.map(([to, t]) => <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => (isActive ? 'on' : '')}>{t}</NavLink>)}
          </nav>
          <div className="moremenu">
            <button className={`morebtn ${inMore ? 'on' : ''}`} onClick={() => { setMore(m => !m); setAcct(false) }} aria-expanded={more} aria-haspopup="menu">More ▾</button>
            {more && <div className="menu" role="menu">{MORE.map(([to, t]) => <NavLink key={to} to={to} className={({ isActive }) => (isActive ? 'on' : '')}>{t}</NavLink>)}</div>}
          </div>
        </div>
        <div className="tools">
          <a href="/ACCOMPLISHMENTS.md" download="SATYAPAN_ACCOMPLISHMENTS.md" className="btn xs" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 4, padding: '4px 8px' }} title="Download Accomplishments Report (.md)">⬇ Report.md</a>
          <button className="searchbox" onClick={() => setPal(true)} aria-label="Search"><span>Search findings and pages</span><kbd>⌘K</kbd></button>
          <div className="lang" role="group" aria-label="Language">{(['en', 'hi', 'mr'] as Lang[]).map(l => <button key={l} className={lang === l ? 'on' : ''} onClick={() => setLang(l)}>{l === 'en' ? 'EN' : l === 'hi' ? 'हिं' : 'मरा'}</button>)}</div>
          <button className="themebtn" onClick={() => setTheme(t => (t === 'dark' ? 'light' : 'dark'))} aria-label="Toggle light or dark theme" title="Toggle theme">{theme === 'dark' ? '☾ Dark' : '☀ Light'}</button>
          {user ? (
            <div className="moremenu"><button className="avatar" onClick={() => { setAcct(a => !a); setMore(false) }} aria-label="Account" title={user.name}>{user.name.trim()[0]?.toUpperCase() ?? '?'}</button>
              {acct && <div className="menu right"><div style={{ padding: '8px 12px' }}><b className="sm">{user.name}</b><div className="xs dim">{user.role}</div></div><div className="sep" /><button onClick={() => { setUser(null); setU(null); setAcct(false) }}>Sign out</button></div>}</div>
          ) : <Link to="/signin" className="signbtn">Sign in</Link>}
        </div>
      </div></header>
      <div className="frame">
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
      <div style={{ marginTop: 8 }}>{items.map(i => <button key={i.label} onClick={() => go(i.to)} className="sm" style={{ display: 'block', width: '100%', textAlign: 'left', border: 'none', borderBottom: '1px solid var(--rule)', background: 'transparent', padding: '9px 4px', borderRadius: 6 }}>{i.label}</button>)}</div></div></>)
}
export const Page = ({ children }: { children: ReactNode }) => <main style={{ paddingTop: 16 }}>{children}</main>
