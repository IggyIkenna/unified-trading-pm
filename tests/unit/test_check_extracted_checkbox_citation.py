"""Unit tests for scripts/plan-hygiene/check_extracted_checkbox_citation.py.

Covers plans/active/issues/na_audit_progress_log_extracted_checkbox_never_flipped_pattern_2026_08_16.md:
a doc's Progress Log records "ruled ... extracted to <path>" but the corresponding checkbox was never
flipped to cite it. The "smoke test" fixtures below reproduce the PRE-FIX shape of the 4 real instances
that run found (same narrative pattern, synthetic doc names) to prove the checker would have caught
them; the negative fixtures prove the two ways a doc can legitimately NOT be a defect: the extraction
is properly cited on a (now-closed) checkbox, or there's no "extracted to" claim at all.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "plan-hygiene" / "check_extracted_checkbox_citation.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_extracted_checkbox_citation", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_extracted_checkbox_citation"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


def _doc(todos: str, progress_log: str) -> str:
    return f"""---
doc_type: issue
title: "test fixture"
summary: test fixture
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [test]
related: []
created: "2026-08-16"
assigned_vm: NA
priority: P2
---

# test fixture

## Todos

{todos}

## Progress Log

{progress_log}
"""


def test_uncited_extraction_flagged_instance1_shape():
    """Real instance 1 shape: sole todo, checkbox never flipped, no citation anywhere."""
    text = _doc(
        todos="- [ ] [DATA] P2. Diagnose the CME expected-coverage drift.",
        progress_log=(
            "- **2026-08-16**: ruled real gap, extracted to "
            "`tradfi_cme_expected_coverage_narrow_ao_dispatch_2026_08_16.md`."
        ),
    )
    findings = MOD.find_uncited_extractions(text)
    assert len(findings) == 1
    assert findings[0]["target"] == "tradfi_cme_expected_coverage_narrow_ao_dispatch_2026_08_16.md"


def test_uncited_extraction_flagged_instance2_shape_no_backticks():
    """Real instance shape without backtick-wrapped filename (e.g. 'extracted ... to X.md item N')."""
    text = _doc(
        todos="- [ ] [CODE] P2. Signoff on legacy twin bucket deletes.",
        progress_log=(
            "- **2026-08-16**: RECLASSIFY -- extracted the bounded item to "
            "tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md item 3."
        ),
    )
    findings = MOD.find_uncited_extractions(text)
    assert len(findings) == 1
    assert findings[0]["target"] == "tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md"


def test_properly_cited_on_closed_checkbox_not_flagged():
    """Fixed shape: checkbox flipped to [x] AND cites the extraction target -- not a defect."""
    text = _doc(
        todos=(
            "- [x] ✅ [DATA] P2. Extracted to "
            "`tradfi_cme_expected_coverage_narrow_ao_dispatch_2026_08_16.md`. Diagnose the drift."
        ),
        progress_log=(
            "- **2026-08-16**: ruled real gap, extracted to "
            "`tradfi_cme_expected_coverage_narrow_ao_dispatch_2026_08_16.md`."
        ),
    )
    assert MOD.find_uncited_extractions(text) == []


def test_cited_on_closed_checkbox_with_other_unrelated_open_todo_not_flagged():
    """Real instance 2's actual post-fix state: extraction cited+closed, but doc keeps another,
    unrelated open todo. Must NOT false-positive just because the citation isn't on an OPEN checkbox."""
    text = _doc(
        todos=(
            "- [x] ✅ [CODE] P2. Extracted to "
            "`tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md` item 3.\n"
            "- [ ] [OPERATOR] P2. Unrelated genuinely-gated signoff item, still open."
        ),
        progress_log=(
            "- **2026-08-16**: extracted the bounded item to "
            "`tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md` item 3."
        ),
    )
    assert MOD.find_uncited_extractions(text) == []


def test_no_extracted_to_claim_not_flagged():
    text = _doc(
        todos="- [ ] [CODE] P2. Ordinary open todo, nothing extracted.",
        progress_log="- **2026-08-16**: made progress, not done yet.",
    )
    assert MOD.find_uncited_extractions(text) == []


def test_progress_log_history_split_excluded_not_a_false_positive():
    """Line-cap remediation ('extracted verbatim to X_progress_log_history_<date>.md') is a distinct,
    well-established convention (moving old narrative, not dispatchable work) -- must not false-positive."""
    text = _doc(
        todos="- [ ] [DATA] P2. Ordinary open todo, nothing about this history split.",
        progress_log=(
            "- **2026-08-06**: full synthesis extracted verbatim to "
            "`/plans/archive/2026_08/some_doc_progress_log_history_2026_08_06.md` (line-cap remediation)."
        ),
    )
    assert MOD.find_uncited_extractions(text) == []


def test_doc_with_zero_open_checkboxes_not_scanned():
    """A doc whose only todo is already closed (e.g. fully archived-pending) is out of scope --
    matches the source doc's own 'every ... doc with open todos' scope."""
    text = _doc(
        todos="- [x] ✅ [CODE] P2. Done, no citation needed.",
        progress_log="- **2026-08-16**: extracted to `some_other_doc_2026_08_16.md`.",
    )
    assert MOD.find_uncited_extractions(text) == []
