from __future__ import annotations

from typing import Any, Iterable, Optional, Union


class GuardBlocked(Exception):
    def __init__(self, open_checks: list[str]):
        super().__init__("open checks")
        self.open_checks = open_checks


def open_checks(
    checks: dict[str, str],
    waivers: Union[dict[str, Any], Iterable[str]],
) -> list[str]:
    """Return sorted list of check IDs that are not PASSED and not waived."""
    wset = set(waivers.keys()) if isinstance(waivers, dict) else set(waivers)
    return sorted(id_ for id_, st in checks.items() if st != "PASSED" and id_ not in wset)


def overall_state(
    checks: dict[str, str],
    waivers: Union[dict[str, Any], Iterable[str]],
) -> str:
    """Return 'READY_FOR_DECISION' if no open checks remain, else 'REVIEW_INCOMPLETE'."""
    return "READY_FOR_DECISION" if len(open_checks(checks, waivers)) == 0 else "REVIEW_INCOMPLETE"


def make_waiver(
    check_id: str,
    officer: str,
    role: str,
    reason: str,
    ts: str,
    roles: tuple[str, ...] = ("senior_officer",),
) -> dict[str, Any]:
    if role not in roles:
        raise PermissionError("role not permitted to waive")
    cleaned_reason = (reason or "").strip()
    if len(cleaned_reason) < 15:
        raise ValueError("a written reason of at least 15 characters is mandatory")
    return {
        "check_id": check_id,
        "checkId": check_id,
        "officer": officer,
        "reason": cleaned_reason,
        "ts": ts,
    }


def decide(
    action: str,
    checks: dict[str, str],
    waivers: Union[dict[str, Any], Iterable[str]],
) -> dict[str, Any]:
    if action != "approve":
        return {"action": action, "allowed": True}
    left = open_checks(checks, waivers)
    if left:
        raise GuardBlocked(left)
    return {"action": action, "allowed": True}
