#!/usr/bin/env python3
"""Soft check: detect active plans whose body-keyword profile doesn't match their
declared parent_epic.

Scores each plan in plans/active/ against every epic's keyword surface in
codex/12-agent-workflow/epic-keyword-surface.yaml.

A plan is flagged as a suspect mismatch only when BOTH hold:
  1. the declared parent_epic is NOT among the top-N keyword matches
     (default N=3), AND
  2. the best-scoring epic beats the declared epic by at least `--margin`
     keyword hits (default 2).

Rationale: keyword overlap is a weak signal on a data-pipeline-heavy corpus
(most plans share mtds/defi/manifest vocabulary), so the old "declared must be
the exact #1 match" rule flagged ~44% of plans — the cutover master, the
deliberately-mtds-parented canonicalisation suite, every features plan, etc.
A plausibly-homed plan sits at rank 2-3 or within a narrow margin of the top;
only a plan whose declared epic is both out-of-top-N and decisively beaten is a
genuine candidate for re-parenting.

Exit 0  — all plans match their declared epic OR are orphans (no parent_epic,
          already caught by the orphan check).
Exit 1  — at least one mismatch (for --strict mode only; default is warn-only).

Usage:
    python3 scripts/plan-hygiene/check_parent_epic_alignment.py [--quiet] [--strict] [--top-n N] [--margin M]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import cast

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PM_DIR = Path(__file__).resolve().parents[2]
PLANS_DIR = PM_DIR / "plans" / "active"
KEYWORD_SURFACE_PATH = PM_DIR / "codex" / "12-agent-workflow" / "epic-keyword-surface.yaml"

# ---------------------------------------------------------------------------
# Minimal YAML loader (no external dependency; parses only the nested-list
# structure used by epic-keyword-surface.yaml)
# ---------------------------------------------------------------------------


def _load_keyword_surface(path: Path) -> dict[str, dict[str, list[str]]]:
    """Parse epic-keyword-surface.yaml without PyYAML dependency.

    Expected format::

        epic_slug:
          keywords:
            - token1
            - token2
          repos:
            - repo1

    Returns {epic_slug: {"keywords": [...], "repos": [...]}}
    """
    surface: dict[str, dict[str, list[str]]] = {}
    current_epic: str | None = None
    current_section: str | None = None

    for line in path.read_text(encoding="utf-8").splitlines():
        # Skip comment lines and blank lines
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Top-level epic key: no leading spaces, ends with ":"
        if not line.startswith(" ") and not line.startswith("\t") and line.rstrip().endswith(":"):
            epic_slug = line.strip().rstrip(":")
            if epic_slug:
                current_epic = epic_slug
                surface[current_epic] = {"keywords": [], "repos": []}
                current_section = None
            continue

        # Second-level key (keywords: / repos:)
        if current_epic and re.match(r"^\s{2,4}\w+\s*:$", line):
            key = stripped.rstrip(":")
            current_section = key if key in ("keywords", "repos") else None
            continue

        # List item under current section
        if current_epic and current_section and re.match(r"^\s+- ", line):
            value = stripped.lstrip("- ").strip()
            if value:
                surface[current_epic][current_section].append(value)

    return surface


# ---------------------------------------------------------------------------
# Frontmatter parser
# ---------------------------------------------------------------------------


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Extract key: value pairs from the YAML frontmatter (--- delimiters)."""
    fm: dict[str, str] = {}
    in_fm = False
    for i, line in enumerate(text.splitlines()):
        if line.strip() == "---":
            if not in_fm and i == 0:
                in_fm = True
                continue
            elif in_fm:
                break
        if in_fm:
            m = re.match(r'^(\w[\w_-]*):\s*"?(.+?)"?\s*$', line)
            if m:
                fm[m.group(1)] = m.group(2)
    return fm


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def _score_plan_against_surface(body: str, surface: dict[str, dict[str, list[str]]]) -> list[tuple[str, int]]:
    """Return list of (epic_slug, score) sorted descending by score."""
    body_lower = body.lower()
    scores: list[tuple[str, int]] = []
    for epic, data in surface.items():
        count = sum(1 for kw in data.get("keywords", []) if kw.lower() in body_lower)  # noqa: qg-empty-fallback
        scores.append((epic, count))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true", help="Suppress PASS output")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on any mismatch")
    parser.add_argument(
        "--top-n",
        type=int,
        default=3,
        help="Declared epic is treated as plausible if within the top-N keyword matches (default 3)",
    )
    parser.add_argument(
        "--margin",
        type=int,
        default=2,
        help="Confidence margin: only WARN if top epic beats declared by >= this many keyword hits (default 2)",
    )
    args = parser.parse_args(argv)
    # argparse Namespace attributes are typed Any; pin them to typed locals so the
    # strict basedpyright ratchet (PM scripts/ baseline) stays clean.
    quiet = cast(bool, args.quiet)
    strict = cast(bool, args.strict)
    top_n = cast(int, args.top_n)
    margin = cast(int, args.margin)

    if not KEYWORD_SURFACE_PATH.exists():
        print(
            f"ERROR: keyword surface not found at {KEYWORD_SURFACE_PATH}\nRun Phase 1.1 to create it first.",
            file=sys.stderr,
        )
        return 1

    surface = _load_keyword_surface(KEYWORD_SURFACE_PATH)
    if not surface:
        print("ERROR: keyword surface loaded empty — check YAML format.", file=sys.stderr)
        return 1

    plans = sorted(
        list(PLANS_DIR.glob("*.md")) + list((PLANS_DIR / "issues").glob("*.md"))
        if (PLANS_DIR / "issues").exists()
        else PLANS_DIR.glob("*.md")
    )

    mismatch_count = 0
    checked_count = 0

    for plan_path in plans:
        text = plan_path.read_text(encoding="utf-8")
        fm = _parse_frontmatter(text)
        declared = fm.get("parent_epic", "").strip()  # noqa: qg-empty-fallback

        if not declared:
            # Orphan — skip (orphan check handles this separately)
            continue

        if declared not in surface:
            # Declared epic not in surface — surface may be incomplete; skip silently
            continue

        checked_count += 1
        scores = _score_plan_against_surface(text, surface)

        if not scores:
            continue

        top_epic, top_score = scores[0]
        top3 = scores[:3]

        if top_score == 0:
            # No keywords matched at all — likely a tiny plan; skip rather than false-positive
            continue

        # Rank (1-based) + score of the DECLARED epic within the full sorted list.
        declared_rank = next((i for i, (e, _s) in enumerate(scores, start=1) if e == declared), None)
        declared_score = next((s for e, s in scores if e == declared), 0)

        # Flag a genuine mismatch only when the declared epic is BOTH outside the
        # top-N AND beaten by the confidence margin. This silences the dominant
        # false-positive class (a plausible epic at rank 2-3, or a near-tie) that
        # made the old "#1-only" rule warn on ~44% of the corpus.
        in_top_n = declared_rank is not None and declared_rank <= top_n
        decisive_gap = (top_score - declared_score) >= margin

        if not in_top_n and decisive_gap:
            mismatch_count += 1
            score_str = ", ".join(f"{e}={s}" for e, s in top3)
            print(
                f"WARN  {plan_path.name}: declared parent_epic={declared!r} "
                f"(rank {declared_rank}, score {declared_score}) "
                f"but top match is {top_epic!r} by >= {margin} "
                f"(top-3 scores: {score_str})"
            )
        elif not quiet:
            note = (
                ""
                if top_epic == declared
                else f" [top={top_epic}; declared rank {declared_rank} within top-{top_n} or inside margin — plausible]"
            )
            print(f"OK    {plan_path.name}: parent_epic={declared!r} (score={declared_score}){note}")

    if not quiet:
        print(
            f"\n{'WARN' if mismatch_count else 'PASS'}  "
            f"Checked {checked_count} plans — {mismatch_count} suspect mismatch(es)."
        )

    if strict and mismatch_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
