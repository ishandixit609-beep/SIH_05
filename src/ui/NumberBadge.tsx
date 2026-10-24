import { numberCheck, sourceText } from '../lib/copilot'
/** Runs the zero-invented-numbers check on a drafted letter, live, against the findings it cites. */
export function NumberBadge({ text, fins }: { text: string; fins: any[] }) {
  const cited = fins.filter(f => text.includes(f.id))
  if (cited.length === 0) return <span className="stamp MANUAL_REVIEW" style={{ marginTop: 6 }}>no findings cited: officer must check</span>
  const nc = numberCheck(text, cited.map(sourceText))
  return (
    <div style={{ marginTop: 8 }}>
      <span className={`stamp ${nc.ok ? 'PASSED' : 'FAILED'}`}>{nc.ok ? `number check passed · ${nc.checked} figures, all from ${cited.length} cited findings` : `number check failed: ${nc.unsupported.join(', ')}`}</span>
    </div>
  )
}
