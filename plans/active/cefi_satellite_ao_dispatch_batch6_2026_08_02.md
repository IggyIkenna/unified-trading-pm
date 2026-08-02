---
doc_type: plan
title: CeFi satellite AO batch 6 — iterative-drain extraction over the batch5 residual
summary: >-
  Sixth AO-dispatch batch for cefi, produced by the `/ag-closeout-audit` skill run 2026-08-02 (scheduled autonomous
  dispatch, tranche=cefi, slot 8). Phase 0 re-derived the covering-plan set via
  `generate_ag_closeout_audit_candidates.py` (98 cefi-tagged AG-primary docs total; 16 real covering docs; 19 "never
  cited in any covering doc" near-certain orphan candidates per the pre-filter's own design) UNIONED with 3 additional
  docs `check_ag_closeout_linkage.py` independently flagged as having zero real graph/mention path to the cefi closeout
  family despite being self-dispatched (a class the citation-based pre-filter alone would have silently passed as
  "covered") — 22 docs deep-audited this run via a Workflow (one agent per doc, all 16 active + 8 archived covering docs
  passed as context); the other 76 already-cited-somewhere docs were not individually re-read this run, consistent with
  the pre-filter's own "low marginal value" design rationale. Verdicts: 6 exclude_cross_cutting (5 genuinely multi-AG in
  scope — one of them, `ag_closeout_audit_rollout_2026_07_25.md`, is the skill's own canonical legitimate-multi-AG
  example; 1 dual-tagged `[prediction, cefi]` whose true owner is prediction per content + the doc's own prior
  na-eligibility-audit pass + cefi's own aggregated-sources digest explicitly deferring to "the prediction closeout"), 3
  covered_self_dispatched (own `assigned_vm: planning` is their dispatch vehicle — 1 flagged for a staleness watch: 7
  days untouched across 3 subsequent batches despite dense initial activity), 1 archivable-verdict-but-held (a same-day
  fresher whole-corpus ruling in `zero_checkbox_sweep_all_tranches_2026_07_31.md` explicitly said hold this doc as a
  live companion to its still-open parent rather than archive), 12 orphaned_never_touched (6 of which are genuinely
  operator-gated/design/research judgment calls with zero AO-eligible content, correctly uncovered by design; 6 carry
  real AO-eligible bounded work). Phase 3 conflict-checked every AO-eligible candidate against the full active+archived
  covering-doc set AND against every OTHER currently self-dispatched `parent_epic: cefi_master` doc (24 checked total,
  not just the batch/track family) — zero overlaps found anywhere. 6 todos cleared into 6 conflict-clear bounded items
  below (drawn from 5 of the 6 orphaned-with-work docs); one further candidate (Schema v10 backfill) is transitively
  gated on a still-open Stage-1 human-design prerequisite despite its own stated dependency (the v2 dedup `--apply`)
  being independently confirmed landed, so it moves to Deferred rather than being drafted ready-to-run. Two docs'
  AO-eligible-looking items are deliberately NOT drafted (crypto_alpha_research's 3 bug fixes, no_active_paper_run's
  DIAG item) because a prior audit pass already considered and explicitly declined extracting them for reasons unrelated
  to boundedness (coupling risk; low standalone value) and no new evidence has emerged to revisit that call.
status: draft
nature: process
asset_group: [cefi]
stage: [data]
repos:
  [
    unified-trading-pm,
    strategy-service,
    market-tick-data-service,
    unified-api-contracts,
    deployment-service,
    instruments-service,
  ]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-6, satellite-docs, iterative-drain]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/active/cefi_satellite_ao_dispatch_batch5_2026_08_02.md,
    /plans/active/cefi_satellite_ao_dispatch_batch5_2026_08_02_finalize.md,
    /plans/active/cefi_satellite_ao_dispatch_batch4_2026_07_31.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-02"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.64
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-08-02 (scheduled autonomous dispatch, agent-orchestrator slot 8, tranche=cefi) —
  Phase 0 used `scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py --tranche cefi` (98 total members, 19
  never-cited) UNIONED with a `scripts/plan-hygiene/check_ag_closeout_linkage.py` cross-check (+3 self-dispatched docs
  with zero real graph/mention linkage), Phase 1 ran a `Workflow` (17 parallel agents over the union set minus 5
  deterministic multi-AG excludes classified directly), Phase 3 conflict-checked every AO-eligible candidate against the
  full covering-doc set and against all 24 currently self-dispatched `parent_epic: cefi_master` docs before drafting,
  and verified the Schema v10 item's transitive Stage-1 gate directly against
  `issues/fail_hard_canonical_enforcement_design_2026_07_20.md`'s own staged-rollout table rather than trusting the
  Phase-1 agent's summary alone.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch5_2026_08_02.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
