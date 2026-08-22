#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Cleanup empty directories and directories containing only .pyc/.pyo files.

Walks the given root, identifies directories that are either empty or contain
only Python bytecode files (transitively, accounting for nested empty /
bytecode-only directories), and deletes them.

By default skips: .git, .venv*, venv, node_modules, .next, .turbo, .mypy_cache,
.pytest_cache, .ruff_cache (these are tool-managed; if empty they regenerate).

Usage:
    cleanup-empty-dirs.py [ROOT] [--dry-run] [--workers N] [--exclude NAME ...]
                          [--include-cache-dirs] [--quiet]

Exit codes: 0 = success (or nothing to do), 1 = some deletions failed.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Directory names we never descend into. They are either VCS-managed,
# tool-managed caches, or env dirs whose layout we must not touch.
DEFAULT_EXCLUDES: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        ".venv-workspace",
        "venv",
        "env",
        "node_modules",
        ".next",
        ".turbo",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
    }
)

# File extensions we treat as "expendable" — a directory containing only
# these (and/or empty/expendable subdirs) is considered deletable.
EXPENDABLE_SUFFIXES: frozenset[str] = frozenset({".pyc", ".pyo"})


def _is_expendable_file(path: Path) -> bool:
    return path.suffix in EXPENDABLE_SUFFIXES


def scan(root: Path, excludes: frozenset[str]) -> set[Path]:
    """Return the set of directories safe to delete under root.

    A directory is "safe to delete" iff every entry it contains (recursively)
    is either an expendable file (.pyc/.pyo) or another safe-to-delete dir.
    Symlinks are never followed and always count as live content.
    """
    deletable: set[Path] = set()

    def visit(path: Path, is_root: bool) -> bool:
        # Don't descend into excluded names. Treat them as live so the parent
        # isn't marked deletable on their behalf.
        if not is_root and path.name in excludes:
            return False

        try:
            entries = list(path.iterdir())
        except (OSError, PermissionError):
            return False

        has_live = False
        for child in entries:
            if child.is_symlink():
                has_live = True
                continue
            if child.is_dir():
                child_deletable = visit(child, is_root=False)
                if not child_deletable:
                    has_live = True
            elif child.is_file():
                if not _is_expendable_file(child):
                    has_live = True
            else:
                # sockets, fifos, devices — treat as live, don't touch
                has_live = True

        if has_live:
            return False
        if not is_root:
            deletable.add(path)
        return True

    visit(root, is_root=True)
    return deletable


def _delete_tree(path: Path) -> tuple[Path, bool, str]:
    try:
        shutil.rmtree(path)
        return (path, True, "")
    except OSError as exc:
        return (path, False, f"{type(exc).__name__}: {exc}")


def _format_count(deletable: set[Path], top_level: list[Path]) -> str:
    nested = len(deletable) - len(top_level)
    if nested:
        return f"{len(top_level)} top-level ({len(deletable)} total incl. {nested} nested)"
    return f"{len(top_level)}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("root", nargs="?", default=".", help="Root directory to scan (default: cwd)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be deleted; no changes")
    parser.add_argument("--workers", type=int, default=8, help="Parallel deletion workers (default: 8)")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="NAME",
        help="Additional directory basename to skip (repeatable)",
    )
    parser.add_argument(
        "--include-cache-dirs",
        action="store_true",
        help="Also clean .mypy_cache / .pytest_cache / .ruff_cache / .tox / .next / .turbo if empty",
    )
    parser.add_argument("--quiet", action="store_true", help="Only print summary + errors")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    excludes: set[str] = set(DEFAULT_EXCLUDES)
    if args.include_cache_dirs:
        excludes -= {
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".tox",
            ".next",
            ".turbo",
        }
    excludes.update(args.exclude)
    excludes_frozen = frozenset(excludes)

    if not args.quiet:
        print(f"Scanning {root}", file=sys.stderr)
        print(f"Excludes: {sorted(excludes_frozen)}", file=sys.stderr)

    deletable = scan(root, excludes_frozen)
    # Only delete top-level — rmtree handles nested ones.
    top_level = sorted(d for d in deletable if d.parent not in deletable)

    if not deletable:
        if not args.quiet:
            print("Nothing to clean.", file=sys.stderr)
        return 0

    if not args.quiet:
        print(f"Found {_format_count(deletable, top_level)} directories to remove.", file=sys.stderr)

    if args.dry_run:
        for d in top_level:
            try:
                rel = d.relative_to(root)
            except ValueError:
                rel = d
            print(rel)
        return 0

    ok = 0
    fail = 0
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(_delete_tree, d): d for d in top_level}
        for fut in as_completed(futures):
            path, success, err = fut.result()
            try:
                rel = path.relative_to(root)
            except ValueError:
                rel = path
            if success:
                ok += 1
                if not args.quiet:
                    print(f"deleted: {rel}")
            else:
                fail += 1
                print(f"FAILED: {rel}: {err}", file=sys.stderr)

    print(f"Done. Deleted {ok}, failed {fail}.", file=sys.stderr)
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
