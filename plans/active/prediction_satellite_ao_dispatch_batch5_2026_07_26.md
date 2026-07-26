---
doc_type: plan
title: Prediction satellite AO batch 5 — the comment-blinded cqg orphan + the un-triaged live-capture stall triage
summary: >-
  Fifth AO-dispatch batch for prediction, produced by a second `/ag-closeout-audit prediction` run on 2026-07-26
  (autonomous). Phase 0-2 re-classified 27 prediction AG-primary docs against the full covering set (consolidated
  closeout + its 4 forked Phase children + native_ao_extract + satellite batch1/2/4 and their finalizes + the archived
  batch3 pair): 21 orphaned, 5 archivable-after-planned-work, 1 digest-only. Of the 21, exactly TWO carry conflict-clear
  bounded AO-eligible work that no batch claims. (1) `prediction_cqg_residual_2026_07_24.md` — ZERO hits in every
  batch/native/phase plan, cited only in the closeout's aggregated-sources digest (the digest trap). It was invisible to
  batch3 (17 docs) and batch4 (26 docs) because its `asset_group` is a multi-line block whose orthogonality-retag
  comment quotes the OLD `[cross-cutting]` value, so a single-line `^asset_group:.*prediction` grep misses the doc
  entirely. Its blocking "operator decision 338" is PROVABLY already ruled + implemented in UAC on 2026-06-16 (10
  in-code citations, all registry EXTENSIONS = option A of its own two-option fork), so its gated todo is now
  dispatchable and its 2026-06-11 premise needs re-basing. (2)
  `issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`'s live-stall triage at `day=2026-06-28` — carried
  unresolved through batch1 (deferred), batch2 (deferred as "one of that doc's OTHER prose items"), batch3 (closed only
  item 3) and batch4 (not mentioned); grep confirms zero competing claim anywhere in the covering set. Every other
  orphan is non-batchable (operator-gated / upstream-blocked / time-gated / human-only / UI-slot-gated) and is cited in
  the Deferred sections, not re-litigated. `status: draft` — a skill-drafted AO batch is never auto-shipped; flipping to
  `active` to dispatch is an operator decision (CLAUDE.md "Plan destination — ASK BEFORE CREATING").
status: draft
nature: process
asset_group: [prediction]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-5, satellite-docs, cqg, conflict-checked]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_cqg_residual_2026_07_24.md,
    /plans/active/issues/kalshi_live_capture_regression_and_drift_2026_07_13.md,
    /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md,
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/active/issues/ag_closeout_audit_asset_group_comment_grep_blindspot_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Second `/ag-closeout-audit prediction` run 2026-07-26 (autonomous, operator away). Ran immediately after the
  `/plan-reconcile prediction` shard, so frontmatter/checkbox state was trustworthy on entry. Phase 1 ran as a
  single-agent per-doc sweep rather than the documented Workflow fan-out — this harness exposes no Workflow/Task/Agent
  tool (verified: `ToolSearch "select:Workflow,Task,Agent"` returns no matching deferred tools), a real fidelity
  difference from the skill as written. Phase 3 conflict-check per the skill's documented methodology; two genuine
  conflicts were PARKED for the operator rather than guessed at (see Deferred).
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# Prediction satellite AO batch 5 — comment-blinded cqg orphan + live-stall triage

> **Status: draft — NOT dispatched.** Drafted autonomously by a second `/ag-closeout-audit prediction` run (2026-07-26,
> operator away for the session). Per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE and the
> ag-closeout-audit skill's autonomous-mode guidance, a skill-drafted AO batch is never auto-shipped: flipping
> `status: draft` → `active` to dispatch these todos is an operator decision. Nothing in this batch was flipped to
> `active`, and no existing plan was edited to resolve a conflict.
>
> **Cross-batch sequencing (read before dispatching).** Todo 2 touches instruments-service cqg-catalogue code;
> `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` todo 3 (still `status: draft`) operationally re-enumerates the
> cqg catalogue for 2026-06-20..22 on an adjacent IS surface. Do NOT dispatch them concurrently — run batch4 todo 3
> first if both are active, mirroring the batch1-todo-7 / batch2-todo-2 collision-note precedent. Todos 1 and 3 touch
> disjoint surfaces (read-only census / read-only GCS+VM-log triage) and are safe to run concurrently with anything.

