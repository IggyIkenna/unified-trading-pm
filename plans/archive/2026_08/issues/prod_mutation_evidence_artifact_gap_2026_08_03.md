---
doc_type: issue
title:
  "Prod DATA-mutation claims (row counts, backstamps, GCS renames, tofu-state ops) have no verifiable evidence artifact
  analogous to `Evidence: cloudbuild=<id>` — completion is self-reported, not machine-checkable"
summary: >-
  PLAN_FORMAT.md §8b mandates `Evidence: cloudbuild=<id>` for deploy/promote claims, and
  `check_evidence_backed_completion.py` fails a `- [x]` build/promote whose cited build isn't SUCCESS. There is NO
  equivalent for prod DATA-mutation completions — restamp/backfill row counts, manifest backstamps, GCS object
  renames/deletes, terraform/tofu state ops. Those `- [x]` claims rest on the worker's self-report of running their own
  script, with no cited log path / manifest-delta / operation id a reviewer can independently resolve. Review has now
  flagged this same class three independent times (see instances below), each time confirming the code looked correct
  but the operational outcome was unverifiable from durable artifacts alone. Filed for an operator ruling on whether to
  extend §8b-style evidence-backing to prod-mutation scripts.
status: archived
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin]
tags: [governance, evidence-backed-completion, prod-mutation, data-correctness, plan-format, process-gap]
related:
  [
    /plans/PLAN_FORMAT.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-03
author: unknown
parent_epic: agent_operating_framework_master
priority: P3
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
resolved_by: unified-trading-pm (this commit)
locked_by:
source:
  "review spot-check msgs #3552 (tofu-state evidence gap), do_rename content-equality finding, + #3572 (prediction
  restamp row-count claim), consolidated by main agt-1756f6 2026-08-03"
drift_direction: advance-process
estimate_class: design
depends_on: []
context_scope:
  [
    /plans/PLAN_FORMAT.md,
    scripts/quality_gates/check_evidence_backed_completion.py,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md,
  ]
---

# Prod DATA-mutation claims have no verifiable evidence artifact (evidence-backing gap)

> **ARCHIVED 2026-08-13** — sole todo done: `plans/PLAN_FORMAT.md` § 8d + `check_evidence_backed_completion.py` sub-rule
> C now extend the § 8b evidence-backing contract to prod DATA-mutation completions, same commit as this archival. See
> the Todos + Progress Log below for what shipped.

## The gap

`plans/PLAN_FORMAT.md` §8b + `scripts/quality_gates/check_evidence_backed_completion.py` enforce a strong contract for
**build/deploy/promote** completions: a `- [x]` claiming a Cloud Build / deploy / promote must cite
`Evidence: cloudbuild=<id>` that resolves to SUCCESS via `gcloud builds describe`, or the QG fails. This makes those
completions **machine-checkable** — a reviewer (human or agent) resolves the id, not the worker's word.

**Prod DATA-mutation completions have no such mechanism.** When a `- [x]` claims "restamped 12,006 rows", "backfilled N
shards", "renamed/deleted M GCS objects", or "removed a resource from tofu state", the evidence is the worker's
self-report of running their own script. There is no cited, independently-resolvable artifact (a written manifest-delta,
a `vm-logs/<vm>/…` log path, a GCS operation id, a `terraform state list` before/after) the way a build id is
resolvable. The code producing the mutation can be verified from the diff; the **operational outcome cannot**.

## Why it matters

Prod data mutations are exactly the class where a wrong outcome is expensive and hard to reverse (the prediction doc
itself cites the 2026-07-12 lost-1.02M-rows incident as precedent). "The code is correct" (verifiable) is not the same
as "it ran and produced the claimed effect" (currently unverifiable). This is a data-correctness-adjacent process gap,
not a code defect.

## Instances review has independently flagged (same class, 3×)

