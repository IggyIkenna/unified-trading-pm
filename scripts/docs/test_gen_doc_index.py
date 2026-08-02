#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Smoke + determinism tests for gen_doc_index (the L0 map generator, W4).

Run: .venv/bin/python -m pytest scripts/docs/test_gen_doc_index.py -q

# Epic: agent_operating_framework_master
# Lifecycle: permanent
"""

from __future__ import annotations

import gen_doc_index
from gen_doc_index import _fmt_val, build_index


def test_fmt_val_list_is_comma_joined():
    assert _fmt_val(["defi", "cefi"]) == "defi,cefi"
    assert _fmt_val("active") == "active"
    assert _fmt_val([]) == ""


def test_build_index_is_deterministic(tmp_path):
    # the whole point of consumer-side-local + gitignored: two regens of the SAME tree are
    # byte-identical (no incidental set/dict-ordering nondeterminism in the renderer).
    #
    # This asserts the RENDERER's algorithm is deterministic for a fixed input -- it must NOT
    # depend on the live, mutable `plans/` corpus staying still for the test's duration.
    # Originally this called `build_index(pm_root)` twice back-to-back against the LIVE PM
    # root, which raced concurrent agents committing/archiving docs on this heavily
    # multi-agent-written shared workspace (found 2026-07-25: a doc's `status: resolved` ->
    # `status: open` landed between the two filesystem walks -- a genuine corpus race, not a
    # renderer bug; see the now-closed
    # test_build_index_deterministic_races_on_concurrent_corpus_writes_2026_07_25 issue). A
    # retry loop reduced the flake rate but never eliminated the race (and the tail assertion
    # still did one more unretried live double-call). Fixed per the issue's own recommendation:
    # build from a FROZEN `tmp_path` fixture seeded with a handful of representative docs
    # instead of the live corpus -- proves determinism without depending on anything else's
    # concurrent writes. `build_index()` skips any of its configured roots that isn't a
    # directory, so a tmp tree only needing 2 of the ~7 roots populated is a valid input.
    plans_dir = tmp_path / "plans" / "active"
    plans_dir.mkdir(parents=True)
    codex_dir = tmp_path / "codex" / "01-example"
    codex_dir.mkdir(parents=True)
    (plans_dir / "frozen_fixture_plan_2026_01_01.md").write_text(
        "---\n"
        "doc_type: plan\n"
        "title: Frozen fixture plan\n"
        "summary: a static, non-live doc used only to prove build_index's render step is\n"
        "  deterministic for a fixed input.\n"
        "status: active\n"
        "nature: process\n"
        "asset_group: [meta]\n"
        "priority: P3\n"
        "assigned_vm: NA\n"
        "---\n\n# Frozen fixture plan\n\nStatic content, never mutated by this test.\n",
        encoding="utf-8",
    )
    (codex_dir / "frozen_fixture_codex_doc.md").write_text(
        "---\n"
        "doc_type: codex-ssot\n"
        "title: Frozen fixture codex doc\n"
        "summary: also static.\n"
        "authoritative_for: nothing-real\n"
        "owner: nobody\n"
        "---\n\n# Frozen fixture codex doc\n",
        encoding="utf-8",
    )
    first = build_index(tmp_path)
    second = build_index(tmp_path)
    assert first == second
    assert "Frozen fixture plan" in first
    assert "Frozen fixture codex doc" in first


def test_build_index_has_sections_and_entries():
    out = build_index(gen_doc_index._pm_root())
    assert out.startswith("# UTS documentation index")
    assert "## plan (" in out  # at least the plan section exists
    assert "\n- [" in out  # at least one doc entry
    # facets render as a greppable bracketed group on seeded docs
    assert "doc_type" not in out or "asset_group=" in out  # if any facets present, they're key=val form
