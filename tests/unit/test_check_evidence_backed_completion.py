"""Unit tests for scripts/quality_gates/check_evidence_backed_completion.py sub-rule B.

Regression fixtures for the 2026-07-21 same-clause-proximity fix
(plans/active/issues/pm_evidence_backed_completion_false_positive_2026_07_21.md): the runtime-verb
(`cloud-build`, `redeploy`, ...) and green-token (`green`/`SUCCESS`/`succeeded`) must co-occur in the
SAME clause, not just anywhere in a long multi-line `- [x]` todo block — a whole-block AND
false-positived on a workflow FILENAME (`cloud-build-router.yml`) in one clause plus an unrelated
`quality-gates.sh` "green" mention in a later, unconnected clause of the same todo.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "quality_gates" / "check_evidence_backed_completion.py"
    spec = importlib.util.spec_from_file_location("check_evidence_backed_completion", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


def _violations(block_text: str) -> list[object]:
    blocks = MOD._iter_todo_blocks(block_text, Path("x.md"))
    return MOD._check_claims_without_evidence(blocks)


class TestFalsePositiveFixed:
    def test_filename_verb_and_unrelated_green_in_different_clauses_not_flagged(self) -> None:
        # The exact false-positive shape: `cloud-build-router.yml` is a GHA call-site filename
        # (not a runtime claim), and the unrelated `quality-gates.sh` green mention is a separate,
        # later clause about a pre-existing repo-wide QG state — not about a Cloud Build run.
        block = (
            "- [x] ✅ Fix the emitting-vs-subject repo defect — threaded the subject through every "
            "caller: `ci-status-update.yml`, `cascade-qg-ordering.yml`, `cloud-build-router.yml` "
            "(9 call sites) — all from data already computed in that workflow, no new derivation. "
            "`quality-gates.sh` green in both repos (a pre-existing, unrelated repo-wide QG red).\n"
        )
        assert _violations(block) == []

    def test_deployment_alerts_ingestion_completeness_regression_fixture(self) -> None:
        # Exact text (collapsed) from the plan block that triggered the 30->31 ratchet regression.
        block = (
            "- [x] ✅ [BACKEND] P0. Fix the emitting-vs-subject repo defect — populate `subject_repo` "
            "distinctly from the emitting repo. — `deployment-api@04b19bd5`: gained an optional "
            "`subject_repo` kwarg. `unified-trading-pm@36db2e858`: threaded the actual subject through "
            "at every confirmed cross-repo caller: `ci-status-update.yml`, `cascade-qg-ordering.yml`, "
            "`escalate-to-orchestrator.yml`, `publish-package.yml`, `cloud-build-router.yml` "
            "(9 call sites), `cloud-build-router-aws.yml` (3 call sites) — all from data already "
            "computed in that workflow, no new derivation. `quality-gates.sh` green in both repos "
            "(a pre-existing, unrelated repo-wide QG red).\n"
        )
        assert _violations(block) == []

    def test_hypothetical_success_mention_not_flagged(self) -> None:
        # "success" inside a counterfactual clause ("a silent-success path would have...") is not a
        # claim that anything actually succeeded — and the cited build in this fixture is FAILURE.
        block = (
            "- [x] ✅ Method: `gcloud storage rm` inside Cloud Build measured ~39 obj/s, blowing the "
            "90-min build timeout (cancelled build). It surfaced only because the script counted "
            "failures instead of swallowing them — a silent-success path would have reported clean.\n"
        )
        assert _violations(block) == []

    def test_code_ship_green_claim_exempt_regardless_of_clause(self) -> None:
        # A `<repo>@<sha>` + "QG green"/"tests passing" code-ship claim is deliberately exempt from
        # sub-rule B (evidenced by the commit + local QG sentinel, not a build-id) — same clause or not.
        block = "- [x] Shipped the fix — myrepo@04b19bd5, QG green, all tests passing.\n"
        assert _violations(block) == []


class TestGenuineClaimsStillFlagged:
    def test_same_clause_redeploy_and_green_flagged(self) -> None:
        block = "- [x] Redeployed to Cloud Run and the build went green in the console, no issues.\n"
        violations = _violations(block)
        assert len(violations) == 1
        assert violations[0].rule == "B-claim-without-evidence"  # type: ignore[attr-defined]

    def test_same_clause_promote_to_main_flagged(self) -> None:
        block = "- [x] Promoted to main — the LDR->main promotion PR merged clean, SUCCESS.\n"
        assert len(_violations(block)) == 1

    def test_cross_clause_but_same_sentence_wrap_still_flagged(self) -> None:
        # Line-wrapped continuation lines are collapsed before clause-splitting, so a claim that
        # happens to wrap across lines (not across a real `.`/`!`/`?` sentence boundary) still counts
        # as one clause.
        block = "- [x] Cloud Build for the release image\n      went green, no failures observed.\n"
        assert len(_violations(block)) == 1

    def test_evidence_ref_suppresses_even_same_clause(self) -> None:
        block = "- [x] Redeployed to Cloud Run, build went green. Evidence: cloudbuild=abcdef1234567890\n"
        assert _violations(block) == []
