// Mirror of backend/app/engines/norm.py. Golden-tested against vectors.json.
const VARIANTS: Record<string, string> = {
  shree: 'shri', sri: 'shri', shrimati: 'smt', pvt: 'private', ltd: 'limited', coll: 'college', engg: 'engineering',
}

export function normaliseText(s: string): string {
  const t = (s ?? '').normalize('NFC').toLowerCase().replace(/&/g, ' and ')
  // Keep Letters, Marks, Numbers: Devanagari matras are Marks (\p{M}).
  return t.replace(/[^\p{L}\p{M}\p{N}_\s]/gu, ' ').split(/\s+/).filter(Boolean).map(w => VARIANTS[w] ?? w).join(' ')
}

export function same(a: unknown, b: unknown, relTol = 0): boolean {
  if (typeof a === 'boolean' || typeof b === 'boolean') return a === b
  if (typeof a === 'number' && typeof b === 'number') {
    return a === b || Math.abs(a - b) <= relTol * Math.max(Math.abs(a), Math.abs(b))
  }
  return normaliseText(String(a)) === normaliseText(String(b))
}
