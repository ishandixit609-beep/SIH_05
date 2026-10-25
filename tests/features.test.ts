// Tests for the PS5 additions: number check, evidence completeness, no-silent-pass lab logic.
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { numberCheck, sourceText } from '../src/lib/copilot'
import { evidenceSummary, pct } from '../src/lib/evalmetrics'
import { overallState } from '../src/lib/guard'
import { LETTER } from '../src/ui/DiffBundle'

const fins: any[] = JSON.parse(readFileSync('public/fixtures/findings.json', 'utf8')).findings
const cited = (t: string) => fins.filter(f => t.includes(f.id)).map(sourceText)

describe('Fix-It Copilot number check', () => {
  it('accepts the shipped letters in all three languages', () => {
    for (const l of ['en', 'hi', 'mr']) { const r = numberCheck(LETTER[l], cited(LETTER[l])); expect(cited(LETTER[l]).length).toBeGreaterThan(0); expect(r.ok, `${l}: ${r.unsupported}`).toBe(true) }
  })
  it('rejects a figure that is not in the cited findings', () => {
    const bad = LETTER.en + ' Please pay 5,000 within 7 days.'
    const r = numberCheck(bad, cited(bad)); expect(r.ok).toBe(false); expect(r.unsupported).toEqual(expect.arrayContaining(['5000', '7']))
  })
})
describe('evidence completeness is counted, not typed', () => {
  it('counts findings that carry evidence, rule version and trace', () => {
    const e = evidenceSummary(fins); expect(e.total).toBe(15); expect(e.complete + e.missing.length).toBe(15)
    expect(e.missing).toContain('F-017'); expect(e.complete).toBeGreaterThan(0)
  })
  it('pct rounds to one decimal and survives zero', () => { expect(pct(10, 10)).toBe(100); expect(pct(1, 3)).toBe(33.3); expect(pct(0, 0)).toBe(0) })
})
describe('No-Silent-Pass lab logic', () => {
  const all = Object.fromEntries(Array.from({ length: 10 }, (_, i) => ['c' + i, 'PASSED'])) as any
  it('ten passed is ready; one manual-only check withholds', () => {
    expect(overallState(all, {})).toBe('READY_FOR_DECISION')
    expect(overallState({ ...all, c6: 'MANUAL_REVIEW' }, {})).toBe('REVIEW_INCOMPLETE')
  })
  it('not configured and unable to verify also withhold', () => {
    expect(overallState({ ...all, c1: 'NOT_CONFIGURED' }, {})).toBe('REVIEW_INCOMPLETE')
    expect(overallState({ ...all, c2: 'UNABLE_TO_VERIFY' }, {})).toBe('REVIEW_INCOMPLETE')
  })
})
