// The fake backend. Fixtures come from the offline generator; guard, waivers, audit chain, resubmission and RuleDial run for real.
import { http, HttpResponse } from 'msw'
import { append, verify, type Row } from '../lib/chain'
import { decide, GuardBlocked, makeWaiver, openChecks, overallState, type Waivers } from '../lib/guard'
import { simulate, type Rule } from '../lib/rules'
import type { CheckState } from '../lib/rung'
import { DEMO_NOW } from '../lib/format'

const cache = new Map<string, Promise<any>>()
const fx = (n: string) => { if (!cache.has(n)) cache.set(n, fetch(`/fixtures/${n}.json`).then(r => r.json()).catch(e => { cache.delete(n); throw e })); return cache.get(n)! }
const OFFICER = 'officer-1'
// which requirement each finding belongs to (so clearing findings can clear the requirement)
const REQ_OF: Record<string, string> = { 'F-011': 'R02', 'F-012': 'R02', 'F-013': 'R02', 'F-023': 'R02', 'F-014': 'R04', 'F-015': 'R04', 'F-016': 'R05',
  'F-017': 'R08', 'F-018': 'R08', 'F-019': 'R08', 'F-020': 'R08', 'F-025': 'R08', 'F-021': 'R07', 'F-022': 'R06', 'F-024': 'R10' }

const chain: Row[] = []
let waivers: Waivers = {}
const decided: Record<string, string> = {}       // findingId -> accept | dismiss | request_info
let resubmitted = false
let startedAt = Date.now()
let booting: Promise<void> | null = null

function boot() { return (booting ??= seed()) }
async function seed() {
  for (const [event, payload] of [['application.submitted', { app: 'APP-0001', version: '1' }], ['stage.read', { docs: '8', fields: '412' }], ['stage.check', { rules: '7', findings: '15' }]] as const)
    await append(chain, { ts: DEMO_NOW, actor: 'system', event, payload })
}

const resolvedByV2 = () => (resubmitted ? new Set(['F-014', 'F-015']) : new Set<string>())

async function live() {
  await boot()
  const cov = await fx('coverage'); const fd = await fx('findings')
  const fins: any[] = fd.findings.map((f: any) => ({ ...f, req: REQ_OF[f.id] ?? null, decision: decided[f.id] ?? null, resolved: resolvedByV2().has(f.id) }))
  const reqs = cov.requirements.map((r: any) => {
    const mine = fins.filter(f => REQ_OF[f.id] === r.id)
    const allCleared = mine.length > 0 && mine.every(f => f.resolved || f.decision === 'accept' || f.decision === 'dismiss')
    if (r.state === 'MANUAL_REVIEW' && allCleared) return { ...r, state: 'PASSED', reason: 'cleared_by_officer', coverage: 'complete', by: 'human', conflict: false }
    if (r.id === 'R04' && resubmitted) return { ...r, state: 'PASSED', reason: 'ok_after_resubmission', coverage: 'complete', rung: 2 }
    return r
  })
  const checks: Record<string, CheckState> = Object.fromEntries(reqs.map((r: any) => [r.id, r.state]))
  return { cov, fins, reqs, checks, bundles: fd.bundles }
}

