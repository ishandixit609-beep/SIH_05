// Mirror of backend/app/engines/guard.py
import type { CheckState } from './rung'

export type Overall = 'REVIEW_INCOMPLETE' | 'READY_FOR_DECISION'
export type Waivers = Record<string, { officer: string; reason: string; ts: string }>

export const openChecks = (checks: Record<string, CheckState>, waivers: Waivers): string[] =>
  Object.entries(checks).filter(([id, st]) => st !== 'PASSED' && !(id in waivers)).map(([id]) => id).sort()

export const overallState = (c: Record<string, CheckState>, w: Waivers): Overall =>
  openChecks(c, w).length === 0 ? 'READY_FOR_DECISION' : 'REVIEW_INCOMPLETE'

export class GuardBlocked extends Error {
  constructor(public openChecks: string[]) { super('open checks') }
}

export function makeWaiver(checkId: string, officer: string, role: string, reason: string, ts: string, roles = ['senior_officer']) {
  if (!roles.includes(role)) throw new Error('role not permitted to waive')
  if ((reason ?? '').trim().length < 15) throw new Error('a written reason of at least 15 characters is mandatory')
  return { checkId, officer, reason: reason.trim(), ts }
}

export function decide(action: 'approve' | 'reject' | 'request_info', c: Record<string, CheckState>, w: Waivers) {
  if (action !== 'approve') return { action, allowed: true }
  const left = openChecks(c, w)
  if (left.length) throw new GuardBlocked(left)   // the mock API turns this into HTTP 409
  return { action, allowed: true }
}
