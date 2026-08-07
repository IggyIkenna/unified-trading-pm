---
doc_type: plan
title: CeFi satellite AO batch 8 — iterative-drain extraction over the batch7 residual
summary: >-
  Eighth AO-dispatch batch for cefi, produced by the `/ag-closeout-audit` skill run 2026-08-06 (scheduled autonomous
  dispatch, tranche=cefi, slot 3, dispatch agt-02411c). Phase 0 re-derived the covering-plan set via
  `generate_ag_closeout_audit_candidates.py` (93 cefi-tagged AG-primary members, 14 real active covering docs — batch4,
  batch6 and batch7 all still count as covering despite sitting `status: draft`, per the skill's widened Phase 0.2 rule
  — none of the three has been operator-reviewed/activated since batch7 was drafted 2026-08-03; 12 "never cited"
  candidates via the citation heuristic) UNIONED with 7 additional docs `check_ag_closeout_linkage.py` (a stricter
  graph/mention check) independently flagged as cefi-tagged orphans — only 1 of those 7 overlapped with the citation
  heuristic's 12, confirming the two checks catch materially different things. 19 docs deep-audited this run via two
  parallel `Workflow` dispatches (one agent per doc, all 14 active covering docs + the relevant archived batch/finalize
  history passed as context per agent). Verdicts: 5 exclude_cross_cutting (genuinely multi-AG or wrong-tranche in scope
  — flagged below for whichever tranche owns them, not drafted here), 3 archivable_now (all fully resolved, zero
  remaining engineering work — pure archival-hygiene, not batch content), 1 self_dispatched_covered (already
  `assigned_vm: planning`, correctly being worked directly — only needs a linkage/`related:` mention, not a new
  dispatch), 5 orphaned_partial_coverage and 5 orphaned_never_touched (10 total genuine orphans, of which 7 are
  correctly non-AO-eligible per 2-3 independent prior audit passes each — design/operator/credential-gated, unchanged —
  and 3 carry real, independently-verified AO-eligible bounded work). Phase 3 conflict-checked all 3 AO-eligible
  candidates against the full 26-doc active+archived covering set (zero overlap, confirmed per-doc by each Phase-1
  agent) AND a corpus-wide grep for each candidate's target files/topics (one adjacent-but-distinct prior finding noted
  in todo 2's own text to prevent future confusion, not a real conflict). 3 todos below, zero genuine conflicts found,
  zero items parked BLOCKED-OPERATOR-DECISION this run (all operator-gated residuals were already correctly parked by
  prior audit rounds and are re-confirmed, not re-parked, in the tranche's parked-findings doc).
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm, market-data-processing-service, market-tick-data-service, instruments-service]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-8, satellite-docs, iterative-drain]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/active/cefi_satellite_ao_dispatch_batch7_2026_08_03.md,
    /plans/active/cefi_satellite_ao_dispatch_batch7_2026_08_03_finalize.md,
    /plans/active/instruments_cefi_g1_g5_gate_execution_2026_07_24.md,
    /plans/archive/issues/mdps_derivative_ticker_single_instrument_high_rss_2026_08_03.md,
    /plans/active/issues/okx_futures_instid_marker_convention_mismatch_2026_07_30.md,
    /plans/archive/2026_08/ag_closeout_audit_cefi_parked_2026_08_06.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-06"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-08-06 (scheduled autonomous dispatch, agent-orchestrator slot 3, dispatch
  agt-02411c, tranche=cefi) — Phase 0 used `scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py --tranche
  cefi` (93 total members, 12 never-cited) UNIONED with a `scripts/plan-hygiene/check_ag_closeout_linkage.py`
  cross-check (+7 independently-flagged cefi-tagged orphans, only 1 overlapping the citation-heuristic's 12), Phase 1
  ran two `Workflow` dispatches (12 + 7 parallel agents over the two candidate sets), Phase 3 conflict-checked every
  AO-eligible candidate against the full covering-doc set and a corpus-wide grep for each candidate's target files
  before drafting.
context_scope:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch7_2026_08_03.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/active/cefi_satellite_ao_dispatch_batch8_2026_08_06_finalize.md,
    /plans/active/instruments_cefi_g1_g5_gate_execution_2026_07_24.md,
  ]
---

# CeFi satellite AO batch 8 — iterative-drain extraction

> **Status: active — operator-approved 2026-08-06, dispatching.** Todo 3 was found already done-elsewhere before
> dispatch (docstring already correct — see its checkbox); todo 1's SHA citation was corrected for the 2026-08-05
> instruments-service history rewrite. batch4/6/7 were reviewed in the same pass and are now also `status: active`.

