#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Check cross-doc reference FORMAT + EXISTENCE for the leading-slash, PM-repo-root-
relative convention (operator ruling 2026-07-23): /codex/... and /plans/....

Two independent counts, each its own SHRINKING ratchet (same shape as
scripts/quality_gates/check_defi_address_citations.py / no_fallback_imports_baseline.yaml
— NOT zero-tolerance from day 1, since a large pre-existing corpus can't be fixed in one
sitting, but it must never get WORSE):

1. FORMAT — every codex/... reference anywhere in plans/**.md + codex/**.md must be
   written /codex/...; every `related:` frontmatter entry must carry a full leading-slash
   path (/plans/... or /codex/...), never a bare filename. The 2026-07-23 corpus-wide
   migration (scripts/plan-hygiene/fix_reference_paths.py) brought this to book-keeping
   near-zero; the baseline count is what it could NOT safely auto-resolve (ambiguous or
   genuinely dangling bare filenames) — see reference_paths_baseline.yaml.
2. EXISTENCE — every /codex/... or /plans/... reference must resolve to a real file.
   ~1,270 pre-existing dangling refs predate this convention (docs describing planned-but-
   never-shipped codex content, references to plans since renamed/archived under a
   different name, etc.) — a real corpus-health finding, not something this migration
   caused; tracked as its own cleanup in
   plans/active/issues/reference_path_convention_2026_07_23.md.

`depends_on` / `parent_epic` / `supersedes` / `superseded_by` / `entry_point_for` are
deliberately OUT OF SCOPE — those are machine-parsed bare-slug fields per
PLAN_FORMAT.md, not file-path references; touching their format changes backend parsing
semantics, not doc hygiene.

Usage:
  python3 scripts/plan-hygiene/check_reference_paths.py [--quiet] [--update-baseline]
Exit 0 if both counts are <= their baseline. NEVER hand-raise a baseline entry — if a
count needs to go up, something regressed; fix it instead. Ratchet DOWN as the
pre-existing debt gets cleaned up: fix real violations, then re-run --update-baseline.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

PM_DIR = Path(__file__).resolve().parents[2]
BASELINE_PATH = Path(__file__).resolve().parent / "reference_paths_baseline.yaml"

# Anything codex-shaped WITHOUT the correct leading-slash-only prefix: bare `codex/...`
# or a relative `../codex/...` — i.e. NOT preceded by exactly one leading '/' with
# nothing else before it in the path token.
BARE_CODEX_RE = re.compile(r"(?<![\w/.-])(?:\.\./)*codex/[0-9]{2}-[a-z-]+/[A-Za-z0-9_./-]+\.md")

GOOD_REF_RE = re.compile(r"/(?:plans|codex)/[A-Za-z0-9_./-]+\.md")
BARE_MD_RE = re.compile(r"(?<![\w/.-])([A-Za-z0-9_-]+\.md)")


@dataclass(frozen=True)
class Baseline:
    format_count: int = 0
    existence_count: int = 0
    note: str = ""


def load_baseline() -> Baseline:
    if not BASELINE_PATH.exists():
        return Baseline()
    raw = yaml.safe_load(BASELINE_PATH.read_text(encoding="utf-8")) or {}
    return Baseline(
        format_count=int(raw.get("format_count", 0)),
        existence_count=int(raw.get("existence_count", 0)),
        note=str(raw.get("note") or ""),
    )


def write_baseline(format_count: int, existence_count: int, existing: Baseline) -> None:
    """Persist a new baseline. Counts are clamped DOWN — never raised above the
    existing baseline (a higher count means a NEW violation landed; fix it, don't
    bake it in)."""
    new_format = min(format_count, existing.format_count) if existing.format_count else format_count
    new_existence = min(existence_count, existing.existence_count) if existing.existence_count else existence_count
    BASELINE_PATH.write_text(
        "# Baseline for check_reference_paths.py — the /plans/... + /codex/... reference\n"
        "# path convention (operator ruling 2026-07-23).\n"
        "#\n"
        "# This is a SHRINKING ratchet. format_count/existence_count are the number of\n"
        "# pre-existing violations the gate tolerates. A live count EXCEEDING its baseline\n"
        "# fails the check — a NEW violation landed; fix the reference, don't grow the\n"
        "# number. LOWER a count (re-run --update-baseline) the moment violations are fixed.\n"
        "# NEVER hand-raise a count.\n"
        "#\n"
        "# SSOT: codex/11-project-management/cross-reference-path-convention.md,\n"
        "# plans/active/issues/reference_path_convention_2026_07_23.md.\n"
        f"note: Seeded 2026-07-23 — corpus-wide migration via fix_reference_paths.py.\n"
        f"format_count: {new_format}\n"
        f"existence_count: {new_existence}\n",
        encoding="utf-8",
    )


def target_files() -> list[Path]:
    files: list[Path] = []
    for top in ("plans", "codex"):
        base = PM_DIR / top
        if base.exists():
            files.extend(base.rglob("*.md"))
    return files


def extract_related_text(text: str) -> str:
    fm_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not fm_match:
        return ""
    fm_text = fm_match.group(1)
    rel_match = re.search(r"^related:\s*(\[.*?\]|(?:\n(?:[ \t]+.*\n?)*))", fm_text, re.MULTILINE)
    return rel_match.group(1) if rel_match else ""


def main() -> int:
    quiet = "--quiet" in sys.argv
    update = "--update-baseline" in sys.argv
    format_violations: list[str] = []
    existence_violations: list[str] = []
    files = target_files()

    for p in files:
        relpath = p.relative_to(PM_DIR).as_posix()
        text = p.read_text(encoding="utf-8")

        for m in BARE_CODEX_RE.finditer(text):
            format_violations.append(f"{relpath}: bare/relative codex ref '{m.group(0)}' — should be /codex/...")

        related_text = extract_related_text(text)
        for m in BARE_MD_RE.finditer(related_text):
            preceding = related_text[: m.start()]
            if not preceding.endswith("/"):
                format_violations.append(
                    f"{relpath}: related: entry '{m.group(1)}' has no path — should be /plans/... or /codex/..."
                )

        for m in GOOD_REF_RE.finditer(text):
            ref = m.group(0)
            if not (PM_DIR / ref.lstrip("/")).is_file():
                existence_violations.append(f"{relpath}: '{ref}' does not resolve to a real file")

    baseline = load_baseline()

    if not quiet:
        print(f"Reference path check ({len(files)} files scanned):")
        print()
        for v in format_violations:
            print(f"  FORMAT    {v}")
        for v in existence_violations:
            print(f"  DANGLING  {v}")
        print()

    fmt_n, exist_n = len(format_violations), len(existence_violations)
    fmt_ok = fmt_n <= baseline.format_count
    exist_ok = exist_n <= baseline.existence_count

    print(
        f"{'✅' if fmt_ok else '❌'} check_reference_paths (format): {fmt_n} violation(s) "
        f"(baseline {baseline.format_count})"
    )
    print(
        f"{'✅' if exist_ok else '❌'} check_reference_paths (existence): {exist_n} dangling ref(s) "
        f"(baseline {baseline.existence_count}) — see plans/active/issues/reference_path_convention_2026_07_23.md"
    )

    if update:
        write_baseline(fmt_n, exist_n, baseline)
        print(
            f"Baseline updated: format_count={min(fmt_n, baseline.format_count or fmt_n)}, "
            f"existence_count={min(exist_n, baseline.existence_count or exist_n)}"
        )

    return 0 if (fmt_ok and exist_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
