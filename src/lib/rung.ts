// Mirror of backend/app/engines/rung.py
import { same } from './norm'

export const CONF_THRESHOLD = 0.85
export type CheckState = 'PASSED' | 'FAILED' | 'MANUAL_REVIEW' | 'NOT_CONFIGURED' | 'UNABLE_TO_VERIFY'
export type AdapterStatus = 'verified' | 'mismatch' | 'expired' | 'pending' | 'source_unavailable' | 'manual_review'

export interface Evidence {
  docValue?: unknown; docConfidence?: number | null; recordValue?: unknown; adapterStatus?: AdapterStatus | null
}
export interface Grade { rung: 0 | 1 | 2 | 3; conflict: boolean }
export interface Check { state: CheckState; reason: string }

export function grade(e: Evidence, relTol = 0, threshold = CONF_THRESHOLD): Grade {
  const has = (v: unknown) => v !== undefined && v !== null
  const docOk = has(e.docValue) && (e.docConfidence ?? 0) >= threshold
  const conflict = e.adapterStatus === 'mismatch' ||
    (has(e.docValue) && has(e.recordValue) && !same(e.docValue, e.recordValue, relTol))
  if (conflict) return { rung: docOk ? 1 : 0, conflict: true }
  if (e.adapterStatus === 'verified') return { rung: 3, conflict: false }
  if (docOk && has(e.recordValue)) return { rung: 2, conflict: false }
  if (docOk) return { rung: 1, conflict: false }
  return { rung: 0, conflict: false }
}

export interface CheckInput {
  configured: boolean; hasDocument: boolean; g: Grade; requiredRung: number; maxRung?: number
  rules?: boolean[]; adapterStatus?: AdapterStatus | null; lowConfidence?: boolean
  expiry?: string | null; mustCoverUntil?: string | null   // ISO yyyy-mm-dd compares correctly as text
}

export function checkState(i: CheckInput): Check {
  if (!i.configured) return { state: 'NOT_CONFIGURED', reason: 'no_rule_or_checklist' }
  if (!i.hasDocument) return { state: 'FAILED', reason: 'missing_document' }
  if (i.adapterStatus === 'expired' || (i.expiry && i.mustCoverUntil && i.expiry < i.mustCoverUntil))
    return { state: 'FAILED', reason: 'expired_or_expires_too_soon' }
  if ((i.rules ?? []).some(r => r === false)) return { state: 'FAILED', reason: 'rule_failed' }
  if (i.g.conflict) return { state: 'MANUAL_REVIEW', reason: 'sources_disagree' }
  if (i.adapterStatus === 'manual_review' || i.lowConfidence) return { state: 'MANUAL_REVIEW', reason: 'needs_human_read' }
  const need = Math.min(i.requiredRung, i.maxRung ?? 3)
  if (i.g.rung < need) {
    const why = i.adapterStatus === 'source_unavailable' || i.adapterStatus === 'pending' ? 'source_unavailable' : 'no_record_to_match'
    return { state: 'UNABLE_TO_VERIFY', reason: why }
  }
  return { state: 'PASSED', reason: 'ok' }
}

export function coverageState(c: Check): string {
  if (c.state === 'FAILED') return c.reason === 'missing_document' ? 'missing' : 'partial'
  return { PASSED: 'complete', MANUAL_REVIEW: 'needs_review', UNABLE_TO_VERIFY: 'unable_to_verify', NOT_CONFIGURED: 'not_configured' }[c.state]
}
