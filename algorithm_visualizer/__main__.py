"""Command-line entry point: ``python -m algorithm_visualizer``."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from .storage import default_db_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="algorithm-visualizer",
        description="Watch sorting algorithms work, one step at a time.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help=f"history database to use (default: {default_db_path()})",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    from .app import run

    return run(args.db or default_db_path())


if __name__ == "__main__":
    raise SystemExit(main())
