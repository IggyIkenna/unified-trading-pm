#!/usr/bin/env python3
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


def test_build_index_is_deterministic():
    # the whole point of consumer-side-local + gitignored: two regens of the SAME tree are
    # byte-identical (no incidental set/dict-ordering nondeterminism in the renderer).
    #
    # Shared multi-agent working tree caveat (found 2026-07-28): build_index() re-globs the
    # live plans/ corpus on every call, and this repo is routinely edited by several concurrent
    # agents committing/archiving docs in real time -- a doc can be added/moved between this
    # test's two back-to-back calls (observed: "issue (426)" vs "issue (429)", a genuine
    # corpus-size change mid-test, not a renderer bug). That's a property of the environment,
    # not of build_index()'s determinism, so retry a few times: two CONSECUTIVE calls matching
    # proves the renderer is deterministic against whatever snapshot was stable at that moment;
    # persistent mismatch across every retry would still fail loudly as a real bug.
    pm_root = gen_doc_index._pm_root()
    first = build_index(pm_root)
    for _ in range(5):
        second = build_index(pm_root)
        if second == first:
            return
        first = second
    assert build_index(pm_root) == build_index(pm_root)


def test_build_index_has_sections_and_entries():
    out = build_index(gen_doc_index._pm_root())
    assert out.startswith("# UTS documentation index")
    assert "## plan (" in out  # at least the plan section exists
    assert "\n- [" in out  # at least one doc entry
    # facets render as a greppable bracketed group on seeded docs
    assert "doc_type" not in out or "asset_group=" in out  # if any facets present, they're key=val form
