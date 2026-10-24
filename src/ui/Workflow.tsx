import { useEffect, useState } from 'react'

export interface Step { n: number; who: 'ai' | 'rules' | 'human'; title: string; big: string; line: string }
/** The whole product in one picture. Every number is counted from the loaded case, so it can be explained and checked. */
export function Workflow({ steps }: { steps: Step[] }) {
  const [on, setOn] = useState(-1)
  useEffect(() => { const t = setInterval(() => setOn(o => (o + 1) % (steps.length + 2)), 1100); return () => clearInterval(t) }, [steps.length])
  const tag = { ai: 'AI reads', rules: 'Rules decide', human: 'Human decides' }
  return (
    <div className="flow" role="list" aria-label="How a case moves through SATYAPAN">
      {steps.map((s, i) => (
        <div key={s.n} role="listitem" className={`fstep ${s.who} ${on >= i ? 'lit' : ''}`}>
          <div className="fn">{s.n}</div>
          <div className="fwho">{tag[s.who]}</div>
          <div className="ft">{s.title}</div>
          <div className="fb">{s.big}</div>
          <div className="fl">{s.line}</div>
        </div>
      ))}
    </div>
  )
}
