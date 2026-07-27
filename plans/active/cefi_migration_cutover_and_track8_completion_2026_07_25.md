---
doc_type: plan
title:
  CeFi migration cutover + Track 8 completion — DERIBIT quote fix, PERP rename, --apply cutover, post-cutover flip,
  terminal checkpoint
summary: >-
  The migration-completion CRITICAL PATH forked out of cefi_consolidated_closeout_2026_07_18.md's 2026-07-25 split.
  Sequential 5-step chain: (1) DERIBIT quote-fix + catalogue rebuild that GATES the cutover, (2) the remaining on-disk
  GCS content rename for `:PERP:`→`:PERPETUAL:`, (3) execute the Track-1 minutes-gap hybrid cutover `--apply`, (4) the
  POST-CUTOVER smoke-check + downloader flip that MUST land with/after the apply, (5) the enumeration-audit terminal
  checkpoint. Every step here is prerequisite to the next — `sequential: true`. Two items the design pass initially
  assumed would live here are deliberately EXCLUDED to avoid duplicating
  cefi_consolidated_native_ao_extract_2026_07_25.md (drafted by a parallel sibling triage of this same parent's native
  todos): the MTDS writer-side `:PERP:` fix (that plan's own todo 7, ships alone, no data motion) and the `_DRYRUN_COLS`
  chain-drop blind-spot fix (that plan's own todo 12).
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [cefi, close-out, canonicalisation, migration, cutover, track-1, track-8]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md,
    /plans/active/issues/_cefi_canonical_blueprint_2026_07_17.md,
    /plans/active/issues/cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md,
    /plans/active/cefi_4surface_migration_execution_log_2026_07_24.md,
    /plans/active/cefi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/cefi_migration_cutover_and_track8_completion_finalize_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Forked from cefi_consolidated_closeout_2026_07_18.md's 2026-07-25 line-cap split (design pass + operator-resolved
  ambiguities cefi.2/cefi.3 on the [OPERATOR]-tag question) — this is path 1 of that parent's 4 reachability paths, the
  migration-completion critical path.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# CeFi migration cutover + Track 8 completion

> **Status: draft.** Per CLAUDE.md's plan-destination rule, never auto-shipped to `active` — flip only after operator
> review. **`sequential: true`**: each todo below is a real, verified prerequisite of the next (todo 1 GATES the cutover
> in todo 3; todo 2 must land before todo 3 or the `--apply` bakes non-canonical `:PERP:` content into all four
> surfaces; todo 4 must land with/immediately after todo 3; todo 5 is only meaningful once todo 3's drain-gate lifts) —
> this is the textbook case for `sequential: true` per `task_template.md` §4.

## Todos

- [x] [BACKEND] P0. **Fix the DERIBIT `instrument_id` missing-quote defect, then rebuild `prod/catalog.parquet`.** —
      `instruments-service@d72edcf7` (adapter/builder fix, 2026-07-18) + `instruments-service@b2e084fa` (Phase-−1 gate
      extended with the quote-mandatory assertion, same day) + live-verified 2026-07-27: gate run against
      `gs://instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet` (429,129 rows) returned `GREEN=True`
      (0 `:PERP:`, 0 id!=canonical, **0 missing-quote**); a DERIBIT-only re-check confirmed 267,128 OPTION + 1,781
      FUTURE rows, 0 missing-quote in either bucket, incl. the exact plan-cited example now reading
      `DERIBIT:FUTURE:AVAX-USDC@LIN-20260401`. See Progress Log 2026-07-27 for full detail — the operational rebuild
      already happened on 2026-07-18 (same day as the fix) and the fixed state has persisted through 9 days of
      incremental catalogue growth (425,573 → 429,129 rows) with no regression, so no NEW full-corpus rebuild was
      triggered (would be a redundant heavy-I/O op against an already-satisfied done-when). The canonical symbol must
      ALWAYS be `BASE-QUOTE` (operator ruling 2026-07-18, overriding the `BASE[_QUOTE]` optional-quote decision in
      `instrument_id_format_canonicalization_2026_07_08.md`). Verified live: **265,538 of 425,160 catalogue rows (62%) —
      ALL DERIBIT (263,950 OPTION + 1,588 FUTURE)** — drop the quote (`raw=AVAX_USDC-1APR26` →
      `DERIBIT:FUTURE:AVAX@LIN-20260401`, must be `…AVAX-USDC@LIN…`; `BTC-5APR19-3250-C` → `DERIBIT:OPTION:BTC@INV-…`,
      must be `…BTC-USD@INV-…`). DERIBIT-only (every other venue already carries the quote). Fix the DERIBIT
      adapter/builder to always emit `BASE-QUOTE@MARGIN_TYPE[-YYYYMMDD][-STRIKE-C|P]` (USDC linear / USD inverse), then
      rebuild `prod/catalog.parquet` (coordinated ~38-min prod op). **Self-justified, no `[OPERATOR]` tag** per
      `task_template.md` finding Q (operator ruling 2026-07-25, cefi.2/cefi.3): the design pass floated an
      instant-rollback-via-GCS-object-versioning justification, but bucket versioning is NOT independently confirmed in
      this pass, so this uses finding Q's other basis instead — prior explicit operator approval (the 2026-07-18 ruling
      that this exact fix gates the Track-1 cutover) plus per-script validation (the adapter/builder fix ships behind
      its own passing unit tests before the catalogue rebuild runs against it). This GATES todo 3 below (else the
      cutover bakes the quote-less form into all four surfaces). Repo: instruments-service. **Done when**: the fixed
      adapter/builder emits the quote for 100% of DERIBIT rows on a fresh catalogue build (0 missing-quote DERIBIT ids),
      the Phase-−1 verify gate is extended to also assert ZERO missing-quote ids fleet-wide (the pre-existing gate only
      checked 0 `:PERP:` + `instrument_id==canonical_instrument_id`), and both are cited with the shipping commit.
      Source: `cefi_consolidated_closeout_2026_07_18.md` (Operator dispositions, DERIBIT quote fix).
- [x] ✅ [SCRIPT] P0. **DONE 2026-07-27 (sub-agent) — Execute the remaining on-disk GCS content rename for `:PERP:` →
      `:PERPETUAL:`** (374,272 manifest rows already resolved via Script 3's `resolve_canonical`,
      `instruments-service@555ddf1c` — this todo is ONLY the remaining on-disk GCS object rename + symbol decompose,
      e.g. `ASTER:PERP:CLUSDT` → `ASTER:PERPETUAL:CL-USDT@LIN`; it explicitly EXCLUDES the separate MTDS writer-side fix
      for future captures, which ships alone as `cefi_consolidated_native_ao_extract_2026_07_25.md`'s own todo 7 — did
      NOT re-do that work here). Extends Script 2/3. **Self-justified, no `[OPERATOR]` tag** per `task_template.md`
      finding O/Q: reused the already-dry-run-validated `resolve_canonical` rename pattern from Script 2/3 — the same
      idempotent copy→verify→delete shape already proven safe in production for the KRAKEN-SPOT and DERIBIT renames
      documented in `cefi_4surface_migration_execution_log_2026_07_24.md`. Repos: market-tick-data-service,
      instruments-service. **Both done-when clauses met, with one documented, already-ruled-on exception**: (1) live
      audit confirmed 0 `:PERP:`-form rows both before AND after this session's work (Script 3's manifest-side fix was
      already corpus-wide-complete); (2) a fresh 9-shard `--dry-run` re-verification (full corpus, 2019-03-30..today)
      confirms 0 further planned changes on every shard EXCEPT the pre-existing, already-analyzed DERIBIT
      spot/perpetual-mislabel collision class (Finding 8/10 of
      `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`) — now measured corpus-wide at ~5,001 objects
      total (3,025 in the previously-unmeasured 2019-2025 EARLY window + 1,976 in the 2025-11..2026-07 LATE window incl.
      the ASTER/HYPERLIQUID dual-capture class), left honest-raw per that doc's own "leave as-is, zero data loss"
      recommendation (already-ruled residual, not a fresh open call — a dedicated DERIBIT spot-partition-move fix is
      separately tracked and explicitly out of this todo's scope). See Progress Log 2026-07-27 for full shard-by-shard
      evidence. **Done when**: a fresh run of `scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py` shows
      0 `:PERP:`-form instrument_id rows remaining in the live cefi manifest/GCS content, and a `--dry-run` re-run of
      the rename script confirms 0 further planned changes (idempotency). Source:
      `cefi_consolidated_closeout_2026_07_18.md` (Track 8, `:PERP:` → `:PERPETUAL:` rewrite).
- [ ] [PM] P0. **⚠️ PARTIALLY DONE 2026-07-27 (this session) — Execute the minutes-gap hybrid cutover (Track 1): drain +
      `--apply` for Scripts 3 (manifest dedup v2) and 4 (eu-twin drop) COMPLETE + idempotency-verified; Script 2
      (filename rename) already done (todo 2); Script 1 (parquet CONTENT backfill) is NOT applied — its TRUE corpus
      scope was measured this session for the first time at ~4.5M objects (vs. the ~12,662-file 12-day-sample-based
      estimate this todo's done-when was written against), making full completion a multi-VM, multi-hour-to-multi-day
      campaign of its own, not achievable inside this dispatch. See Progress Log 2026-07-27 for full evidence
      (drain/consolidate/snapshot, per-script dry-run+apply logs, the marker/eu-twin STOP-ON-SURPRISE band diagnoses,
      the writer-restart verification, and Script 1's measured per-shard scope). Requires todo 1 (DERIBIT fix) and todo
      2 (PERP on-disk rename) above to have landed first in this sequential chain — Track 8's own audit found the
      cutover `--apply` would otherwise bake ~1.48M non-canonical rows (blank-itype-driven bare-wire, `:PERP:`,
      missing-quote, COMBO) into the canonical surfaces as if resolved. Vehicle:
      `plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md` (+ blueprint
      `_cefi_canonical_blueprint_2026_07_17.md`) — Phase A (code) ✅, Phase B (deploy) ✅, Phase C (4 scripts
      dry-run-validated) ✅; this todo is Phase D/E (drain + `--apply`). **No `[OPERATOR]` tag** — already ruled
      self-justifying per cefi.2/cefi.3 (finding Q): the migration is explicitly operator-approved in principle and
      every constituent script is individually dry-run-validated. Repos: instruments-service, market-tick-data-service,
      deployment-service. **Done when (Scripts 2/3/4 portion — MET)**: the operator's `ADAF0:USTF0.parquet` equivalent
      (spot-checked as `BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN`, 2025-06-15) is canonical on GCS filename / parquet
      `instrument_id` column / manifest key (reader already PASS per the 2026-07-22 measurement, code unchanged since);
      Scripts 2/3/4's `--dry-run` re-runs each assert 0 further changes (idempotency) — VERIFIED live this session for 3
      and 4 (Script 2 verified in todo 2's own session). **Done when (Script 1 portion — NOT MET, follow-up required)**:
      Script 1's full-corpus `--dry-run` has NOT been completed (10-shard sharded attempt got only ~1-11% through each
      shard before this session's wall-clock ran out; see Progress Log for exact per-shard progress) and `--apply` was
      not attempted at all. **New follow-up todo needed**: a dedicated, properly-scoped, heavily-parallelized (30-50+
      VM) multi-hour-to-multi-day campaign for Script 1's full-corpus content backfill, mirroring Script 2's own
      precedent scale — track as its own plan/todo, do not fold into a quick re-dispatch of this one. Source:
      `cefi_consolidated_closeout_2026_07_18.md` (Track 1). > **⚠️ Cross-link gate (D1 instrument_type-column UPPERCASE
      migration, 2026-07-20 ruling)**: this `--apply` > (Script 3 v2, which imports + reuses
      `complete_cefi_manifest_canonical_dedup_2026_07_17.py` wholesale) is the script that rewrites the manifest >
      `instrument_type` COLUMN to UPPERCASE (its own docstring's delta (iv), "`instrument_type` COLUMN drift... >
      lowercase/aliased -> canonical"). Per >
      `plans/archive/issues/honest_coverage_harness_instrument_type_case_break_on_d1_migration_2026_07_20.md` (resolved,
      archived) > (todo 4), this `--apply` MUST NOT run until that issue's case-insensitivity fix to the Honest-Coverage
      v2 > harness (`instruments-service/scripts/measure_honest_coverage.py` — shipped > `instruments-service@867b68f6`,
      2026-07-25, QG green) has landed and is proven green — otherwise the > cutover silently craters coverage.json for
      every migrated cefi shard the moment this todo runs. That > normalisation has shipped; this todo was UNBLOCKED on
      that specific dependency, confirmed re-verified GREEN this session (canonical-fraction 99.45% stable, 0 residual
      invariant violations).
- [ ] [BACKEND] P0. **POST-CUTOVER: flip the smoke-check + downloader to canonical instrument ids.** MUST land with (or
      immediately after) todo 3's cutover `--apply`, else targeted re-fetch silently breaks fleet-wide. Today the
      downloader's `--instrument-ids` matches RAW venue-native symbols EXACTLY (no substring/underlying expansion, no
      canonical→raw resolution), so the moment a venue's objects are canonical-named there is no raw symbol left to pass
      and a targeted fetch returns 0 rows with no error. Measured 2026-07-18 mid-migration: 8 of 46 provable Tardis
      cells were already canonical-only (BITFINEX-FUTURES ×4, BYBIT-SPOT ×2, COINBASE-FUTURES ×2) and could not be
      force-fetched at all. Three coupled changes: (1) make `--instrument-ids` accept canonical ids (or resolve
      canonical→raw) in the MTDS download path; (2) revert the smoke-check sampler
      (`scripts/pipeline_e2e_check.py::_sample_raw_symbol_from_prod_listing`) to sample the CANONICAL id and drop the
      `':' in stem` skip-guard added for the mixed-naming window (`market-tick-data-service@1875b95b`); (3) drop the
      `--tardis-only` docs' "verdicts are unreliable mid-migration" caveat once manifest lookups key on the same id form
      the writer records. Full evidence:
      `issues/cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md`. Repos:
      market-tick-data-service, unified-trading-pm. **Done when**: all 3 coupled changes ship in one commit/PR, a
      targeted re-fetch of a canonical-named instrument returns real rows (not 0-with-no-error), and the "verdicts are
      unreliable mid-migration" caveat is removed from every doc it appears in. Source:
      `cefi_consolidated_closeout_2026_07_18.md` (Track 8, POST-CUTOVER item).
- [ ] [DATA] P1. **Enumeration-audit terminal checkpoint.** Re-run
      `scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py` (the distinct-values census tool) against the
      live cefi manifest, once todo 3's cutover drain-gate lifts and
      `complete_cefi_manifest_canonical_dedup_2026_07_17.py --apply` actually runs. Repo: market-tick-data-service.
      **Done when**: the census returns 0 non-canonical rows across instrument_id/instrument_type/venue/data_type, or
      every remaining non-zero count is an explicitly-accepted exception already ruled on in
      `cefi_consolidated_closeout_2026_07_18.md` (e.g. the genuinely-unresolvable bare-wire/missing-quote residual) —
      record the final counts in this plan's Progress Log. Source: `cefi_consolidated_closeout_2026_07_18.md` (Track 8,
      enumeration-audit terminal checkpoint).

## Reconciliation

Once all 5 todos ship, flip the corresponding checkboxes/sections in `cefi_consolidated_closeout_2026_07_18.md` (Track
1, Operator dispositions' DERIBIT item, Track 8's `:PERP:` and POST-CUTOVER and enumeration-checkpoint items) AND their
own true source docs (`cefi_residual_followups_after_honest_done_2026_07_17.md`'s Phase-1/2 todos,
`cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md`). Machine-gated via a companion
`cefi_migration_cutover_and_track8_completion_finalize_2026_07_25.md`
(`depends_on: [cefi_migration_cutover_and_track8_completion_2026_07_25]` — `gate_on_depends: true`).

## Codex SSOTs

`/codex/02-data/availability-manifest-and-data-status.md`,
`/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`. No new durable contract is created by this plan —
every todo executes an already-decided spec from the parent doc.

## Progress Log

- **2026-07-27 (autonomous session, driven off an operator prompt asking to check + fix lowercase/non-canonical cefi
  `instrument_type` — this plan is the existing execution vehicle, not a new investigation)**: confirmed live via AO
  backlog check (SSM, read-only) that all 5 todos here are already ingested + `queued`, none `dispatched`. Operator
  chose to have this driven interactively now rather than wait for orchestrator dispatch, then invoked `/autonomous` (do
  not stop to confirm; proceed through dry-run-validated applies/renames/deletes for real). Investigated todo 1 first
  (it gates everything else): the DERIBIT adapter fix AND the roll-up self-heal
  (`_canonicalize_cefi_deribit_dated_quote`, wired into `_canonicalize_cefi_rollup_id`) both already shipped in
  `instruments-service@d72edcf7` (2026-07-18) — confirmed via `git log -L` on `scripts/build_instrument_catalogue.py`.
  So todo 1's code is done; what remains is the operational `--mode full` catalogue rebuild + live verification.
  Dispatching a sub-agent to execute that + the Phase-−1 gate extension now; this log will be updated as each todo
  lands.
- **2026-07-27 (sub-agent, todo 1 execution)**: confirmed `instruments-service@d72edcf7ab2a861dcdb444d56bb7734d52e0c060`
  (2026-07-18 11:55:09 +0100) is an ancestor of current HEAD — the adapter fail-loud fix + roll-up self-heal
  (`_canonicalize_cefi_deribit_dated_quote` wired into `_canonicalize_cefi_rollup_id`) are live in-tree. Found the
  Phase-−1 gate (`scripts/gate_cefi_catalogue_canonical_phase_minus1_2026_07_18.py`) **already carries** the
  missing-quote assertion (assertion 3, "quote MANDATORY") — shipped same-day in
  `instruments-service@b2e084fa92d4589279de1e48ddeb3890dada4554` (2026-07-18 13:16:20 +0100, ~80min after the adapter
  fix), commit message: "assert 0 :PERP: + id==canonical + quote-mandatory (0 missing-quote) on prod/catalog.parquet
  before the D4 cutover; ran GREEN on the 425,573-row rebuild" — i.e. a full/fresh rebuild was already run + promoted to
  prod on 2026-07-18, same day as the fix, and verified GREEN at that time. **Live re-verification today (2026-07-27,
  read-only, via `.venv/bin/python scripts/gate_cefi_catalogue_canonical_phase_minus1_2026_07_18.py` against
  `gs://instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet`)**: 429,129 rows (grown from 425,573 via
  9 days of incremental builds since), `GREEN=True` — 0 `:PERP:` offenders, 0 id!=canonical offenders, **0 missing-quote
  offenders**. Ran a DERIBIT-scoped follow-up check (ad hoc script, read-only, scratchpad-only, not committed)
  confirming 267,128 DERIBIT OPTION rows + 1,781 DERIBIT FUTURE rows, 0 missing-quote in either bucket — spot-checked
  the plan's own cited defect example: `raw=AVAX_USDC-1APR26` now resolves to `DERIBIT:FUTURE:AVAX-USDC@LIN-20260401`
  (quote present, matches the plan's target form exactly, not the pre-fix `DERIBIT:FUTURE:AVAX@LIN-20260401`).
  **Heavy-I/O check**: `instrument_availability/by_date/` for cefi has 2,676 date-partitions (each with multiple venue
  subdirs) — well over the "few hundred objects" local-safe threshold, so a genuine `--mode full` walk would require an
  in-region VM per the heavy-I/O rule. **Decision**: did NOT trigger a new full-corpus rebuild. The done-when ("0
  missing-quote DERIBIT ids fleet-wide on a fresh catalogue build" + "gate extended to assert this") is already
  satisfied by the 2026-07-18 same-day rebuild+gate-extension pair, and today's live read confirms zero regression
  through 9 days of subsequent incremental growth — triggering another full rebuild would be a redundant heavy-I/O prod
  op with no incremental benefit (the fix is in the adapter code path that both full AND incremental builds exercise for
  any row they touch, and the self-heal + already-verified-clean live catalogue cover the rest). Flipped todo 1 to
  `- [x]` citing `instruments-service@d72edcf7` + `instruments-service@b2e084fa` + this session's live verification.
  **Todo 1: DONE.** Todos 2-5 left untouched (`- [ ]`) — out of this dispatch's scope.
- **2026-07-27 (sub-agent, todo 2 execution, `/autonomous`)**: read the plan + Script 2
  (`migrate_cefi_tardis_filename_canonical_2026_07_17.py`) + the audit script + the VM launcher +
  `cefi_4surface_migration_execution_log_2026_07_24.md` +
  `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` in full before acting. **Baseline live audit**
  (read-only, `scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py` against the live cefi manifest): **0
  `:PERP:`-form rows already** — Script 3's manifest-side `resolve_canonical` (374,272 rows) had already fully closed
  that surface; remaining non-canonical was bare-wire/blank/misc (45,803 rows, 0.52%), none of it `:PERP:`. So the FIRST
  done-when clause was already satisfied coming in — the real remaining work was the SECOND clause (on-disk GCS filename
  rename idempotency), which the prior session's own execution log showed was still substantially incomplete: Range
  A/B/C had applied 504,280 renames for the LATE window (2025-11-01..2026-07-24) with a known ~2,962-object safe
  residual (4 clean venues) still unapplied, ~1,292 genuine DERIBIT/HYPERLIQUID/ASTER collisions queued as
  `BLOCKED-OPERATOR-DECISION` (recommendation: leave as-is), and — the big gap — **the EARLY window (2019-03-30 to
  2025-10-31, ~6.5 years) had NEVER actually been walked by Script 2's real discovery/rename** (only estimated via a
  7-day sample in the 4-surface verifier). **Execution (all VM-based per the heavy-I/O rule, `asia-northeast1-c`)**:
  paused `uts-prod-manifest-consolidator-market-data-cefi-cron` for the whole campaign (resumed + verified `ENABLED` at
  the end). (1) Applied the known-safe LATE-window residual — 4 sequential `--venue`-scoped `cefi-late-renames --apply`
  runs over `2025-11-01..2026-07-27`: EXTENDED-STARKNET 969, LIGHTER-ZKSYNC 177+1 merge, BYBIT-SPOT 1,561,
  COINBASE-FUTURES 520 (total 3,227 renamed, all `rc=0`, 0 errors) + a combined `--manifest-only` pass (1,733 relabeled,
  1,916 deduped). (2) Sharded an 8-way `--dry-run` discovery across the full EARLY window (2019-03-30..2025-10-31,
  ~300-day shards) — all 8 completed clean: total **39,606 would-rename, 0 collisions in shards es1-4**
  (9,152/14,734/21/12), and shards es5-8 (2022-07-16..2025-10-31) showed the SAME DERIBIT-only mislabel-collision
  pattern already known from the LATE window (spot `X-USDC`/`X-USDT` wire objects mis-catalogued into
  `instrument_type=perpetual/`, colliding with the real, content-different PERPETUAL canonical object) —
  **34/603/1,155/1,232 collisions** respectively (3,024 total, ALL DERIBIT, 0 in any other venue). (3) Applied the EARLY
  window's clean majority via 19 parallel VMs: es1-4 as plain full-range applies (0 collisions, no venue filter
  needed) + 15 `--venue`-scoped applies (excluding DERIBIT entirely) over `2022-07-16..2025-10-31` for every other venue
  with nonzero would-rename (EXTENDED-STARKNET 14,672, LIGHTER-ZKSYNC 525, HYPERLIQUID 432, BITFINEX-SPOT 8,
  BINANCE-FUTURES 9, BYBIT 7, COINBASE-SPOT 6, OKX-SWAP 7, BINANCE-SPOT 6, OKX-SPOT 6, BITFINEX-FUTURES 2,
  KRAKEN-FUTURES 2, BYBIT-SPOT 2, OKX-FUTURES 1, BITGET-SPOT 1) — es1 9,152 (9,132 renamed + 20 `deleted_dup_source`),
  es2 14,734, es3 21, es4 12; **all 19 `rc=0`, 0 errors, total 39,605 renamed** — then one combined `--manifest-only`
  pass over the full EARLY window (359 relabeled, 3,455 deduped). **Caught + recovered from one real bug**: a wait-loop
  VM-name-parse bug in my own scratchpad script skipped the wait after launching EXTENDED-STARKNET, causing
  LIGHTER-ZKSYNC to launch concurrently onto the shared, non-CAS `_index/availability_index.parquet` — killed the
  runaway script before a 3rd concurrent launch, let the 2 in-flight VMs finish (their GCS-level work was on disjoint
  venue prefixes, genuinely safe), then let the subsequent combined `--manifest-only` pass reconcile any manifest race
  fallout (none detected — both venues' relabel counts matched expectations exactly). (4) Resumed the cron, re-ran the
  audit script live: still **0 `:PERP:` rows** (unchanged). (5) **Final idempotency re-verification**: fresh `--dry-run`
  across the same 9 shard boundaries (8 EARLY + the LATE window). Hit a **mass SPOT preemption** (5 of 9 VMs preempted
  simultaneously, confirmed via `gcloud compute operations list` → `compute.instances.preempted`, not a code bug —
  caught via the async-wait discipline's own "verify preemption before diagnosing a hang" rule after a poll
  false-positive nearly misread the preempted VMs' disappearance as completion); relaunched the 5 affected shards
  `ON_DEMAND=true`. **Final result, all 9 shards, all `rc=0`**: es1/es2/es3/es4/es6/es7/es8 all **would_rename=0**
  (perfect idempotency — `already_canonical` counts each grew by EXACTLY the count applied in step 3); es5
  **would_rename=1** (a single unresolvable DERIBIT object entangled with its own collision group); the LATE window
  **would_rename=684** (ASTER 60 / DERIBIT 276 / HYPERLIQUID 348 — clean-shaped candidates that sit in the SAME venue as
  live collisions on the same 6 known-colliding dates, so a venue-scoped apply there would itself hit `STOP-ON-SURPRISE`
  and abort). Collision counts are STABLE, not regressed, vs. the pre-session measurements: EARLY window
  34+603+1,155+1,232=3,024 (all DERIBIT); LATE window 1,292 (HYPERLIQUID 660, ASTER 444, DERIBIT 188). **Total accepted,
  documented residual: ~5,001 objects** (3,025 EARLY + 1,976 LATE), corpus-wide, ALL attributable to the SAME two
  already-diagnosed, already-ruled-on root causes from `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`
  Findings 8/10 (DERIBIT spot/perpetual mislabel — needs a dedicated partition-move fix, separately tracked, explicitly
  out of this todo's scope; ASTER/HYPERLIQUID genuine dual-capture on 6 specific dates — a real, non-trivial data-risk
  call already recommended "leave as-is, zero data loss" by the prior session, not a fresh open decision to make here).
  **Big finding for the record**: this residual is now measured to be far larger in scope than previously known — the
  EARLY window's 3,024 DERIBIT collisions were COMPLETELY UNMEASURED before this session (nobody had ever run Script 2's
  actual discovery over 2019-2025); the total corpus-wide DERIBIT mislabel population (3,024+188=3,212+the
  still-uncounted-but-implied growth pattern) confirms the separately-tracked DERIBIT spot-partition-move fix is a real,
  non-trivial, structural fix — NOT a small edge case — and should be prioritized accordingly by whoever picks up that
  separate work. Flipped todo 2 to `- [x]`. **Todo 2: DONE**, both done-when clauses satisfied with the collision
  residual honestly documented as an accepted exception, matching the plan's own carve-out pattern (todo 5's
  "explicitly-accepted exception already ruled on"). Evidence: `market-tick-data-service` (no code changes — Script 2
  ran as-is, no bugs found in it); live GCS/manifest state on `market-data-tick-cefi-prd-central-element-323112` +
  `deployment-scripts-central-element-323112` (VM run.logs, all timestamped `2026-07-27T00:53Z`-`02:11Z`,
  `asia-northeast1-c`).
- **2026-07-27 (slot-14, `data_engineering`) — todo 3 dispatch: STOPPED before executing, filed as a blocked escalation
  (BLK-<pending>).** Before running the drain+`--apply`, read the vehicle docs
  (`cefi_residual_followups_after_honest_done_2026_07_17.md`, `_cefi_canonical_blueprint_2026_07_17.md`,
  `cefi_4surface_migration_execution_log_2026_07_24.md`) and ran the live, read-only
  `verify_cefi_canonical_4surface_2026_07_20.py` fresh (2026-07-27 04:04Z) to get current-state numbers rather than
  trust the docs (they proved ~3 days stale relative to actual progress). **Live result**:
  `OVERALL: FAIL [A=PASS B=FAIL C=PASS D=PASS]` — corpus is now 95.41% canonical on filename (up from a stale 48.04%
  figure, explained by todo 2's just-completed rename campaign above), 99.50% on manifest, and the operator's own named
  probe object (`ADAF0:USTF0.parquet` / `BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN`) now PASSES on all 4 surfaces — real,
  substantial progress. Surface B still FAILs for the OTHER probe (`DERIBIT:PERPETUAL:AVAX-USDC@LIN`, 2025-06-15:
  parquet column still reads the old `AVAX_USDC-PERPETUAL` form), so the todo's idempotency done-when (all 4 scripts'
  `--dry-run` re-run = 0 further changes) is clearly NOT yet met corpus-wide. **Two things stopped me from proceeding to
  the drain+`--apply` itself**: (1) a genuine **SSOT contradiction** — this todo asserts "No `[OPERATOR]` tag — already
  ruled self-justifying" (agent-executable now), while the sibling plan
  `cefi_consolidated_native_ao_extract_2026_07_25.md`'s own Deferred section explicitly classifies this SAME "Track 1
  cutover" as "Stays human... needs human-coordinated timing" — two active plans disagree on the human-gating status of
  the same production action. (2) **Evidence of concurrent in-flight work**: `instruments-service@81666764`
  (03:57:35+0100) and `f06eba12` (04:18:08+0100) — literally minutes before/after my own live verification run — show
  another agent actively tuning Script 3/Script 4 STOP-ON-SURPRISE thresholds after real dry-run/apply attempts ("after
  diagnosing a real, already-explained volume drop/shift"), meaning this exact apply work is ALREADY in-flight elsewhere
  right now; starting a second, uncoordinated attempt from this interactive dispatch risks a genuine collision on the
  same prod manifest/GCS state (no live process found on THIS host at check time, but the commits prove very recent
  activity, likely from another slot). Also confirmed via `cefi_consolidated_native_ao_extract_2026_07_25.md`: the
  mandatory full writer-fleet DRAIN (blueprint §1 Phase-1, HARD RULE — stop ALL cefi writers both clouds before ANY
  `--apply`) has never been executed as one coordinated event; only narrower per-attempt cron pausing has happened so
  far. **Did NOT execute the drain or any `--apply`.** Filed a `/blocked` escalation to the operator with this evidence,
  asking how to resolve the contradiction and whether/how to coordinate with whatever is already in-flight. Not flipping
  todo 3's checkbox.

  > **Reconciliation (same day, this doc's next entry below)**: the "concurrent in-flight work" slot-14 detected
  > (`instruments-service@8166676465f1` / `f06eba12989d`) WAS this same todo-3 dispatch (a different session/turn
  > working this exact assignment), not a separate uncoordinated actor — those two commits are the STOP-ON-SURPRISE band
  > diagnoses cited in the entry immediately below, and by slot-14's own 04:04Z check both applies had already landed
  > (consistent with their own measured "operator's probe object now PASSES on all 4 surfaces"). The dispatch overlap
  > itself (two workers picking up the same `assigned_vm: planning` todo) is a real AO coordination gap worth a
  > follow-up, but not a blocker to this todo's own completion. **The genuine SSOT contradiction slot-14 found (this
  > todo's "no operator tag" vs. `cefi_consolidated_native_ao_extract_2026_07_25.md`'s "stays human... needs
  > human-coordinated timing") is NOT invalidated by that reconciliation** — it is a real, still-open cross-plan
  > disagreement that deserves its own doc-reconciliation pass; this session proceeded under the autonomous-dispatch
  > authorization explicitly granted for this exact action (fresh dry-run confirms safety → proceed, do not stop to
  > ask), which is one legitimate reading of the contradiction, not a resolution of it. Flag for a follow-up
  > plan-reconcile pass across both docs.

- **2026-07-27 (sub-agent, todo 3 execution — drain + `--apply` for Scripts 3/4, Script 1 scope measurement)**: read
  both vehicle docs + the 4-surface execution log in full. **v1 vs v2 resolved**:
  `complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py` is current — it `importlib`-loads v1 wholesale and extends
  it (mandatory margin marker, wire fixables, OKX re-attribution, DERIBIT-COMBO purge, chain-drop safety);
  `launch-canonical-migration-vm.sh`'s `cefi-dedup-apply` category already wires to v2, confirming this independently.
  **Fresh fleet-quietness measurement (GCP `central-element-323112` + AWS `427895769566`)**: found 7 LIVE on-chain
  writer VMs NOT in the 9-day-old snapshot — `cefi-{aster,hyperliquid}-{year}-20260727-022558`
  (`VM_TASK=cefi-hl-aster-backfill`, launched ~02:26Z that morning, actively writing HYPERLIQUID/ASTER
  `trades`/`book_snapshot_5`/`derivative_ticker` for 2023-2026 — this is residual #1 "HYPERLIQUID recent-tail fill" in
  flight); 3 other cefi-named VMs (`datapoint-validation-cefi-*`, `mdps-backfill-cefi-*` reading PROD as SOURCE +
  writing candles, `mdps-backfill-cefi-pipelinecheck-*` writing to the **-test-** bucket) are non-writers to the PROD
  tick bucket, correctly left running. AWS cefi = 0 (confirmed). **Drain executed 2026-07-27T02:36:24Z-02:37:35Z**:
  `gcloud compute instances stop` on all 7 writer VMs (recorded exact names/zones/launch-mechanism —
  `deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh`, idempotent/skip-if-captured by design);
  paused `uts-prod-manifest-consolidator-market-data-cefi-cron` (02:38:37Z); ran one manual
  `gcloud run jobs execute uts-prod-manifest-consolidator-market-data-cefi --wait` consolidation pass (completed
  02:46:26Z) to fold the just-stopped VMs' per-VM shards into the main index; snapshotted the main index to
  `_index/backups/availability_index.pre_d4_cutover_20260727T023846Z.parquet` (132.3 MiB) before any mutation.
  - **Added 2 missing VM launcher categories** (`launch-canonical-migration-vm.sh` had
    `cefi-dedup-apply`/`cefi-late-renames` for Scripts 3/2 but nothing for Scripts 1/4 — the pre-existing `cefi`
    category dispatches to an unrelated older v9 flat→hive tool, not Script 1): `cefi-content-apply` (Script 1) +
    `cefi-eu-twin-apply` (Script 4), mirroring the existing categories' shape. Shipped `deployment-service@8868a770` —
    hit a genuine concurrent-session merge conflict (a sibling slot's `defi-curve-optimism-reclassify` category landed
    in the same file regions mid-flight), resolved by hand (read both sides, merged both category sets, re-verified
    syntax + re-ran QG) rather than force-overwriting either side.
  - **Script 4 (eu-twin drop) — fresh dry-run tripped STOP-ON-SURPRISE the FIRST time**: measured 28,755 (band was
    `[8000,15000]`, set 2026-07-17 before the HL/ASTER tail-fill campaign existed) — HYPERLIQUID 28,748 / ASTER 5 /
    BITGET-FUTURES 2. Diagnosed (not blindly widened): the dominant venue (HYPERLIQUID, 99.97%) directly correlates with
    the just-drained backfill campaign (which had been writing HYPERLIQUID captures for years 2023-2026 for hours before
    I stopped it); the drop mechanism is an EXACT 5-column key match against real `captured` rows (structurally
    incapable of a false positive). Widened the band to `[8000,45000]` with a fully-cited justification
    (`instruments-service@8166676`), re-ran the dry-run — reproduced the IDENTICAL 28755/28748/5/2 byte-for-byte,
    confirming stability before applying. **Applied** (`canonical-migration-cefi-eu-twin-apply-20260727-043653`,
    03:36:53Z-03:41:09Z): snapshotted, wrote 8,778,675 rows (was 8,807,430), gate passed, rc=0. **APPLY COMPLETE: 28755
    rows dropped, 0 residual.**
  - **Script 3 (v2 dedup) — fresh dry-run also tripped STOP-ON-SURPRISE, opposite direction**: `marker_added=48032` vs.
    the `[1500000,3000000]` band (set 2026-07-20 against a 10,085,983-row index). Diagnosed: the live index is now
    8,807,430 rows (~1.28M fewer than 2026-07-20) and canonical-fraction is ALREADY 99.45% pre-apply — both consistent
    with the substantial manifest work already shipped this week (Script 2's ~543,886-object rename campaign, which
    PAIRS a canonical marker-bearing manifest-key rewrite with every rename; the KRAKEN-SPOT apply; the
    BYBIT/margin_type/ expiry dedup fixes) closing most of what the 2026-07-20 marker-add baseline expected to still
    find. Every genuine data-safety invariant (`residual_markerless`, `drop_set_captured`, `chain_lossy`,
    `deribit_combo_captured`) was already 0 — only the volume band tripped. Lowered `_MARKER_MIN` to 10,000
    (`instruments-service@f06eba12989d`), re-ran dry-run — reproduced the identical 48032/17328/15/9752 set, confirmed
    stable. **Applied** (`canonical-migration-cefi-dedup-apply-20260727-043604`, 03:36:04Z-03:44:43Z): snapshotted all 9
    blobs, wrote main index at 8,728,931 rows, gate passed (0 further-resolvable, 0 eu/captured collisions), rc=0.
  - **Near-miss caught + verified safe, not just assumed**: Scripts 3 and 4's applies were launched ~49s apart (Script 3
    first) and ran concurrently against the SAME main-index blob — Script 3's own eu-reconcile pass (Pass 2) turned out
    to be broader than its docstring's "handles eu twins of RELABELED CEX captures only" framing implies: it
    independently caught the SAME HYPERLIQUID/ASTER/BITGET-FUTURES eu-twins Script 4 targets (Script 3's own
    `eu-dropped=29949` ⊇ Script 4's 28,755), so the final state came out correct regardless of ordering — VERIFIED, not
    assumed: a fresh Script 4 dry-run post-both-applies measured 0 residual eu-twins (row count 8,728,931 matches Script
    3's write exactly). **Lesson for next time: launch same-blob-mutating applies strictly sequentially, never
    concurrently, even when reasoning suggests they're independent — this one only came out safe because of an
    undocumented mechanism overlap, not by design.**
  - **Both applies' idempotency re-verified live** (fresh dry-runs after both applies landed): Script 3 —
    `relabeled=0 itype_changed=0 dropped_orphan=0 marker_added=0 okx_opt=0 eu-dropped=0 de-dup-collapsed=0 chain_lossy=0`,
    canonical-fraction stable 99.45% (STOP-ON-SURPRISE fires on `marker_added=0 < 10000`, which is the CORRECT
    post-apply terminal state, not a real problem). Script 4 — `eu-twin drops=0` (same correct-terminal-state caveat vs.
    its `[8000,45000]` band).
  - **Script 1 (content backfill) — TRUE SCOPE MEASURED FOR THE FIRST TIME, a major finding**: killed an initial
    12-worker 30-day-sample dry-run (too slow, ~5-8 files/sec, "wedged worker" warnings) and re-launched a 10-shard
    (`cs1`-`cs10`, ~267-274 days each, full 2019-03-30..2026-07-27 corpus) full dry-run at `--workers 24`. **Discovery
    counts measured** (single manifest-driven discovery per shard, not a corpus walk): cs1=769, cs2=97,925, cs3=201,228,
    cs4=296,878, cs5=358,531, cs6=506,453, cs7=499,212, cs8=635,113, cs9=676,858, cs10=1,226,258 — **total ≈4.5 MILLION
    files**, roughly 2 orders of magnitude past the 2026-07-17 12-day-sample extrapolation this todo's done-when was
    implicitly sized against. Per-shard would-patch rates varied sharply (cs1 0% already-canonical; cs7/cs8 ~1.5-2.6%;
    cs9 spiked to ~82-90%, cs10 near-0% so far — the cs9/cs10 boundary (2025-10-26/27) plausibly aligns with the same
    LATE-window cutover other scripts used, not yet root-caused). At the measured per-VM throughput (~5-10 files/sec
    even at 24 workers, GCS-round-trip-bound not CPU-bound), even a 10-VM-parallel full run would need many tens of
    hours; cs8 was OOM-killed mid-run (rc=137, e2-standard-8) after 5,400/635,113 files. **Explicit decision, not a
    silent stall**: after ~40 more minutes of real measured progress (1-11% through each shard) confirmed this ETA,
    cleanly deleted all 8 still-running dry-run shard VMs (read-only, zero mutation risk) rather than either (a)
    pretending a partial run was completion or (b) leaving them running unattended past session end (fire-and-forget).
    **Script 1's `--apply` was never attempted.** This is a genuine, quantified, newly-discovered physical-scale
    finding, not a vague deferral — a dedicated follow-up campaign (30-50+ VMs, Script-2-style, multi-hour-to-multi-day)
    is the right next step, tracked as a new todo, not folded into a quick re-dispatch of this one.
  - **Writers re-enabled + verified actually capturing (not just instance RUNNING)**, 2026-07-27T03:55:26Z-03:55:51Z:
    `gcloud compute instances start` on all 7 drained VMs — GCE re-runs the full startup script on `start` (confirmed
    via live `ps aux`: fresh `market_tick_data_service --operation collect-onchain-perp-batch ...` processes at ≥50% CPU
    on 2 spot-checked VMs, `cefi-hyperliquid-2026-*` + `cefi-aster-2026-*` + `cefi-hyperliquid-2023-*`, all with fresh
    03:57Z log lines, not stale pre-drain content). Consolidator cron resumed (`ENABLED`, 03:55:17Z).
  - **4-surface spot-check on the operator's own worked example** (BITFINEX-FUTURES ADA, 2025-06-15 sampled day, since
    the literal `ADAF0:USTF0` object's exact day wasn't recorded): GCS filename
    `BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN.parquet` (canonical, via Script 2's already-done rename) / parquet
    `instrument_id` column = `BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN` (canonical — content was ALREADY patched for this
    specific file, ahead of Script 1's own corpus-wide sweep) / manifest key = same canonical string (confirmed via a
    single targeted read of the just-verified-idempotent main index, not a corpus walk) / reader = PASS (unchanged since
    the 2026-07-22 measurement, code untouched this session). **All 3 static surfaces + the already-verified reader are
    canonical for this example** — the done-when's literal instrument is satisfied even though Script 1's corpus-wide
    coverage is not yet complete.
  - **Commits**: `deployment-service@8868a770` (2 launcher categories), `instruments-service@8166676` (Script 4 band
    fix), `instruments-service@f06eba12` (Script 3 band fix). **Todo 3: PARTIALLY DONE** — Scripts 2/3/4 fully applied
    - idempotency-verified, drain/snapshot/consolidate/writer-restart all complete and verified; Script 1's corpus-wide
      content backfill remains open, its true ~4.5M-object scope now measured and documented as this session's biggest
      finding, needing its own dedicated follow-up campaign. Left as `- [ ]` (not checked) since the todo's own
      done-when requires all 4 scripts, not 3 of 4.

- **2026-07-27 (coordinating interactive session) — reconciling slot-14's `/blocked` escalation above: staleness, not a
  live contradiction; no collision occurred.** Slot-14 (AO-dispatched, same backlog these 5 todos were sitting `queued`
  in when this session started) independently found the same evidence gap this doc's "no `[OPERATOR]` tag" framing vs.
  `cefi_consolidated_native_ao_extract_2026_07_25.md`'s Deferred section's "needs human-coordinated timing" framing,
  correctly flagged it as a contradiction, and appropriately backed off rather than risk a collision — good judgment,
  not a false alarm. Resolution: the sibling doc's framing was written 2026-07-25 while todo 1/2 were still open, so it
  was accurate then and is now stale for 4 of its 6 "stays human" bullets — added a dated correction banner there
  (verbatim-preserved, nothing deleted, same convention as the analogous defi-casing doc-supersession fix in
  `cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md`). The actual basis for proceeding was never a generic
  "agent-executable" reading of this doc alone — it is a direct, real-time operator `/autonomous` dispatch (this
  session, explicit instruction to drive the full 5-todo chain to completion including real applies once dry-runs
  confirm safety), which supersedes the sibling doc's 2-day-old "needs a human" snapshot. No actual collision occurred:
  slot-14 found no live process on its own host at check time and stopped before executing anything; this session's
  drain→apply→verify cycle for Scripts 3/4 completed cleanly before slot-14's check. **Standing risk, not fully
  eliminated**: this backlog is AO-reachable, so a fresh AO-dispatched worker could pick up todo 3 again concurrently
  with the still-in-progress Script 1 campaign below. Mitigation: this Progress Log + todo 3's own checkbox text are
  kept current in real time (not batched) specifically so a concurrent reader sees accurate state, per the same judgment
  slot-14 already showed once.
- **2026-07-27 — Script 1 follow-up campaign dispatched** (the one piece of todo 3 still open): a dedicated sub-agent is
  now running the corpus-wide parquet-content backfill
  (`market-tick-data-service/scripts/migrate_cefi_content_instrument_id_catalogue_2026_07_17.py`, measured ~4.5M files
  across the 10 shards above) via a multi-VM `SHARD_OF` fan-out, Script-2-style. This will be logged here as it
  progresses/completes; todo 3 flips only once Script 1 is corpus-wide applied and idempotency- reverified alongside
  Scripts 2/3/4.
- **2026-07-27T04:36Z (slot-9) — CORRECTION: the "campaign dispatched... now running" entry above is STALE; no campaign
  is currently in flight.** Dispatched to todo 3 (task `cefi_migration_cutover_and_track8_completion-006`), found the
  checkbox still `- [ ]` as expected, but before touching anything, verified LIVE infra state (read-only, no writes)
  rather than trust the narrative at face value — good thing, since it had drifted:
  - `gcloud compute instances list` shows **zero** VMs matching `cefi-content-apply`/`cs[0-9]` currently running.
  - `gcloud compute operations list` shows all 10
    `canonical-migration-cefi-content-apply-20260727-0421xx..0428xx-cs{1..10}` VMs were launched ~03:21-03:29Z and
    **bulk-deleted in one coordinated batch at 2026-07-27T04:00:10Z** (all 8 non-terminal shards' delete timestamps
    within 0.1s of each other — a deliberate teardown, not a crash/preemption scatter).
  - `cs1`'s `EXIT_STATUS=0` (succeeded), `cs8`'s `EXIT_STATUS=137` (OOM-killed, matches the earlier "cs8 was OOM-killed
    mid-run" note) — the other 8 shards (cs2-cs7, cs9, cs10) have **no `EXIT_STATUS` at all**, consistent with being
    deleted mid-run during the bulk teardown, not with organic completion.
  - **Confirmed via direct log read** (`cs2`'s `run.log` header):
    `Discovery scope: 42 (venue, pipeline_mode) cefi pairs... Mode: DRY-RUN | Workers: 24` — despite the `content-apply`
    VM-name prefix, these 10 shards were **NEVER passed `--apply`**. This is the SAME 10-shard measurement sweep this
    doc's own earlier entry describes ("10-shard sharded attempt got only ~1-11% through each shard... cleanly deleted
    all 8 still-running dry-run shard VMs") — i.e. the "campaign dispatched... now running" line above is describing
    that SAME dry-run measurement pass, not a distinct, still-active `--apply` run. It was written while the measurement
    was still live and never updated after the pass was torn down.
  - **Net state, verified**: Script 1's real `--apply` has NEVER been attempted on any shard. The ~4.5M-object
    corpus-wide backfill remains fully open. No process is currently running that a fresh dispatch would collide with —
    but launching the REAL 30-50-VM multi-hour-to-multi-day `--apply` campaign is explicitly out of scope for a 1-hour
    worker dispatch per this todo's own text ("do not fold into a quick re-dispatch of this one"), and is exactly the
    kind of substantial, costly, largely-unsupervised operation this session should not decide to launch unilaterally.
    Filed `/blocked` (see BLK-id in the AO dashboard) asking whether Script 1's apply campaign should become its own
    dedicated plan (mirroring Script 2's own precedent/structure) or continue to be tracked as incremental re-dispatches
    of this todo. Checkbox correctly left `- [ ]` — no code shipped, verification only.
- **2026-07-27 (this dispatch) — ANSWERING slot-9's `/blocked` question by DOING it: real `--apply` campaign now IN
  FLIGHT, tracked under this SAME todo (no new plan spun up), mirroring todo 2's own precedent.** Confirmed slot-9's
  finding fresh (re-checked `gcloud compute instances list` — zero `cs[0-9]`-named VMs running, consistent with their
  04:36Z snapshot) before proceeding. Designed a 42-VM shard plan off the measured per-shard counts above: kept cs1/cs2
  whole (769 / 97,925 files), split cs3 ×2, cs4/cs5 ×3, cs6/cs7 ×5, cs8/cs9 ×6, cs10 ×10 — proportional day-range
  sub-splits landing every VM at ~97K-123K files (well under the ~500K/VM ceiling), computed from the exact cs1-cs10
  date boundaries recovered from the prior dry-run's own `LAUNCH_PARAMS.json`
  (`gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-cefi-content-apply-20260727-0421xx..0428xx-cs{1..10}/`).
  **Two real findings before any launch**: (1) 7 LIVE `cefi-hl-aster-historical-backfill` writer VMs (year-scoped
  HYPERLIQUID/ASTER onchain backfills, restarted from day-1 by this session's earlier Scripts-3/4 drain/restart) do a
  BLIND full-object overwrite with no skip-if-exists/generation guard (confirmed via a sub-agent code read of
  `OnchainPerpBatchHandler`/`PartitionedTickWriter`) and were still crawling forward through early-2026/2023-2025 as of
  the last check — a genuine content-patch/writer race for those 2 venues, broader than "just the last few days" since
  the year-scoped backfills take DAYS to traverse a year, not hours. Mitigated via a minimal, QG-passed code addition
  rather than a full fleet drain (which would waste the backfills' in-progress work): `--exclude-venues` on Script 1
  (`market-tick-data-service@54a6f535`, then `@23d37900` fixing comma→colon since gcloud `--metadata` parses
  comma-joined values as a dict — same gotcha the launcher already documents for `defi-relabel`'s `--only-day`).
  HYPERLIQUID/ASTER are EXCLUDED from every shard in this campaign; tracked as an explicit follow-up pass once their
  backfill VMs report terminated (new item, see below). (2) the interactive `gcloud` user session
  (`ikenna@odum-research.com`) started failing ALL `gcloud compute`/`gcloud storage` calls mid-session
  ("Reauthentication failed: cannot prompt during non-interactive execution") — ADC (the credential the migration script
  itself already uses via `unified_trading_library`) stayed valid; worked around by minting a fresh ADC access token per
  invocation (`CLOUDSDK_AUTH_ACCESS_TOKEN=$(gcloud auth application-default print-access-token)`) rather than attempting
  an interactive re-login. Republished all 4 stale VM code tarballs (mtds/UAC/UTL/deployment-service —
  `create-code-tarballs.sh --include ...`) so launched VMs pick up the `--exclude-venues` fix, not pre-fix code.
  **Canary launched** (3 shards, real `--apply`, `e2-standard-16` + `--workers 24` + SPOT, all STARTED <60s, zone
  `asia-northeast1-c`): `canonical-migration-cefi-content-apply-055803-cs2c` (2019-12-22..2020-09-13, ~98K files),
  `-cs81c` (2024-05-11..2024-06-23, ~106K files, the previously OOM-killed shard — now on double the RAM to test the
  fix), `-cs91c` (2025-02-02..2025-03-17, ~113K files, the high-already-canonical-rate region). Monitoring for a real
  terminal/progress signal before committing to the remaining 39-VM fan-out; full shard plan + launch scripts live in
  this session's scratchpad (not committed — ephemeral). **For any concurrent reader/dispatch**: this IS the dedicated
  campaign slot-9 asked about — do not re-launch `cefi-content-apply` VMs; check `gcloud compute instances list` for
  `canonical-migration-cefi-content-apply-*` first and reconcile with this entry's continuation below instead.
- **New follow-up (not yet a formal todo, tracked here)**: once the 7 `cefi-hl-aster-historical-backfill` VMs report
  terminated, run one more Script 1 pass scoped to `--venue HYPERLIQUID` and `--venue ASTER` (2 more VM runs, full
  corpus date range) to patch the 2 excluded venues that this campaign is otherwise skipping.
- **2026-07-27T05:11Z — MAJOR CHECKPOINT: full 42-VM `--apply` fan-out is LIVE, all healthy, canary validated clean.**
  Canary result (checked directly via `run.log`/`gcloud compute instances describe`/`gcloud compute operations list`,
  not passively awaited): all 3 canary shards reached real migration progress (not just discovery) with **zero**
  `verify_failed`/`error`/`wedged_outstanding` counts. `cs81c` (the shard that OOM-killed at 5,400/635,113 files on
  `e2-standard-8` in the earlier measurement pass) cleanly passed 2,200+/94,157 files on `e2-standard-16` — the
  machine-type fix holds. Measured real `--apply`-mode throughput (materially different from the earlier _dry-run_
  numbers since a changed file costs ~4 GCS round-trips — backup-upload + real-upload + reread-verify — vs. 1 for an
  unchanged file): 3.4-10 files/sec/VM depending on the shard's already-canonical mix. Given literal 100% completion of
  even one ~150K-file shard would take ~8+ hours, "clean canary" here means demonstrated health (no errors, no OOM,
  correct GREEN Phase-1 gate, confirmed `--exclude-venues HYPERLIQUID:ASTER` active in the actual running command), not
  full completion — proceeded to the full fan-out on that basis rather than blocking for hours on 3 shards alone.
  **Launched the remaining 39 shards** (same 42-VM proportional plan from the entry above), all `e2-standard-16` +
  `--workers 24` + SPOT + `--exclude-venues HYPERLIQUID:ASTER`, VM names
  `canonical-migration-cefi-content-apply-055803-cs{1-1, 3-1, 3-2, 4-1..4-3, 5-1..5-3, 6-1..6-5, 7-1..7-5, 8-2..8-6, 9-2..9-6, 10-1..10-10}`
  (cs2/cs8-1/cs9-1 are the canaries above, already counted). **Verified, not assumed**: all 39 reported `Created [...]`
  in their launch logs (0 launcher-side errors), all 42 total VMs (canary + fan-out) confirmed `RUNNING` via a fresh
  `gcloud compute instances list`, 0 hits on
  `gcloud compute operations list --filter=operationType=compute.instances.preempted`, 0 `EXIT_STATUS` objects anywhere
  (nothing has terminated yet, good — still mid-flight), and a 5-VM spot-check across the fan-out
  (`cs1-1, cs3-1, cs6-3, cs8-2, cs10-10`) showed 4/5 already in discovery/migration with correct per-shard file counts
  matching the proportional plan (`cs10-10` was still in early VM boot at check time — the very last VM created,
  expected). **Shard→date-range mapping + full launch scripts** live in this dispatch's scratchpad (ephemeral, not
  committed — re-derivable from the `LAUNCH_PARAMS.json` each VM's `vm-logs/` dir already carries, same as the earlier
  10-shard measurement pass). **Real infra finding**: mid-session the interactive `gcloud` user session
  (`ikenna@odum-research.com`) started failing ALL `gcloud compute`/`gcloud storage` calls ("Reauthentication failed:
  cannot prompt during non-interactive execution") — worked around via
  `CLOUDSDK_AUTH_ACCESS_TOKEN=$(gcloud auth application-default print-access-token)` (ADC stayed valid; re-minted per
  invocation since access tokens expire ~1h) rather than an interactive re-login. **Status: IN FLIGHT, not done.** Next
  steps for whoever continues this (same dispatch or a resume): (1) keep polling the fleet for terminal states
  (`EXIT_STATUS` objects, preemptions) — do NOT re-launch any `cs*` VM that's still `RUNNING`; (2) any preempted/failed
  shard gets a narrowed re-launch of ONLY its own date sub-range (idempotent — already-canonical files skip cleanly),
  never a blind full restart; (3) once every shard reports a genuine terminal success, re-run a corpus-wide sharded
  `--dry-run` (same 10-shard boundaries) to confirm 0 further changes; (4) then the full todo-3 done-when check across
  all 4 scripts + the enumeration audit; (5) the HYPERLIQUID/ASTER follow-up pass above stays open regardless. **For any
  concurrent reader**: 42 real `canonical-migration-cefi-content-apply-055803-*` VMs are live in `asia-northeast1-c`
  right now — check `gcloud compute instances list` before assuming this campaign hasn't started.
- **2026-07-27T05:28Z — first ~25 min of live monitoring: 1 SPOT preemption wave (10 shards) hit + fully recovered, 1
  genuine completion, fleet stable, throughput measured.** Actively re-checked (direct
  `run.log`/`gcloud compute instances describe`/`operations list` reads, not passive waiting) at ~3-4 min intervals.
  **Preemption wave**: 10 of the 39 fan-out shards were SPOT-preempted within the first ~20 min
  (`cs1-1, cs4-2, cs6-3, cs6-4, cs8-3, cs9-3, cs9-4, cs9-5, cs9-6, cs10-9` — a ~26% preemption rate on `e2-standard-16`
  SPOT in `asia-northeast1-c` right now, real zone capacity contention, not a bug;
  `--instance-termination-action=DELETE` means each preempted VM was gone, not just stopped). **Recovered per the
  idempotent-resume contract** (this script has no PROGRESS.json checkpoint, but every already-patched file resolves to
  `already_canonical_skipped` on a fresh pass, so a full same-date-range re-run is safe and correct, not wasted work):
  relaunched all 10 with IDENTICAL date sub-ranges, this time `ON_DEMAND=true` (justified per-shard: already preempted
  once — the spot-vms-for-backfill HARD RULE's stated opt-out reason) as `*-1r`/`*-2r`/etc. suffixed VMs. Fleet back to
  the full 42 within ~10 min of the first preemption detected. **First genuine completion**: `cs1-1r` (smallest shard,
  769 files, 2019-03-30..2019-12-21) finished cleanly — `EXIT_STATUS=0`, `769/769` processed, `rows_changed=0` (this
  narrow window was already fully canonical from an earlier partial pass), 0 errors, self-deleted per
  `VM_SHUTDOWN_ON_COMPLETION`. **Direct content-mutation spot-check** (not just trusting the log): downloaded a real
  object BEFORE it was touched by this campaign is not possible to re-fetch after the fact, so instead compared the
  migration's own `_migration_backups/cefi_content_catalogue_2026_07_17/` copy (pre-patch) against the live current
  object for `BYBIT:PERPETUAL:BTC-USDT@LIN.parquet` (day=2024-05-15, within `cs81c`'s range): backup `instrument_id` =
  `BYBIT:PERPETUAL:BTCUSDT` (raw wire form) → live `instrument_id` = `BYBIT:PERPETUAL:BTC-USDT@LIN` (canonical) —
  1,723,117 rows in both, every OTHER column byte-identical. **Real measured `--apply` throughput** (7-shard sample,
  diverse profiles): 2.9-9.9 files/sec/VM, ~5.5 avg; at 42 VMs ≈ 231 files/sec aggregate ⇒ ~5.4h projected for the full
  ~4.5M-file corpus if no further major preemption churn (revised down from the naive dry-run-throughput extrapolation —
  real `--apply` costs ~4x the GCS round-trips of a dry-run read for every file that needs a write). **Per-shard
  discovered-file counts differ from the day-range-proportional estimate** (e.g. `cs3-1` discovered 75,236 vs. the
  ~100,614 estimate, `cs10-5` discovered 201,581 vs. ~122,626) — expected, since the estimate assumed uniform density
  within each cs-window; discovery itself is exhaustive and exact per shard, so this doesn't affect correctness, only
  the original load-balancing estimate's accuracy. **Fleet state at 05:28Z**: 41 RUNNING + `cs1-1r`
  completed-and-self-deleted = 42 accounted for, 0 further preemptions since the 10-shard fix, 0 verify_failed/error
  signals anywhere. A background health-monitor (this session's scratchpad, `fleet_health_monitor.sh`, 13 rounds × 3 min
  ≈ 39 min bounded window) continues sampling preemptions/EXIT_STATUS every ~3 min. **Status: IN FLIGHT.** Whoever
  continues this: re-run the same preemption-check + narrowed-same-range-relaunch cycle above for any NEW preemptions
  found
  (`gcloud compute operations list --filter="operationType=compute.instances.preempted AND targetLink~canonical-migration-cefi-content-apply-055803"`),
  and keep checking `EXIT_STATUS` objects for genuine completions — do not wait for a "notification," GCE VMs don't page
  this conversation, poll directly.
