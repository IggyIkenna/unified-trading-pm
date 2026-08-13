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

    def test_hyphenated_success_reporting_compound_term_not_flagged(self) -> None:
        # Regression for evidence_backed_completion_regression_24_vs_23_2026_08_09.md todo 1:
        # "success-reporting" is a named dispatch mechanism used throughout the
        # ci_satellite_ao_dispatch_batchN_* corpus (never a claim that anything succeeded), and
        # `cloudbuild.yaml` here is a bare filename reference, not an infra deploy verb. The two
        # incidentally co-occur in the same clause but neither is a runtime-green claim.
        block = (
            "- [x] ✅ [REVIEW] P1. DONE — D5-3 (F3 success-reporting — 12+ services' "
            "`cloudbuild.yaml`/`buildspec.aws.yaml` `service-deployed` dispatch) — RESOLVED, no "
            "longer a batch-6 candidate.\n"
        )
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


class _FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout


class TestNotFoundVsUnavailable:
    """Regression for cloud_build_evidence_citation_short_hash_unresolvable_2026_07_27.md:
    _describe_build_status must distinguish "gcloud couldn't run at all here" (soft-skip by
    default) from "gcloud ran and confirmed this id does not resolve" (always a violation) --
    the original code conflated both into a single None, so a bogus 8-char git short-hash
    citation silently passed the gate even when gcloud/auth WAS available and confirmed the
    id was NOT_FOUND."""

    def _blocks_with_citation(self, build_id: str) -> list[object]:
        text = f"- [x] Deployed. Evidence: cloudbuild={build_id}\n"
        return MOD._iter_todo_blocks(text, Path("x.md"))

    def test_gcloud_not_found_is_always_a_violation(self, monkeypatch) -> None:
        monkeypatch.setattr(MOD.subprocess, "run", lambda *a, **k: _FakeCompletedProcess(returncode=1, stdout=""))
        blocks = self._blocks_with_citation("de50eace")  # a short git hash, not a real build id
        violations = MOD._check_builds(blocks, region="us-central1", project="p", require_verification=False)
        assert len(violations) == 1
        assert violations[0].rule == "A-cited-build-not-found"

    def test_gcloud_unavailable_soft_skips_by_default(self, monkeypatch) -> None:
        def _raise(*a, **k):
            raise FileNotFoundError("gcloud not installed")

        monkeypatch.setattr(MOD.subprocess, "run", _raise)
        blocks = self._blocks_with_citation("2ea305e9-1234-4abc-9def-0123456789ab")
        violations = MOD._check_builds(blocks, region="us-central1", project="p", require_verification=False)
        assert violations == []

    def test_gcloud_unavailable_is_a_violation_under_require_verification(self, monkeypatch) -> None:
        def _raise(*a, **k):
            raise FileNotFoundError("gcloud not installed")

        monkeypatch.setattr(MOD.subprocess, "run", _raise)
        blocks = self._blocks_with_citation("2ea305e9-1234-4abc-9def-0123456789ab")
        violations = MOD._check_builds(blocks, region="us-central1", project="p", require_verification=True)
        assert len(violations) == 1
        assert violations[0].rule == "A-unverifiable"

    def test_resolved_success_is_not_a_violation(self, monkeypatch) -> None:
        monkeypatch.setattr(
            MOD.subprocess, "run", lambda *a, **k: _FakeCompletedProcess(returncode=0, stdout="SUCCESS\n")
        )
        blocks = self._blocks_with_citation("2ea305e9-1234-4abc-9def-0123456789ab")
        violations = MOD._check_builds(blocks, region="us-central1", project="p", require_verification=False)
        assert violations == []

    def test_resolved_failure_is_always_a_violation(self, monkeypatch) -> None:
        monkeypatch.setattr(
            MOD.subprocess, "run", lambda *a, **k: _FakeCompletedProcess(returncode=0, stdout="FAILURE\n")
        )
        blocks = self._blocks_with_citation("2ea305e9-1234-4abc-9def-0123456789ab")
        violations = MOD._check_builds(blocks, region="us-central1", project="p", require_verification=False)
        assert len(violations) == 1
        assert violations[0].rule == "A-cited-build-not-success"

    def test_uuid_shaped_not_found_is_not_a_violation_by_default(self, monkeypatch) -> None:
        # A well-formed Cloud Build UUID that no longer resolves is most likely aged out of
        # GCP's retention window, not a bogus citation -- must NOT retroactively fail an
        # already-shipped claim.
        monkeypatch.setattr(MOD.subprocess, "run", lambda *a, **k: _FakeCompletedProcess(returncode=1, stdout=""))
        blocks = self._blocks_with_citation("2ea305e9-1234-4abc-9def-0123456789ab")
        violations = MOD._check_builds(blocks, region="us-central1", project="p", require_verification=False)
        assert violations == []

    def test_uuid_shaped_not_found_is_a_violation_under_require_verification(self, monkeypatch) -> None:
        monkeypatch.setattr(MOD.subprocess, "run", lambda *a, **k: _FakeCompletedProcess(returncode=1, stdout=""))
        blocks = self._blocks_with_citation("2ea305e9-1234-4abc-9def-0123456789ab")
        violations = MOD._check_builds(blocks, region="us-central1", project="p", require_verification=True)
        assert len(violations) == 1
        assert violations[0].rule == "A-unverifiable"