---

# CeFi satellite AO batch 6 — iterative-drain extraction

> **Status: draft — NOT dispatched.** Per CLAUDE.md's plan-destination HARD RULE and the ag-closeout-audit skill's
> autonomous-mode guidance, a skill-drafted AO batch is never auto-flipped to `active`. This run was a scheduled
> autonomous dispatch (no operator present), so the flip is explicitly reserved for operator review. Flip this
> frontmatter's `status` to `active` only after that review.

> **Cross-todo file-collision check: PASS.** The 6 todos touch, respectively: (1) `strategy-service`'s
> `scripts/run_2yr_config_grid_backtest.py` (extend `SUPPORTED_ARCHETYPES` + per-archetype dimension tables); (2) a
> read-only `gcloud storage` census script (new, one-off, no source file edited) against DERIBIT GCS objects; (3)
> `market-tick-data-service`'s manifest-write and read-path call sites for id-form classification (a DIFFERENT set of
> call sites than todo 6's new test file — no overlap); (4) `deployment-service`/Cloud Run job investigation, with a
> conditional image rebuild only if the investigation finds a job still-relevant (does not touch
> market-tick-data-service source); (5) a NEW `market-tick-data-service/tests/unit/` parity-test file; (6) a read-only
> OKX public-API research pull, no source file edited. Todos 3 and 5 both touch market-tick-data-service but a different
> file class (existing source vs. new test file) — no collision. Safe to dispatch concurrently; `sequential: false`.

> **Conflict-check scope note.** Every candidate below was checked against: (a) all 16 active covering docs (the
> consolidated closeout, batches 3/4/5 + finalizes, tracks 2/7 + finalizes, native-ao-extract + finalize,
> deribit-binance-futures-bundle-verification + finalize, the 4surface-migration-execution-log) and 8 archived covering
> docs (batch1/batch2 + finalizes, migration-cutover-and-track8 + finalize, misc-audits-and-hygiene + finalize); (b)
> every OTHER currently `assigned_vm: planning`, `parent_epic: cefi_master` doc in the corpus (24 total, including
> stand-alone self-dispatched issues like `cefi_content_migration_fleet_half_incomplete_2026_07_26.md`,
> `cefi_high_attempted_failed_batch_cluster_2026_07_23.md`, `deribit_combo_perpetual_partition_move_2026_07_21.md`,
> etc.) — not just the named batch/track family, per the shared conflict-check protocol's surface (a). Zero overlaps
> found on either surface for any of the 6 todos below.

## Todos

- [ ] [BACKEND] P2. **Extend `run_2yr_config_grid_backtest.py` with an `ML_DIRECTIONAL_CONTINUOUS` archetype entry.** In
      `strategy-service/scripts/run_2yr_config_grid_backtest.py`, the script currently only supports
      `StrategyArchetype.CARRY_STAKED_BASIS` and `StrategyArchetype.ARBITRAGE_PRICE_DISPERSION` (both DeFi archetypes)
      in `SUPPORTED_ARCHETYPES` (line 136) and every per-archetype dispatch point (dimension tables ~line 227/234,
      branch logic ~line 356/362/526/537/602/606). Mirror the existing pattern to add `ML_DIRECTIONAL_CONTINUOUS` with
      grid dimensions `position_size_pct` / `confidence_threshold` / `stop_loss_bps` / `take_profit_bps` /
      `model_family`. This is a pure code task — no live-capital or wallet-credential dependency, and is deliberately
      separable from the actual 2-year VM-run + GCS-output-inspection half of the same source-doc gate, which 3
      independent audit passes have consistently classified operator-scheduled (not drafted here). Source:
      `cefi_ml_directional_continuous_live_2026_06_20.md` (the `[VERIFY] P0` todo's first sub-requirement only). **Done
      when**: `ML_DIRECTIONAL_CONTINUOUS` is added to `SUPPORTED_ARCHETYPES` with a working dimension table and branch
      coverage at every existing per-archetype dispatch point, QG is green, and a unit test proves the new archetype is
      accepted by the script's own validation (mirroring an existing `CARRY_STAKED_BASIS`/ `ARBITRAGE_PRICE_DISPERSION`
      test). Do NOT flip the source doc's `[VERIFY] P0` checkbox — that requires the still-operator-gated VM run + GCS
      inspection to actually complete.