export const handlers = [
  http.post('/api/applications', async () => { startedAt = Date.now(); await boot(); return HttpResponse.json({ id: 'APP-0001', state: 'queued' }, { status: 202 }) }),
  http.get('/api/applications/:id/events', () => {
    const stages = ['intake', 'read', 'change', 'check', 'verify', 'coverage', 'resolve', 'review']
    const i = Math.min(stages.length, Math.floor((Date.now() - startedAt) / 900))
    return HttpResponse.json({ stages, completed: i, done: i >= stages.length })
  }),
  http.get('/api/applications/:id/summary', async () => {
    const { checks, fins } = await live(); const s = await fx('summary')
    return HttpResponse.json({ ...s, overall: overallState(checks, waivers), open_checks: openChecks(checks, waivers), findings_open: fins.filter(f => !f.resolved && !f.decision).length, version: resubmitted ? 2 : 1 })
  }),
  http.get('/api/applications/:id/coverage', async () => {
    const { reqs, checks } = await live()
    return HttpResponse.json({ requirements: reqs.map((r: any) => ({ ...r, waived: r.id in waivers })), checks, overall: overallState(checks, waivers), open_checks: openChecks(checks, waivers), waivers })
  }),
  http.get('/api/applications/:id/claims', async () => HttpResponse.json(await fx('claims'))),
  http.get('/api/applications/:id/diff', async () => HttpResponse.json(await fx('diff'))),
  http.get('/api/applications/:id/timeline', async () => HttpResponse.json(await fx('timeline'))),
  http.get('/api/applications/:id/photos', async () => HttpResponse.json(await fx('photos'))),
  http.get('/api/findings', async () => { const { fins, bundles } = await live(); return HttpResponse.json({ findings: fins, bundles }) }),
  http.get('/api/findings/:id/graph', async ({ params }) => HttpResponse.json((await fx('graphs'))[params.id as string] ?? { trace: [] })),
  http.get('/api/network/faculty/:token', async () => HttpResponse.json(await fx('network'))),
  http.get('/api/documents/:id/boxes', async () => HttpResponse.json(await fx('boxes'))),
  http.get('/api/alerts', async () => HttpResponse.json(await fx('alerts'))),
  http.get('/api/rules', async () => HttpResponse.json(await fx('rules'))),

  http.post('/api/findings/:id/decision', async ({ params, request }) => {
    const { action } = (await request.json()) as { action: 'accept' | 'dismiss' | 'request_info' }
    const f = (await live()).fins.find(x => x.id === params.id)
    if (f?.state === 'FAILED' && action !== 'request_info')
      return HttpResponse.json({ detail: 'A FAILED finding cannot be accepted or dismissed. Ask the institution to fix it, or record a documented waiver.' }, { status: 422 })
    decided[params.id as string] = action
    await append(chain, { ts: DEMO_NOW, actor: OFFICER, event: `finding.${action}`, payload: { finding: params.id as string } })
    return HttpResponse.json({ ok: true })
  }),
  http.post('/api/applications/:id/resubmit', async () => {
    resubmitted = true
    await append(chain, { ts: DEMO_NOW, actor: 'institution', event: 'application.resubmitted', payload: { version: '2' } })
    return HttpResponse.json(await fx('diff'))
  }),
  http.post('/api/applications/:id/waivers', async ({ request }) => {
    const b = (await request.json()) as { check_id: string; reason: string }
    try {
      const w = makeWaiver(b.check_id, OFFICER, 'senior_officer', b.reason, DEMO_NOW)
      waivers = { ...waivers, [b.check_id]: { officer: w.officer, reason: w.reason, ts: w.ts } }
      await append(chain, { ts: DEMO_NOW, actor: OFFICER, event: 'waiver.recorded', payload: { check: b.check_id, reason: w.reason } })
      return HttpResponse.json(w)
    } catch (e) { return HttpResponse.json({ detail: (e as Error).message }, { status: 403 }) }
  }),
  http.post('/api/applications/:id/decision', async ({ request }) => {
    const { action } = (await request.json()) as { action: 'approve' | 'reject' | 'request_info' }
    const { checks } = await live()
    try {
      const r = decide(action, checks, waivers)
      await append(chain, { ts: DEMO_NOW, actor: OFFICER, event: `decision.${action}`, payload: { app: 'APP-0001' } })
      return HttpResponse.json(r)
    } catch (e) {
      if (e instanceof GuardBlocked) return HttpResponse.json({ detail: 'Seal withheld: required checks are open.', open_checks: e.openChecks }, { status: 409 })
      throw e
    }
  }),
  http.get('/api/audit', async () => { await boot(); return HttpResponse.json(chain) }),
  http.get('/api/audit/verify', async () => { await boot(); const b = await verify(chain); return HttpResponse.json({ intact: b === null, entries: chain.length, first_broken_seq: b, head: chain.at(-1)?.hash ?? '' }) }),
  http.post('/api/audit/_tamper', async () => { await boot(); if (chain[2]) chain[2].event = { ...chain[2].event, payload: { rules: '7', findings: '3' } }; return HttpResponse.json({ ok: true }) }),
  http.post('/api/audit/_repair', async () => { chain.length = 0; booting = null; await boot(); return HttpResponse.json({ ok: true }) }),
  http.post('/api/rules/simulate', async ({ request }) => {
    const b = (await request.json()) as { rule_id: string; param: string; value: number }
    const [rules, peers]: [{ rules: Rule[] }, any[]] = await Promise.all([fx('rules'), fx('peers')])
    const rule = rules.rules.find(r => r.id === b.rule_id)!
    const res = simulate(rule, peers, b.param, b.value)
    return HttpResponse.json({ ...res, total: peers.length, first10: res.first10 })
  }),
  http.post('/api/replay', async () => HttpResponse.json(await fx('replay'))),
  http.get('/api/eval/summary', async () => {
    const [truth, found] = await Promise.all([fx('ground_truth'), fx('findings_ids')])
    const rows = truth.planted.map((p: any) => ({ ...p, found: found.flagged_ids.includes(p.id) }))
    return HttpResponse.json({ rows, planted: rows.length, found: rows.filter((r: any) => r.found).length, false_positives: found.false_positives_on_valid_but_unusual })
  }),
]
