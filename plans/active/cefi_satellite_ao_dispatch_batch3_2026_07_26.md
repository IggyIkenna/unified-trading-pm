---
doc_type: plan
title: CeFi satellite AO batch 3 — iterative-drain extraction over the batch2 orphan residual
summary: >-
  Third AO-dispatch batch for cefi, produced by the `/ag-closeout-audit` skill run 2026-07-26 (autonomous mode)
  immediately after the cefi `/plan-reconcile` pass. Phase 0-2 re-derived the covering-plan set (19 plans + the epic)
  and classified all 43 cefi AG-primary docs outside it: 16 fully covered, 3 mistags, 1 archivable_now, and **23
  orphaned**. Per the skill's iterative-drain rule this run re-checked batch2's own 12 Deferred items FIRST (all 12
  gates re-verified still closed — batch2 was authored the same day, so nothing had cleared) and then ran a fresh
  Phase-1/Phase-3 pass over the residual, including two docs batch2 could not have seen because its own work created
  them. 5 items cleared the conflict-check into todos below; everything else is held in Deferred with its blocking class
  named. One genuine cross-tranche conflict was found and is PARKED for the operator rather than guessed at.
status: draft
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm, instruments-service, market-tick-data-service, deployment-service]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-3, satellite-docs, iterative-drain]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/active/cefi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/cefi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md,
    /plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-07-26 (autonomous, operator away) — Phase 0 re-derived the cefi covering-plan set,
  Phase 1 classified all 43 cefi AG-primary docs outside it (inline per-doc reads; no Workflow/Agent tool exists in this
  runtime, so the documented per-doc fan-out was performed serially by the single agent), Phase 3 conflict-checked every
  candidate against the covering set AND every other tranche's live batch before drafting.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# CeFi satellite AO batch 3 — iterative-drain extraction

> **Status: draft — NOT dispatched.** Per CLAUDE.md's plan-destination HARD RULE and the ag-closeout-audit skill's
> autonomous-mode guidance, a skill-drafted AO batch is never auto-flipped to `active`. This run was autonomous with the
> operator unreachable, so the flip is explicitly reserved for operator review. Flip this frontmatter's `status` to
> `active` only after that review.

> **Cross-todo file-collision check: PASS.** The 5 todos touch, respectively:
> `plans/active/data_completion_cefi_2026_07_15.md` · instruments-service CLI + `t1_batch_scheduler.tf` ·
> `/codex/05-infrastructure/deployment-observability.md` · MTDS `engine/orchestrator/sentinels.py`+`__init__.py` ·
> (read-only, no code edit). Todos 1 and 3 are both in unified-trading-pm but touch different files. Todos 4 and 5 are
> both market-tick-data-service but todo 5 makes no code change. Safe to dispatch concurrently.

## Todos

- [ ] [DOCS] P3. **Retire the stale "~50% attempted_failed (1.33M)" cefi figure at its source.**
      `data_completion_cefi_2026_07_15.md`'s E6 CF-7 line item (line ~277) still reads "Investigate the 50%
      `attempted_failed` rows (1.33M)". That figure was re-measured against the live cefi availability index on
      2026-07-26 (9,138,791 rows, single read) as **11.61% / 1,060,613 rows** — the denominator grew ~3.5x while the
      numerator fell, so the "~50%" framing overstates a correctness problem that is already ~95% attributed to open P0
      work. Edit that line item to (a) strike the stale ~50%/1.33M figure, (b) cite 11.61% / 1,060,613 as the current
      measurement, and (c) link `/plans/active/issues/cefi_e6_cf7_relabel_and_attempted_failed_remeasure_2026_07_26.md`
      as the measurement + attribution record. Also strike the same line's "COINBASE↔COINBASE-SPOT mismatch" relabel
      premise — that doc measured bare `venue == "COINBASE"` at **0 rows** (already fully canonical), so there is no
      relabel to do. Do NOT touch the blank-`data_type` half of that line item — it is PARKED as a cross-tranche
      conflict (see Deferred). Repo: unified-trading-pm. Source:
      `issues/cefi_e6_cf7_relabel_and_attempted_failed_remeasure_2026_07_26.md`. **Done when**:
      `data_completion_cefi_2026_07_15.md`'s E6 CF-7 item carries the corrected figure + the link, the COINBASE relabel
      premise is struck with the 0-row measurement cited, that source doc's `[DOCS] P3` checkbox is flipped `[x]` with
      the commit cited, and prek is green.
