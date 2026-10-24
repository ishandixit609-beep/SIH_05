// Honest badge maths for the FoldStack. Mirror of backend/app/engines/sampler.py
export const nRequired = (p: number, conf = 0.95) => Math.ceil(Math.log(1 - conf) / Math.log(1 - p))

/** Largest number of stale claims among N still consistent (at `conf`) with finding none in n draws. */
export function maxStaleIfZeroFound(N: number, n: number, conf = 0.95): number {
  const alpha = 1 - conf
  let best = 0
  for (let K = 0; K <= N; K++) {
    let prob = 1
    for (let i = 0; i < n; i++) prob *= Math.max(N - K - i, 0) / (N - i)
    if (prob >= alpha) best = K
  }
  return best
}

export function badgeText(N: number, n: number, stale: number): string {
  if (stale > 0) return `${stale} of ${n} sampled claims were stale. Re-verify all ${N} carried-forward claims.`
  const k = maxStaleIfZeroFound(N, n)
  return `${n} of ${N} re-verified, 0 stale. 95% confidence: at most ${k} of ${N} (${Math.round(100 * k / N)}%) are stale.`
}
