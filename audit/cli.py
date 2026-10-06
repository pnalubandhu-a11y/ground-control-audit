"""argparse entrypoint for `audit`.

This increment wires `-l/--list` end to end. The run flags (`-m`, `-u`,
`--profile`, `--json`, ...) are parsed and validated against the catalog/bundles
but execution is not yet implemented — they print a clear notice and exit 0.
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .core import registry
from .core.catalog import ModuleSpec
from .core.context import Context
from .core.profile import get_profile
from .core.runner import run_modules
from .render import terminal
from .verdicts import evaluate


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="audit",
        description="CoreWeave GPU-fabric flight director (Ground Control)",
    )
    p.add_argument("--version", action="version", version=f"audit {__version__}")
    p.add_argument("-l", "--list", action="store_true",
                   help="list all modules + use-case bundles")
    p.add_argument("-m", "--modules", metavar="IDS",
                   help="run explicit modules, e.g. A1,B3,C16,G7")
    p.add_argument("-u", "--usecase", metavar="BUNDLE",
                   help="run a use-case bundle, e.g. ncc_slow")
    p.add_argument("--profile", choices=["internal", "customer", "support"],
                   default="internal", help="audience profile (default: internal)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--allow-active", action="store_true",
                   help="permit active (fabric-perturbing) tests")
    p.add_argument("--fixture", metavar="DIR",
                   help="run against a recorded fixture set instead of live host")
    p.add_argument("--no-verdict", action="store_true",
                   help="skip the verdict banner; per-module output only")
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def _select(args) -> list[ModuleSpec] | None:
    """Resolve -m / -u into an ordered list of specs, or None if neither given."""
    if args.modules:
        ids = [s.strip() for s in args.modules.split(",") if s.strip()]
        return [registry.get_module(mid) for mid in ids]
    if args.usecase:
        return registry.resolve_bundle(args.usecase)
    return None


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list:
        terminal.print_list()
        return 0

    try:
        specs = _select(args)
    except registry.RegistryError as exc:
        print(f"audit: {exc}", file=sys.stderr)
        return 2

    if specs is None:
        build_parser().print_help()
        return 0

    if args.fixture:
        ctx = Context(mode="fixture", fixture_dir=args.fixture)
    else:
        ctx = Context(mode="live")

    profile = get_profile(args.profile)
    results = run_modules(specs, ctx, allow_active=args.allow_active, profile=profile)
    verdicts = evaluate(results)
    terminal.print_run(results, verdicts, show_verdict=not args.no_verdict,
                       profile=profile)
    return terminal.exit_code(results)


if __name__ == "__main__":
    sys.exit(main())