- [ ] [SCRIPT] P2. **Make the cefi IS t1-recon job's date window default to the run day instead of a hardcoded range.**
      The cefi instruments-service recon job runs on a hardcoded `--start-date`/`--end-date`, so it re-processes a fixed
      historical window every day instead of doing true T+1 forward-fill. Implement EITHER (a) the IS CLI defaults
      `--start-date`/`--end-date` to the run day (yesterday for true T+1) when `--run-tag=t1-recon` and both are unset,
      OR (b) `t1_batch_scheduler.tf`'s scheduler injects `{start-date,end-date}` via `httpTarget.body` overrides — (a)
      is preferred because it keeps the default in the CLI where every caller inherits it, but either satisfies this
      todo; this is an implementation choice, not a design fork. Repos: instruments-service, deployment-service.
      **Coordination note (conflict-check)**: `cefi_satellite_ao_dispatch_batch2_2026_07_26.md`'s `[SCRIPT] P1` hygiene
      sweep sub-item (c) already imported these t1-recon Cloud Run JOB specs into the shared prod tofu state
      (`deployment-service@54aa6f5`, **already DONE/`[x]`** — verified re-plan clean). Build ON that state; do not
      re-import or re-create the job specs. Sub-items (a)/(b) of that same sweep (dead-CLI daily Workflow; all-AG
      producer crash) are also already closed — this todo is the remaining, uncovered date-default half. Source:
      `issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md` (line ~167). **Done when**: a cefi t1-recon run with no
      explicit date arguments processes the run day (or run-day-minus-1) rather than the old hardcoded window,
      demonstrated by one real execution's logged date range; a unit test covers the defaulting branch; `tofu plan` is
      clean if (b) was chosen; `quality-gates.sh` green in every touched repo.
- [ ] [DOCS] P2. **Correct the codex Slack-parity contract for the umbrella-driven channel split.**
      `/codex/05-infrastructure/deployment-observability.md` § "Slack parity + alert enrichment" (line ~267) still
      documents deployment-lifecycle alerts as routing to `#data-pipeline-alerts` only. The real, shipped routing is an
      umbrella-driven split — LIVE→`#uts-live-alerts`, BATCH→`#data-pipeline-alerts` — plus an emitter umbrella-stamping
      contract. **This is a correct-codex edit only** (codex is factually stale versus already-shipped code), which is
      the one class of codex edit the backend/plan-reconciler discipline permits without an operator ruling — so BEFORE
      editing, verify the drift is real: confirm `alerting-service@f94b3b5` and `deployment-service@94dfcfc` both exist
      and are reachable on `origin/live-defi-rollout`, and read the live routing code to confirm the split is what
      actually ships. If either sha does not resolve, or the code does not match the claimed split, do NOT edit — record
      the discrepancy in the source doc instead and leave codex alone. Repo: unified-trading-pm. Source:
      `issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md` (line ~465). **Done when**: both shas are verified reachable
      and the routing code read, the § "Slack parity" section states the umbrella-driven channel split + the emitter
      umbrella-stamping contract, the source doc's `[DOCS] P2` checkbox is flipped with the commit cited — or, on a
      failed verification, an explicit written finding replaces the edit.
- [ ] [SCRIPT] P2. **Delete the now-inert cefi pre-listing plumbing from MTDS.** With the pre-listing source retired,
      `catalog_list_not_yet_listed_cefi` always returns empty → `cefi_pre_listing_by_venue` is always `{}` → the
      `record_expected_empty(EXPECTED_INSTRUMENT_NOT_LISTED)` write loop never fires. The threaded parameter and the
      write block are dead code across ~6 call sites in market-tick-data-service's `engine/orchestrator/sentinels.py`
      and `engine/orchestrator/__init__.py`. Remove them for a clean break per the workspace "delete deprecated code, no
      shims" rule — do NOT leave a stub or a feature flag. Repo: market-tick-data-service. **Coordination note
      (conflict-check)**: `cefi_4surface_migration_execution_log_2026_07_24.md`'s item 7c (`[INFRA] P2`, state "Not
      done") separately targets `engine/orchestrator/__init__.py::get_venues_for_asset_groups` to drop the stale
      hard-coded `DERIBIT-COMBO` cefi venue. Different symbol, same file. Before editing, re-check whether 7c has
      started; if it has, sequence after it rather than editing concurrently. Source:
      `issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md` (line ~840). **Done when**:
      `grep -rn     'catalog_list_not_yet_listed_cefi\|cefi_pre_listing_by_venue' market-tick-data-service/` returns 0
      hits outside tests-being-deleted, no `EXPECTED_INSTRUMENT_NOT_LISTED` write path remains in the cefi orchestrator,
      `quality-gates.sh` is green, and the source doc's `[SCRIPT] P2` checkbox is flipped with the commit cited.
