/** Fix-It Copilot flow per finding: Finding > Explained > Checklist > Resubmitted > Re-check. Built from the real finding. */
export function FixNote({ f, resolved }: { f: any; resolved: boolean }) {
  if (!f) return null
  const steps: [string, boolean][] = [['Finding raised', true], ['Explained', true], ['Fix listed', true], ['Resubmitted', resolved], [resolved ? 'Re-check: resolved' : 'Re-check: pending', resolved]]
  return (
    <div style={{ marginTop: 6 }}>
      <div className="xs dim"><b>Why it matters:</b> {f.explanation} <span className="t">({f.rule_id}, {f.rule_version})</span></div>
      <div className="journey" aria-label="Fix progress">{steps.map(([s, on], i) => <span key={s} className={on ? 'on' : ''}>{i + 1}. {s}</span>)}</div>
    </div>
  )
}