- [ ] [DATA] P2. **Corpus-wide GCS census of DERIBIT dated-option-shaped trades objects misclassified as
      `instrument_type=perpetual`.** Read-only enumeration of
      `gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=*/pipeline_mode=batch_tardis/asset_group=cefi/venue=DERIBIT/instrument_type=perpetual/data_type=trades/**`
      matching the dated-option wire-symbol shape (`<BASE>_<QUOTE>-<EXPIRY>-<STRIKE>-<C|P>.parquet`) across 2019-present
      (the source doc's own evidence is only 5 sampled days) to determine total affected days and total byte volume.
      Strictly a measurement task — no writes, no deletes, no root-cause fix (that sub-item stays open in the source doc
      as genuine judgment/design work). Source:
      `issues/deribit_dated_option_trades_perpetual_misclassification_2026_07_27.md` ("What's NOT done" item 2 only).
      **Done when**: the census completes, total affected-day count + byte volume are recorded with the exact `gcloud`
      commands used as evidence, and the source doc's item 2 is checked off citing this run (items 1/3/4 stay open —
      root-cause, backfill, and re-canonicalization are design/dependent work, not batched here).

- [ ] [DATA] P2. **Fail-hard Stage 0 — classify-and-log at cefi manifest-write and read-path call sites.** In
      `market-tick-data-service`, the write-side observe-log already shipped (`enforce_structural_and_observe_id_form()`
      wired into `partitioned_writer.py`/`websocket_runner.py`/ `book_microstructure_handler.py` via
      `market-tick-data-service@e49e1395`) — this todo covers the two remaining halves only: add the SAME id-form
      classification (count + log only, **zero behaviour change**, per the source doc's own Stage-0 definition) at (a)
      the manifest-recording call sites and (b) the read-path call sites for cefi instrument ids. Do NOT touch Stage 1
      (write-enforce/raise) or Stage 2 (schema v10 + backfill) — both stay open, see Deferred below. Source:
      `issues/fail_hard_canonical_enforcement_design_2026_07_20.md` (the `[DATA] P2` Stage 0 todo only). **Done when**:
      manifest- and read-site classify-and-log land with zero behaviour change (a regression test proves no existing
      write/read path changes outcome), QG is green, and the source doc's Stage-0 todo is checked off citing the
      shipping commit.

- [ ] [OPS] P2. **Determine dead-vs-alive for the 7 stale-image cefi Cloud Run jobs, then act on the finding.**
      Investigate whether `market-tick-cefi-binance-futures`/`-okx`/`-daily-download`/`-binance-spot`/`-bybit`/
      `-coinbase`/`-upbit` (all currently pinned to the same 5.5-month-stale `market-data-tick-handler:latest` image)
      are still-relevant or dead/superseded by the VM-based Tardis launcher path, using the SAME evidentiary method
      already proven on the sibling job `market-tick-cefi-daily-download` in the archived
      `cefi_satellite_ao_dispatch_batch1_2026_07_25.md` (line 388-392: 3 independent threads — the job's own invocation/
      audit history, an outage doc's independent re-confirmation, a launcher script's header documenting the
      replacement) — a bounded, worker-executable template, not a fresh unstructured judgment call. **Note for the
      reviewer**: this doc's own 2026-07-31 na-eligibility-audit pass classified this determination as "not
      worker-determinable," but that pass did not have the batch1 precedent in view; this todo applies the
      dispatch-scope eligibility test fresh against that precedent. If the reviewer disagrees, park this item instead of
      dispatching it. Per-job verdict, then: if confirmed dead/superseded, delete the Cloud Run job(s) (removes the
      landmine outright); if any job is confirmed still-relevant, rebuild + push a fresh `market-data-tick-handler`
      image before it can next fire. Source: `issues/mtds_cefi_docker_image_stale_5mo_2026_07_30.md`. **Done when**: a
      per-job dead/alive verdict is recorded with cited evidence for all 7 jobs, the corresponding action (delete or
      rebuild) is taken, and the source doc's 2 todos are checked off citing this run.

- [ ] [SCRIPT] P2. **Add a live-vs-batch OKX-FUTURES `instrument_id` parity test.** In
      `market-tick-data-service/tests/unit/`, add a new test mirroring the existing BINANCE-FUTURES/KRAKEN-FUTURES
      live-vs-batch instrument_id parity coverage, scoped to OKX-FUTURES, so a future drift between the live WS
      connector's id-derivation and the batch/reference-data builder's convention can't silently regress again
      (precedent: this exact class of drift is what produced the source doc in the first place). Source:
      `issues/okx_futures_instid_marker_convention_mismatch_2026_07_30.md` (the `[SCRIPT] P2` parity-test todo only).
      **Done when**: the new test exists, passes against the currently-shipped convention
      (`market-tick-data-service@8a6bbc97`), and the source doc's `[SCRIPT] P2` checkbox is checked off citing the test
      file + a passing QG run.

- [ ] [RESEARCH] P2. **Live-verify whether AAPL-USD (and other equity-underlying) OKX-FUTURES dated-future universe
      entries are real, currently-listed OKX contracts.** Pull `/api/v5/public/instruments?instType=FUTURES` live (NOT
      ccxt's cached market list) and check whether `AAPL-USD@LIN-20310613`-shaped entries correspond to actual
      OKX-listed contracts or a synthetic/placeholder universe entry. This is the source doc's own Option-C
      data-integrity prerequisite, now flagged MORE urgent since the `[OPERATOR]`/`[SCRIPT]` P1 items already shipped
      Option A in production without it. Read-only research — no code change. Source:
      `issues/okx_futures_instid_marker_convention_mismatch_2026_07_30.md` (the `[RESEARCH] P2` todo only). **Done
      when**: the live API pull result is recorded in the source doc with the exact response evidence, and its
      `[RESEARCH] P2` checkbox is checked off citing this run.

## What was NOT drafted and why

- **`crypto_alpha_research_2026_07_24.md`'s 3 nominally-bounded bug fixes** (a `_mom_tb.py` daily-PnL save-gating bug,
  an audit-script $1M-vs-$250k order-book-column bug, a combined-book vol-normalization bug). All 3 are judgment-free
  code fixes in isolation, but the archived `cefi_satellite_ao_dispatch_batch2_2026_07_26.md` already explicitly
  considered extracting the first two and declined, citing tight coupling to this doc's still-outstanding,
  twice-reaffirmed `BLOCKED-OPERATOR-DECISION` trading-judgment track (16 items, most-recently reconfirmed 2026-07-28 as
  a PERMANENT hard-stop). No new evidence has emerged since to revisit that call — not re-litigated here. The intended
  re-check mechanism for this doc lapsed when its owning finalize plan archived (2026-07-26) with no successor picking
  up the loop; flagging this process gap for the operator rather than guessing.
- **`no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31.md`'s `[DIAG] P2` item** (check strategy-service's
  active instrument-universe config for an existing BINANCE-FUTURES/ASTER/OKX-FUTURES paper run). Technically bounded,
  but the doc's own 2026-08-01 na-eligibility-audit pass already considered splitting it off and explicitly declined,
  reasoning its answer "only serves the gated DECISION" and has no standalone value. Respecting that considered call.

