#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Corpus-wide `authoritative_for` collision scanner for the `/docs-reconcile` skill's Phase 1
item 1 hunter (`cursor-configs/skills/docs-reconcile/SKILL.md`).

Why this exists: a hand-rolled `rg`/`awk` pass over `authoritative_for:` lines only catches the
same-line flow-style form (`authoritative_for: [topic]`). A meaningful fraction of docs use
YAML BLOCK-style lists (`authoritative_for:` on its own line, followed by indented `- "topic"`
items) or a multi-line flow list (`authoritative_for: [\n  "topic",\n]`) — a naive single-line
grep silently drops these from the scan, which is exactly the kind of blind spot this skill's
own charter warns about ("An absence result is evidence ONLY once you've confirmed you probed
the vocabulary the WRITER actually emits"). This script reuses `docspec.parse_frontmatter` (the
SAME trusted YAML parser `check_frontmatter_schema.py` uses) instead, so every YAML style is
handled uniformly and correctly.

Reports:
  1. Exact-string collisions: the same normalized topic claimed by 2+ different `status: current`
     docs — this is the primary, high-confidence signal (skill Phase 1 item 1's core check).
  2. Near-duplicate candidate pairs (topics sharing a 3+-word run): a cheap secondary signal for
     a human/sub-agent to triage — expect noise from shared boilerplate phrasing (e.g. every
     alerting runbook opens "operator response when..."), NOT every pair is a real collision.

Usage:
  python3 scripts/docs/docs_reconcile_authoritative_for_collisions.py [--pm-root PATH]

Exit code is always 0 (this is a report, not a gate) — the skill's own Phase 2 adversarial
verification step is what decides whether a candidate is real.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import docspec
import yaml


def _pm_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--pm-root",
        type=Path,
        default=None,
        help="override the PM repo root (default: derived from this script's own location)",
    )
    args = ap.parse_args(argv)

    pm_root = args.pm_root or _pm_root()

    by_topic: dict[str, list[str]] = defaultdict(list)
    total_files = 0
    total_claims = 0
    current_files = 0
    no_status_field: list[str] = []
    parse_errors: list[tuple[str, str]] = []

    for md_path in sorted(pm_root.rglob("*.md")):
        rel = str(md_path.relative_to(pm_root))
        if "/node_modules/" in rel or rel.startswith(".git/"):
            continue
        try:
            text = md_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        try:
            fm, _ = docspec.parse_frontmatter(text)
        except yaml.YAMLError as e:
            parse_errors.append((rel, str(e).splitlines()[0]))
            continue
        if not fm:
            continue
        af = fm.get("authoritative_for")
        if not af:
            continue
        total_files += 1
        status = fm.get("status")
        if status is None:
            no_status_field.append(rel)
            continue
        if status != "current":
            continue
        current_files += 1
        topics = af if isinstance(af, list) else [af]
        for t in topics:
            if not isinstance(t, str) or not t.strip():
                continue
            total_claims += 1
            norm = " ".join(t.strip().lower().split())
            by_topic[norm].append(rel)

    print(f"YAML parse errors (skipped -- plans/archive/**, SKILL.md-style non-docspec files): {len(parse_errors)}")
    print(f"files with authoritative_for: {total_files}")
    print(f"status:current files among them: {current_files}")
    print(f"total status:current topic claims: {total_claims}")
    print(f"files with authoritative_for but no status field: {len(no_status_field)}")

    print()
    print("=== EXACT-STRING collisions (same normalized topic, 2+ different status:current files) ===")
    collisions = {t: files for t, files in by_topic.items() if len(set(files)) > 1}
    if not collisions:
        print("none")
    for t, files in collisions.items():
        print(f"TOPIC: {t!r}")
        for f in sorted(set(files)):
            print(f"  - {f}")

    print()
    print("=== Near-duplicate candidates (shared 3+-word run) — noisy, triage before acting ===")
    topics_list = list(by_topic.keys())
    seen_pairs: set[tuple[str, str]] = set()
    near_dupe_count = 0
    for i, t1 in enumerate(topics_list):
        w1 = t1.split()
        if len(w1) < 3:
            continue
        grams1 = {tuple(w1[j : j + 3]) for j in range(len(w1) - 2)}
        for t2 in topics_list[i + 1 :]:
            w2 = t2.split()
            if len(w2) < 3:
                continue
            grams2 = {tuple(w2[j : j + 3]) for j in range(len(w2) - 2)}
            if grams1 & grams2:
                files1, files2 = set(by_topic[t1]), set(by_topic[t2])
                if files1 - files2 or files2 - files1:
                    pair_key = (t1, t2) if t1 < t2 else (t2, t1)
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)
                    near_dupe_count += 1

    print(f"near-duplicate candidate pairs: {near_dupe_count} (count only; re-run on a smaller slice to inspect)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
