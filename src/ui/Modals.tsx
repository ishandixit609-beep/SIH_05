import { useEffect, useRef, useState } from 'react'

export function WaiveModal({ checkId, onSubmit, onClose }: { checkId: string; onSubmit: (reason: string) => Promise<void>; onClose: () => void }) {
  const [reason, setReason] = useState(''); const [err, setErr] = useState(''); const ref = useRef<HTMLTextAreaElement>(null)
  useEffect(() => ref.current?.focus(), [])
  const ok = reason.trim().length >= 15
  return (
    <>
      <div className="veil" onClick={onClose} />
      <div className="modal" role="dialog" aria-label="Record a waiver">
        <h3>Waive {checkId}</h3>
        <p className="xs dim">A waiver is a human act. Your id, the check, this reason and the time are written to the audit chain. Minimum 15 characters.</p>
        <textarea ref={ref} rows={4} value={reason} onChange={e => setReason(e.target.value)} placeholder="e.g. University portal down; original consent letter seen at inspection." />
        {err && <div className="err">{err}</div>}
        <div className="row" style={{ marginTop: 10, justifyContent: 'flex-end' }}>
          <button className="btn" onClick={onClose}>Cancel</button>
          <button className="btn dark" disabled={!ok} onClick={() => onSubmit(reason).catch(e => setErr(e.message))}>Record waiver</button>
        </div>
      </div>
    </>
  )
}

export function ClauseDrawer({ f, rule, onClose }: { f: any | null; rule: any | null; onClose: () => void }) {
  return (
    <>
      {f && <div className="veil" onClick={onClose} />}
      <aside className={`drawer ${f ? 'on' : ''}`} aria-label="Clause">
        {f && <>
          <div className="row between"><h2>Clause behind the rule</h2><button className="btn" onClick={onClose}>Close</button></div>
          <div className="stack" style={{ marginTop: 14 }}>
            <div className="t sm">{f.id} · {f.rule_id} · {f.rule_version}</div>
            {rule ? <>
              <div className="slip" style={{ borderRightStyle: 'solid' }}><div className="who rules">Rule {rule.id}</div><div style={{ fontFamily: 'var(--serif)', margin: '4px 0' }}>{rule.title}</div>
                <div className="t xs">inputs: {rule.inputs.join(', ')}</div><div className="t xs">params: {JSON.stringify(rule.params)}</div></div>
              <div className="slip" style={{ borderRightStyle: 'solid' }}><div className="who human">Clause pointer</div>
                <div className="t sm">{rule.clause.doc} · ref {rule.clause.ref} · page {rule.clause.page ?? 'n/a'}</div>
                <div style={{ marginTop: 6 }}><span className="stamp NOT_CONFIGURED">illustrative</span></div>
                <div className="xs dim" style={{ marginTop: 6 }}>Norm values and clause text are placeholders. Copy them from the AICTE Approval Process Handbook 2024-27 into rules/eoa_v1.yaml before real use.</div></div>
            </> : <div className="slip" style={{ borderRightStyle: 'solid' }}>This finding comes from a reader, a sampler or a hint rather than a numeric rule, so it has no clause. It is a prompt for human review.</div>}
          </div>
        </>}
      </aside>
    </>
  )
}
