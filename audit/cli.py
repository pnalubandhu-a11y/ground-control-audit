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
from .render import terminal


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
    p.add_argument("--no-verdict", action="store_true",
                   help="skip the verdict banner; per-module output only")
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def _not_implemented(what: str) -> int:
    print(
        f"audit: {what} is parsed but not implemented yet in this build.\n"
        f"       The module runner + verdict engine land in the next increment.\n"
        f"       Try `audit -l` to see the catalog.",
        file=sys.stderr,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list:
        terminal.print_list()
        return 0

    # Validate run selectors against the catalog/bundles even though execution
    # is not wired yet — fail fast on typos, and prove the registry works.
    try:
        if args.modules:
            ids = [s.strip() for s in args.modules.split(",") if s.strip()]
            for mid in ids:
                registry.get_module(mid)  # raises RegistryError on unknown id
            return _not_implemented(f"running modules {ids}")

        if args.usecase:
            specs = registry.resolve_bundle(args.usecase)  # raises on unknown bundle
            ids = [s.id for s in specs]
            return _not_implemented(f"running bundle {args.usecase!r} ({ids})")
    except registry.RegistryError as exc:
        print(f"audit: {exc}", file=sys.stderr)
        return 2

    build_parser().print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