- [ ] [DIAG] P2. **Profile whether the 17s CPU-bound block in `catalogue_symbols_for_venue` is GCS-parse time or an
      in-memory filter — read-only fact-finding, implement NEITHER fix option.** Every per-day cefi backfill subprocess
      rebuilds a `CeFiCatalogReader` and calls `list_instruments("cefi", day, day, venues=[venue])`, loading the full
      ~428k-row catalogue and re-resolving the universe — ~34s wall for a 0-row day, of which ~17s is CPU-bound. The
      source doc's own "Proper fix (two options)" is an undecided architectural fork (A: range-loop in one process,
      touching the shared VM startup script; B: a cross-process local-disk cache in `CeFiCatalogReader`) that is
      **operator-gated and explicitly NOT in scope here**. Option B is only correct if the 17s is the cacheable
      GCS-download+parse; if it is an in-memory filter over 428k rows, caching would not fix it and option B is the
      wrong design. Profile one real invocation of
      `market_tick_data_service/cli/handlers/_onchain_perp_batch_symbols.py::catalogue_symbols_for_venue` (cProfile or
      equivalent) and attribute the ~17s between (i) GCS object download, (ii) parquet parse, (iii) in-memory
      filter/universe resolution. Do NOT change any code, do NOT launch a backfill VM, do NOT pick option A or B — this
      is complementary evidence for the pending operator ruling, exactly the pattern batch1 used for the PACIFICA-SOLANA
      Tardis probe. Repo: market-tick-data-service (read-only). Source:
      `issues/cefi_backfill_per_day_catalogue_reload_2026_07_20.md`. **Done when**: a written profile breakdown
      attributing the ~17s across the three phases with measured numbers is appended to that issue doc, the doc states
      explicitly which of options A/B the evidence favours **as information for the operator** without adopting either,
      and zero code/GCS/manifest mutations occurred.

## Deferred — BLOCKED-OPERATOR-DECISION (a genuine conflict, parked not guessed)

- **Blank-`data_type` cefi manifest rows — two docs in two tranches claim overlapping ground with different
  dispositions.** `issues/cefi_e6_cf7_relabel_and_attempted_failed_remeasure_2026_07_26.md`'s `[DATA] P3` proposes
  root-causing **9,750** blank-`data_type` `captured` rows and "either backfill the correct `data_type` per row or
  confirm honest-absence-safe disposition". `instruments_mtds_consistency_remediation_residuals_2026_07_24.md:449`
  (`asset_group: [cross-cutting]`, open `[DATA] P2`) instead claims the **COINBASE(7)+OKX(7)** subset as "malformed
  blank-shard-dim aggregate captured rows with no concrete object", explicitly says the bare→suffixed venue map is
  AMBIGUOUS and therefore NOT a mechanical canon, and prescribes **reclassify**, not backfill. The cefi doc's venue
  breakdown literally contains the row `OKX 7`, so these are the same rows. The cefi doc asserts "No existing open issue
  doc found tracking this specific population" — that claim is **wrong**, and the reason is instructive: it grepped for
  lowercase "blank data_type" and the exact row count, while the cross-cutting doc writes "BLANK
  data_type/instrument_type". Two todos, different prescribed fixes, same manifest rows, no evidence that settles which
  is right. Not drafted; see the operator question raised by this run.

## Deferred — operator-gated (re-verified 2026-07-26, all still closed)

All 10 of batch2's operator-gated Deferred items were re-read this run; **none has cleared** (batch2 was authored the
same day, so this is expected, not a stall). They are NOT re-listed here — see
`cefi_satellite_ao_dispatch_batch2_2026_07_26.md`'s own Deferred sections, which remain the authoritative record, and
`cefi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md`'s todo 2, which already owns the re-check loop. Additional
operator-gated ground confirmed this run:

- **`issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md`** — the only cefi-primary doc with **zero**
  covering-plan citations anywhere (cited solely in the aggregated-sources digest, which is explicitly non-covering).
  All 3 of its open todos are tagged `[HUMAN]`: create the Bybit trade-scope GCP secrets, decide OKX/Hyperliquid's
  scope-separation design, decide whether to build the Aster execution adapter / provision 4 venues' credentials. Zero
  AO-eligible content — a genuine orphan that only a human can drain.