1. **tofu/terraform state ops** (review msg #3552, slot-12): a prod tofu-state-rm completion cited the wrong repo/SHA
   and did not paste a re-verification — no durable artifact proved the state change.
2. **`do_rename` GCS object renames** (review, do_rename content-equality finding): renames/deletes gated on new-name
   existence alone, with no content-equality (crc32c/size/row-count) evidence written for the completion.
3. **prediction restamp row counts** (review msg #3572, slot-2, prediction_phantom_reconciler): the "12,006 target rows
   / 0 residual mismatched KALSHI rows" operational claim is unverifiable from git artifacts alone — no cited log/build
   id, just the worker's self-report of running their own restamp script. (Code-level verification gave review high
   confidence it worked; the point is the _outcome_ isn't machine-checkable.)

## Todos

- [x] ✅ [SCRIPT] P3. **RULED 2026-08-06: YES, extend it.** `[SCRIPT]` tag (was `[OPERATOR]`) — directly supports the
      existing data-pipeline-correctness HARD RULE; prod data mutations deserve the same evidence rigor builds already
      get. Add the artifact convention + the `check_evidence_backed_completion.py` prod-mutation branch. — DONE
      2026-08-13: added `plans/PLAN_FORMAT.md` § 8d (the `manifest-delta=|vm-log=|gcs-op=|tofu-state=` artifact
      convention) + sub-rule C to `check_evidence_backed_completion.py` (same baselined-ratchet shape as sub-rule B;
      baseline seeded at 51 pre-existing corpus claims via `--baseline-write`, matching the QG's actual no-issues
      invocation); `--only` precommit mode + `quality-gates.sh`'s log lines extended to cover it; 10 new unit tests in
      `tests/unit/test_check_evidence_backed_completion.py` (all 26 in the file passing); basedpyright clean. Code +
      this flip ship in the same unified-trading-pm commit (single-repo case).

## Progress Log

- **2026-08-03 (main agt-1756f6)**: Consolidated three independent review flags of the same class (tofu-state,
  do_rename, prediction restamp row-counts) into this single durable finding rather than surfacing each as an ephemeral
  operator message (which scroll out of the role-history window — the exact bounded-window problem that also lost the
  BLK-7318d847 ruling reference this session). Filed for an operator ruling; no code/data changed.
- **context-scout 2026-08-03**: populated context_scope (4 entries) — the two SSOTs define the existing §8b
  evidence-backing contract this issue asks to extend, the QG script is the machine enforcer that would grow a
  prod-mutation branch, and the cited prediction incident doc is the precedent making the stakes concrete.
- **na-eligibility-audit 2026-08-04**: KEEP-NA, valid — brand-new doc; the sole open todo is explicitly `[OPERATOR]`-
  tagged, a standards/scope-change ruling request (whether to extend PLAN_FORMAT.md §8b evidence-backing to prod
  data-mutation completions) consolidating 3 independent review-flagged instances — a genuine policy decision, not a
  worker-determinable fact.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — reaffirms 2026-08-04 (unchanged): sole todo is an [OPERATOR]
  policy-scope-change ruling request (extend PLAN_FORMAT.md §8b), not a worker-determinable fact.

- **na-eligibility-audit 2026-08-06 (governance-sweep reclassification pass, later same day) — CORRECTS the marker
  above.** RECLASSIFY, `assigned_vm: NA -> planning`. The stale audit-log entries above predate this session's own
  ruling: "RULED 2026-08-06: YES, extend it" with an `[OPERATOR] -> [SCRIPT]` retag resolves the operator policy
  question. The remaining work — add the artifact-convention section to `PLAN_FORMAT.md` and a prod-mutation branch to
  `check_evidence_backed_completion.py` — is a bounded, precedented QG-script extension following the existing
  §8b/cloudbuild pattern, not open-ended judgment. No hard-rule veto (no redirect banner, no revert, no `depends_on`
  gate, scoped single-script change, not dispatch-critical-path machinery). Conflict-check cleared (no overlapping claim
  in `parent_epic: agent_operating_framework_master`). `assigned_role` was unset; filled `infra` (PM-repo QG-tooling
  scope).

- **infra worker (slot 18) 2026-08-13**: Shipped the ruled follow-up. `plans/PLAN_FORMAT.md` § 8d adds the
  `manifest-delta=|vm-log=|gcs-op=|tofu-state=` evidence-artifact convention for a quantified prod DATA-mutation claim
  (restamp/backfill row-shard count, GCS object rename/delete, tofu/terraform state op), mirroring § 8b's
  `cloudbuild=<id>` shape but as citation-presence only (no single live API resolves every one of these artifact kinds
  the way `gcloud builds describe` resolves a build). `check_evidence_backed_completion.py` grew sub-rule C: same-clause
  verb+quantity detection (`_PROD_MUTATION_VERB_RE` + `_PROD_MUTATION_QUANTITY_RE`, or the tofu/terraform-state-op verb
  alone), baselined ratchet against `evidence_backed_completion_baseline.yaml`'s new
  `prod_mutation_claim_without_evidence_baseline` key (seeded at 51 — the corpus-wide count under the QG's actual
  no-`--include-issues` invocation, confirmed matching `quality-gates.sh`'s call). `--only` precommit mode and
  `quality-gates.sh`'s log lines extended to cover sub-rule C alongside B. 10 new unit tests (all 26 in the test file
  passing); basedpyright clean on both changed Python files. Also archived this doc per the "done + unlocked → archive
  immediately" HARD RULE (same-repo/same-commit flip+archive is sanctioned for a PM-direct worker) — referrer paths
  updated corpus-wide to point at the new `plans/archive/2026_08/issues/` location.
