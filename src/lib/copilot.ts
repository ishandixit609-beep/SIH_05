// Mirror of backend/app/engines/copilot.py: LLM text is accepted only if every figure appears in the findings it cites.
const NUM = /\d[\d,]*\.?\d*/g
export const figures = (s: string): string[] => (s.match(NUM) ?? []).map(n => n.replace(/[,.]+$/, '').replace(/,/g, ''))

export interface NumberCheck { ok: boolean; checked: number; unsupported: string[] }
export function numberCheck(output: string, sources: string[]): NumberCheck {
  const allowed = new Set(sources.flatMap(figures))
  const used = figures(output)
  const bad = used.filter(n => !allowed.has(n))
  return { ok: bad.length === 0, checked: used.length, unsupported: [...new Set(bad)] }
}

/** The text of a finding that the letter is allowed to quote from. */
export const sourceText = (f: any) => `${f.id} ${f.rule_id} ${f.rule_version} ${f.explanation}`