## Why this batch exists (the gap batch3 AND batch4 both missed, and why)

`prediction_cqg_residual_2026_07_24.md` (2 open todos, `status: active`, `asset_group: [prediction]`) appears in ZERO
batch, native-extract, or Phase-child plan. Its only mentions corpus-wide are two entries in
`prediction_consolidated_closeout_2026_07_18.md`'s "Aggregated source docs" digest (lines 302-306 and 349-355) — which
that section's own header declares is "referenced, not duplicated", i.e. the confirmed DIGEST TRAP: being listed there
is not dispatch.

**Why two prior same-day audits missed it** — and this is the reusable lesson, not a one-off. On 2026-07-25 the
ag-closeout-audit Orthogonality HARD CHECK correctly retagged this doc from `[cross-cutting]` to `[prediction]`, and,
exactly as the skill prescribes ("never silently left dual-tagged"), recorded the correction as an inline YAML comment
that QUOTES the old value:

```yaml
asset_group:
  [prediction] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cross-cutting], a genuine
  # mistag: cqg-classifier coverage is prediction-market-specific, inherited the parent harness's cross-cutting
  # tag on fork instead of being corrected to its real single-AG scope
```

That shape breaks tag discovery in BOTH directions: a single-line `rg '^asset_group:.*prediction'` returns NOTHING for
this doc (the value is on the continuation line), while a naive whole-block tokenizer reads the quoted `[cross-cutting]`
as a LIVE second tag and excludes the doc as a peer-AG cross-cutting candidate. Either way the doc falls out of the
candidate set — the exact invisible-orphan failure class the Orthogonality HARD CHECK exists to prevent, reintroduced by
the fix itself. Filed as `/plans/active/issues/ag_closeout_audit_asset_group_comment_grep_blindspot_2026_07_26.md`; the
skill-side remediation is tracked there, not here (it is process/tooling work, not prediction data work).

**And its blocking gate has already cleared.** Both cqg_residual todos hang off "operator decision 338" (todo 2 says
`Blocked-on: 338` literally). Decision 338 was ruled and implemented in UAC on **2026-06-16** — five weeks BEFORE this
doc was even forked (2026-07-24), and the fork's own Progress Log admits "no work done yet on either todo beyond what
the parent's archived Progress Log already recorded", i.e. the gate was never re-checked at fork time. Evidence, read
from source at `unified-api-contracts/unified_api_contracts/canonical/domain/predictions/`:

- `classifiers.py` carries **10 in-code "decision 338" citations**, all dated 2026-06-16, and every one is a registry
  EXTENSION: alt-coin daily up/down groups (line 282), weather EVENT resolution (296), the dead-`FED_RATE`-key fix
  (312), macro economic-release groups UNEMPLOYMENT/NONFARM_PAYROLLS/GDP/PPI/PCE (315), range-bracket cadence (326), and
  "decision 338 pass 2 (2026-06-16) — granular sub-type routing" (332, 423, 449, 561).
- That is precisely **option A** of cqg_residual todo 1's own two-option fork ("EXTEND the UAC
  `canonical_question_group` registry coverage — most Polymarket markets are sports/politics/entertainment outside the
  MVP crypto set"): sports, macro, weather and alt-coins are exactly the non-MVP-crypto categories it names.
- Separately, `classify_polymarket_to_canonical_group`'s docstring (classifiers.py:538-545) records that unmatched
  Polymarket combinations now return `CanonicalQuestionGroup.OTHER` — "**Previously returned `None` (caller routed to
  `attempted_failed[reason=ClassifierConfidenceLow]`) — changed to `OTHER` so honest-absence capture replaces silent
  failure**". So the doc's stated premise ("under the operator-corrected contract: None → NOT bundled, no `OTHER`
  fallback") no longer describes the live Polymarket path at all, and its 94.5% figure (measured 2026-06-11, five days
  before 338 landed) is stale by construction.

