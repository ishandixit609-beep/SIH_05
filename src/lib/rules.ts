// Evaluates the JSON syntax tree exported by bengine.export_json(). No eval(), no new Function(), no dependency.
export type Node =
  | { t: 'num'; v: number }
  | { t: 'ref'; p: string }
  | { t: 'bin'; op: '+' | '-' | '*' | '/'; l: Node; r: Node }
  | { t: 'cmp'; op: '>=' | '<=' | '>' | '<' | '==' | '!='; l: Node; r: Node }

export interface Rule {
  id: string; title: string; inputs: string[]; params: Record<string, number>; severity: string
  required_rung: number; clause: { doc: string; ref: string; page: number | null }; message: string
  value: Node; expr: Node
}

function ev(n: Node, env: Record<string, number>): number | boolean {
  switch (n.t) {
    case 'num': return n.v
    case 'ref': { if (!(n.p in env)) throw new Error('unknown ref ' + n.p); return env[n.p] }
    case 'bin': {
      const a = ev(n.l, env) as number, b = ev(n.r, env) as number
      return n.op === '+' ? a + b : n.op === '-' ? a - b : n.op === '*' ? a * b : a / b
    }
    case 'cmp': {
      const a = ev(n.l, env) as number, b = ev(n.r, env) as number
      return { '>=': a >= b, '<=': a <= b, '>': a > b, '<': a < b, '==': a === b, '!=': a !== b }[n.op]
    }
  }
}

export interface RuleResult { ruleId: string; state: 'PASSED' | 'FAILED' | 'NOT_EVALUATED'; value?: number }

export function evalRule(r: Rule, claims: Record<string, number>, paramOverride: Record<string, number> = {}): RuleResult {
  if (!r.inputs.every(k => k in claims)) return { ruleId: r.id, state: 'NOT_EVALUATED' }
  const params = { ...r.params, ...paramOverride }
  const env: Record<string, number> = { ...claims }
  for (const [k, v] of Object.entries(params)) env['params.' + k] = v
  const value = ev(r.value, env) as number
  env['value'] = value
  return { ruleId: r.id, state: ev(r.expr, env) ? 'PASSED' : 'FAILED', value }
}

/** RuleDial: how many institutions change status if a parameter moves. Applies nothing. */
export function simulate(rule: Rule, institutions: { id: string; claims: Record<string, number> }[], param: string, next: number) {
  const changed = institutions.filter(i =>
    evalRule(rule, i.claims).state !== evalRule(rule, i.claims, { [param]: next }).state)
  return { count: changed.length, first10: changed.slice(0, 10).map(i => i.id) }
}
