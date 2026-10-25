// Mirror of backend/app/audit/chain.py. Uses the browser's Web Crypto. No floats in payloads.
export const GENESIS = '0'.repeat(64)

export function canonical(v: unknown): string {
  if (Array.isArray(v)) return '[' + v.map(canonical).join(',') + ']'
  if (v && typeof v === 'object') {
    const o = v as Record<string, unknown>
    return '{' + Object.keys(o).sort().map(k => JSON.stringify(k) + ':' + canonical(o[k])).join(',') + '}'
  }
  return JSON.stringify(v)
}

export async function sha256Hex(text: string): Promise<string> {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('')
}

export interface Row { seq: number; event: Record<string, unknown>; prev_hash: string; hash: string }

export const entryHash = (prev: string, event: unknown) => sha256Hex(prev + canonical(event))

export async function append(chain: Row[], event: Record<string, unknown>): Promise<Row> {
  const prev = chain.length ? chain[chain.length - 1].hash : GENESIS
  const row = { seq: chain.length + 1, event, prev_hash: prev, hash: await entryHash(prev, event) }
  chain.push(row)
  return row
}

/** null when intact, else the first broken seq. */
export async function verify(chain: Row[]): Promise<number | null> {
  let prev = GENESIS
  for (const r of chain) {
    if (r.prev_hash !== prev || r.hash !== await entryHash(prev, r.event)) return r.seq
    prev = r.hash
  }
  return null
}