## Deferred — transitively operator-gated (own dependency cleared, upstream stage did not)

- **`issues/fail_hard_canonical_enforcement_design_2026_07_20.md`'s `[DATA] P3` Schema v10 `instrument_id_form` +
  backfill (Stage 2).** The todo's own stated dependency ("after the v2 dedup `--apply`") IS cleared — Script 3
  (manifest dedup v2) finished with every shard `EXIT_STATUS=0` per `cefi_consolidated_closeout_2026_07_18.md`'s Track 1
  record (DONE 2026-07-27). However, the source doc's own §2 staged-rollout table states Stage 2 also depends on **Stage
  1 (write-enforce)**, which has NOT shipped — Stage 1 is itself blocked on the still-open `[DESIGN] P1` §5-gaps item (a
  human design-session task, not drafted in any batch to date). Drafting the Stage-2 schema/backfill work now would run
  ahead of a stage the source doc's own dependency table says must land first. Re-check this once `[DESIGN] P1` closes
  and Stage 1 ships — at that point this becomes a normal batch7 candidate with no remaining gate.

## Deferred — BLOCKED-OPERATOR-DECISION (carried from batch4, still unresolved)

- **`issues/estate_orphan_assessment_2026_07_21.md` todo 6 — contested boundedness across three tranches.** Re-checked
  this run: still no operator ruling as of 2026-08-02 (2-1 KEEP-NA majority — cefi + sports KEEP-NA, defi RECLASSIFY —
  per batch4's own record). Not drafted here for the same reason batch4 declined it: a genuine cross-tranche
  disagreement this run cannot resolve by evidence alone.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox in its named source doc, citing this plan's commit as evidence.
This plan's own reconciliation-then-archive step is machine-gated via the companion
`cefi_satellite_ao_dispatch_batch6_2026_08_02_finalize.md` (`depends_on` + `gate_on_depends: true`), mirroring the
batch1 through batch5 finalize pattern.

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual this batch's
  finalize plan executes.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — the
  bounded-vs-judgment-call test applied to every Phase-1/Phase-3 verdict above.
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the shared conflict-check protocol
  this batch's Phase 3 ran before drafting (§3), including the surface-(a) cefi_master-wide sweep beyond just the
  batch/track family.
