/** Small SVG/CSS charts. No chart library: everything follows the theme variables, so dark mode just works. */
export interface Part { label: string; value: number; color: string }

export function Donut({ parts, center, sub, size = 150 }: { parts: Part[]; center: string; sub: string; size?: number }) {
  const total = parts.reduce((a, p) => a + p.value, 0) || 1; const r = 52, c = 2 * Math.PI * r; let off = 0
  return (
    <svg viewBox="0 0 150 150" width={size} height={size} role="img" aria-label={`${sub}: ${parts.map(p => `${p.label} ${p.value}`).join(', ')}`}>
      <circle cx="75" cy="75" r={r} fill="none" stroke="var(--manila-lo)" strokeWidth="16" />
      {parts.map(p => { const len = (p.value / total) * c; const el = <circle className="dseg" style={{ ['--c' as any]: c, animationDelay: `${parts.indexOf(p) * 0.12}s` }} key={p.label} cx="75" cy="75" r={r} fill="none" stroke={p.color} strokeWidth="16" strokeDasharray={`${Math.max(len - 2, 0)} ${c}`} strokeDashoffset={-off} transform="rotate(-90 75 75)" />; off += len; return el })}
      <text x="75" y="76" textAnchor="middle" fontSize="28" fontWeight="600">{center}</text>
      <text x="75" y="94" textAnchor="middle" fontSize="9" fontFamily="var(--type)" fill="var(--ink-2)">{sub}</text>
    </svg>
  )
}

export function Legend({ parts }: { parts: Part[] }) {
  return <div className="legend" style={{ flexDirection: 'column', gap: 5 }}>{parts.map(p => <span key={p.label}><i style={{ background: p.color }} />{p.label} <b style={{ color: 'var(--ink)' }}>{p.value}</b></span>)}</div>
}

/** One row per requirement: three steps for the evidence rung reached; dashed outline marks the rung the requirement needs. */
export function CoverageBars({ reqs }: { reqs: any[] }) {
  return (
    <div>
      {reqs.map(r => (
        <div key={r.id} className="hbar" title={`${r.title}: rung ${r.rung}, needs ${Math.min(r.required_rung, 3)}`}>
          <b className="t xs">{r.id}</b>
          <span className="trk">{[1, 2, 3].map(i => <i key={i} className={`${i <= r.rung ? (r.conflict ? 'bad' : 'on') : ''} ${i === Math.min(r.required_rung, 3) ? 'need' : ''}`} />)}</span>
          <span className="t xs dim" style={{ minWidth: 70, textAlign: 'right' }}>{r.conflict ? 'conflict' : r.rung >= Math.min(r.required_rung, 3) ? 'enough' : `${r.rung} of ${Math.min(r.required_rung, 3)}`}</span>
        </div>
      ))}
      <div className="legend"><span><i style={{ background: 'var(--acc)' }} />rung reached</span><span><i style={{ background: 'var(--stamp)' }} />sources disagree</span><span><i style={{ outline: '1.5px dashed var(--warn)', outlineOffset: 1 }} />rung needed</span></div>
    </div>
  )
}

