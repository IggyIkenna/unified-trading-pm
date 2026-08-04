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
status: open
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
  ]
created: 2026-08-03
parent_epic: agent_operating_framework_master
priority: P3
assigned_vm: NA
execution_scope: local-only
resolved_by:
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

- [ ] [OPERATOR] P3. Rule on whether to extend the §8b evidence-backing contract to prod DATA-mutation completions:
      require restamp/backfill/rename/delete/tofu-state scripts to emit a verifiable summary artifact (a manifest-delta
      row, a `vm-logs/<unit>/RESULT.json`, a GCS operation id, or a before/after `state list`) that a `- [x]` must cite,
      the same way builds cite `cloudbuild=<id>` — and whether `check_evidence_backed_completion.py` should grow a
      prod-mutation branch. This is a standards/scope change (PLAN_FORMAT.md + the QG), hence operator-gated, not a
      worker fix. If ruled yes, the follow-up ([SCRIPT] to add the artifact convention + QG branch) is dispatchable.
      (repo: unified-trading-pm, decision only)

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
