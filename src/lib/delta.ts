// Mirror of backend/app/engines/delta.py (bucketing). Runs for real in the browser on claims.json.
import { same } from './norm'
export type Bucket = 'NEW' | 'UNCHANGED' | 'CHANGED_WITH_EVIDENCE' | 'CHANGED_NO_EXPLANATION'

export function bucket(next: unknown, prev: unknown | undefined, o: { declared?: boolean; supports?: boolean; tol?: number } = {}): Bucket {
  if (prev === undefined) return 'NEW'
  if (same(next, prev, o.tol ?? 0)) return 'UNCHANGED'
  return o.declared && o.supports ? 'CHANGED_WITH_EVIDENCE' : 'CHANGED_NO_EXPLANATION'
}

export function counts(b: Bucket[]) {
  return b.reduce((m, x) => ({ ...m, [x]: (m[x] ?? 0) + 1 }), {} as Record<Bucket, number>)
}
