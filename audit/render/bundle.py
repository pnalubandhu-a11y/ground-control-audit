"""Support bundle (`--bundle`): a tarball to attach to a ticket (DESIGN §7).

Contains the structured result (result.json) plus the raw evidence actually
collected during the run (the cached data sources). Redaction is applied when
the profile requires it, so a customer/support bundle carries no internal
identifiers.
"""

from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

from ..core.profile import Profile
from ..core.redact import redact_text
from . import json_out


def _add(tar: tarfile.TarFile, name: str, data: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    tar.addfile(info, io.BytesIO(data))


def write_bundle(
    results,
    verdicts,
    ctx,
    *,
    profile: Profile,
    timestamp: str,
    label: str = "host",
    out_dir: str = ".",
) -> str:
    """Write audit-bundle-<label>-<timestamp>.tar.gz and return its path."""
    stem = f"audit-bundle-{label}-{timestamp}"
    path = Path(out_dir) / f"{stem}.tar.gz"

    payload = json_out.build_payload(results, verdicts, profile=profile)
    result_json = json.dumps(payload, indent=2, default=str).encode()

    with tarfile.open(path, "w:gz") as tar:
        _add(tar, f"{stem}/result.json", result_json)
        # raw evidence = the data sources read during the run (ctx cache)
        for src, text in sorted(ctx._cache.items()):
            if profile.redact:
                text = redact_text(text)
            _add(tar, f"{stem}/evidence/{src}.txt", text.encode())

    return str(path)
