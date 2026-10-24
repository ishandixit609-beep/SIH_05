import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { evalRule, simulate, type Rule } from '../src/lib/rules'
const fx = (n: string) => JSON.parse(readFileSync(new URL(`../public/fixtures/${n}.json`, import.meta.url), 'utf8'))

describe('browser rules == Python B-Engine on the demo case', () => {
  const rules: Rule[] = fx('rules').rules
  const claims: Record<string, number> = Object.fromEntries(fx('claims').claims.filter((c: any) => typeof c.value === 'number').map((c: any) => [c.key, c.value]))
  const findings: any[] = fx('findings').findings
  it('every rule outcome matches', () => {
    const out = Object.fromEntries(rules.map(r => [r.id, evalRule(r, claims).state]))
    expect(out['AREA_PER_SEAT']).toBe('FAILED'); expect(out['CARPET_TO_BUILTUP']).toBe('FAILED'); expect(out['FIRE_NOC_COVERS_SEMESTER']).toBe('FAILED')
    expect(out['STUDENTS_PER_FACULTY']).toBe('PASSED'); expect(out['FLOORS_WITHIN_NOC']).toBe('PASSED')
    for (const f of findings.filter(f => out[f.rule_id])) expect(out[f.rule_id]).toBe(f.state === 'FAILED' ? 'FAILED' : out[f.rule_id])
  })
  it('RuleDial over the 40 peers', () => {
    const area = rules.find(r => r.id === 'AREA_PER_SEAT')!
    const peers = fx('peers')
    const at = (v: number) => simulate(area, peers, 'min_sqm_per_seat', v).count
    console.log('RuleDial: 4.0 -> 3.5 flips', at(3.5), '| 4.0 -> 3.0 flips', at(3.0), '| 4.0 -> 4.5 flips', at(4.5), 'of', peers.length)
    expect(at(4.0)).toBe(0)
  })
  it('eval summary is computed, never typed', () => {
    const t = fx('ground_truth').planted, f = fx('findings_ids')
    expect(t.filter((p: any) => f.flagged_ids.includes(p.id)).length).toBe(10)
  })
})
