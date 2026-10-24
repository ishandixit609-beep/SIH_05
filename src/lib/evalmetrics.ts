// Measured, never typed: evidence completeness is counted from the findings themselves.
export const evidenceComplete = (f: any): boolean =>
  Array.isArray(f.evidence) && f.evidence.length > 0 && !!f.rule_version && Array.isArray(f.trace) && f.trace.length > 0

export function evidenceSummary(fins: any[]) {
  const missing = fins.filter(f => !evidenceComplete(f)).map(f => f.id as string)
  return { total: fins.length, complete: fins.length - missing.length, missing }
}
export const pct = (a: number, b: number) => (b === 0 ? 0 : Math.round((1000 * a) / b) / 10)
