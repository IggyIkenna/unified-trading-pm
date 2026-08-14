---
doc_type: issue
title:
  "escalation.py:_poll_wall_resolution auto-resolves 6 of 8 wall types on ANY unrelated repo QG-green, silently closing
  CRITICAL data_pipeline_failure escalations with zero worker dispatched"
summary: >-
  `server/escalation.py:_poll_wall_resolution` falls through, for any `wall_type` not explicitly special-cased
  (`merge_conflict`/`stuck_promotion_pr`/`ldr_qg_failure`(PR-scoped)), to a generic "is the repo's LDR quality-gates-v2
  green" check and returns `qg_v2_green` if so — with zero relation to whether the actual filed problem was fixed. This
  correctly applies to `ldr_qg_failure`/`main_ci_red` (QG conclusion IS the right signal for those) but incorrectly
  applies to 6 other wall types: `data_pipeline_failure`, `provenance_blocked`, `sit_failure`, `sit_retry_cap`,
  `plan_health`, `harness_lint`, `label_mismatch`. DB confirms historical auto-close rates via this path:
  `data_pipeline_failure` 599/604 (99%), `provenance_blocked` 80/80 (100%), `sit_failure` 39/39 (100%), `plan_health`
  221/222 (99.5% — directly contradicting the function's OWN docstring, which documents `plan_health` returning `None`
  and closing via watch-TTL instead, an intent never actually implemented). Live-observed during filing: two CRITICAL
  `data_pipeline_failure` escalations (DP-VM-003, stalled backfill VM needing manual relaunch; DP-FETCH-009, CRITICAL 1%
  cefi `book_snapshot_5` cell-loss gap) were both auto-closed as `qg_v2_green` within ~4 minutes of filing, zero worker
  ever dispatched. Directly violates the data-pipeline-correctness-is-the-heartbeat HARD RULE. A scoped allowlist fix
  (gate the fallthrough to only `ldr_qg_failure`(pr_number==0)/`main_ci_red`, return `None` for the other 6, matching
  the function's own already-documented intent) was approved same-tick (BLK-2a812311, answered A) and dispatched to slot
  11 for a regression-tested quickmerge fix. This doc is the operator-notification + historical-blast-radius record
  required alongside that fix, not a substitute for it — DP-VM-003 and DP-FETCH-009 specifically still need real
  investigation since nobody has actually looked at either.
status: open
nature: issue
asset_group:
  [ao] # corrected 2026-08-10 (/ag-closeout-audit cross-cutting) -- was [cross-cutting]. Content is 100% an
  # agent-orchestrator server-code defect (server/escalation.py:_poll_wall_resolution); the wall_type values it
  # mishandles are escalation CATEGORIES the mechanism routes, not asset groups the doc spans -- same mistag
  # pattern already corrected elsewhere (data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md).
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [escalation, data-pipeline-correctness, false-resolution, hard-rule-violation, qg-fallthrough]
related: [/plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md]
created: 2026-08-09
author: agt-22de53 (main), consolidating a finding from escalation_queue_reconciler (slot 11, task agt-21fadd)
parent_epic: agent_operating_framework_master
priority: P1
assigned_vm: NA
execution_scope: local-only
estimate_class: research
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-09
locked_since:
context_scope:
  [
    agent-orchestrator/server/escalation.py,
    /plans/active/issues/escalation_queue_sit_failure_no_pr_closed_resolution_2026_08_10.md,
  ]
archive_exempt: true # 2026-08-10 — all 4 todos resolved, but doc serves as operator-visible historical-blast-radius record per its own stated scope (§Disposition item 1)
source: >-
  escalation_queue_reconciler's routine 3-hourly check (slot 11, task agt-21fadd) was triaging an unrelated wall when it
  found this bug in the reconciliation mechanism itself, filed BLK-2a812311 asking whether to (A) apply a scoped fix now
  + quickmerge, or (B) file-and-defer (its own recommendation). Main (agt-22de53) independently verified the code
  directly (server/escalation.py lines 1660-1753) before deciding, confirmed the finding exactly, and answered A —
  overriding the reporting worker's own more conservative B recommendation — because the fix is mechanical (it makes the
  code match intent the function's own docstring already states, not a new design call), is provably non-regressive for
  the two currently-correct wall types, and every additional tick live risks more CRITICAL escalations being silently
  auto-closed. This doc covers the parts A does NOT cover: operator visibility into the historical blast radius, and the
  two specific live escalations that need manual follow-up regardless of the code fix.
---

# escalation_queue_reconciler: false-resolution bug closes CRITICAL data-pipeline escalations on unrelated CI green

## What was found

`_poll_wall_resolution` (`server/escalation.py:1660-1753`) is the terminal-signal probe the escalation watchdog uses to
decide whether a dispatched wall has cleared. Its own docstring (lines 1660-1691) documents intent precisely:

- PR-centric walls (`merge_conflict`/`stuck_promotion_pr`) resolve via PR merge/close state.
- `ldr_qg_failure` (PR-scoped) resolves via the PR's own head-branch QG conclusion, never the bare trunk.
- `ldr_qg_failure` (bare, pr_number==0) and `main_ci_red` resolve via the repo's LDR/main QG conclusion — QG green IS
  the correct signal for those two, because the wall itself WAS "this repo's QG is red."
- "Walls with no machine-readable CI signal (`plan_health`) return `None` here and are closed by the watch-TTL, not
  falsely re-escalated."

The code does not implement that last carve-out. Lines 1736-1753 are an **unconditional** fall-through: any `wall_type`
that doesn't match one of the earlier `if` branches reaches the generic `ci_reconcile.repo_ldr_qg_conclusion(repo)`
check and returns `"qg_v2_green"` the instant that repo's LDR QG happens to be green — regardless of whether the actual
filed problem (a stalled VM, a provenance gap, a SIT failure, a data cell-loss gap) was ever touched.

**Historical DB confirmation** (as reported by escalation_queue_reconciler, not independently re-queried by main):

| wall_type               | auto-closed via qg_v2_green | total       |
| ----------------------- | --------------------------- | ----------- |
| `data_pipeline_failure` | 599                         | 604 (99%)   |
| `provenance_blocked`    | 80                          | 80 (100%)   |
| `sit_failure`           | 39                          | 39 (100%)   |
| `plan_health`           | 221                         | 222 (99.5%) |

**Live-observed during filing**: two CRITICAL `data_pipeline_failure` escalations were both auto-closed within ~4
minutes of filing, zero worker ever dispatched:

- **DP-VM-003** — a stalled backfill VM needing manual relaunch.
- **DP-FETCH-009** — a CRITICAL 1% cefi `book_snapshot_5` cell-loss gap.

This is a direct violation of the data-pipeline-correctness-is-the-heartbeat HARD RULE (CLAUDE.md): a RED data-pipeline
problem was marked resolved without being fixed, silently, at scale, for an unknown period (the 599/604 and similar
ratios suggest this has been the STEADY-STATE behavior, not a recent regression).

## Disposition

- **Code fix**: approved same-tick via BLK-2a812311 (answered A by main after independent code verification) —
  dispatched to slot 11 (task agt-21fadd) as a scoped allowlist fix. **That dispatch never shipped it**: `agt-21fadd`
  registered 2026-08-09 05:16:46 and was reaped `exit_reason=reaped-stale` at 05:40:26 (confirmed live via the
  orchestrator's `agents` table), 24 minutes in, with no matching commit ever landing on `live-defi-rollout`. The bug
  sat live+unfixed for another ~6 hours until an unrelated main-agent session (diagnosing a different escalation
  anomaly, live-queried the same DB) independently rediscovered it, found this doc already covering it, and shipped the
  exact scoped fix described here: gated the line-1736 fallthrough to
  `_QG_SIGNAL_WALLS = {"ldr_qg_failure", "main_ci_red"}`, added a parametrized regression test sweeping every wall type
  NOT in that set (so a future new wall type defaults to the safe `None` branch too) plus a `main_ci_red`-unaffected
  guard test. Shipped `agent-orchestrator@884a9bfe1` (`live-defi-rollout`), full `quality-gates.sh` green (2908 passed)
  before shipping.
- **This doc's scope**: (1) operator-visible record of the historical blast radius given the HARD RULE violation, per
  CLAUDE.md's "big finding (data-correctness...) → NOTIFY OPERATOR + issue doc"; (2) tracking the two specific live
  escalations that were wrongly auto-closed and still need real investigation — the code fix does not retroactively
  investigate them.

## Todos

- [x] ✅ [DATA] P1. **RESOLVED 2026-08-10 — DP-VM-003 relaunched and progressing.** Verified live: VM
      `mtds-backfill-odds-smallchunk14-20260809` RUNNING in asia-northeast1-c, created 2026-08-10T09:29:02Z (fresh
      relaunch by another actor after the 08:36Z SPOT-preemption STOP), `run.log` tail shows chunk 45/2171 progressing
      (league=ARGENTINA_PRIMERA, date=2020-10-11), 0 CHUNK_FAILED/OOM/exit=137 since relaunch. Full live evidence +
      Progress Log entry in `/plans/active/meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md` (todo 11, slot 22,
      2026-08-10T16:10Z). Retagged `[OPERATOR]` → `[DATA]` per `task_template.md` finding U — a named-launcher relaunch
      is not operator-gated; both cloud identities are IAM-self-service.
- [x] ✅ [VERIFY] P1. Confirm DP-FETCH-009 (CRITICAL 1% cefi `book_snapshot_5` cell-loss gap) has been manually
      investigated — **it has, extensively**:
      `cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md` carries a 25+-dispatch escalation
      history (confirmed via `na-eligibility-audit 2026-08-09`'s own full re-read) with 5 shipped fixes (3 root-cause
      schema-contract fixes — MTDS `339ca767`/`6bf568ee`, UAC `8db188fe`/`1c4d8864` — plus 2 alerting-layer fixes —
      deployment-service `a564cca` materiality downgrade, `9102eb9b` dedup-gap fix). This doc's framing ("nobody has
      actually looked at either") is stale for DP-FETCH-009 specifically; DP-VM-003 above is untouched by this
      re-verification and remains open.
- **[BACKEND] P2. EXTRACTED 2026-08-09 → `cross_cutting_satellite_ao_dispatch_batch7_2026_08_09.md`.** Now that the
  BLK-2a812311 quickmerge fix has landed (`agent-orchestrator@884a9bfe1`), spot-check a bounded sample of the historical
  `data_pipeline_failure`/`provenance_blocked`/`sit_failure`/`plan_health` rows auto-closed via this bug (beyond
  DP-VM-003/DP-FETCH-009) for any other still-live, still-unaddressed problems masquerading as resolved. See the batch
  doc for the full scoped todo; do not duplicate-dispatch from here.
- [x] ✅ [REVIEW] P2. **DONE 2026-08-09 (main) — verified against `agent-orchestrator@884a9bfe1`.** Allowlist gate
      exactly matches scope: `_QG_SIGNAL_WALLS = frozenset({"ldr_qg_failure", "main_ci_red"})`, checked via
      `if     wall_type not in _QG_SIGNAL_WALLS: return None` right before the generic
      `ci_reconcile.repo_ldr_qg_conclusion` call. Regression coverage:
      `test_poll_wall_resolution_non_qg_signal_walls_never_auto_resolve` is parametrized over
      `escalation.WALL_TYPES - escalation._QG_SIGNAL_WALLS` (all 7 non-QG-signal types, derived from the real set, not
      hand-listed — a future new wall type defaults to the same safe branch) plus asserts the unrelated poll is never
      even CALLED; `test_poll_wall_resolution_main_ci_red_unaffected_still_resolves_via_qg_green` confirms main_ci_red
      is unchanged; all pre-existing `ldr_qg_failure` PR-scoped/bare tests pass unmodified (diff-reviewed, not just
      green). Full `quality-gates.sh` 2908 passed before shipping.

## Progress log

- 2026-08-09 (main agt-22de53): Filed after answering BLK-2a812311 as A (scoped fix now, dispatched to slot 11) —
  independently verified the code at `server/escalation.py:1660-1753` before deciding, confirming the reporting worker's
  finding exactly (down to the docstring/implementation mismatch). This doc covers the operator-notification and
  live-follow-up scope that the code fix alone does not: historical blast radius, and DP-VM-003/DP-FETCH-009 needing
  real (not silently-marked) resolution.
- **stale-`[OPERATOR]`-flip sweep 2026-08-09**: DP-FETCH-009's "confirm investigated" todo was stale — re-verified
  against `cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md`'s own Progress Log: 25+
  dispatches, 5 shipped fixes across 3 repos. Flipped `[x]`, retagged `[OPERATOR]` → `[VERIFY]`. DP-VM-003 (separate
  todo above) was not re-verified this pass and stays open.
- **2026-08-09 (main, separate session)**: while diagnosing an unrelated escalation-queue anomaly (root_key staleness,
  see the sibling finding this session also fixed), live-queried `GET /api/escalations/active` and the orchestrator's
  `escalation_queue`/`agents` tables directly and found this doc's "dispatched to slot 11, shipped via quickmerge" claim
  was inaccurate — `agt-21fadd` died `reaped-stale` after 24 minutes, no commit ever landed, and the bug was still live
  (still auto-closing data_pipeline_failure walls against `market-tick-data-service` within 1-7 minutes, observed
  directly: 9 instances in a 2h window, `dispatched_at` null on every one). Implemented the exact scoped fix this doc
  already specified, added regression tests, ran full `quality-gates.sh` (2908 passed) — which also surfaced and
  required fixing an unrelated stale-`.venv` pip-audit gate failure (msgpack/pip/pyasn1/setuptools — `uv.lock` already
  had the patched versions from the CVE remediation doc's 2026-07-30 pass, the checked-out `.venv` just never ran
  `uv sync` after — fixed via `uv sync --frozen`, no lockfile/floor changes needed). Shipped
  `agent-orchestrator@884a9bfe1` via quickmerge. DP-VM-003 and the P2 historical-sample todo remain genuinely open —
  this entry only covers the code-fix landing.
- **round9-cross-cutting-sweep 2026-08-09**: satellite-extracted the bounded `[BACKEND] P2` historical-sample audit into
  `cross_cutting_satellite_ao_dispatch_batch7_2026_08_09.md` — the code-fix prerequisite it was waiting on has landed.
  Whole-doc RECLASSIFY not applied — the `[OPERATOR] P1` DP-VM-003 confirm/relaunch item stays open and genuinely
  operator-tagged.
- **2026-08-10 (slot 17, infra, task `meta_plan_corpus_hygiene_ao_dispatch_batch1-eab99d85fdc7`, todo 9)**: Verified +
  flipped the 3 resolved checkboxes per `ag_closeout_audit_cross_cutting_parked_2026_08_10.md` finding 3. Items 2
  (DP-FETCH-009 `[VERIFY] P1`) and 4 (code-fix `[REVIEW] P2`) were already `[x]` — confirmed by direct doc read. Item 1
  (DP-VM-003 `[OPERATOR] P1`) flipped `[x] ✅ [DATA] P1`: live `gcloud compute instances describe` confirmed VM
  `mtds-backfill-odds-smallchunk14-20260809` RUNNING (asia-northeast1-c, created 2026-08-10T09:29:02Z), matching the
  independent verification in `/plans/active/meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md` Progress Log
  (todo 11, slot 22). All 4 todos in this doc are now resolved (2 flipped `[x]`, 1 extracted to batch7, 1 flipped here).
- **context-scout 2026-08-14**: populated context_scope (2 entries).
