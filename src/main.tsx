import { StrictMode, useCallback, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import './styles.css'
import { AppCtx, type Lang } from './ctx'
import { Shell } from './ui/Shell'
import { Inbox } from './pages/Inbox'
import { Case } from './pages/Case'
import { Precheck, Fixes } from './pages/Institution'
import { RuleLab, Alerts, AuditPage, Results } from './pages/Others'
import { About } from './pages/About'
import { AuthPage } from './pages/Auth'
import { Translator } from './i18n/Translator'

function Root() {
  const [rev, setRev] = useState(0); const [lang, setLangState] = useState<Lang>(() => { try { const v = localStorage.getItem('satyapan-lang'); return v === 'hi' || v === 'mr' ? v : 'en' } catch { return 'en' } });
  const setLang = useCallback((l: Lang) => { setLangState(l); try { localStorage.setItem('satyapan-lang', l) } catch { /* private mode */ } }, []); const [msg, setMsg] = useState('')
  const bump = useCallback(() => setRev(r => r + 1), [])
  const say = useCallback((m: string) => { setMsg(m); setTimeout(() => setMsg(''), 2600) }, [])
  const v = useMemo(() => ({ rev, bump, lang, setLang, say }), [rev, bump, lang, setLang, say])
  return (
    <AppCtx.Provider value={v}>
      <BrowserRouter>
        <Routes><Route path="signin" element={<AuthPage />} /><Route element={<Shell />}>
          <Route index element={<Inbox />} /><Route path="case" element={<Case />} />
          <Route path="institution/precheck" element={<Precheck />} /><Route path="institution/fixes" element={<Fixes />} />
          <Route path="rules" element={<RuleLab />} /><Route path="alerts" element={<Alerts />} /><Route path="audit" element={<AuditPage />} /><Route path="eval" element={<Results />} /><Route path="about" element={<About />} />
        </Route></Routes>
      </BrowserRouter>
      {msg && <div className="toast" role="status">{msg}</div>}
      <Translator lang={lang} />
    </AppCtx.Provider>
  )
}

async function boot() {
  // Mock backend is on unless VITE_API_BASE points at the real FastAPI server.
  if (!import.meta.env.VITE_API_BASE) { try { const { worker } = await import('./mocks/browser'); await worker.start({ onUnhandledRequest: 'bypass', quiet: true }) } catch (e) { console.error('mock service worker failed to start', e) } }
  createRoot(document.getElementById('root')!).render(<StrictMode><Root /></StrictMode>)
}
boot()
