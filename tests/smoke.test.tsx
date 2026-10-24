// Renders every page against the mock API (jsdom). Catches runtime errors a type-check cannot.
// @vitest-environment jsdom
import { describe, it, expect, vi, beforeAll, afterAll, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent, cleanup } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { readFileSync } from 'node:fs'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { handlers } from '../src/mocks/handlers'
import { AppCtx } from '../src/ctx'
import { Inbox } from '../src/pages/Inbox'
import { Case } from '../src/pages/Case'
import { Precheck, Fixes } from '../src/pages/Institution'
import { RuleLab, Alerts, AuditPage, Results } from '../src/pages/Others'

vi.mock('../src/ui/PdfViewer', () => ({ PdfViewer: ({ doc, page, box }: any) => <div data-testid="pdf">{doc} p.{page} {box ? 'BOX:' + box.text : ''}</div> }))
const fixtures = http.get('/fixtures/:name', ({ params }) => new HttpResponse(readFileSync(`public/fixtures/${params.name}`), { headers: { 'content-type': 'application/json' } }))
const server = setupServer(fixtures, ...handlers.map(h => h))
beforeAll(() => { server.listen({ onUnhandledRequest: 'error' }); const patched = globalThis.fetch; globalThis.fetch = ((u: any, i?: any) => patched(typeof u === 'string' && u.startsWith('/') ? location.origin + u : u, i)) as any })
afterAll(() => server.close())
afterEach(() => cleanup())

const wrap = (el: JSX.Element, path = '/') => render(
  <AppCtx.Provider value={{ rev: 0, bump: () => {}, lang: 'en', setLang: () => {}, say: () => {} }}><MemoryRouter initialEntries={[path]}><Routes><Route path="*" element={el} /></Routes></MemoryRouter></AppCtx.Provider>)

describe('PS5 additions render against the mock API', () => {
  it('Rule lab hosts the guard lab: one manual-only check withholds the overall state', async () => {
    wrap(<RuleLab />); expect(await screen.findByText(/Click a check to change its state/)).toBeTruthy()
    expect(screen.getByText('Ready for decision')).toBeTruthy()
    fireEvent.click(screen.getByText('make Accreditation manual-only'))
    expect(await screen.findByText('Review incomplete')).toBeTruthy()
  })
  it('Fixes shows a live number check; Results shows recall, evidence completeness and the timer', async () => {
    wrap(<Fixes />); expect(await screen.findByText(/number check passed/)).toBeTruthy(); expect(screen.getAllByText(/Why it matters/).length).toBeGreaterThan(0)
    cleanup(); wrap(<Results />); expect(await screen.findByText(/recall on planted issues/)).toBeTruthy()
    expect(await screen.findByText(/findings with a document page, rule version and trace/)).toBeTruthy(); expect(screen.getByText(/Task for the volunteer/)).toBeTruthy()
  })
})

describe('pages render with the mock API', () => {
  it('Inbox shows the honest fold stack and the red queue', async () => {
    wrap(<Inbox />); expect(await screen.findByText(/carried forward, not re-read/)).toBeTruthy()
    expect(screen.getByText(/at most 23 of 62/)).toBeTruthy(); expect(screen.getAllByText(/F-014/).length).toBeGreaterThan(0)
  })
  it('Case desk: seal withheld with 7 open checks, finding selected, evidence box passed to viewer', async () => {
    wrap(<Case />, '/case?f=F-014'); expect(await screen.findByText(/Seal withheld: 7 open checks/)).toBeTruthy()
    await waitFor(() => expect(screen.getByTestId('pdf').textContent).toContain('D-03 p.8 BOX:Built-up area: 1,800 sq m'))
  })
  it('Approve while open returns the guard 409 in the UI', async () => {
    wrap(<Case />); await screen.findByText(/Seal withheld/)
    fireEvent.click(screen.getByText('Approve (officer decision)'))
    expect(await screen.findByText(/HTTP 409/)).toBeTruthy()
  })
  it('Fixes, Precheck, Rule lab, Alerts, Audit, Results render', async () => {
    wrap(<Fixes />); expect(await screen.findByText(/What we need from you/)).toBeTruthy()
    cleanup(); wrap(<Precheck />); expect(await screen.findByText(/Check your file/)).toBeTruthy()
    cleanup(); wrap(<RuleLab />); expect(await screen.findByText(/peer institutions would change status/)).toBeTruthy()
    cleanup(); wrap(<Alerts />); expect(await screen.findByText(/Document expires inside the semester/)).toBeTruthy()
    cleanup(); wrap(<AuditPage />); expect(await screen.findByText(/Audit chain intact/)).toBeTruthy()
    cleanup(); wrap(<Results />); expect(await screen.findByText(/planted issues found/)).toBeTruthy()
  })
  it('waiver + clear + approve path ends READY FOR DECISION', async () => {
    const post = (p: string, json: any) => fetch(p, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(json) }).then(async r => ({ status: r.status, body: await r.json() }))
    await post('/api/applications/APP-0001/resubmit', {})
    for (const id of ['F-011', 'F-012', 'F-013', 'F-023', 'F-017', 'F-018', 'F-019', 'F-020', 'F-025', 'F-021', 'F-024']) expect((await post(`/api/findings/${id}/decision`, { action: 'accept' })).status).toBe(200)
    expect((await post('/api/findings/F-016/decision', { action: 'accept' })).status).toBe(422)
    expect((await post('/api/applications/APP-0001/decision', { action: 'approve' })).status).toBe(409)
    expect((await post('/api/applications/APP-0001/waivers', { check_id: 'R05', reason: 'too short' })).status).toBe(403)
    for (const id of ['R05', 'R06']) expect((await post('/api/applications/APP-0001/waivers', { check_id: id, reason: 'Renewal receipt seen; original to follow at inspection.' })).status).toBe(200)
    expect((await post('/api/applications/APP-0001/decision', { action: 'approve' })).status).toBe(200)
    const v = await fetch('/api/audit/verify').then(r => r.json()); expect(v.intact).toBe(true); console.log('audit entries at end of flow:', v.entries)
  })
})
