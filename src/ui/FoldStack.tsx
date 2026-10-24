import { useState } from 'react'
import { badgeText } from '../lib/sampler'

/** Carried-forward claims as a folded stack. The badge states the exact finite-population bound, not a flattering one. */
export function FoldStack({ claims, sample, stale = 0 }: { claims: { key: string; bucket: string }[]; sample: string[]; stale?: number }) {
  const [open, setOpen] = useState(false)
  const un = claims.filter(c => c.bucket === 'UNCHANGED')
  return (
    <div className={`fold ${open ? 'open' : ''}`}>
      <button className="sheet1" onClick={() => setOpen(o => !o)} aria-expanded={open}>
        <div className="row between"><span className="who rules">Delta engine</span><span className="xs t dim">{open ? 'click to fold' : 'click to unfold'}</span></div>
        <div className="row" style={{ alignItems: 'baseline', gap: 14, marginTop: 4 }}>
          <span className="big">{un.length}</span><span style={{ fontFamily: 'var(--serif)', fontSize: '1.15rem' }}>carried forward, not re-read</span>
        </div>
        <div className="t sm" style={{ marginTop: 6 }}>{sample.length} sampled · {stale} stale</div>
        <div className="xs dim" style={{ marginTop: 4 }}>{badgeText(un.length, sample.length, stale)} A sample is a tripwire, not a clearance.</div>
        {open && <div className="cols">{un.map(c => <div key={c.key} className={sample.includes(c.key) ? 'samp' : ''}>{sample.includes(c.key) ? '» ' : ''}{c.key}</div>)}</div>}
      </button>
    </div>
  )
}
