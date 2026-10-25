/** Three headline tiles, every number counted from the coverage matrix and photo checks. One segment per requirement or photo. */
export function HealthTiles({ cov, ph }: { cov: any; ph: any }) {
  const reqs: any[] = cov.requirements; const photos: any[] = ph?.photos ?? []
  const passed = reqs.filter(r => (r.waived ? 'PASSED' : r.state) === 'PASSED')
  const enough = reqs.filter(r => r.rung >= Math.min(r.required_rung, 3) && !r.conflict)
  const inside = photos.filter(p => p.status === 'inside_campus'), far = photos.filter(p => p.status === 'far_from_campus')
  const P = (a: number, b: number) => (b ? Math.round((100 * a) / b) : 0)
  return (
    <div className="tiles">
      <div className="tile c1"><div className="tl">Regulatory compliance</div><div className="big">{P(passed.length, reqs.length)}%</div><div className="sub">{passed.length} of {reqs.length} requirements passed</div>
        <div className="segs">{reqs.map(r => <i key={r.id} title={r.id} className={(r.waived ? 'PASSED' : r.state) === 'PASSED' ? 'on' : r.state === 'FAILED' ? 'bad' : 'mid'} />)}</div>
        <div className="how">Each bar is one requirement: white passed, amber needs a human, red failed. Percent = passed ÷ all requirements.</div></div>
      <div className="tile c2"><div className="tl">Infrastructure evidence</div><div className="big">{P(inside.length, photos.length)}%</div><div className="sub">{inside.length} of {photos.length} photos verified on campus · {far.length} far</div>
        <div className="segs">{photos.map(p => <i key={p.photo} title={`photo ${p.photo}`} className={p.status === 'inside_campus' ? 'on' : p.status === 'far_from_campus' ? 'bad' : ''} />)}</div>
        <div className="how">Each bar is one photo: white inside the campus polygon, red far away, grey has no GPS. Percent = inside ÷ all photos.</div></div>
      <div className="tile c3"><div className="tl">Document verification</div><div className="big">{P(enough.length, reqs.length)}%</div><div className="sub">{enough.length} of {reqs.length} reach the evidence rung needed</div>
        <div className="segs">{reqs.map(r => <i key={r.id} title={r.id} className={r.conflict ? 'bad' : r.rung >= Math.min(r.required_rung, 3) ? 'on' : 'mid'} />)}</div>
        <div className="how">Each bar is one requirement: white reached the proof level it needs, amber short, red sources disagree. Percent = reached ÷ all.</div></div>
    </div>
  )
}