> **Cross-todo file-collision check: PASS.** The 3 todos touch, respectively: (1)
> `plans/active/instruments_cefi_g1_g5_gate_execution_2026_07_24.md` — a self-file checkbox/banner edit only, no code;
> (2) `market-data-processing-service/market_data_processing_service/app/core/live_workers.py` — a code fix to
> `_read_tick_data`; (3) `market-tick-data-service/market_tick_data_service/live/connectors/okx_futures_ws.py` — a
> docstring-only edit. No file is touched by more than one todo. Safe to dispatch concurrently; `sequential: false`.

> **Every claim below was re-verified against live corpus/code state on 2026-08-06**, not carried over from the source
> docs' own prose without a fresh check (each Phase-1 agent independently confirmed cited commits exist via `git show` /
> `git cat-file` before this batch drafted a todo against them).

## Todos

- [ ] [DOCS] P2. **Re-verify and flip 3 stale-open markers in `instruments_cefi_g1_g5_gate_execution_2026_07_24.md` —
      all 3 already independently confirmed true against live corpus/code state, just never flipped.** (1) G1.2's "wire
      thin-day→attempted_failed at capture time" sub-item is marked `[~]` partial but its shipped half is confirmed on
      current LDR HEAD (`instruments-service@5ebd7f6c`, "G1.2 thin-day partial-capture routing —
      `_detect_thin_day_venues` in `_finalize_completeness`"). **Verification note added 2026-08-06**: this exact SHA is
      NOT a `git merge-base --is-ancestor` hit against current LDR HEAD — instruments-service underwent a documented
      history rewrite around 2026-08-05 (see
      `plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`); the SHA
      survives only in `wip-preserve/*stale-pre-history-rewrite*` branches. **Verify by CONTENT instead**: confirm
      `_detect_thin_day_venues` is present and wired in `process_completeness.py` on current HEAD (it is, as of
      2026-08-06) — do not rely on literal commit-ancestry, which will produce a false negative post-rewrite. Then flip
      the checkbox citing the content-verification instead of the (now-unreachable) SHA — only if the doc's own second
      sub-item, the 06-26 re-capture, is also confirmed moot after 40+ days of subsequent production capture — check the
      manifest before flipping the top-level G1 item, not just G1.2). (2) GATE G4's banner reads "OPEN, pending D2" — D2
      (`cefi_layer1_denominator_gaps`, archived) is `status: resolved`, and both of its named residual threads
      (`instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md`, `tardis_concurrent_ip_lockout_2026_07_12.md`) are
      also `status: resolved` — re-verify all three resolutions directly, then flip the G4 banner to reflect the cleared
      gate. (3) The `MANIFEST_ALLOW_STALE_FALLBACK=true` revert todo — re-verify directly against the live
      `deployment-service` HEAD (`launch-cefi-instruments-backfill.sh` no longer hardcodes the flag;
      `setup-data-pipeline-vm.sh` reads it metadata-driven/opt-in only, confirmed at `deployment-service@7538587a`),
      then flip the checkbox. **Do NOT touch** the doc's other 2 open items (EXTENDED-STARKNET CF-11 honest-absence
      raise-vs-fallback decision, formal GATE G1 sign-off) — both are genuine operator/design gates, independently
      reaffirmed KEEP-NA by na-eligibility-audit runs on 2026-07-30 and 2026-08-04; leave them open. Source:
      `instruments_cefi_g1_g5_gate_execution_2026_07_24.md` (G1.2, GATE G4, MANIFEST_ALLOW_STALE_FALLBACK items only).
      **Done when**: each of the 3 claims is re-confirmed with a cited commit/verification command, the corresponding
      checkbox/banner is flipped `[x]`/updated with that evidence, and the doc's other 2 open items remain untouched.
      Repo: unified-trading-pm (doc-only edit).

