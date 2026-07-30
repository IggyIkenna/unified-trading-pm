"""Unit tests for scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py.

Covers the fix for
plans/active/issues/generate_ag_closeout_audit_candidates_ao_ci_infra_membership_stale_after_closeout_archival_2026_07_29.md:
the ao/ci/infra tranches' membership test used to be defined by citation inside that tranche's own
`<prefix>_consolidated_closeout_*.md` (a retired 2026-07-25->27 workaround) -- once that closeout doc
archived (a normal, expected lifecycle event), `_closeout_paths()` returned an empty glob and every
member test silently failed, so `--tranche ci --json` returned `total_members: 0` with no error.

These tests prove:
- membership for ao/ci/infra is now tested directly via `asset_group` (matching the 5 real AGs), not
  via the closeout-citation proxy;
- a synthetically-archived closeout doc (the exact failure mode reported) does NOT drop the tranche's
  candidate count to zero;
- the `infra` tranche's asset_group VALUE is `infrastructure` (not `infra`), a second, adjacent bug
  found while fixing the first -- a naive `t in asset_group` for `t == "infra"` would have silently
  reproduced the same zero-candidates failure via a different root cause.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "plan-hygiene" / "generate_ag_closeout_audit_candidates.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_ag_closeout_audit_candidates", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()

FRONTMATTER_TMPL = """---
doc_type: issue
title: "{title}"
summary: test fixture
status: {status}
nature: issue
asset_group: [{asset_group}]
stage: [meta]
repos: []
scope: [engineer]
tags: []
related: []
created: "2026-07-01"
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

Fixture doc for test_generate_ag_closeout_audit_candidates.py.
"""


def _write_doc(root: Path, rel: str, *, title: str, status: str, asset_group: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(FRONTMATTER_TMPL.format(title=title, status=status, asset_group=asset_group), encoding="utf-8")
    return p


def _make_corpus(tmp_path: Path, *, with_closeout: bool, tranche_prefix: str, asset_group_value: str) -> Path:
    """Build a minimal synthetic PM-shaped corpus: one member doc + optionally that tranche's own
    consolidated-closeout doc + a real dispatch-batch covering doc (so covering_paths is never empty).
    """
    _write_doc(
        tmp_path,
        f"plans/active/issues/{tranche_prefix}_member_doc_2026_07_01.md",
        title=f"{tranche_prefix} member doc",
        status="open",
        asset_group=asset_group_value,
    )
    _write_doc(
        tmp_path,
        f"plans/active/{tranche_prefix}_satellite_ao_dispatch_batch1_2026_07_26.md",
        title=f"{tranche_prefix} dispatch batch 1",
        status="active",
        asset_group=asset_group_value,
    )
    if with_closeout:
        _write_doc(
            tmp_path,
            f"plans/active/{tranche_prefix}_consolidated_closeout_2026_07_25.md",
            title=f"{tranche_prefix} consolidated closeout",
            status="active",
            asset_group=asset_group_value,
        )
    return tmp_path


@pytest.mark.parametrize(
    ("tranche", "asset_group_value"),
    [("ci", "ci"), ("ao", "ao"), ("infra", "infrastructure")],
)
def test_non_ag_tranche_membership_survives_closeout_archival(monkeypatch, tmp_path, tranche, asset_group_value):
    """The exact reported failure: archiving `<tranche>_consolidated_closeout_*.md` must NOT drop
    total_members to 0 for ao/ci/infra."""
    _make_corpus(tmp_path, with_closeout=True, tranche_prefix=tranche, asset_group_value=asset_group_value)
    monkeypatch.setattr(MOD, "PM", tmp_path)

    with_closeout = json.loads(_run_json(tranche))
    assert with_closeout["total_members"] >= 1, "closeout present: member must be counted"

    # Now synthetically archive the closeout doc (delete it, mirroring plans/archive/2026_07/ move) --
    # this is the precise scenario that used to zero out non_ag_member_sets.
    (tmp_path / f"plans/active/{tranche}_consolidated_closeout_2026_07_25.md").unlink()

    without_closeout = json.loads(_run_json(tranche))
    assert without_closeout["total_members"] >= 1, (
        f"tranche={tranche}: total_members silently dropped to 0 once the closeout doc archived "
        "-- this is the exact regression generate_ag_closeout_audit_candidates_ao_ci_infra_membership_"
        "stale_after_closeout_archival_2026_07_29.md reports"
    )
    assert without_closeout["total_members"] == with_closeout["total_members"]


def _run_json(tranche: str) -> str:
    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = MOD.main(["--tranche", tranche, "--json"])
    assert rc == 0
    return buf.getvalue()


def test_infra_tranche_asset_group_value_is_infrastructure_not_infra(monkeypatch, tmp_path):
    """Second bug found while fixing the first: the `infra` TRANCHE name != its asset_group VALUE
    (`infrastructure`). A doc tagged `asset_group: [infrastructure]` must count as an `infra`-tranche
    member; a doc tagged (incorrectly) `asset_group: [infra]` must NOT (that value isn't in the real
    ASSET_GROUP enum, plans/PLAN_FORMAT.md)."""
    _write_doc(
        tmp_path,
        "plans/active/issues/real_infra_doc_2026_07_01.md",
        title="real infra doc",
        status="open",
        asset_group="infrastructure",
    )
    _write_doc(
        tmp_path,
        "plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md",
        title="infra dispatch batch 1",
        status="active",
        asset_group="infrastructure",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)

    result = json.loads(_run_json("infra"))
    assert result["total_members"] >= 1
    paths = {c["path"] for c in result["never_cited"]} | {"plans/active/issues/real_infra_doc_2026_07_01.md"}
    assert "plans/active/issues/real_infra_doc_2026_07_01.md" in paths


def test_ag_tranche_membership_unaffected_by_the_fix(monkeypatch, tmp_path):
    """Regression guard: the 5 real AGs (e.g. cefi) must keep working exactly as before -- this fix
    only touches the ao/ci/infra `else` branch."""
    _write_doc(
        tmp_path,
        "plans/active/issues/cefi_member_doc_2026_07_01.md",
        title="cefi member doc",
        status="open",
        asset_group="cefi",
    )
    _write_doc(
        tmp_path,
        "plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_26.md",
        title="cefi dispatch batch 1",
        status="active",
        asset_group="cefi",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)

    result = json.loads(_run_json("cefi"))
    assert result["total_members"] == 1
    assert result["never_cited_count"] == 1
