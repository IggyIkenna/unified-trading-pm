"""STEP 5.64 — PM script path-reference ratchet.

Scans workflow templates, GHA workflows, and operator bash scripts for references
to PM script paths (relative `scripts/` refs and workspace-absolute
`$WORKSPACE_ROOT/unified-trading-pm/scripts/` refs) and asserts every referenced
path actually exists.

Intent: catch silent regressions where a PM script is renamed or deleted but its
callers (CI workflows, operator runbooks) still reference the old path. These refs
are invisible to the language linter and only fail at operator-runtime.

Exit 0 = all referenced paths resolve.
Exit 1 = one or more broken references (blocking).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ── scan targets (relative to PM root) ──────────────────────────────────────
_SCAN_GLOBS = [
    "scripts/workflow-templates/**/*.yml",
    "scripts/workflow-templates/**/*.yaml",
    "scripts/workflow-templates/**/*.tmpl",
    ".github/workflows/**/*.yml",
    ".github/workflows/**/*.yaml",
    "scripts/**/*.sh",
]

# Patterns that extract a `scripts/<path>` fragment.
# Group 1 is always the path fragment (no leading `scripts/`).
_PATTERNS: list[re.Pattern[str]] = [
    # Relative: bash/python3/source scripts/<path>
    re.compile(
        r'(?:bash|python3?|source)\s+["\']?(?:\./)?scripts/([\w./\-]+)',
        re.IGNORECASE,
    ),
    # Workspace-absolute: ${WORKSPACE_ROOT}/unified-trading-pm/scripts/<path>
    #                  or $WORKSPACE_ROOT/unified-trading-pm/scripts/<path>
    re.compile(
        r"\$\{?WORKSPACE_ROOT\}?/unified-trading-pm/scripts/([\w./\-]+)",
    ),
]

# Lines to skip entirely (existence-guarded, pure-comment, or doc-string patterns).
_SKIP_LINE_RE = re.compile(
    r"""
      ^\s*\#              # full-line comment
    | \[\[?\s*-[fe]       # bash -f / -e existence guard on same line
    | \[\s+-[fe]          # POSIX test -f / -e guard
    | \bif\b[^;]+\s+-[fe]\s  # if ... -f <path>
    | ^\s*echo\b          # echo "... bash scripts/..." — documentation string
    | ^\s*printf\b        # printf "... bash scripts/..." — documentation string
    | ^\s*log_            # log_info/log_warn/log_success helper lines
    """,
    re.VERBOSE,
)

# Extensions / suffixes that are directories, not files
_DIR_SUFFIXES: frozenset[str] = frozenset()


def _scan_file(
    path: Path,
    pm_root: Path,
) -> list[tuple[Path, int, str, Path]]:
    """Return list of (file, lineno, matched_fragment, resolved_path) for broken refs."""
    broken: list[tuple[Path, int, str, Path]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return broken

    for lineno, raw_line in enumerate(lines, start=1):
        if _SKIP_LINE_RE.search(raw_line):
            continue
        for pat in _PATTERNS:
            for m in pat.finditer(raw_line):
                fragment = m.group(1)
                # Strip trailing quote / whitespace noise
                fragment = fragment.rstrip("\"' \t\\")
                if not fragment:
                    continue
                resolved = pm_root / "scripts" / fragment
                if not resolved.exists():
                    broken.append((path, lineno, f"scripts/{fragment}", resolved))
    return broken


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pm-root",
        type=Path,
        default=None,
        help="Path to unified-trading-pm root (default: inferred from this script's location)",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="Workspace root — if set, also scans adjacent repos' workflows and scripts",
    )
    args = parser.parse_args(argv)

    # __file__ lives in scripts/quality_gates/ — two levels up is PM root
    pm_root: Path = args.pm_root.resolve() if args.pm_root else Path(__file__).resolve().parent.parent.parent

    # Collect files to scan from the PM repo itself
    files_to_scan: list[Path] = []
    for glob in _SCAN_GLOBS:
        files_to_scan.extend(pm_root.glob(glob))

    # Optionally scan adjacent repos (workspace-absolute refs used by operators)
    if args.workspace_root and args.workspace_root.is_dir():
        ws = args.workspace_root.resolve()
        for repo_dir in sorted(ws.iterdir()):
            if not repo_dir.is_dir() or repo_dir.name == "unified-trading-pm":
                continue
            for sub_glob in [
                ".github/workflows/**/*.yml",
                "scripts/**/*.sh",
            ]:
                files_to_scan.extend(repo_dir.glob(sub_glob))

    all_broken: list[tuple[Path, int, str, Path]] = []
    for f in sorted(set(files_to_scan)):
        all_broken.extend(_scan_file(f, pm_root))

    if not all_broken:
        print("✅ PM script path-reference ratchet passed — all references resolve")
        return 0

    print(f"❌ PM script path-reference ratchet: {len(all_broken)} broken reference(s) found\n")
    for src_file, lineno, fragment, resolved in sorted(all_broken):
        rel_src = src_file.relative_to(pm_root) if src_file.is_relative_to(pm_root) else src_file
        print(f"  {rel_src}:{lineno}  →  {fragment}  (resolved: {resolved})")

    print(
        "\nFix: ensure the referenced script exists at the resolved path above."
        "\nIf the script was renamed, update all callers."
        "\nIf a reference is documentation-only (not executed), prefix its line with '#'."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
