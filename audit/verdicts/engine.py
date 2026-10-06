"""The correlation layer: ModuleResults -> named Verdicts.

Rules are authored in rules.yaml. A rule fires when every condition matches a
result whose status is in the allowed set AND (if `same_scope` is set) all the
matched results share one scope. The shared scope is substituted into the
verdict sentence.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from ..core.result import ModuleResult, Status, Verdict

_RULES_PATH = Path(__file__).resolve().parent / "rules.yaml"


@lru_cache(maxsize=1)
def load_rules(path: str | None = None) -> list[dict]:
    p = Path(path) if path else _RULES_PATH
    with p.open() as fh:
        rules = yaml.safe_load(fh) or []
    if not isinstance(rules, list):
        raise ValueError(f"{p} must be a list of rules")
    return rules


def evaluate(results: list[ModuleResult], rules: list[dict] | None = None) -> list[Verdict]:
    """Return verdicts for all rules that fire, highest severity first."""
    if rules is None:
        rules = load_rules()
    by_id: dict[str, ModuleResult] = {r.id: r for r in results}
    verdicts: list[Verdict] = []
    for rule in rules:
        v = _match(rule, by_id)
        if v is not None:
            verdicts.append(v)
    verdicts.sort(key=lambda v: v.severity, reverse=True)
    return verdicts


def _match(rule: dict, by_id: dict[str, ModuleResult]) -> Verdict | None:
    when = rule.get("when", {})
    conditions = when.get("all", [])
    matched: list[ModuleResult] = []
    for cond in conditions:
        res = by_id.get(cond["module"])
        if res is None:
            return None
        allowed = {Status(s) for s in cond["status"]}
        if res.status not in allowed:
            return None
        matched.append(res)

    scopes = {m.scope for m in matched}
    if when.get("same_scope") and len(scopes) != 1:
        return None  # conditions matched but not on one shared scope
    # Use the shared scope when the matched results agree; else fall back to node.
    scope = next(iter(scopes)) if len(scopes) == 1 else "node"

    return Verdict(
        id=rule["id"],
        verdict=rule["verdict"].format(scope=scope),
        confidence=rule.get("confidence", "medium"),
        severity=rule.get("severity", 0),
        scope=scope,
        supporting=[m.id for m in matched],
    )
