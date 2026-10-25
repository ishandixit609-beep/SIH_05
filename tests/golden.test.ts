import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { same } from '../src/lib/norm'
import { grade, checkState, coverageState } from '../src/lib/rung'
import { openChecks, overallState } from '../src/lib/guard'
import { append, verify, entryHash } from '../src/lib/chain'
import { bucket } from '../src/lib/delta'
import { nRequired, maxStaleIfZeroFound } from '../src/lib/sampler'
import { evalRule, simulate } from '../src/lib/rules'
import { inr, num } from '../src/lib/format'

const V = JSON.parse(readFileSync(new URL('./vectors.json', import.meta.url), 'utf8'))

describe('golden vectors (Python == TypeScript)', () => {
  it('text normalisation, incl. Devanagari', () => V.same_text.forEach((c: any) => expect(same(c.a, c.b)).toBe(c.same)))
  it('numeric tolerance', () => V.same_num.forEach((c: any) => expect(same(c.a, c.b, c.tol)).toBe(c.same)))
  it('rung grade', () => V.grade.forEach((c: any) =>
    expect(grade({ docValue: c.doc, docConfidence: c.conf, recordValue: c.rec, adapterStatus: c.adapter })).toEqual(c.expect)))
  it('check state + coverage', () => V.check_state.forEach((c: any) => {
    const i = c.in
    const r = checkState({ configured: i.configured ?? true, hasDocument: i.has_document ?? true, g: i.g ?? { rung: 2, conflict: false },
      requiredRung: i.required_rung ?? 2, maxRung: i.max_rung, rules: i.rules, adapterStatus: i.adapter_status,
      lowConfidence: i.low_confidence, expiry: i.expiry, mustCoverUntil: i.must_cover_until })
    expect(r).toEqual(c.expect); expect(coverageState(r)).toBe(c.coverage)
  }))
  it('guard', () => V.guard.forEach((c: any) => {
    const w = Object.fromEntries(c.waivers.map((x: string) => [x, { officer: 'o', reason: 'r', ts: 't' }]))
    expect(openChecks(c.checks, w)).toEqual(c.open); expect(overallState(c.checks, w)).toBe(c.overall)
  }))
  it('audit chain hashes are byte-identical to Python', async () => {
    const mine: any[] = []
    for (const e of V.chain.events) await append(mine, e)
    expect(mine.map(r => r.hash)).toEqual(V.chain.rows.map((r: any) => r.hash))
    expect(await verify(mine)).toBeNull()
    mine[1].event.actor = 'mallory'
    expect(await verify(mine)).toBe(2)
    expect(await entryHash('0'.repeat(64), V.chain.events[0])).toBe(V.chain.rows[0].hash)
  })
  it('delta buckets', () => V.bucket.forEach((c: any) =>
    expect(bucket(c.new, c.missing ? undefined : c.old, { declared: c.declared, supports: c.supports, tol: c.tol })).toBe(c.expect)))
  it('sampler maths', () => {
    V.sampler.n_required.forEach((c: any) => expect(nRequired(c.p)).toBe(c.n))
    V.sampler.bound.forEach((c: any) => expect(maxStaleIfZeroFound(c.N, c.n)).toBe(c.k))
  })
})

describe('rules from exported JSON tree', () => {
  const rule: any = JSON.parse(readFileSync(new URL('../public/fixtures/rules.json', import.meta.url), 'utf8')).rules[0]
  it('area per seat fails at 3.0 and passes at norm 3.0', () => {
    expect(evalRule(rule, { 'intake.total': 600, 'area.built_up_sqm': 1800 }).state).toBe('FAILED')
    expect(evalRule(rule, { 'intake.total': 600, 'area.built_up_sqm': 1800 }, { min_sqm_per_seat: 3 }).state).toBe('PASSED')
  })
  it('RuleDial counts status changes', () => {
    const inst = [{ id: 'A', claims: { 'intake.total': 600, 'area.built_up_sqm': 1800 } }, { id: 'B', claims: { 'intake.total': 300, 'area.built_up_sqm': 1500 } }]
    expect(simulate(rule, inst, 'min_sqm_per_seat', 3)).toEqual({ count: 1, first10: ['A'] })
  })
})

describe('formatting', () => {
  it('Indian digit grouping', () => { expect(num(180000)).toBe('1,80,000'); expect(inr(2500000)).toContain('25,00,000') })
})
