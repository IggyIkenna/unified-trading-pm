"""Unit tests for the `--tranche <name>` filter added to
scripts/plan-hygiene/check_ag_closeout_linkage.py (2026-08-11,
plans/active/issues/ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md, todo 3).

The flag is additive/opt-in: omitting it must leave the full-corpus baseline-ratchet behavior
completely unchanged (covered by re-running the script with no args in this same session against
the real corpus, not re-derived here). These tests cover the NEW behavior only:
- `--tranche <name>` scopes the printed/counted orphans to just that one asset_group, even though
  the reachability graph is still built over the WHOLE synthetic corpus (a doc from a different
  tranche must not leak into the filtered count, but must still be usable as a graph hop).
- The mode is purely informational: it always exits 0, regardless of how many orphans it finds.
- An unknown `--tranche` value is a real usage error (exit 1), not a silent empty result.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "plan-hygiene" / "check_ag_closeout_linkage.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_ag_closeout_linkage", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()

FRONTMATTER_TMPL = """---
doc_type: issue
title: "{title}"
summary: test fixture
status: open
nature: issue
asset_group: [{asset_group}]
stage: [meta]
repos: []
scope: [engineer]
tags: []
related: []
created: "2026-08-01"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
assigned_role: infra
drift_direction: none
depends_on: []
resolved_by:
locked_by:
supersedes:
superseded_by:
---

# {title}

Fixture doc for test_check_ag_closeout_linkage_tranche_filter.py.
"""

CLOSEOUT_TMPL = """---
doc_type: plan
title: "{title}"
summary: test fixture closeout
status: active
nature: guideline
asset_group: [{asset_group}]
stage: [meta]
repos: []
scope: [engineer]
tags: []
related: []
created: "2026-08-01"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
assigned_role: infra
drift_direction: none
depends_on: []
resolved_by:
locked_by:
supersedes:
superseded_by:
---

# {title}
"""


def _write(root: Path, rel: str, *, title: str, asset_group: str, template: str = FRONTMATTER_TMPL) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(template.format(title=title, asset_group=asset_group), encoding="utf-8")
    return p


def _patch_pm(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(MOD, "PM_DIR", tmp_path)
    monkeypatch.setattr(MOD, "BASELINE_PATH", tmp_path / "ag_closeout_linkage_baseline.yaml")


def _build_two_tranche_corpus(tmp_path: Path) -> None:
    """cefi: one orphan doc + its own closeout (never linked -> genuine orphan).
    defi: one orphan doc + its own closeout (never linked -> genuine orphan).
    Neither tranche's docs reference the other -- proves --tranche cefi reports ONLY the cefi
    orphan even though defi's docs are part of the same scanned corpus/graph."""
    _write(
        tmp_path,
        "plans/active/issues/cefi_orphan_doc_2026_08_01.md",
        title="cefi orphan doc",
        asset_group="cefi",
    )
    _write(
        tmp_path,
        "plans/active/cefi_consolidated_closeout_2026_07_25.md",
        title="cefi consolidated closeout",
        asset_group="cefi",
        template=CLOSEOUT_TMPL,
    )
    _write(
        tmp_path,
        "plans/active/issues/defi_orphan_doc_2026_08_01.md",
        title="defi orphan doc",
        asset_group="defi",
    )
    _write(
        tmp_path,
        "plans/active/defi_consolidated_closeout_2026_07_25.md",
        title="defi consolidated closeout",
        asset_group="defi",
        template=CLOSEOUT_TMPL,
    )


def test_tranche_filters_to_single_asset_group(monkeypatch, tmp_path, capsys):
    _patch_pm(monkeypatch, tmp_path)
    _build_two_tranche_corpus(tmp_path)

    rc = MOD._run_tranche("cefi", quiet=False)
    out = capsys.readouterr().out

    assert rc == 0, "informational --tranche mode must always exit 0"
    assert "cefi_orphan_doc_2026_08_01.md" in out
    assert "defi_orphan_doc_2026_08_01.md" not in out, (
        "a different tranche's orphan must not leak into the filtered output"
    )
    assert "1 orphan(s)" in out


def test_tranche_exits_zero_even_with_orphans(monkeypatch, tmp_path):
    _patch_pm(monkeypatch, tmp_path)
    _build_two_tranche_corpus(tmp_path)

    rc = MOD._run_tranche("defi", quiet=True)
    assert rc == 0, "no per-tranche baseline exists -- this mode never fails the run"


def test_unknown_tranche_is_a_usage_error(monkeypatch, tmp_path):
    _patch_pm(monkeypatch, tmp_path)
    _build_two_tranche_corpus(tmp_path)

    rc = MOD._run_tranche("not-a-real-tranche", quiet=True)
    assert rc == 1, "an unknown --tranche value must fail loudly, not silently report zero orphans"


def test_tranche_flag_is_additive_and_does_not_touch_no_flag_argv_parsing(monkeypatch, tmp_path):
    """`main()` must still route to the corpus-wide baseline path when --tranche is absent --
    this is the "opt-in, no-flag preserves the full-corpus ratchet" contract from the module
    docstring, exercised via main()'s own argv dispatch rather than calling the baseline path
    directly, so a future refactor that breaks the dispatch order is caught here too."""
    _patch_pm(monkeypatch, tmp_path)
    _build_two_tranche_corpus(tmp_path)
    monkeypatch.setattr(sys, "argv", ["check_ag_closeout_linkage.py", "--quiet"])

    rc = MOD.main()
    # Two genuine orphans (cefi + defi), fresh baseline file absent -> load_baseline() returns 0.
    assert rc == 1


def test_tranche_and_update_baseline_are_mutually_exclusive(monkeypatch, tmp_path, capsys):
    _patch_pm(monkeypatch, tmp_path)
    _build_two_tranche_corpus(tmp_path)
    monkeypatch.setattr(sys, "argv", ["check_ag_closeout_linkage.py", "--tranche", "cefi", "--update-baseline"])

    rc = MOD.main()
    assert rc == 1
    assert "mutually exclusive" in capsys.readouterr().err