- [x] ✅ [BACKEND] P1. **Fix the confirmed HYPERLIQUID `derivative_ticker` OOM defect — predicate-pushed parquet read in
      `_read_tick_data`.** market-data-processing-service@4f2b99e — `_read_tick_data` now accepts
      `filter_data_type`/`filter_related_types`; uses `pl.scan_parquet + filter + collect` for predicate-pushed reads,
      loading only derivative_ticker row groups (skipping book_snapshot_5/trades entirely). QG green, 2346 tests passed.
      `market-data-processing-service/market_data_processing_service/app/core/live_workers.py`'s `_read_tick_data`
      (~line 489) calls `pl.read_parquet(io.BytesIO(raw_bytes), low_memory=True)` to load HYPERLIQUID's raw
      multi-`data_type` `ticks.parquet` blob IN FULL (book_snapshot_5 + trades + derivative_ticker for a whole
      underlying/quote/margin), then filters to the target `data_type` only AFTER full materialization (~line 295) —
      `book_snapshot_5` (L5 book at 10/sec) dominates and drives RSS to 18.5GB+ even for a single `derivative_ticker`
      instrument on one day (reproduced on a quiet host 2026-08-05: RSS climbed 1,121MiB→18,492MiB in ~33s, then
      OOM-killed — see source doc's Progress Log for the full repro). Replace the full-materialize-then-filter read with
      a predicate-pushed / row-group-filtered read scoped to the target `data_type` column — Polars
      `scan_parquet(...).filter(pl.col("data_type")==data_type)` is the simplest viable option (native predicate
      pushdown, no new dependency); a pyarrow `ParquetFile.read_row_groups()` filtered by row-group stats is the named
      alternative if Polars' pushdown doesn't apply cleanly to this blob shape. **Scope note — this is NOT the same
      question `data_pipeline_check_mdps_features_2026_07_20.md`'s todo 12 already assessed and declined**
      ("faster-libs/Rust where it pays... Python service-kernel work (`_read_tick_data`'s full-blob-to-RAM read...) is
      backend_engineer-craft scope... Already assessed... as LOW priority (polars core groupby is already fast; Rust
      would shave only ~6% of wall-clock) — no infra action follows"): that assessment was about a ~6% wall-clock
      speedup from a Rust rewrite (declined, not worth it); THIS todo is about eliminating a confirmed 18.5GB OOM-crash
      via a Polars-native predicate-pushdown read (a correctness/reliability fix, no language change, no
      infra-vs-backend_engineer boundary question) — different problem, different fix, not a duplicate or a reversal of
      that prior verdict. Source: `mdps_derivative_ticker_single_instrument_high_rss_2026_08_03.md` (the "Implement the
      fix" prose item — never promoted to its own checkbox in the source doc; this todo IS that promotion). **Done
      when**: `_read_tick_data` no longer materializes the full raw blob before filtering; re-run the doc's own repro
      command
      (`market-data-processing-service process --operation process --mode batch --start-date 2026-07-19     --end-date 2026-07-19 --force`
      scoped to `HYPERLIQUID:PERPETUAL:ADA-USD@LIN`) on a quiet host and confirm RSS no longer balloons into
      double-digit GB; confirm output parquet content is unchanged against the doc's known-good baseline (1440-row 1m
      parquet, 24 non-null `mark_price_mean`/`funding_rate_mean` observations); source doc's checkbox/prose is updated
      citing this commit. Repo: market-data-processing-service.

- [x] ✅ [SCRIPT] P2. **DONE-ELSEWHERE 2026-08-06 (governance-sweep activation-readiness check) — docstring was already
      correct.** Live-checked `okx_futures_ws.py`'s current module docstring: it already describes the shipped
      `@LIN`/`@INV` marker convention in full ("This module previously claimed the opposite... that was ONLY ever true
      of the narrow 2026-07-09 ruling..."), landed as part of `market-tick-data-service@8a6bbc97` itself (the same
      commit this todo cites as the code fix) and re-confirmed present in the LDR→main squash-promote `b5a1aa73`
      (2026-07-31). The todo's premise ("still claims no marker") was already false when this batch was drafted
      2026-08-06 — the source doc's own `[SCRIPT] P1` item inherited a stale claim without checking current file
      content. No action needed; flip the source doc's sub-item (a) citing `8a6bbc97` if not already reflected there.
      Original text preserved below for record. **Reconcile `okx_futures_ws.py`'s stale "no marker" docstring against
      the already-shipped Option-A code.**
      `market-tick-data-service/market_tick_data_service/live/connectors/     okx_futures_ws.py`'s module docstring
      still claims OKX-FUTURES `instId` carries no settlement-currency marker, but Option A (the `@LIN`/`@INV` marker
      convention) already shipped to production (`market-tick-data-service@8a6bbc97`). Source:
      `okx_futures_instid_marker_convention_mismatch_2026_07_30.md`.

## Cross-tranche notes (informational — out of cefi scope, not drafted here)

- **`issues/features_service_clean_check_dangling_revert_of_hyperliquid_cefi_bucket_fix_2026_08_03.md`** —
  `asset_group: [defi]`, `parent_epic: defi_master`. Despite the "hyperliquid_cefi_bucket" in its title (thematically
  adjacent to this batch's own todo 2 and the active
  `hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md` migration), this doc's own scope is a
  `features-service`-side stash-drift incident, genuinely defi-primary. Its one remaining open item (`[OPERATOR] P2`,
  drop a specific ruled-abandoned `git stash` entry) is explicitly human-only per the workspace's destructive-command
  guardrail — not AO-eligible under any tranche. Flagging only for defi's own `/ag-closeout-audit` run to confirm
  coverage; not drafted here.
- **`mdps_features_deadcode_consolidation_2026_07_20.md`**,
  **`ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md`**,
  **`phantom_audit_estate_coverage_gap_2026_07_10.md`**, **`prediction_capture_incident_remediation_2026_07_06.md`** —
  all `exclude_cross_cutting` (genuinely multi-AG in scope, tagged with 3-5 asset groups each including cefi as one of
  several peers). Each carries some genuinely open work, none of it cefi-specific — see this tranche's parked-findings
  doc for the one-line-per-doc breakdown; not drafted here, for whichever tranche's own audit run owns the primary
  content (mostly prediction/infrastructure-flavored per each doc's actual text).

## Archival-hygiene housekeeping (informational — not AO-eligible batch content)

Three docs this run confirmed `archivable_now` with **zero** remaining engineering work — their only remaining action is
the standard 6-step archival ritual (frontmatter `status`/`resolved_by` flip + move to `plans/archive/issues/` +
referrer fix, all three have zero active-corpus referrers to fix). Not batch items; noted here for traceability only:

- `issues/cefi_bare_okx_venue_removal_2026_08_04.md` — both todos done, both cited commits
  (`unified-api-contracts@d67a226f`, `market-tick-data-service@f3467634`) independently re-verified genuine via
  `git show`.
- `issues/cross_instrument_delta_one_listing_recurring_hang_2026_08_03.md` — all 4 todos done, all 4 cited commits
  independently re-verified genuine.
- `issues/okx_futures_trades_zero_capture_and_polymarket_perp_funding_failed_2026_08_05.md` — both todos done, both
  underlying fixes verified present in the codebase. **One correction needed before archiving**: the POLYMARKET-PERP
  todo cites the wrong commit hash (`market-tick-data-service@b2497b73`, an unrelated commit) — the real fix is
  `@b29285ae`; fix the citation as part of the archival ritual, not a separate todo.

## Self-dispatched, linkage-fix-only (informational — not AO-eligible batch content)

- `issues/multi_timeframe_phantom_captured_manifest_rows_on_universal_write_failure_2026_08_03.md` —
  `assigned_vm: planning`, `status: open`: self-dispatched, correctly covering itself (the orchestrator backlog picks it
  up directly). All engineering work is done and shipped (`features-service@7eca96ac`, `@31bef7c3`, `@b0be030b`); the
  sole remaining item is `[OPERATOR] P2` (a genuine compute-cost-tradeoff design decision spanning cefi and other
  asset_groups sharing delta-one's default feature-group set) — not AO-eligible under any tranche. Needs only a
  `related:`/mention link added to the cefi closeout family for discoverability (a light hygiene fix, not a new dispatch
  todo) — not drafted here.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox in its named source doc, citing this plan's commit as evidence.
This plan's own reconciliation-then-archive step is machine-gated via the companion
`cefi_satellite_ao_dispatch_batch8_2026_08_06_finalize.md` (`depends_on` + `gate_on_depends: true`), mirroring the
batch1 through batch7 finalize pattern.

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual the
  archival-hygiene housekeeping section above still needs, separately from this batch.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — the
  bounded-vs-judgment-call test applied to every Phase-1/Phase-3 verdict above.
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the shared conflict-check protocol
  this batch's Phase 3 ran before drafting.

## Progress Log

- **context-scout 2026-08-07**: populated context_scope (5 entries) — the companion
  `cefi_satellite_ao_dispatch_batch8_2026_08_06_finalize.md` gate, the prior batch7 link, the 2 core codex SSOTs, and
  `instruments_cefi_g1_g5_gate_execution_2026_07_24.md` — the actual target doc for the sole remaining open todo (todo
  1, a doc-only checkbox/banner re-verify-and-flip against that exact file). Todos 2-3 are DONE.
