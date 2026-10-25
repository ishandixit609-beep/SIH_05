from __future__ import annotations

from typing import Any, Optional


def ev(n: dict[str, Any], env: dict[str, Any]) -> Any:
    t = n.get("t")
    if t == "num":
        return n["v"]
    if t == "ref":
        p = n["p"]
        if p not in env:
            raise KeyError(f"unknown ref {p}")
        return env[p]
    if t == "bin":
        a = ev(n["l"], env)
        b = ev(n["r"], env)
        op = n["op"]
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            return a / b
    if t == "cmp":
        a = ev(n["l"], env)
        b = ev(n["r"], env)
        op = n["op"]
        if op == ">=":
            return a >= b
        if op == "<=":
            return a <= b
        if op == ">":
            return a > b
        if op == "<":
            return a < b
        if op == "==":
            return a == b
        if op == "!=":
            return a != b
    raise ValueError(f"Unknown node: {n}")


def eval_rule(
    rule: dict[str, Any],
    claims: dict[str, Any],
    param_override: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    if param_override is None:
        param_override = {}
    inputs = rule.get("inputs", [])
    if not all(k in claims for k in inputs):
        return {"ruleId": rule["id"], "state": "NOT_EVALUATED"}

    params = {**rule.get("params", {}), **param_override}
    env = {**claims}
    for k, v in params.items():
        env["params." + k] = v

    val = ev(rule["value"], env)
    env["value"] = val
    passed = ev(rule["expr"], env)
    return {
        "ruleId": rule["id"],
        "state": "PASSED" if passed else "FAILED",
        "value": val,
    }


def simulate(
    rule: dict[str, Any],
    institutions: list[dict[str, Any]],
    param: str,
    next_val: Any,
) -> dict[str, Any]:
    """RuleDial simulation: how many institutions change status if a parameter moves."""
    changed: list[str] = []
    for inst in institutions:
        inst_claims = inst.get("claims", {})
        curr_state = eval_rule(rule, inst_claims).get("state")
        next_state = eval_rule(rule, inst_claims, {param: next_val}).get("state")
        if curr_state != next_state:
            changed.append(inst["id"])
    return {
        "count": len(changed),
        "total": len(institutions),
        "first10": changed[:10],
    }
