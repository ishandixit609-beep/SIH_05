import { useState } from 'react'
import { overallState } from '../lib/guard'
import type { CheckState } from '../lib/rung'
import { Stamp } from './Stamp'

const NAMES = ['Land details', 'Faculty data', 'Facilities', 'Financial proof', 'Trust identity', 'Fire safety', 'Accreditation', 'Affiliation', 'Infrastructure photos', 'Intake match']
const CYCLE: CheckState[] = ['PASSED', 'MANUAL_REVIEW', 'NOT_CONFIGURED', 'UNABLE_TO_VERIFY', 'FAILED']

/** No-Silent-Pass demo: flip any required check and watch the overall state. Uses the real guard function. */
export function GuardLab() {
  const [st, setSt] = useState<Record<string, CheckState>>(Object.fromEntries(NAMES.map(n => [n, 'PASSED' as CheckState])))
  const overall = overallState(st, {}); const passed = NAMES.filter(n => st[n] === 'PASSED').length
  const flip = (n: string) => setSt(s => ({ ...s, [n]: CYCLE[(CYCLE.indexOf(s[n]) + 1) % CYCLE.length] }))
  return (
    <div className="slip ink rules" data-no="GUARD LAB · NO-SILENT-PASS" style={{ marginTop: 18, borderRightStyle: 'solid' }}>
      <div className="row between"><span className="sm">Click a check to change its state. {passed} of {NAMES.length} passed.</span>
        <span className="row"><button className="btn" onClick={() => setSt(s => ({ ...s, Accreditation: 'MANUAL_REVIEW' }))}>make Accreditation manual-only</button>
          <button className="btn" onClick={() => setSt(Object.fromEntries(NAMES.map(n => [n, 'PASSED' as CheckState])))}>reset</button></span></div>
      <div className="guardgrid">{NAMES.map(n => <button key={n} className="guardcell" onClick={() => flip(n)}><span className="sm">{n}</span><Stamp state={st[n]} /></button>)}</div>
      <div className="row" style={{ marginTop: 12 }}>
        <span className={`stamp big ${overall === 'READY_FOR_DECISION' ? 'PASSED' : 'FAILED'}`}>{overall === 'READY_FOR_DECISION' ? 'Ready for decision' : 'Review incomplete'}</span>
        <span className="xs dim">{overall === 'READY_FOR_DECISION' ? 'Every required check is passed. The system still never approves; an officer decides.' : 'One open required check is enough. There is no green "all good" label while a check is missing.'}</span>
      </div>
      <div className="xs dim" style={{ marginTop: 6 }}>This lab is separate from the case. It only demonstrates the rule.</div>
    </div>
  )
}
