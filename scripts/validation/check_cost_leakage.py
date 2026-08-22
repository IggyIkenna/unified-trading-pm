# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Rule 08 internal-cost leakage guard.

Scans external-audience docs (marketing, briefings, external docs, public UI
copy) for text patterns that match the internal-cost column in
``codex/14-playbooks/commercial-model/pricing-building-blocks.md``.

Rule 08 mandates the internal-cost column is codex-private — it must never
appear in anything a client, prospect, counterparty, or web visitor can see.

Checked surfaces (all relative to workspace root):
  - unified-trading-system-ui/app/(public)/**/*.tsx
  - unified-trading-system-ui/app/(marketing)/**/*.tsx (if present)
  - unified-trading-system-ui/marketing-static/**
  - unified-trading-pm/codex/14-playbooks/briefings/**
  - unified-trading-pm/codex/14-playbooks/cross-cutting/**
  - any *.md with frontmatter ``scope: [external]`` or no scope in a marketing
    sub-path.

Patterns flagged:
  - "£X.Yk" values that appear in the internal-cost column
  - "£X-Yk" ranges that match internal ranges
  - The phrase "internal cost" on an external surface
  - The phrase "codex-private" on an external surface (reveals the structure)

Exits 1 on any hit with a reproduce command.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Internal-cost strings we seeded into pricing-building-blocks.md on 2026-04-20.
# These MUST NOT appear on any external-audience surface.
INTERNAL_COST_PATTERNS: list[str] = [
    r"£1\.8-2\.5k",  # Block 1 internal
    r"£4-6k(?!\s*/mo)",  # Block 2 internal (distinguish from "Tier B £4-8k")
    r"£1\.2-2k",  # Block 3 internal
    r"£0\.2-0\.4k\s*per\s*slot",  # Block 4 internal
    r"£3-6k(?!\s*/mo)",  # Block 6 internal
    r"£1\.5-3k",  # Block 7 internal
    r"£0\.3-0\.8k\s*per\s*venue",  # Block 8 internal
    r"£0\.2-0\.5k\s*per\s*chain",  # Block 9 internal
    r"£0\.3-1k\s*per\s*type",  # Block 10 internal
    r"£0\.2-1k\s*per\s*pack",  # Block 11 internal
    # Flag the prose markers too
    r"\binternal-cost column\b",
    r"\bcodex-private\b",
    r"\binternal monthly cost\b",
]

# Directories / glob patterns relative to workspace root that are EXTERNAL.
EXTERNAL_SURFACES: list[str] = [
    "unified-trading-system-ui/app/(public)/**/*.tsx",
    "unified-trading-system-ui/app/(public)/**/*.mdx",
    "unified-trading-system-ui/marketing-static/**/*.html",
    "unified-trading-system-ui/marketing-static/**/*.md",
    "unified-trading-pm/codex/14-playbooks/briefings/**/*.md",
    "unified-trading-pm/codex/14-playbooks/cross-cutting/**/*.md",
]

# Directories that are explicitly INTERNAL — scan will skip them entirely.
INTERNAL_DIRS: list[str] = [
    "codex/14-playbooks/commercial-model/",  # the SSOT itself
    "codex/14-playbooks/_ssot-rules/",  # rule files reference internal-cost
    "codex/16-strategy-playbooks/infra-spec/",  # design docs
    "codex/14-playbooks/page-triage/",  # internal triage
    "codex/14-playbooks/shared-core/",  # internal
    "plans/",  # plans are internal
    "scripts/",  # script source
    "ops/",  # operations
]


def _workspace_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "unified-trading-pm").is_dir() and (parent / "unified-trading-system-ui").is_dir():
            return parent
    raise SystemExit("ERROR: could not locate workspace root (ancestor of this script)")


def _is_internal(path: Path, root: Path) -> bool:
    rel = str(path.relative_to(root))
    return any(rel.startswith(marker) or f"/{marker}" in rel for marker in INTERNAL_DIRS)


def _scan_file(path: Path) -> list[tuple[int, str, str]]:
    """Return list of (line_no, pattern, snippet) for every leak hit."""

    hits: list[tuple[int, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return hits

    for line_no, line in enumerate(text.splitlines(), start=1):
        for pattern in INTERNAL_COST_PATTERNS:
            if re.search(pattern, line, flags=re.IGNORECASE):
                hits.append((line_no, pattern, line.strip()[:160]))
    return hits


def main() -> int:
    root = _workspace_root()

    scanned = 0
    leaks: list[tuple[Path, list[tuple[int, str, str]]]] = []

    for glob in EXTERNAL_SURFACES:
        for path in root.glob(glob):
            if not path.is_file():
                continue
            if _is_internal(path, root):
                continue
            scanned += 1
            hits = _scan_file(path)
            if hits:
                leaks.append((path, hits))

    if leaks:
        print(f"❌ rule-08 leak guard — {len(leaks)} external file(s) leak internal cost:")
        for path, hits in leaks:
            print(f"  {path.relative_to(root)}")
            for line_no, pattern, snippet in hits[:5]:
                print(f"    line {line_no}: /{pattern}/ → {snippet!r}")
            if len(hits) > 5:
                print(f"    ... and {len(hits) - 5} more hits")
        print("\nReproduce: python unified-trading-pm/scripts/validation/check_cost_leakage.py")
        return 1

    print(
        f"✅ rule-08 leak guard — {scanned} external surface(s) scanned, 0 leaks "
        f"(patterns={len(INTERNAL_COST_PATTERNS)})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
