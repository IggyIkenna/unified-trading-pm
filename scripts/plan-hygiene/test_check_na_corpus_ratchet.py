# Epic: plan_hygiene_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_na_corpus_ratchet.py's --diff-base fence-aware checkbox count
(plan_reconciler_findings_cross_cutting_2026_08_10.md Item J /
plan_reconciler_findings_all_2026_08_12.md Section 3 -- check_na_corpus_ratchet.py's
--diff-base mode inherited the fenced-code-block checkbox-overcounting bug documented in
na_inventory_counts_fenced_code_block_checkboxes_as_open_todos_2026_08_02.md via its own
hand-duplicated _CHECKBOX_RE). Pins the fence-toggle so a checkbox-shaped line QUOTED
inside a ``` code block (e.g. a doc citing another plan's todo list as evidence) is never
counted as this doc's own open todo, while a real un-fenced checkbox still is.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import check_na_corpus_ratchet as checker


def test_real_open_checkbox_counted() -> None:
    text = "- [ ] a real open todo\n- [x] a done todo\n"
    assert checker._count_open_checkboxes_fence_aware(text) == 1


def test_checkbox_inside_fence_not_counted() -> None:
    text = (
        "- [ ] the only real open todo\n"
        "\n"
        "quoting the upstream plan for context:\n"
        "```\n"
        "- [ ] a quoted todo from another doc\n"
        "- [ ] another quoted one\n"
        "```\n"
    )
    assert checker._count_open_checkboxes_fence_aware(text) == 1


def test_all_checkboxes_fenced_reports_zero() -> None:
    # Live case: gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md reported 5
    # open todos with 0 real ones -- every `- [ ]` line was inside a quoted code block.
    text = "```\n- [ ] quoted 1\n- [ ] quoted 2\n- [ ] quoted 3\n```\n- [x] the only real todo, already done\n"
    assert checker._count_open_checkboxes_fence_aware(text) == 0


def test_star_bullet_variant_still_matches_when_unfenced() -> None:
    text = "* [ ] star-bullet open todo\n"
    assert checker._count_open_checkboxes_fence_aware(text) == 1


def test_na_open_todos_from_text_uses_fence_aware_count() -> None:
    text = "---\nassigned_vm: NA\nstatus: active\n---\n- [ ] real open todo\n```\n- [ ] quoted, must not count\n```\n"
    assert checker._na_open_todos_from_text(text) == 1
