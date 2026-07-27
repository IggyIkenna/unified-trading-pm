#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Shrinking-ratchet gate on the assigned_vm:NA corpus size (doc count + open-todo count).

Operator directive 2026-07-27: the `assigned_vm: NA` backlog must not grow unattended. Most NA
content is genuinely operator-gated/judgment work and correctly stays NA (see
na_docs_validity_and_ao_eligibility_audit_2026_07_26.md's own sampling: ~2/3 of reviewed NA docs
are dated, evidenced KEEP-NA calls) -- so the target is NOT "drive NA to zero". The target is that
new NA content is only ever added alongside an equal-or-greater amount of existing NA content being
reclassified or archived, so the raw backlog size trends flat-or-down, not "load-bearing content
plus an ever-growing pile nobody re-triages."

Reuses generate_na_doc_tranche_inventory.py's own classification (proper PyYAML frontmatter parse,
not a line-grep -- that script's own docstring explains why line-grepping this population is
unsound) rather than re-deriving the NA population a third time.

Usage: check_na_corpus_ratchet.py
  --update-baseline   regenerate na_corpus_baseline.yaml from the CURRENT corpus state. Run this
                       ONLY after a genuine /na-eligibility-audit or manual triage pass -- never to
                       silence a run that just found the backlog grew (see the baseline file's own
                       header). If the new numbers are HIGHER than the old ones, a loud warning
                       prints (still written -- a deliberate raise is a real, visible signal, not a
                       block), so a genuine spike in new NA-worthy work stays honest in the commit
                       history rather than looking like a routine update.
Exit 0 = current NA docs/todos <= baseline on both axes. Exit 1 = either axis grew beyond baseline.

See codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md § 4.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

PM = Path(__file__).resolve().parents[2]
INVENTORY_SCRIPT = Path(__file__).resolve().parent / "generate_na_doc_tranche_inventory.py"
BASELINE = Path(__file__).resolve().parent / "na_corpus_baseline.yaml"

_BASELINE_HEADER = """\
# Shrinking-ratchet baseline for the assigned_vm:NA corpus size (check_na_corpus_ratchet.py).
#
# Tracks two numbers over the LIVE `assigned_vm: NA` + status in {active, open} population
# (plans/active/*.md + plans/active/issues/*.md) -- the same population
# generate_na_doc_tranche_inventory.py already computes and /na-eligibility-audit walks. This is
# a SHRINKING ratchet, same convention as doc_reference_baseline.yaml / doc_body_link_baseline.yaml:
# a run that finds the CURRENT corpus bigger than this baseline on EITHER axis fails. The goal is
# not "drive NA to zero" -- most NA content is genuinely operator-gated/judgment work and should
# stay NA -- the goal is that the backlog cannot grow unattended: new NA content is fine when it's
# genuinely NA-worthy, but it must be offset by /na-eligibility-audit (or manual triage)
# reclassifying/archiving existing NA content, not just accumulated net forever.
#
# NEVER hand-raise these numbers to silence a run that just found the backlog grew -- only
# --update-baseline after a genuine /na-eligibility-audit or manual triage pass. A deliberate raise
# (a real spike in legitimate new NA-worthy work) is a real signal -- make it visible with why in
# the commit message, same convention as any other ratchet exception in this corpus.
#
# See codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md § 4 for the full
# rationale.
"""


def _current_counts() -> tuple[int, int]:
    """(doc_count, total_open_todos) over the live assigned_vm:NA + active/open population."""
    proc = subprocess.run(
        [sys.executable, str(INVENTORY_SCRIPT), "--tranche", "all", "--json"],
        capture_output=True,
        text=True,
        check=True,
        cwd=PM,
    )
    records = json.loads(proc.stdout)
    return len(records), sum(r["open_todos"] for r in records)


def _load_baseline() -> dict[str, object]:
    if not BASELINE.is_file():
        return {}
    return yaml.safe_load(BASELINE.read_text()) or {}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    update_baseline = "--update-baseline" in args
    quiet = "--quiet" in args

    docs, open_todos = _current_counts()
    baseline = _load_baseline()
    max_docs = baseline.get("max_na_docs")
    max_todos = baseline.get("max_na_open_todos")

    if update_baseline:
        warnings = []
        if isinstance(max_docs, int) and docs > max_docs:
            warnings.append(f"max_na_docs RAISED {max_docs} -> {docs}")
        if isinstance(max_todos, int) and open_todos > max_todos:
            warnings.append(f"max_na_open_todos RAISED {max_todos} -> {open_todos}")
        BASELINE.write_text(
            _BASELINE_HEADER
            + f"max_na_docs: {docs}\n"
            + f"max_na_open_todos: {open_todos}\n"
            + f'last_updated: "{datetime.now(UTC).date().isoformat()}"\n'
        )
        print(f"na_corpus_baseline.yaml regenerated: max_na_docs={docs}, max_na_open_todos={open_todos}")
        for w in warnings:
            print(f"⚠️  {w} -- verify this is a reviewed, justified raise, not a silenced failure", file=sys.stderr)
        return 0

    problems = []
    if isinstance(max_docs, int) and docs > max_docs:
        problems.append(f"NA doc count grew: {docs} > baseline {max_docs}")
    if isinstance(max_todos, int) and open_todos > max_todos:
        problems.append(f"NA open-todo count grew: {open_todos} > baseline {max_todos}")

    if problems:
        print("❌ check_na_corpus_ratchet: assigned_vm:NA backlog grew beyond baseline:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print(
            "  Remedy: run /na-eligibility-audit (or manual triage) to reclassify/archive existing NA\n"
            "  content until the backlog is back at or below baseline, then re-run this check. If this\n"
            "  growth is a reviewed, justified exception (a real spike in new NA-worthy work), re-run with\n"
            "  --update-baseline and explain why in the commit message -- never hand-edit the YAML.",
            file=sys.stderr,
        )
        return 1

    if not quiet:
        print(
            f"✅ check_na_corpus_ratchet: {docs} NA docs / {open_todos} open todos (baseline: {max_docs}/{max_todos})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