- **`issues/deribit_combo_perpetual_partition_move_2026_07_21.md`** — its 2 `P1` code todos are **provably already
  shipped**: `cefi_4surface_migration_execution_log_2026_07_24.md` item 7 records "INVESTIGATED, NO CODE NEEDED — the
  guard-widen already shipped this session (`mtds@2ddc6d4a`) and `tardis_cefi_shards.py` already shares the fixed
  classifier (no duplicate code path to port into)". Per the conflict-check's provably-stale branch, no competing todo
  is drafted; the 2 stale checkboxes are a `/plan-reconcile` flip, not a batch item. Its remaining 2 `[DATA] P2` todos
  (the 15,119-row partition-move `--apply` + its review) are held by an explicit 2026-07-23 operator ruling that
  approved the code prep and **withheld** the data move.

## Deferred — prerequisite-gated (cannot be drafted until a named gate lands)

- **`MANIFEST_ALLOW_STALE_FALLBACK=true` revert** in
  `deployment-service/scripts/vm/launch-cefi-instruments-backfill.sh:138` (+ the GCS-uploaded
  `setup-data-pipeline-vm.sh`), from `instruments_cefi_g1_g5_gate_execution_2026_07_24.md:702`. The flag is a documented
  INTERIM escape-hatch that must be reverted "once the consolidator is healthy" — and consolidator health is itself an
  open todo in **another tranche** (`cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`, `[INFRA] P1`, "Restore
  the manifest consolidator (R5-fix-5)"). Reverting first would re-break every cefi backfill launch. Extract in a later
  batch once that todo lands.
- **features-service raw cefi day-scan is unbounded** (`issues/cefi_residual_followups_after_honest_done_2026_07_17.md`,
  `[BACKEND] P2`). The doc itself sequences it AFTER its sibling `[BACKEND] P1` schema-gap todo — and that sibling is
  operator-gated, not AO-eligible: shaping the flat L5 MTDS schema into the calculators' `bids`/`asks`/`mid_price`
  contract is a **feature-definition change** (formula-hash, `/codex/02-data/feature-formula-versioning.md`), which the
  doc explicitly declines to invent. Both stay deferred until that definition is ruled.
- **`create-code-tarballs.sh` per-repo dirty-tree SKIP** (`issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md`
  `[SCRIPT] P3`). Cross-plan file collision: `prediction_cross_venue_arb_and_coverage_2026_07_24.md:102` and
  `prediction_consolidated_closeout_2026_07_18.md:406` both carry an OPEN `[OPS] P2` on the **same script** for a
  different defect (the concurrent-fleet tarball-overwrite race). Two live claims on one file across two tranches —
  bundle them, don't race them.
- **cefi zero-capture data_type gaps** (`issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md` `[SCRIPT] P2`,
  "`perp_funding`=0 captured, `futures_chain`=223, `options_chain`=3, `ohlcv_1m`=738"). Measured 2026-06-24; the
  2026-07-26 live re-read in `issues/cefi_e6_cf7_relabel_and_attempted_failed_remeasure_2026_07_26.md` reports a
  materially different picture, and the `futures_chain`/`options_chain` population is the already-P0-tracked DERIBIT
  Tardis-403 backlog. Re-measure before drafting, or it dispatches a worker against month-stale numbers into contested
  ground.

## Deferred — too-large-or-risky-for-a-batch-todo

- **`issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`** — a live, actively-draining migration whose
  remaining work is **prose-only** (zero checkboxes in the file, the confirmed corpus trap): a 2,962-object safe
  residual rename needing a cron-pause drain + 4 sequential venue-scoped `--apply` runs, a colon_wire loop-until-dry
  reconfirmation, a final 4-surface re-proof, and a 1,292-object collision residual already `BLOCKED-OPERATOR-DECISION`.
  Dated Findings 8/9/10 supersede each other inside the same file and the file's own table is self-labelled STALE.
  `cefi_satellite_ao_dispatch_batch1_2026_07_25.md` already excluded this doc on live-conflict grounds; that exclusion
  still holds. Needs its own dedicated session, not a batch slot.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox in its named source doc, citing this plan's commit as evidence.
This plan's own reconciliation-then-archive step is machine-gated via the companion
`cefi_satellite_ao_dispatch_batch3_finalize_2026_07_26.md` (`depends_on` + `gate_on_depends: true`), mirroring the
batch1/batch2 finalize pattern.

## Codex SSOTs

- `/codex/05-infrastructure/deployment-observability.md` — todo 3 corrects its § "Slack parity" section (correct-codex
  only, gated on verifying the two cited shas first).
- `/codex/02-data/feature-formula-versioning.md` — cited by the deferred features schema-gap fork as the reason that
  work is a feature-definition decision, not a loader tweak.
- No new durable contract is created by this plan; every other todo executes an already-decided spec from its source
  doc.