Todo 1 below therefore re-bases the measurement rather than re-asking the decision; todo 2 executes the now-unblocked
wiring. The residual semantic question that this evidence does NOT settle is parked for the operator (see Deferred —
parked conflicts).

## Todos

- [ ] [DATA] P1. **Re-base the prediction cqg-classifier coverage census post-decision-338 (read-only; does NOT make the
      extend-vs-ratify call).** `prediction_cqg_residual_2026_07_24.md` todo 1 rests on a 2026-06-11 measurement
      (542,169/573,536 objects = 94.5% routing to `attempted_failed[ClassifierConfidenceLow]`, captured cqg bundles
      ending 2026-04-14) taken five days BEFORE decision 338's registry extension landed in UAC and before
      `classify_polymarket_to_canonical_group` was changed to return `OTHER` instead of `None`. Re-measure against
      today's UAC registry + the live prediction manifest and record: (a) the current
      `attempted_failed[ClassifierConfidenceLow]` row/object share, broken out **per venue** (the two venues take
      genuinely different code paths — `rebuild_prediction_manifest.py:409-429` calls
      `classify_kalshi_to_canonical_group` for KALSHI, which still returns `None` for unmatched, versus
      `classify_polymarket_to_canonical_group` for POLYMARKET, which now returns `OTHER`); (b) the current share bundled
      into `canonical_question_group=OTHER`; (c) whether captured cqg bundles still end 2026-04-14 or now extend later.
      Repo: unified-trading-pm (analysis only; reads unified-api-contracts' registry + the live prediction
      `availability_index.parquet`). **Read-only — no `--apply`, no manifest mutation, no VM launch, no delete.**
      Source: `prediction_cqg_residual_2026_07_24.md` (todo 1). **Done when**: (a), (b) and (c) are recorded as dated
      measured numbers with the method and read timestamp in that doc's Progress Log, and todo 1's inline "94.5% /
      2026-06-11" premise is annotated in place as either re-based (citing the new numbers) or confirmed-still- accurate
      — never left implying the stale figure is current. **Explicitly out of scope**: choosing between "extend the
      registry further" and "ratify out-of-registry-stays-failed". That fork is the operator's (see Deferred — parked
      conflicts); this todo only supplies the numbers the choice needs.

