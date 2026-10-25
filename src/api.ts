import { useContext, useEffect, useState } from 'react'
import { AppCtx } from './ctx'

// Mock backend is ON unless VITE_API_BASE is set (then every call goes to the real FastAPI server).
const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? '/api'

export async function api<T = any>(path: string, init?: RequestInit & { json?: unknown }): Promise<T> {
  const { json, ...rest } = init ?? {}
  const ctl = new AbortController(); const timer = setTimeout(() => ctl.abort(), 8000)   // never hang forever: abort, then useApi retries
  const r = await fetch(BASE + path, { ...rest, signal: ctl.signal, headers: { 'Content-Type': 'application/json', ...(rest.headers ?? {}) }, body: json !== undefined ? JSON.stringify(json) : rest.body }).finally(() => clearTimeout(timer))
  const body = await r.json().catch(() => ({}))
  if (!r.ok) throw Object.assign(new Error(body.detail ?? body.error ?? r.statusText), { status: r.status, body })
  return body as T
}

/** GET with automatic refresh whenever any mutation calls bump(). Retries 3 times, then exposes err and reload(). */
export function useApi<T = any>(path: string | null) {
  const { rev } = useContext(AppCtx)
  const [data, setData] = useState<T | null>(null)
  const [err, setErr] = useState<Error | null>(null)
  const [tries, setTries] = useState(0)
  useEffect(() => {
    if (!path) return
    let live = true
    const go = (n: number) => api<T>(path).then(d => { if (live) { setData(d); setErr(null) } }).catch(e => {
      if (!live) return
      if (n < 3) setTimeout(() => live && go(n + 1), 500 * (n + 1)); else setErr(e)
    })
    go(0)
    return () => { live = false }
  }, [path, rev, tries])
  return { data, err, reload: () => { setErr(null); setTries(t => t + 1) } }
}
