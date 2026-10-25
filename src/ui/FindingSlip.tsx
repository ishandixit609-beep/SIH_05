import { Stamp } from './Stamp'

const COST = ['', 'read a QR', 'request one document', 'query the original issuer']
export function FindingSlip({ f, sel, onPick }: { f: any; sel: boolean; onPick: () => void }) {
  const who = f.ai_read ? 'ai' : 'rules'
  return (
    <div className={`slip ink ${who} ${sel ? 'sel' : ''}`} data-no={f.id} onClick={onPick} style={{ cursor: 'pointer', borderRightStyle: 'solid', opacity: f.resolved ? .55 : 1 }}>
      <div className="row between"><span className={`who ${who}`}>{f.ai_read ? 'AI-read value · rule decided' : 'rule decided'}</span><Stamp state={f.resolved ? 'PASSED' : f.state} /></div>
      <div className="sm" style={{ margin: '5px 0' }}>{f.explanation}</div>
      <div className="t xs dim">{f.rule_id} · {f.rule_version} · {f.severity}{f.decision ? ` · officer: ${f.decision.replace('_', ' ')}` : ''}{f.resolved ? ' · resolved by resubmission' : ''}</div>
    </div>
  )
}

export function NextStep({ f }: { f: any }) {
  if (!f) return null
  const c = f.next_step.cost
  return (
    <div className="slip ink human" data-no="CHEAPEST NEXT STEP" style={{ borderRightStyle: 'solid' }}>
      <div className="row between"><b style={{ fontFamily: 'var(--serif)' }}>{f.next_step.kind.replace(/_/g, ' ')}</b>
        <span className="cost" title={`cost ${c}`}>{Array.from({ length: 5 }, (_, i) => <i key={i} className={i < Math.min(c, 5) ? 'on' : ''} />)}<span className="t xs" style={{ marginLeft: 4 }}>cost {c}</span></span></div>
      <div className="xs dim" style={{ marginTop: 4 }}>{f.next_step.why}</div>
      <div className="xs" style={{ marginTop: 4 }}>Ladder of effort: read QR 1 · request document 2 · query issuer 3 · physical inspection 10</div>
    </div>
  )
}
export { COST }
