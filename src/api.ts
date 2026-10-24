import { useContext, useEffect, useState } from 'react'
import { AppCtx } from './ctx'

// Mock backend is ON unless VITE_API_BASE is set (then every call goes to the real FastAPI server).
const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? '/api'

export async function api<T = any>(path: string, init?: RequestInit & { json?: unknown }): Promise<T> {
  const { json, ...rest } = init ?? {}
  const r = await fetch(BASE + path, { ...rest, headers: { 'Content-Type': 'application/json', ...(rest.headers ?? {}) }, body: json !== undefined ? JSON.stringify(json) : rest.body })
  const body = await r.json().catch(() => ({}))
  if (!r.ok) throw Object.assign(new Error(body.detail ?? body.error ?? r.statusText), { status: r.status, body })
  return body as T
}

/** GET with automatic refresh whenever any mutation calls bump(). */
export function useApi<T = any>(path: string | null) {
  const { rev } = useContext(AppCtx)
  const [data, setData] = useState<T | null>(null)
  const [err, setErr] = useState<Error | null>(null)
  useEffect(() => {
    if (!path) return
    let live = true
    api<T>(path).then(d => live && setData(d)).catch(e => live && setErr(e))
    return () => { live = false }
  }, [path, rev])
  return { data, err }
}
