import { Ladder } from './Ladder'
import { Stamp } from './Stamp'
import { dateIN } from '../lib/format'

/** The Proof-Coverage Matrix as a vertical spine: requirement, document and page, evidence ladder, state, math, expiry. */
export function Spine({ cov, fins, sel, onPick }: { cov: any; fins: any[]; sel: string | null; onPick: (reqId: string, doc: string, page: number) => void }) {
  const math: Record<string, string> = { R04: '3.0 sq m per seat vs 4.0 (illustrative)', R05: 'ends 30 Sep 2027, semester ends 18 Dec 2027', R08: '58 to 83, no declared change' }
  return (
    <div className="slip" data-no="REQUIREMENT SPINE" style={{ padding: 0, borderRightStyle: 'solid' }}>
      {cov.requirements.map((r: any) => {
        const st = r.waived ? 'PASSED' : r.state
        return (
          <button key={r.id} onClick={() => onPick(r.id, r.doc, r.page)} className={r.id === sel ? 'sel' : ''}
            style={{ display: 'block', width: '100%', textAlign: 'left', background: r.id === sel ? 'var(--manila)' : 'transparent', border: 'none', borderBottom: '1px solid var(--rule)', padding: '8px 10px' }}>
            <div className="row between"><span><b className="t sm">{r.id}</b> <span className="sm">{r.title}</span></span><Stamp state={r.conflict ? 'CONFLICT' : st} /></div>
            <div className="row between xs dim" style={{ marginTop: 3 }}>
              <span className="t">{r.doc} p.{r.page}</span><Ladder rung={r.rung} need={Math.min(r.required_rung, 3)} conflict={r.conflict} />
            </div>
            {(math[r.id] || r.waived || r.by === 'human') && <div className="xs" style={{ marginTop: 3 }}>{math[r.id] && <span className="t">{math[r.id]}</span>}{r.waived && <b className="t" style={{ color: 'var(--human)' }}> · WAIVED by officer</b>}{r.by === 'human' && <b className="t" style={{ color: 'var(--human)' }}> · cleared by officer</b>}</div>}
          </button>
        )
      })}
    </div>
  )
}
