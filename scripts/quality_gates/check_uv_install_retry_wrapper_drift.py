#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""PM post-gate (warn-only): detect a dropped ``uv pip install`` retry wrapper across the fleet.

**Context**: every production Dockerfile whose editable install resolves
``unified-trading-library``/``unified-api-contracts`` from the LIVE Artifact Registry index (i.e.
carries a ``RUN --mount=type=secret,id=gar_token`` layer) MUST wrap that layer's
``uv pip install ... --no-sources`` call in a 3-attempt retry loop with exponential backoff — this
absorbs the transient publish-ordering race between a downstream repo's floor-bump landing and the
upstream wheel fully propagating through the registry (root-caused + first fixed
2026-07-29/30, see the incident doc below). The canonical wrapper::

    RUN --mount=type=secret,id=gar_token \\
        UV_EXTRA_INDEX_URL="https://oauth2accesstoken:$(cat /run/secrets/gar_token)@..." \\
        sh -c 'i=1; until uv pip install --system --no-sources -e .; do [ "$i" -ge 3 ] && \\
        { echo "uv pip install failed after 3 attempts" >&2; exit 1; }; w=$((15 * i)); \\
        echo "uv pip install failed (attempt $i/3) -- retrying in ${w}s"; sleep "$w"; \\
        i=$((i + 1)); done'