def _mutation_violations(block_text: str) -> list[object]:
    blocks = MOD._iter_todo_blocks(block_text, Path("x.md"))
    return MOD._check_mutations_without_evidence(blocks)


class TestProdMutationEvidenceRuleC:
    """Sub-rule C (2026-08-06 operator ruling, plans/PLAN_FORMAT.md § 8d): a `- [x]` asserting a
    prod DATA mutation with a measured outcome must cite a data-mutation artifact (vm-logs=/
    manifest-delta=/gcs-op=/state-list=/tofu-state=/...). A `cloudbuild=<id>` ref does NOT
    satisfy it — a build id proves a build, not a data mutation."""

    def test_restamp_with_row_count_flagged(self) -> None:
        block = "- [x] ✅ restamped 12,006 target rows, 0 residual mismatched rows.\n"
        violations = _mutation_violations(block)
        assert len(violations) == 1
        assert violations[0].rule == "C-mutation-without-evidence"

    def test_purge_with_shard_count_flagged(self) -> None:
        block = "- [x] ✅ Purged 28 legacy T-0 shards deleted.\n"
        assert len(_mutation_violations(block)) == 1

    def test_tofu_state_op_flagged(self) -> None:
        block = "- [x] ✅ Removed the resource from tofu state.\n"
        assert len(_mutation_violations(block)) == 1

    def test_backfill_with_million_object_count_flagged(self) -> None:
        block = "- [x] ✅ Backfilled 1.02M objects to the cefi _index.\n"
        assert len(_mutation_violations(block)) == 1

    def test_mutation_with_vm_logs_artifact_not_flagged(self) -> None:
        block = "- [x] ✅ restamped 12,006 rows. Evidence: vm-logs=pred-restamp-20260803T17/RESULT.json\n"
        assert _mutation_violations(block) == []

    def test_mutation_with_manifest_delta_artifact_not_flagged(self) -> None:
        block = "- [x] ✅ Deleted 28 legacy shards. Evidence: manifest-delta=cefi/_index/2026-07-31.before.after\n"
        assert _mutation_violations(block) == []

    def test_mutation_with_gcs_op_artifact_not_flagged(self) -> None:
        block = "- [x] ✅ GCS renames applied. Evidence: gcs-op=central-element-323112:op-12345\n"
        assert _mutation_violations(block) == []

    def test_mutation_with_state_list_artifact_not_flagged(self) -> None:
        block = "- [x] ✅ Removed the resource from tofu state. Evidence: state-list=before.r7x/after.q2y\n"
        assert _mutation_violations(block) == []

    def test_cloudbuild_ref_does_not_suppress_rule_c(self) -> None:
        # A build id proves a build, not a data mutation — must still be flagged.
        block = "- [x] ✅ restamped 12,006 rows. Evidence: cloudbuild=9159f9c7-2597-493a-89a3-7a56fdd1486c\n"
        assert len(_mutation_violations(block)) == 1

    def test_backfill_without_measured_outcome_not_flagged(self) -> None:
        # "Launched the backfill VM" is not a mutation-with-measured-outcome claim.
        block = "- [x] ✅ Launched features recompute VM fts-backfill-20260805 with no issues.\n"
        assert _mutation_violations(block) == []

    def test_code_ship_backfill_mention_not_flagged(self) -> None:
        # A code task named "mtds-backfill branch" (no measured outcome) is not a mutation claim.
        block = "- [x] Wire VM_FORCE_WINDOW into the mtds-backfill branch.\n"
        assert _mutation_violations(block) == []

    def test_analysis_block_drop_completed_not_flagged(self) -> None:
        # Regression for the 2026-08-13 false-positive shape: generic `drop` + generic `completed`
        # in an analysis/review block is NOT a data mutation.
        block = (
            "- [x] ✅ [REVIEW] P1. Post-window analysis + writeup, all writing into the same source "
            "doc. Pull the post-window comparison (todo 9): real `$/task`, `$/plan`, avg turn count, "
            "avg total tokens/task for pro vs flash over the full monitoring window — completed.\n"
        )
        assert _mutation_violations(block) == []
