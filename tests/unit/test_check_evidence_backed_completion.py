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


def _rule_c_violations(block_text: str) -> list[object]:
    blocks = MOD._iter_todo_blocks(block_text, Path("x.md"))
    return MOD._check_prod_mutation_claims_without_evidence(blocks)


class TestSubRuleCProdMutationEvidence:
    """Sub-rule C (plans/archive/2026_08/issues/prod_mutation_evidence_artifact_gap_2026_08_03.md, RULED
    2026-08-06, PLAN_FORMAT.md § 8d): a quantified prod DATA-mutation claim (restamp/backfill row
    or shard count, GCS object rename/delete count, tofu/terraform state op) with no
    `manifest-delta=`/`vm-log=`/`gcs-op=`/`tofu-state=` Evidence token is flagged."""

    def test_restamp_row_count_without_evidence_flagged(self) -> None:
        block = "- [x] Restamped 12,006 rows to the corrected instrument_id, 0 residual mismatches.\n"
        violations = _rule_c_violations(block)
        assert len(violations) == 1
        assert violations[0].rule == "C-prod-mutation-claim-without-evidence"  # type: ignore[attr-defined]

    def test_backfilled_shards_without_evidence_flagged(self) -> None:
        block = "- [x] Backfilled 340 shards for the sports asset_group, all capture_status=captured.\n"
        assert len(_rule_c_violations(block)) == 1

    def test_gcs_object_rename_with_count_without_evidence_flagged(self) -> None:
        block = "- [x] Renamed 40 GCS objects to the canonical path, verified content-equality.\n"
        assert len(_rule_c_violations(block)) == 1

    def test_tofu_state_removal_without_evidence_flagged(self) -> None:
        block = "- [x] Removed the orphaned bucket resource from tofu state, apply now clean.\n"
        assert len(_rule_c_violations(block)) == 1

    def test_manifest_delta_evidence_suppresses(self) -> None:
        block = "- [x] Restamped 12,006 rows. Evidence: manifest-delta=sports/2026-08-01/shard-004\n"
        assert _rule_c_violations(block) == []

    def test_vm_log_evidence_suppresses(self) -> None:
        block = "- [x] Backfilled 340 shards. Evidence: vm-log=vm-logs/backfill-sports-01/RESULT.json\n"
        assert _rule_c_violations(block) == []

    def test_gcs_op_evidence_suppresses(self) -> None:
        block = "- [x] Renamed 40 GCS objects. Evidence: gcs-op=rename-batch-2026-08-13-001\n"
        assert _rule_c_violations(block) == []

    def test_tofu_state_evidence_suppresses(self) -> None:
        block = "- [x] Removed the orphaned bucket from tofu state. Evidence: tofu-state=12-resources-before/11-after\n"
        assert _rule_c_violations(block) == []

    def test_unquantified_backfill_design_discussion_not_flagged(self) -> None:
        # A bare mention with no accompanying quantity is design discussion, not a completion claim.
        block = "- [x] Decided to backfill the missing venue coverage in a follow-up plan.\n"
        assert _rule_c_violations(block) == []

    def test_unrelated_quantity_in_different_clause_not_flagged(self) -> None:
        # Same-clause-proximity discipline mirrors sub-rule B: a quantity in an unconnected later
        # clause must not combine with an earlier verb to fabricate a claim.
        block = (
            "- [x] Renamed the config helper function for clarity. The corpus now has 12,006 total "
            "files across the fleet.\n"
        )
        assert _rule_c_violations(block) == []