was hand-applied across 8 repos with nothing enforcing it going forward — a new repo, or a future
edit to one of the 8, can silently drop the retry wrapper (e.g. reverting to a plain
``uv pip install ... --no-sources`` line) with nothing to catch it. This gate makes that drift
visible: it scans every repo's top-level ``Dockerfile`` for a ``RUN --mount=type=secret,id=gar_token``
layer whose ``uv pip install ... --no-sources`` call is NOT wrapped in the documented retry loop, and
WARNS (never blocks — mirrors ``check_base_image_digest_drift.py``'s warn-only post-gate shape).

Scope explicitly excludes ``market-tick-data-service`` (installs UTL/UAC from vendored local
``.deps/`` paths — never resolves from the live GAR index at build time) and
``unified-trading-system-ui`` (no Cloud Build trigger) — same exclusions documented in the SSOT.

Always exits 0 (warn-only post-gate). Violations are prefixed ``⚠ WARN`` and printed to stdout so
the CI log + operator can scan them.

SSOT: codex/06-coding-standards/dockerfile-standards.md § "uv pip install Retry Wrapper
(BuildKit-secret GAR auth)".
Incident provenance: plans/active/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md.

Usage::

    # Standalone -- against local workspace
    python check_uv_install_retry_wrapper_drift.py --workspace-root /path/to/workspace

    # PM quality-gates.sh post-gate (no args needed when CWD is PM root)
    python scripts/quality_gates/check_uv_install_retry_wrapper_drift.py
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR: Final[Path] = Path(__file__).resolve().parent
PM_ROOT: Final[Path] = SCRIPT_DIR.parent.parent
DEFAULT_WORKSPACE_ROOT: Final[Path] = PM_ROOT.parent

GAR_TOKEN_MOUNT: Final[str] = "--mount=type=secret,id=gar_token"
UV_INSTALL_MARKER: Final[str] = "uv pip install"
NO_SOURCES_FLAG: Final[str] = "--no-sources"
RETRY_WRAP_RE: Final[re.Pattern[str]] = re.compile(r"\buntil\s+uv\s+pip\s+install\b")

RUN_INSTRUCTION_RE: Final[re.Pattern[str]] = re.compile(r"^\s*RUN\b", re.IGNORECASE)

# Repos exempt from this check -- same exclusions as
# codex/06-coding-standards/dockerfile-standards.md § "uv pip install Retry Wrapper":
# market-tick-data-service installs UTL/UAC from vendored local .deps/ paths (never resolves
# from the live GAR index at build time); unified-trading-system-ui has no Cloud Build trigger.
EXEMPT_REPOS: Final[frozenset[str]] = frozenset(
    {
        "market-tick-data-service",
        "unified-trading-system-ui",
    }
)


@dataclass(frozen=True)
class Finding:
    """One un-wrapped ``RUN --mount=type=secret,id=gar_token`` layer."""

    dockerfile: Path
    line_no: int  # 1-indexed, the RUN instruction's start line
    snippet: str


# ---------------------------------------------------------------------------
# Dockerfile parsing
# ---------------------------------------------------------------------------


def find_run_spans(lines: list[str]) -> list[tuple[int, int]]:
    """
    Return ``[(start_idx, end_idx), ...]`` (0-indexed, inclusive) for every ``RUN``
    instruction, joining backslash-continuation lines into one logical instruction.
    """
    spans: list[tuple[int, int]] = []
    i = 0
    n = len(lines)
    while i < n:
        if RUN_INSTRUCTION_RE.match(lines[i]):
            start = i
            j = i
            while lines[j].rstrip("\n").rstrip().endswith("\\"):
                j += 1
                if j >= n:
                    j = n - 1
                    break
            spans.append((start, j))
            i = j + 1
        else:
            i += 1
    return spans


def scan_dockerfile(dockerfile: Path) -> list[Finding]:
    """Return every un-wrapped gar_token install layer found in ``dockerfile``."""
    try:
        text = dockerfile.read_text(encoding="utf-8")
    except OSError:
        return []
    lines = text.splitlines(keepends=True)
    findings: list[Finding] = []
    for start, end in find_run_spans(lines):
        joined = "".join(lines[start : end + 1])
        if GAR_TOKEN_MOUNT not in joined:
            continue
        if UV_INSTALL_MARKER not in joined or NO_SOURCES_FLAG not in joined:
            continue
        if RETRY_WRAP_RE.search(joined):
            continue  # already wrapped
        snippet = lines[start].strip()
        findings.append(Finding(dockerfile=dockerfile, line_no=start + 1, snippet=snippet))
    return findings


def scan_fleet(workspace_root: Path) -> dict[str, list[Finding]]:
    """Return ``{repo_name: [Finding, ...]}`` for every repo carrying drift. Clean repos omitted."""
    result: dict[str, list[Finding]] = {}
    for repo_dir in sorted(workspace_root.iterdir()):
        if not repo_dir.is_dir() or repo_dir.name.startswith("."):
            continue
        repo_name = repo_dir.name
        if repo_name in EXEMPT_REPOS:
            continue
        dockerfile = repo_dir / "Dockerfile"
        if not dockerfile.exists():
            continue
        findings = scan_dockerfile(dockerfile)
        if findings:
            result[repo_name] = findings
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=DEFAULT_WORKSPACE_ROOT,
        help="Workspace root containing all repo dirs (default: inferred from script location).",
    )
    args = parser.parse_args(argv)

    workspace_root: Path = args.workspace_root.resolve()
    drift = scan_fleet(workspace_root)

    total_scanned = sum(
        1
        for d in sorted(workspace_root.iterdir())
        if d.is_dir() and not d.name.startswith(".") and d.name not in EXEMPT_REPOS and (d / "Dockerfile").exists()
    )
    print(f"check_uv_install_retry_wrapper_drift: {total_scanned} repo Dockerfile(s) scanned.")

    if not drift:
        print("  No uv pip install retry-wrapper drift detected ✓")
        return 0

    print(f"⚠ WARN — uv pip install retry-wrapper drift detected in {len(drift)} repo(s) (warn-only, non-blocking):")
    for repo_name in sorted(drift):
        for finding in drift[repo_name]:
            rel = finding.dockerfile.relative_to(workspace_root)
            print(f"  {repo_name}: {rel}:{finding.line_no}: {finding.snippet}")
            print(
                "    -> RUN --mount=type=secret,id=gar_token layer's uv pip install ...--no-sources"
                " call is not wrapped in the documented 3-attempt retry loop"
            )
    print(
        "  Remedy: python scripts/propagation/apply-uv-install-retry-wrapper.py --repo <repo>"
        "  (see codex/06-coding-standards/dockerfile-standards.md"
        ' § "uv pip install Retry Wrapper")'
    )

    return 0  # always warn-only


if __name__ == "__main__":
    sys.exit(main())
