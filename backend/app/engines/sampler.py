from __future__ import annotations

import math


def n_required(p: float, conf: float = 0.95) -> int:
    """Number of carried-forward claims required to sample."""
    return math.ceil(math.log(1.0 - conf) / math.log(1.0 - p))


# Alias to match TypeScript naming if imported
nRequired = n_required


def max_stale_if_zero_found(N: int, n: int, conf: float = 0.95) -> int:
    """Largest number of stale claims among N still consistent (at conf) with finding 0 in n draws."""
    alpha = 1.0 - conf
    best = 0
    for K in range(N + 1):
        prob = 1.0
        for i in range(n):
            prob *= max(N - K - i, 0) / (N - i)
        if prob >= alpha:
            best = K
    return best


maxStaleIfZeroFound = max_stale_if_zero_found


def badge_text(N: int, n: int, stale: int) -> str:
    if stale > 0:
        return f"{stale} of {n} sampled claims were stale. Re-verify all {N} carried-forward claims."
    k = max_stale_if_zero_found(N, n)
    pct = round(100.0 * k / N) if N else 0
    return f"{n} of {N} re-verified, 0 stale. 95% confidence: at most {k} of {N} ({pct}%) are stale."


badgeText = badge_text
