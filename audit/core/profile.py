"""Audience profiles — the one branch point for audience behavior (DESIGN §2).

The same checks run for everyone; a profile changes only three things: safety
(read-only enforcement), redaction, and output packaging. Modules and the
verdict engine stay profile-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Profile:
    name: str
    enforce_readonly: bool   # block active (fabric-perturbing) tests outright
    redact: bool             # mask internal IPs / hostnames / serials / UUIDs
    show_remediation: bool   # print plain-English fix + support escalation


PROFILES: dict[str, Profile] = {
    "internal": Profile("internal", enforce_readonly=False, redact=False,
                        show_remediation=False),
    "customer": Profile("customer", enforce_readonly=True, redact=True,
                        show_remediation=True),
    # support reuses customer safety/redaction; its bundle packaging is a
    # later increment.
    "support": Profile("support", enforce_readonly=True, redact=True,
                       show_remediation=True),
}


def get_profile(name: str) -> Profile:
    return PROFILES[name]