/** Peers as dots, a fitted line through them, the application in red. An outlier is visible without reading a number. */
export function Scatter({ pts, me, xl, yl }: { pts: { x: number; y: number }[]; me: { x: number; y: number; label: string }; xl: string; yl: string }) {
  const W = 440, H = 250, L = 46, B = 36, T = 14, R = 14
  const all = [...pts, me]; const xs = all.map(p => p.x), ys = all.map(p => p.y)
  const x0 = Math.min(...xs) * 0.92, x1 = Math.max(...xs) * 1.05, y0 = Math.min(...ys) * 0.85, y1 = Math.max(...ys) * 1.08
  const X = (v: number) => L + ((v - x0) / (x1 - x0)) * (W - L - R), Y = (v: number) => H - B - ((v - y0) / (y1 - y0)) * (H - B - T)
  const n = pts.length || 1, mx = pts.reduce((a, p) => a + p.x, 0) / n, my = pts.reduce((a, p) => a + p.y, 0) / n
  const sxx = pts.reduce((a, p) => a + (p.x - mx) ** 2, 0) || 1, k = pts.reduce((a, p) => a + (p.x - mx) * (p.y - my), 0) / sxx, b = my - k * mx
  const ticks = (a: number, z: number) => [0, 1, 2, 3].map(i => a + ((z - a) * i) / 3)
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={`${yl} against ${xl} for peer institutions, this application highlighted`}>
      {ticks(y0, y1).map(v => <g key={'y' + v}><line x1={L} x2={W - R} y1={Y(v)} y2={Y(v)} stroke="var(--rule)" /><text x={L - 6} y={Y(v) + 3} textAnchor="end" fontSize="9" fontFamily="var(--type)" fill="var(--ink-2)">{Math.round(v)}</text></g>)}
      {ticks(x0, x1).map(v => <text key={'x' + v} x={X(v)} y={H - B + 14} textAnchor="middle" fontSize="9" fontFamily="var(--type)" fill="var(--ink-2)">{Math.round(v)}</text>)}
      <line className="trend" x1={X(x0)} y1={Y(k * x0 + b)} x2={X(x1)} y2={Y(k * x1 + b)} stroke="var(--acc)" strokeWidth="1.5" strokeDasharray="5 4" opacity=".7" />
      {pts.map((p, i) => <circle className="dot" style={{ animationDelay: `${Math.min(i * 0.025, 0.9)}s` }} key={i} cx={X(p.x)} cy={Y(p.y)} r="4" fill="var(--acc)" opacity=".55" />)}
      <circle cx={X(me.x)} cy={Y(me.y)} r="13" fill="var(--stamp)" opacity=".18"><animate attributeName="r" values="9;16;9" dur="2.2s" repeatCount="indefinite" /></circle>
      <circle cx={X(me.x)} cy={Y(me.y)} r="6" fill="var(--stamp)" stroke="var(--paper)" strokeWidth="2" />
      <text x={Math.min(X(me.x) + 10, W - 120)} y={Y(me.y) - 10} fontSize="10" fontFamily="var(--type)" fontWeight="700" fill="var(--stamp)">{me.label}</text>
      <text x={(L + W - R) / 2} y={H - 6} textAnchor="middle" fontSize="9.5" fontFamily="var(--type)" fill="var(--ink-2)">{xl}</text>
      <text transform={`translate(11 ${(T + H - B) / 2}) rotate(-90)`} textAnchor="middle" fontSize="9.5" fontFamily="var(--type)" fill="var(--ink-2)">{yl}</text>
    </svg>
  )
}

/** Distribution of a peer measure with the rule threshold drawn on it. Bars to the left of the line would change status. */
export function Histogram({ values, marker, label, bins = 14 }: { values: number[]; marker: number; label: string; bins?: number }) {
  const W = 900, H = 230, L = 30, B = 34, T = 20
  if (!values.length) return null
  const lo = Math.min(...values, marker) * 0.95, hi = Math.max(...values, marker) * 1.03, bw = (hi - lo) / bins
  const counts = Array.from({ length: bins }, (_, i) => values.filter(v => v >= lo + i * bw && (i === bins - 1 ? v <= hi : v < lo + (i + 1) * bw)).length)
  const mx = Math.max(...counts, 1); const X = (v: number) => L + ((v - lo) / (hi - lo)) * (W - L - 26)
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={`Distribution of ${label} across peers with the rule threshold at ${marker.toFixed(1)}`}>
      {counts.map((c, i) => { const x = X(lo + i * bw), w = X(lo + (i + 1) * bw) - x - 2, h = (c / mx) * (H - B - T), under = lo + (i + 1) * bw <= marker; return <rect className="hb" style={{ animationDelay: `${i * 0.04}s` }} key={i} x={x} y={H - B - h} width={Math.max(w, 1)} height={h} rx="2" fill={under ? 'var(--stamp)' : 'var(--acc)'} opacity={under ? .85 : .55} /> })}
      <line x1={L} x2={W - 26} y1={H - B} y2={H - B} stroke="var(--ink-2)" />
      <line x1={X(marker)} x2={X(marker)} y1={T - 4} y2={H - B} stroke="var(--ink)" strokeWidth="1.5" strokeDasharray="4 3" />
      <text x={X(marker) + 5} y={T + 6} fontSize="12" fontFamily="var(--type)" fontWeight="700">rule {marker.toFixed(1)}</text>
      {[0, 1, 2, 3, 4].map(i => { const v = lo + ((hi - lo) * i) / 4; return <text key={i} x={X(v)} y={H - B + 14} textAnchor="middle" fontSize="11" fontFamily="var(--type)" fill="var(--ink-2)">{v.toFixed(1)}</text> })}
      <text x={(L + W) / 2} y={H - 3} textAnchor="middle" fontSize="11" fontFamily="var(--type)" fill="var(--ink-2)">{label}</text>
    </svg>
  )
}

/** Horizontal found / planted bars for the results page. */
export function RatioBars({ rows }: { rows: { label: string; a: number; b: number }[] }) {
  return <div>{rows.map(r => <div key={r.label} style={{ margin: '10px 0' }}><div className="row between xs"><span>{r.label}</span><b className="t">{r.a} / {r.b}</b></div>
    <div style={{ height: 10, borderRadius: 5, background: 'var(--manila-lo)', marginTop: 4, overflow: 'hidden' }}><div style={{ width: `${r.b ? (100 * r.a) / r.b : 0}%`, height: '100%', background: 'var(--rules)', borderRadius: 5, transformOrigin: 'left' }} className="rbar" /></div></div>)}</div>
}
