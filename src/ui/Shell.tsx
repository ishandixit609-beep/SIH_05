import { useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { AppCtx, type Lang } from '../ctx'
import { useApi } from '../api'
import { dateTimeIST, DEMO_NOW } from '../lib/format'
import { getUser, setUser, type User } from '../lib/session'

/** Sidebar navigation (PS5). Three groups so a judge always knows where they are:
    Review = the officer's day, Institution = the applicant's side, Insight = proof that it works. */
const ICON: Record<string, string> = {
  docket: 'M3 13l3-8h12l3 8v6H3z M3 13h5l1 3h6l1-3h5',
  case: 'M4 4h10l6 6v10H4z M14 4v6h6',
  alerts: 'M6 17v-6a6 6 0 0 1 12 0v6l2 2H4z M10 21h4',
  precheck: 'M4 4h16v16H4z M8 12l3 3 5-6',
  fixes: 'M12 16V4 M7 9l5-5 5 5 M4 20h16',
  rules: 'M4 7h10 M18 7h2 M4 17h2 M10 17h10 M14 5v4 M6 15v4',
  audit: 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z M9 12l2 2 4-4',
  eval: 'M5 20V10 M12 20V4 M19 20v-7',
  about: 'M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z M8 8h8',
  menu: 'M4 7h16 M4 12h16 M4 17h16',
}
const Icon = ({ n }: { n: string }) => <svg viewBox="0 0 24 24" aria-hidden><path d={ICON[n]} /></svg>
interface Item { to: string; label: string; icon: string; sub: string }
const GROUPS: { name: string; items: Item[] }[] = [
  { name: 'Review', items: [
    { to: '/', label: 'Docket', icon: 'docket', sub: 'Reviewer queue' },
    { to: '/case', label: 'Case desk', icon: 'case', sub: 'Evidence, checks and the decision' },
    { to: '/alerts', label: 'Alerts', icon: 'alerts', sub: 'What needs attention soon' }] },
  { name: 'Institution', items: [
    { to: '/institution/precheck', label: 'Pre-check', icon: 'precheck', sub: 'Dry run before submission' },
    { to: '/institution/fixes', label: 'Fixes', icon: 'fixes', sub: 'What the applicant must do' }] },
  { name: 'Insight', items: [
    { to: '/rules', label: 'Rule lab', icon: 'rules', sub: 'Versioned rules and what-if' },
    { to: '/audit', label: 'Audit', icon: 'audit', sub: 'Hash-chained record of every act' },
    { to: '/eval', label: 'Results', icon: 'eval', sub: 'Measured against planted issues' },
    { to: '/about', label: 'Method', icon: 'about', sub: 'Scope, sources and limits' }] },
]
const ALL = GROUPS.flatMap(g => g.items)

export function Shell() {
  const { lang, setLang } = useContext(AppCtx)
  const [pal, setPal] = useState(false); const nav = useNavigate(); const loc = useLocation()
  const [acct, setAcct] = useState(false); const [mob, setMob] = useState(false); const [user, setU] = useState<User | null>(() => getUser())
  const [theme, setTheme] = useState<'light' | 'dark'>(() => (document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'))
  // The sidebar folds itself to icons on the Case desk (that page needs the width); a manual choice is remembered.
  const [pref, setPref] = useState<boolean | null>(() => { try { const v = localStorage.getItem('satyapan-side'); return v === null ? null : v === '1' } catch { return null } })
  const collapsed = pref ?? loc.pathname.startsWith('/case')
  const toggleSide = () => { const n = !collapsed; setPref(n); try { localStorage.setItem('satyapan-side', n ? '1' : '0') } catch { /* private mode */ } }
  const sm = useApi<any>('/applications/APP-0001/summary')
  const here = ALL.find(i => (i.to === '/' ? loc.pathname === '/' : loc.pathname.startsWith(i.to)))

  useEffect(() => { document.documentElement.dataset.theme = theme; try { localStorage.setItem('satyapan-theme', theme) } catch { /* private mode */ } }, [theme])
  useEffect(() => { setAcct(false); setMob(false) }, [loc.pathname])
  useEffect(() => {
    const k = (e: KeyboardEvent) => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setPal(p => !p) } if (e.key === 'Escape') { setPal(false); setAcct(false); setMob(false) } }
    window.addEventListener('keydown', k); return () => window.removeEventListener('keydown', k)
  }, [])
  const open = sm.data?.open_checks?.length ?? 0; const ready = sm.data && open === 0

  return (
    <div className={`app ${collapsed ? 'collapsed' : ''} ${mob ? 'mobopen' : ''}`}>
      <svg width="0" height="0" style={{ position: 'absolute' }} aria-hidden><defs>
        <marker id="a" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="var(--ink)" /></marker></defs></svg>
      <aside className="side" aria-label="Main navigation">
        <Link to="/" className="brand" aria-label="SATYAPAN home"><span className="word">SATYAPAN</span><span className="dv" lang="hi">सत्यापन</span></Link>
        <nav>
          {GROUPS.map(g => (
            <div key={g.name}><div className="grp">{g.name}</div>
              {g.items.map(i => <NavLink key={i.to} to={i.to} end={i.to === '/'} title={i.label} className={({ isActive }) => `nav ${isActive ? 'on' : ''}`}><Icon n={i.icon} /><span className="label">{i.label}</span></NavLink>)}
            </div>))}
        </nav>
        <div className="foot">
          <Link to="/case" className="casechip" title="Open the case desk">
            <span className={`dot ${ready ? 'ok' : 'open'}`} />
            <span className="cc-txt"><b>APP-0001 · v{sm.data?.version ?? 1}</b><span>{sm.data ? (ready ? 'Ready for decision' : `${open} checks open`) : '…'}</span></span>
          </Link>
          <div className="clock cc-txt">{dateTimeIST(DEMO_NOW)} <span>(demo clock)</span></div>
          <a href="/ACCOMPLISHMENTS.md" download="SATYAPAN_ACCOMPLISHMENTS.md" className="sidelink" title="Download Accomplishments Report (.md)"><span aria-hidden>⬇</span><span className="label">Report.md</span></a>
        </div>
      </aside>
      {mob && <div className="scrim" onClick={() => setMob(false)} />}
      <div className="mainpane">
        <header className="bar">
          <button className="iconbtn" onClick={() => (window.innerWidth <= 960 ? setMob(m => !m) : toggleSide())} aria-label="Toggle navigation" title="Toggle navigation"><Icon n="menu" /></button>
          <div className="ptitle"><b>{here?.label ?? 'SATYAPAN'}</b><span>{here?.sub ?? 'Application integrity'}</span></div>
          <div className="tools">
            <button className="searchbox" onClick={() => setPal(true)} aria-label="Search"><span>Search findings and pages</span><kbd>⌘K</kbd></button>
            <div className="lang" role="group" aria-label="Language">{(['en', 'hi', 'mr'] as Lang[]).map(l => <button key={l} className={lang === l ? 'on' : ''} onClick={() => setLang(l)} lang={l}>{l === 'en' ? 'EN' : l === 'hi' ? 'हिं' : 'मरा'}</button>)}</div>
            <button className="themebtn" onClick={() => setTheme(t => (t === 'dark' ? 'light' : 'dark'))} aria-label="Toggle light or dark theme" title="Toggle theme">{theme === 'dark' ? '☾ Dark' : '☀ Light'}</button>
            {user ? (
              <div className="moremenu"><button className="avatar" onClick={() => setAcct(a => !a)} aria-label="Account" title={user.name}>{user.name.trim()[0]?.toUpperCase() ?? '?'}</button>
                {acct && <div className="menu right"><div style={{ padding: '8px 12px' }}><b className="sm">{user.name}</b><div className="xs dim">{user.role}</div></div><div className="sep" /><button onClick={() => { setUser(null); setU(null); setAcct(false) }}>Sign out</button></div>}</div>
            ) : <Link to="/signin" className="signbtn">Sign in</Link>}
          </div>
        </header>
        <div className="page"><Outlet /></div>
      </div>
      <div className="strip">SYNTHETIC DATA · SIMULATED CONNECTORS · NORMS AND CLAUSES ILLUSTRATIVE UNTIL COPIED FROM APH 2024-27 · FLAGS ARE INDICATORS, OFFICIALS DECIDE</div>
      {pal && <Palette onClose={() => setPal(false)} go={p => { setPal(false); nav(p) }} />}
    </div>
  )
}

function Palette({ onClose, go }: { onClose: () => void; go: (p: string) => void }) {
  const [q, setQ] = useState(''); const { data } = useApi<any>('/findings')
  const items = useMemo(() => [...ALL.map(i => ({ label: `Go to ${i.label}`, to: i.to })), ...(data?.findings ?? []).map((f: any) => ({ label: `${f.id}  ${f.rule_id}  ${f.explanation.slice(0, 60)}`, to: `/case?f=${f.id}` }))]
    .filter(i => i.label.toLowerCase().includes(q.toLowerCase())).slice(0, 9), [q, data])
  return (<><div className="veil" onClick={onClose} />
    <div className="modal" role="dialog" aria-label="Command palette"><input type="text" autoFocus value={q} onChange={e => setQ(e.target.value)} placeholder="Jump to a page or a finding…" onKeyDown={e => e.key === 'Enter' && items[0] && go(items[0].to)} />
      <div style={{ marginTop: 8 }}>{items.map(i => <button key={i.label} onClick={() => go(i.to)} className="sm" style={{ display: 'block', width: '100%', textAlign: 'left', border: 'none', borderBottom: '1px solid var(--rule)', background: 'transparent', padding: '9px 4px', borderRadius: 6 }}>{i.label}</button>)}</div></div></>)
}
export const Page = ({ children }: { children: ReactNode }) => <main style={{ paddingTop: 16 }}>{children}</main>
