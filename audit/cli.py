"""argparse entrypoint for `audit`.

Wires the full DESIGN §4 flag set: -l, -m, -u, --profile, --json, --allow-active,
--fixture, --no-verdict, -v/--verbose, --bundle, --nodes.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from . import menu
from .core import registry
from .core.catalog import ModuleSpec
from .core.context import Context
from .core.nodes import expand_nodes
from .core.profile import Profile, get_profile
from .core.runner import run_modules
from .render import bundle, json_out, terminal
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
    p.add_argument("--bundle", action="store_true",
                   help="write a support tarball (audit-bundle-*.tar.gz)")
    p.add_argument("--nodes", metavar="SPEC",
                   help="cluster fan-out, e.g. gpu-[210-214] (needs --fixture)")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="show per-module evidence")
    return p


def _select(args) -> list[ModuleSpec] | None:
    """Resolve -m / -u into an ordered list of specs, or None if neither given."""
    if args.modules:
        ids = [s.strip() for s in args.modules.split(",") if s.strip()]
        return [registry.get_module(mid) for mid in ids]
    if args.usecase:
        return registry.resolve_bundle(args.usecase)
    return None


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run_one(specs, ctx, args, profile: Profile, *, label: str) -> int:
    """Run one node's modules, render, optionally bundle. Return its exit code."""
    results = run_modules(specs, ctx, allow_active=args.allow_active, profile=profile)
    verdicts = evaluate(results)
    if args.json:
        json_out.print_json(results, verdicts, profile=profile)
    else:
        terminal.print_run(results, verdicts, show_verdict=not args.no_verdict,
                           profile=profile, verbose=args.verbose)
    if args.bundle:
        path = bundle.write_bundle(results, verdicts, ctx, profile=profile,
                                   timestamp=_timestamp(), label=label)
        print(f"audit: wrote {path}", file=sys.stderr)
    return terminal.exit_code(results)


def _fanout(specs, args, profile: Profile) -> int:
    """Run the audit across several nodes and aggregate (needs --fixture)."""
    if not args.fixture:
        print("audit: --nodes requires --fixture in this build "
              "(live multi-node fan-out is a stretch goal)", file=sys.stderr)
        return 2
    base = Path(args.fixture)
    worst, failing = 0, []
    for node in expand_nodes(args.nodes):
        fdir = base / node if (base / node).is_dir() else base
        ctx = Context(mode="fixture", fixture_dir=fdir)
        print(f"\n===== node: {node} =====")
        code = _run_one(specs, ctx, args, profile, label=node)
        worst = max(worst, code)
        if code == 2:
            failing.append(node)
    print(f"\n===== cluster rollup: {len(expand_nodes(args.nodes))} nodes, "
          f"{len(failing)} with failures "
          f"{'(' + ', '.join(failing) + ')' if failing else ''} =====")
    return worst


def _launch_menu(args, profile: Profile) -> int:
    """Interactive symptom picker; each choice runs a bundle via the normal path."""
    def run_bundle(name: str) -> int:
        specs = registry.resolve_bundle(name)
        ctx = (Context(mode="fixture", fixture_dir=args.fixture) if args.fixture
               else Context(mode="live"))
        return _run_one(specs, ctx, args, profile, label="host")
    return menu.run_menu(run_bundle, out=sys.stdout)


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
        # No modules/bundle chosen: open the troubleshooting menu on an
        # interactive terminal; otherwise fall back to help (keeps pipes/CI safe).
        if sys.stdin.isatty() and not args.json:
            return _launch_menu(args, get_profile(args.profile))
        build_parser().print_help()
        return 0

    profile = get_profile(args.profile)

    if args.nodes:
        return _fanout(specs, args, profile)

    ctx = (Context(mode="fixture", fixture_dir=args.fixture) if args.fixture
           else Context(mode="live"))
    return _run_one(specs, ctx, args, profile, label="host")


if __name__ == "__main__":
    sys.exit(main())
