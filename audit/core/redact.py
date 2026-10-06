"""Profile-based redaction of internal identifiers (DESIGN §2, customer profile).

Masks real IPs, hostnames, MAC addresses, GPU UUIDs, and serial numbers from
anything shown to a customer, while keeping device-class scopes (gpu:3, mlx5_4,
eth1) intact — the customer still needs to know *which* device is affected.
"""

from __future__ import annotations

import re
from dataclasses import replace

from .result import ModuleResult, Verdict

# (pattern, replacement) applied in order. UUID/MAC before IP; serial last.
_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}"), "GPU-<uuid>"),
    (re.compile(r"\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b"), "<mac>"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "<ip>"),
    # node hostnames: h100-233-129, g08387e, *.coreweave.com / k8s hosts
    (re.compile(r"\bh\d{2,4}-[\w.-]+"), "<host>"),
    (re.compile(r"\bg[0-9a-f]{6}\b"), "<host>"),
    (re.compile(r"\b[a-z0-9-]+\.(?:coreweave\.com|k8s[\w.-]*)\b"), "<host>"),
    # serial numbers / long opaque ids (>=10 digits) — after IPs (which have dots)
    (re.compile(r"\b\d{10,}\b"), "<serial>"),
]


def redact_text(text: str) -> str:
    if not text:
        return text
    for pat, repl in _RULES:
        text = pat.sub(repl, text)
    return text


def redact_result(r: ModuleResult) -> ModuleResult:
    """Return a copy of a result with internal identifiers masked."""
    return replace(
        r,
        summary=redact_text(r.summary),
        scope=redact_text(r.scope),
        remediation=redact_text(r.remediation),
        evidence=_redact_obj(r.evidence),
    )


def redact_verdict(v: Verdict) -> Verdict:
    return replace(v, verdict=redact_text(v.verdict), scope=redact_text(v.scope))


def _redact_obj(obj):
    if isinstance(obj, str):
        return redact_text(obj)
    if isinstance(obj, dict):
        return {k: _redact_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact_obj(v) for v in obj]
    return obj