- [ ] [CODE] P2. **Wire the canonical-question-group into the instruments-service catalogue-rollup loader so
      `prediction_canonical_question_group` cqg-grain rows emit — the gate on this provably cleared 2026-06-16.**
      `prediction_cqg_residual_2026_07_24.md` todo 2 ("249-b") states the rollup ALREADY materialises the cqg grain
      whenever `cqg_str` is non-empty, and that the loader yields `cqg=""` today; the only thing holding it was operator
      decision 338, which this batch's "Why this batch exists" section proves was ruled + implemented in UAC on
      2026-06-16. Wire the cqg through (from the classifier, or from a `_canonical_group` write-back, whichever the
      loader's existing shape supports) so the grain populates. Repos: instruments-service, unified-api-contracts.
      **Scope boundary — do NOT run the prod `prod/catalog.parquet` promotion as part of this todo.**
      `prediction_phase_ab_residuals_2026_07_24.md`:132-152 holds an open P0 for the full
      `build_instrument_catalogue.py --asset-group prediction` prod regen and states it is "intentionally NOT executed
      yet (staged rollout, gated on the in-flight shared canonical-identity migration so it doesn't bake
      transitional/half-migrated ids into the persisted catalogue)" — promoting a catalogue here would execute exactly
      that deliberately-held step. Verify with tests instead, and let phase_ab's gated regen carry this wiring to prod
      when it runs. **Sequencing**: do not dispatch concurrently with
      `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` todo 3 (adjacent IS cqg-catalogue surface). Source:
      `prediction_cqg_residual_2026_07_24.md` (todo 2). **Done when**: a new/extended instruments-service unit or
      integration test proves the loader now yields a non-empty `cqg_str` for a fixture prediction record and that the
      rollup consequently materialises `prediction_canonical_question_group` cqg-grain rows (previously zero);
      `quality-gates.sh` is green in every touched repo; the prod promotion is explicitly recorded as NOT run, with a
      pointer to `prediction_phase_ab_residuals_2026_07_24.md`'s gated regen todo as its carrier.

- [ ] [DIAG] P1. **Confirm or deny the prediction live-capture stall at `day=2026-06-28` (read-only).**
      `issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`'s "Suggested next step" item 1 has never been
      actioned: `raw_tick_data/by_date/` appeared to have no day partitions after `day=2026-06-28` (~2 weeks stale as of
      2026-07-13, no July partitions at all). The doc itself flags this as the higher-stakes of its findings — "#2
      touches live data-pipeline correctness directly (a stalled capture path silently produces gaps that look like
      'genuine unavailability' downstream rather than a known, fixable break). Per the data-pipeline-correctness HARD
      RULE this should not sit un-triaged." Determine whether the gap is a genuine live-capture stall or a path/prefix
      read artifact (the prediction estate has a documented history of exactly this false positive — the cqg-first
      partition ordering and the env-short `-pred-prd-` vs env-less `-prediction-` bucket split have BOTH previously
      produced "stale/empty" misreads, see `prediction_live_clob_depth_capture_2026_07_24.md`'s 2026-06-23 entries).
      Check the live producer VM logs / process state directly, and probe both bucket forms and both partition shapes
      before concluding. Repo: market-tick-data-service (read-only). **Read-only diagnosis — no fix, no backfill, no VM
      launch, no manifest write in scope; if a genuine stall is confirmed, the remediation is a follow-up todo, not this
      one.** Source: `issues/kalshi_live_capture_regression_and_drift_2026_07_13.md` (Suggested next step item 1).
      **Done when**: a dated verdict is appended to that doc's Progress Log — either ARTIFACT (naming the exact
      prefix/bucket/partition shape that was misread, plus the day partitions that DO exist) or GENUINE STALL (naming
      the last real capture day, the producer VM(s) involved, and what their logs show) — and item 1 of that doc's
      "Suggested next step" list is struck through with the verdict cited, matching how item 3 was closed on 2026-07-26.

## Deferred — parked conflicts (BLOCKED-OPERATOR-DECISION; NOT guessed at, NOT silently drafted)

Both were surfaced by this run's Phase-3 conflict-check and are returned to the operator as structured questions with
marked recommendations. Neither is drafted as a todo here, and **no existing plan was edited to resolve them**.

- **Out-of-lifecycle prediction cell — `empty_confirmed[EXPECTED_*]` (out-of-window) vs `expected_unattempted`?**
  `prediction_phase_ab_residuals_2026_07_24.md`:124-128 wants inactive days to land as "an honest `EXPECTED_*`" instead
  of `SOURCE_RETURNED_ZERO`. `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` todo 1 leg (2) wants them as
  "honest BLANK / `expected_unattempted`, **NEVER `empty_confirmed`**", and its leg (3) proposes evaluating whether
  `EXPECTED_INSTRUMENT_NOT_LISTED`/`PRE_VENUE_LAUNCH`/`DELISTED` should be REMOVED from `EMPTY_CONFIRMED_REASONS`. Read
  from source: all three are already members of `OUT_OF_COVERAGE_WINDOW_REASONS`
  (`unified-api-contracts/.../crosscutting/_honest_coverage_empty_reasons.py:590-616`), the operator-directed
  (2026-06-12, extended again by operator 2026-07-17) coverage-denominator partition that clips them from numerator AND
  denominator while keeping the raw rows honestly `empty_confirmed` + a visible reason badge, "so an out-of-model range
  is always VISIBLE, never silently dropped". So batch4's stated intent appears already delivered by a different shipped
  mechanism, and removing the enum members would break `record_empty(reason=...)` validation
  (`UnknownEmptyConfirmedReasonError`) for every asset group that emits them. This is a cross-repo canonical-set change
  — outside dispatch-scope eligibility either way. Operator ruling needed before batch4 todo 1 is dispatched.
- **Unmatched prediction market — `OTHER` (capture-and-flag) or `attempted_failed[ClassifierConfidenceLow]` (honest
  failure)?** Three surfaces currently disagree: `classifiers.py`'s module docstring (lines 21-24) still documents
  "return `None`; caller marks the shard as `attempted_failed[reason=ClassifierConfidenceLow]`";
  `classify_polymarket_to_canonical_group` (538-545) returns `OTHER` instead; and MTDS
  `rebuild_prediction_manifest.py`:612 still implements `Unclassified cids → attempted_failed[ClassifierConfidenceLow]`,
  which now only bites KALSHI. `predictions_other_bucket_and_ui_drilldown_2026_06_20.md` (shipped `[x]`,
  `unified-api-contracts@306923a`) asserts the opposite of cqg_residual todo 1's premise: "The classifier MUST map every
  Polymarket `conditionId` (and Kalshi ticker) to SOME canonical question group ... Treating `OTHER` as a known
  catch-all is honest absence". Todo 1 above measures the consequence per venue; it deliberately does not rule on it.

## Deferred — non-batchable orphans (triaged this run, NOT re-litigated)

Per the skill's iterative-drain rule and non-batchable taxonomy. 21 of the 27 AG-primary docs classified this run came
back orphaned; the 19 not extracted above are listed with WHY, so none is silently dropped:

- **Operator-gated** (no re-triage resolves these):
  `issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` (sign-off for a third remediation
  attempt on a twice-reverted live index; the code precondition `unified-trading-library@14301571` HAS shipped and
  proven stable on a sibling bucket), `issues/prediction_arb_live_execution_bridge_2026_07_20.md` (architectural
  transport-seam decision), `issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md` (its
  one residual is the `[INFRA] P1 BLOCKED-OPERATOR-DECISION` historical re-backfill launch; its `[VERIFY] P2` leg is
  batch1 todo 4), `prediction_cross_venue_arb_and_coverage_2026_07_24.md`'s 2 `[DESIGN]` items + the `[UAC]`
  politics/geo arbability audit + its 2 `[OPERATOR]`-gated manifest-walk items (all already in batch4's Deferred),
  `prediction_phase_ab_residuals_2026_07_24.md`'s `[DECISION] P1` ambiguous-canonical-form item,
  `issues/sports_odds_naming_migration_uncommitted_wip_and_checkbox_drift_2026_07_25.md` item 3 (dispatch-track
  re-flag).
- **Permanently human-only**: `issues/kalshi_execution_credential_secret_name_mismatch_2026_07_26.md` (`BLK-c2d1fff9` —
  live trading-exchange credential material, a CLAUDE.md wallet-key-adjacent hard stop; its second todo is gated on that
  ruling), `data_completion_prediction_2026_07_15.md` (0 AO-eligible / 21 human-only, now independently re-triaged FOUR
  times: batch1, batch2, batch3-finalize 2026-07-26, and this run).
- **Upstream/credential-blocked**: `prediction_perps_kalshi_polymarket_parked_2026_07_24.md` (no public Polymarket perps
  API exists — `perps-api.polymarket.com` NXDOMAIN, Gamma perp filters silently ignored),
  `prediction_capture_incident_remediation_2026_07_06.md` (6 of its 9 open items are the Kalshi-margin-API repoint chain
  gated on Kalshi member-rollout access plus the Polymarket perps research; its 2 AO-eligible items are batch1 todos
  2-3, and 1 is `[DESCOPED-NOT-MVP]`).
- **Time-gated / Phase-B-gated**: `predictions_ml_walk_forward_and_arb_2026_06_20.md` (one chain rooted on sports_master
  Group E's FSS ≥95% non-NULL threshold; best measured figures are FIXTURE_STATS 34% / ODDS 26% / WEATHER 17%),
  `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md` (2 P0 post-migration skill runs + the MVP backfill
  readiness gate, all gated on the un-started Phase-B migration; its PRE-Phase-B slice is native_ao_extract todos
  2/3/5), `prediction_phase_e_football_arb_live_2026_07_24.md` (all 3 items machine-gated on B+D),
  `prediction_phase_ab_residuals_2026_07_24.md`'s Phase-B enumeration-driven migration + A4 fixture-attribute backfill
  (drain-window / shared-file gated).
- **UI-capable-slot gated (infra resource, not a decision)**: `prediction_phase_c_data_status_ui_2026_07_24.md`'s
  data-status dimensions-enumeration view and `predictions_other_bucket_and_ui_drilldown_2026_06_20.md`'s `[VERIFY][UI]`
  panel re-walk — both need `pw:L2 ✓` on a slot with a running deployment-ui dev server
  (`/codex/06-coding-standards/ui-testing-layers.md`). The latter doc's Phase-5 ~24-group backfill remainder is plain
  unscheduled backlog with no blocking condition.
- **Owned by the sports tranche, excluded to avoid duplicate dispatch**:
  `sports_odds_feature_naming_canonicalization_2026_07_21.md` and
  `issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md` (both covered by
  `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s ml-service migration todo, re-confirmed still unshipped
  2026-07-26), `sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md` (8 `[DESIGN]` todos, 3 unanswered operator
  sign-offs), `sports_group_c_execution_backtest_harness_2026_07_21.md` (todos 3/5 `[DESIGN]`),
  `sports_predictions_live_mode_activation_readiness_2026_07_21.md` (rooted on "decide whether to pursue a live
  sports-odds ingestion path at all").
- **Belongs to a different tranche**: `prediction_cross_venue_arb_and_coverage_2026_07_24.md`'s `[OPS] P2`
  tarball-overwrite race is generic deployment/CI infrastructure — route to the `infra`/`ci` closeout, as batch4 also
  flagged.
- **Digest, no dispatch surface**: `prediction_cross_cutting_debt_index_2026_07_25.md` (0 open todos, pure index).
- **Covered, pending their batch**: `prediction_live_clob_depth_capture_2026_07_24.md` (batch4),
  `issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md` (batch1 todo 5 + batch4 todo 4),
  `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` (now its own `assigned_vm: planning` dispatch
  surface, migrated out of the archived batch3), `issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md`
  (batch2 todo 6).

## Reconciliation

Once a todo here ships, flip the corresponding checkbox/section in its named source doc, citing this plan's commit as
evidence. This plan's own reconciliation-then-archive step is machine-gated via a companion
`prediction_satellite_ao_dispatch_batch5_2026_07_26_finalize.md`
(`depends_on: [prediction_satellite_ao_dispatch_batch5_2026_07_26]` + `gate_on_depends: true`), mirroring the
batch1/2/3/4 finalize pattern.

## Codex SSOTs

`/codex/02-data/honest-absence-downstream-handling.md` (the out-of-window vs within-window empty partition, load-bearing
for both parked conflicts — read before touching either), `/codex/02-data/availability-manifest-and-data-status.md` (the
prediction shard atom is keyed on `canonical_question_group`, load-bearing for todo 2),
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" (the bar applied
to every classification above). No new durable contract is created by this plan — todos 1 and 3 are read-only
measurements and todo 2 executes an already-ruled decision (338).

## Progress Log

- 2026-07-26 (autonomous, second `/ag-closeout-audit prediction` run of the day): drafted. Phase 0 discovered the
  covering set via BOTH documented paths (filename-pattern + the closeout's `depends_on`/`related` dependency graph,
  which is what surfaces the 4 forked Phase children as covering plans). Phase 1 classified 27 AG-primary docs by
  per-doc read: 21 orphaned (11 partial-coverage, 10 never-touched), 5 archivable-after-planned-work, 1 digest-only.
  Orthogonality HARD CHECK: 0 single-AG+cross-cutting mistags corpus-wide. Phase 3 extracted 3 conflict-clear bounded
  todos from the 2 orphans that had any, PARKED 2 genuine conflicts, and routed 1 process finding to its own issue doc.
  Left `status: draft` per the autonomous-mode safety rail — operator flips to `active` to dispatch.
