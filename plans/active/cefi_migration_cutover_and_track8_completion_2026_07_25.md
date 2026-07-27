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
    /plans/archive/issues/cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md,
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
- [x] ✅ [BACKEND] P0. **CODE SHIPPED 2026-07-27 (slot-13) — `market-tick-data-service@a4f90769`.** POST-CUTOVER: flip
      the smoke-check + downloader to canonical instrument ids. All 3 coupled changes landed in one commit: (1)
      `venue_fetch._process_venue` now resolves a canonical-form `--instrument-ids` entry to its venue raw wire symbol
      via the existing `CeFiWireCanonicalMap.raw_symbol_for` (the same cefi catalogue map FIX D3 already builds
      candidate filename stems from — no new resolver), split into a new leaf module `_canonical_instrument_ids.py`
      (`venue_fetch.py` is cap-critical at 900 lines); (2)
      `scripts/pipeline_e2e_check.py::_sample_raw_symbol_from_prod_listing` no longer skips canonical-named parquet
      stems — the `':' in stem` skip-guard is gone; (3) the "verdicts are unreliable mid-migration" caveat marked
      RESOLVED in `issues/cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md` (see that
      doc's own RESOLVED section for the reference back to this commit). 6 new + 1 updated unit test file prove the
      resolution logic against a synthetic `CeFiWireCanonicalMap` (canonical→raw hit, raw passthrough, mixed list,
      unresolvable-honest-passthrough, no-catalogue-registered passthrough) — full `quality-gates.sh` green
      (sentinel-verified SHA == HEAD before quickmerge). **Residual gap, not yet closed**: the plan's own Done-when also
      asks for "a targeted re-fetch of a canonical-named instrument returns real rows" — a LIVE end-to-end proof via a
      real VM smoke run (`scripts/pipeline_e2e_check.py --tardis-only`) against one of the 8 already-canonical-only
      cells measured 2026-07-18 (BITFINEX-FUTURES / BYBIT-SPOT / COINBASE-FUTURES). NOT performed in this session —
      launching a VM smoke check is a real-cost, Tardis-N=1-gated operation outside a routine single-worker dispatch's
      scope without confirming no other slot is mid-Tardis-fetch; deferred to whichever session runs todo 5's live
      backfill (already a VM-launch context) or a dedicated follow-up. Repos: market-tick-data-service,
      unified-trading-pm. Source: `cefi_consolidated_closeout_2026_07_18.md` (Track 8, POST-CUTOVER item).
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
- **2026-07-27T05:31Z — SECOND, much larger preemption wave: 33 of the remaining 41 SPOT shards wiped out at once; root
  cause found (zone-wide `e2-standard-16` SPOT stockout in `asia-northeast1-c`); pivoted the whole campaign to
  `ON_DEMAND`.** A fresh direct check (not the 3-min-interval monitor, an out-of-band re-verify) found only 9 VMs still
  `RUNNING` — and all 9 were exactly the 10 shards relaunched `ON_DEMAND` in the entry above (minus `cs1-1r`, already
  completed) — every single remaining SPOT VM (all 33: the 3 canaries `cs2c/cs81c/cs91c` included) had been preempted.
  **Diagnosed, not just patched**: attempted a same-machine-type `ON_DEMAND` relaunch of the 32 missing shards; 31/32
  succeeded immediately, but `cs2d` hit `ZONE_RESOURCE_POOL_EXHAUSTED_WITH_DETAILS` — GCP's own error confirms
  `asia-northeast1-c` has **zero `e2-standard-16` capacity available right now, for ANY provisioning model** (the exact
  error suggests `asia-northeast1-b`/`-a` have capacity instead) — this is what was silently causing both preemption
  waves (SPOT gets reclaimed first when a zone is genuinely capacity-constrained). **Fix**: retried `cs2d` on
  `e2-standard-8` (half the RAM) in the SAME zone — succeeded immediately, confirming `e2-standard-8` capacity exists
  even though `e2-standard-16` doesn't right now. Did not fall back to a different zone (would fragment the fleet across
  zones for no benefit once `e2-standard-8` proved available in `asia-northeast1-c` itself) or re-litigate the earlier
  OOM-mitigation reasoning — the OOM history was tied to ONE monolithic 635K-file shard on `e2-standard-8`; every shard
  in this campaign is already sub-sharded to ~75K-200K files, well under the scale that OOM'd, so `e2-standard-8` should
  be safe for the rest too if `e2-standard-16` capacity disappears again. **All 32 relaunches now landed**: 31 on
  `e2-standard-16` + `cs2d` on `e2-standard-8`, all `ON_DEMAND` (immune to further SPOT reclaim). **Fleet state
  05:35Z**: 41 RUNNING + `cs1-1r` completed = 42 accounted for, ALL non-completed VMs now `ON_DEMAND`, 0 new preemptions
  since the pivot (expected — nothing left on SPOT to reclaim), 0 verify_failed/error signals. **Cost note for the
  record**: this campaign is no longer SPOT-cost-optimized (the HARD RULE's stated opt-out condition — "ON_DEMAND is the
  only opt-out... if you have a specific reason" — is squarely met here: two full preemption waves + a confirmed hard
  zone stockout is about as concrete a reason as this rule anticipates). **Status: IN FLIGHT, fleet materially more
  stable now than the last checkpoint.** Whoever continues this:
  `gcloud compute operations list --filter="operationType=compute.instances.preempted"` should show NO NEW entries
  beyond the 42 total already recorded (10 wave-1 + 32 wave-2, though `cs1-1`/`cs1-1r` overlap the two counts) — if new
  preemption operations DO appear, something is still on SPOT and needs the same on-demand fix; otherwise the fleet
  should just need periodic `EXIT_STATUS`-completion polling from here. Full wave-2 shard→date-range map + launch
  scripts remain in this dispatch's scratchpad.
- **2026-07-27T05:41Z — naming clarification + final stability confirmation for this dispatch turn.** The 3 canary VMs
  (`cs2c`, `cs81c`, `cs91c`) were among wave-2's 33 preemptions and are now superseded by their `ON_DEMAND` replacements
  `cs2d` (e2-standard-8, the one that hit the zone stockout), `cs8-1d`, `cs9-1d` (both e2-standard-16) — those 3 shards'
  own progress restarts from the discovery phase (idempotent, no work lost, just the ~1-2 GCS-listing minutes redone).
  **Current live fleet (verified via a fresh full `gcloud compute instances list`, 41 rows + `cs1-1r` completed = 42)**:
  9 `*-r`-suffixed (wave-1 recovery) + 31 `*-d`-suffixed on `e2-standard-16` (wave-2 recovery) + 1 `*-d` (`cs2d`) on
  `e2-standard-8` + `cs1-1r` done. Preemption-operations count holds steady at 42 (unchanged since the pivot — no new
  entries), confirming nothing is still SPOT-exposed. **This dispatch turn's work is done here** — the campaign is
  healthy, fully on-demand, and will keep running unattended in GCE for the ~5h projected remainder. A resumed
  dispatch/turn should: re-run the exact preemption/EXIT_STATUS checks in the entries above, keep narrow-relaunching
  (same date range, `ON_DEMAND=true`, `e2-standard-16` — or `-8` if `-16` stockouts again) anything that shows a NEW
  preemption, and once every one of the 42 shards has a genuine `EXIT_STATUS=0`, proceed to the plan's own next steps
  (corpus-wide idempotency `--dry-run`, the 4-script done-when check, the enumeration audit, then flip todo 3).
- **2026-07-27T05:47Z — continued-stability confirmation, ~30 min post-pivot; noting an unrelated concurrent-slot
  finding for the record.** Fresh direct re-check: 41 RUNNING + `cs1-1r` completed = 42 accounted for, preemption-ops
  count still exactly 42 (0 new since the pivot), 0 `verify_failed`/`VERIFY FAILED` hits sampled across 5 diverse
  shards, all sampled shards show steady forward progress (3.3-9.8 files/sec, e.g. `cs8-1d` 3,600/94,157 @ 368s,
  `cs10-5d` 3,800/201,581 @ 491s) — fleet is healthy and stable on `ON_DEMAND`. **Unrelated, for cross-plan awareness
  only**: the operator confirmed a concurrent AO slot (slot-13) independently shipped **todo 4's** code portion
  (`market-tick-data-service@a4f90769` — canonical→raw resolution in the downloader + smoke-check sampler fix) while
  this campaign was running; it left the live re-fetch proof as a residual, deferred to todo 5/a follow-up. Not this
  dispatch's todo (leaving todo 4 alone), noted here only so a future pass on the same repo doesn't collide with or
  duplicate that commit. **Continuing to poll at sensible (not tight-loop) intervals** per the operator's explicit
  instruction — this will span several more resumed turns given the ~5h projected remainder; next checkpoint will follow
  once either a new preemption is found, a meaningful batch of shards completes, or another natural pause point is
  reached.
- **2026-07-27T06:30Z (scheduled 30-min check-in) — 3 shards OOM-killed (`rc=137`), NOT genuine completions; relaunched
  with reduced concurrency; fleet-wide memory-risk sampled, no reliable early-warning signal found.** Fresh poll found 4
  `EXIT_STATUS` objects (up from 1) — first read as 4 completions, but direct verification caught the real signal:
  `cs8-1d`, `cs10-2d`, `cs10-3d` all show `EXIT_STATUS=137` (SIGKILL/OOM, matching the ORIGINAL cs8 OOM signature from
  the pre-campaign measurement) with NO `SCRIPT 1 CONTENT MIGRATION SUMMARY` block — genuinely killed mid-run, not
  completed (`bash: ... Killed` + `rc=137` in each `run.log` tail). Only `cs1-1r` (769 files) is a real `EXIT_STATUS=0`
  success. **This means the earlier "e2-standard-16 fixes the OOM" conclusion from the canary was WRONG or incomplete**
  — these 3 are ALSO `e2-standard-16`, same as the canary that looked clean; OOM recurred anyway. **Diagnosed, not
  blindly retried**: sampled `bytes_read` across ~37 of the other currently-running shards (a `--workers 24` fleet) —
  found several perfectly healthy shards ALREADY well past the ~47-52GB `bytes_read` level the 3 OOM'd shards died at
  (e.g. `cs7-1d` at 113GB, `cs4-1d`/`cs5-2d` at ~107GB, `cs3-1d` at 102GB, all still running fine) — so cumulative
  bytes-read is NOT a reliable OOM leading indicator; this looks like transient bad luck of many large files (likely
  `book_snapshot_5`-heavy days) converging on the SAME worker pool at once, not a deterministic per-shard property.
  **Mitigation applied**: relaunched all 3 with identical date ranges + `ON_DEMAND` + `e2-standard-16`, but
  `--workers 10` (down from 24) — fewer concurrent workers directly caps peak concurrent per-file memory buffers (each
  in-flight file costs ~2-4 buffers: download bytes, parsed DataFrame, patched copy, serialized write bytes, plus a
  second read+parse on the immediate post-write verify), so this should reduce recurrence probability without needing a
  corpus-wide restart. **Deliberately did NOT preempt/restart the other ~37 healthy, already-progressed `--workers 24`
  shards** (several 30-60%+ through their own file counts, e.g. `cs7-1d` at 38,600/72,064=54%, `cs6-4r` at
  26,000/83,490=31%) — killing healthy progress on a THEORETICAL risk that hasn't materialized for them costs more
  (redone idempotent work) than it saves; the policy going forward is REACTIVE, evidence-based recovery (any shard that
  OOMs gets relaunched at `--workers 10`), not a blanket preemptive derate. **New VM names**: `cs8-1d2`, `cs10-2d2`,
  `cs10-3d2`. **Fleet state 06:30Z**: 41 RUNNING + 1 genuine completion (`cs1-1r`) = 42 accounted for, 0 new preemptions
  (still exactly 42 preemption-ops, unchanged), 1 isolated `read_error=1` noted in `cs8-6d`'s stats (per-file isolation
  — the tool counts and skips, does not abort the run; not itself a failure mode needing action, just noted for the
  record). **Whoever continues this: watch for MORE `EXIT_STATUS=137` completions going forward** (not just `=0`) —
  treat any as an OOM, relaunch same date-range at `--workers 10` (or lower, e.g. 6, if 10 recurs), never assume a fresh
  `EXIT_STATUS` object means success without checking its actual value + the run.log's SUMMARY block.
- **2026-07-27T06:55Z (scheduled 30-min check-in) — TRUE root cause of the OOM class found: pathologically huge
  mis-classified DERIBIT files, not worker concurrency. Reduced-worker fix from the last entry did NOT work; corrected
  course.** Direct re-verification (per the standing "always check actual EXIT_STATUS value + SUMMARY block" rule):
  found 2 MORE `EXIT_STATUS=137` events — `cs10-3d2` (my own `--workers 10` retry from the last checkpoint, died EVEN
  FASTER: 4,000/168,624 files @ 391s, vs. the original's 7,800 @ ~2,020s) and `cs8-5d` (a previously-untouched
  `--workers 24` shard, first failure). **Diagnosed properly this time, not just re-patched**: `cs10-3d2` dying faster
  at FEWER workers proved concurrency wasn't the driver. Sampled the largest objects in each OOM'd shard's own date
  range and found the same signature in EVERY case — one giant DERIBIT file per range, always
  `venue=DERIBIT/instrument_type=perpetual/data_type=trades/<BASE>_<QUOTE>-<DATE>-<STRIKE>-<C|P>.parquet` (a
  DATED-OPTION wire symbol, sitting in the WRONG `perpetual/` partition — a real, separate DERIBIT option→perpetual
  mis-classification bug, consistent with the already-tracked "DERIBIT mislabel" finding class elsewhere in this plan's
  history, but out of THIS todo's scope to fix): `cs10-3` day=2025-12-25 → 2.45GB; `cs8-5` day=2024-11-10 → 2.08GB;
  `cs8-1` day=2024-05-20 → 1.73GB; `cs10-2` day=2025-12-01 → **6.3GB**. These files are so large because the
  mis-classification bug appears to merge MANY distinct dated-option instruments' trades into one "perpetual" blob per
  day — a single such file, once downloaded + parsed to a DataFrame + copied (the tool's own `df.copy()`) +
  reserialized + re-downloaded-and-reparsed for the post-write verify, plausibly peaks at 30-50+GB resident for that ONE
  file alone — enough to OOM even `e2-standard-16` (64GB) regardless of how many OTHER workers are concurrently doing
  normal-sized files, which is exactly why cutting `--workers` 24→10 didn't help (and made it worse, since a smaller
  worker pool doesn't change whether a giant file lands on the schedule, it just changes overall throughput). **Fix**:
  extended `--exclude-venues` to `HYPERLIQUID:ASTER:DERIBIT` for the 4 confirmed-affected shards (DERIBIT excluded
  alongside the existing HL/ASTER exclusion), `--workers` back to 24 (no longer the lever — the exclusion removes the
  actual landmine), same `e2-standard-16`/`ON_DEMAND`. **Proactively stopped `cs10-2d2` mid-run** (only ~20% done,
  6,000/29,444) rather than let it keep going — its date range is CONFIRMED to contain the 6.3GB landmine
  (day=2025-12-01 falls inside `cs10-2`'s 2025-11-23..2025-12-20 window), so letting it continue would only guarantee a
  LATER, more-wasteful OOM. New VM names: `cs8-1e`, `cs8-5e`, `cs10-2e`, `cs10-3e` — all `RUNNING` immediately after
  launch. **Deliberately did NOT preemptively kill/re-exclude-DERIBIT on the other ~37 currently- healthy shards** —
  this bug is very likely present in MOST DERIBIT-containing shards across the corpus (DERIBIT has been captured since
  near the start of the corpus), meaning more of the currently-healthy fleet may hit their OWN DERIBIT landmine later —
  but preemptively killing dozens of shards with real, unaffected progress on a "might contain one too" theory is
  disproportionate versus the same reactive policy already working: **the moment any other shard shows
  `EXIT_STATUS=137`, add `DERIBIT` to its relaunch's `--exclude-venues` immediately** (no need to re-diagnose from
  scratch — this IS the diagnosis now). **New follow-up tracked** (alongside the existing HYPERLIQUID/ASTER one): a
  dedicated DERIBIT content-patch pass is needed once the rest of the corpus is done, ideally after the
  mis-classification bug itself is understood/fixed upstream (or at minimum with a much bigger machine / lower worker
  count / a size-aware pre-filter that isolates the outlier file for solo processing). **Fleet state 06:55Z**: 41
  RUNNING + `cs10-2d2` stopping (self-inflicted, not a failure) + 1 genuine completion (`cs1-1r`) = 42 accounted for
  once `cs10-2d2`'s replacement `cs10-2e` is counted. 0 new preemption-ops (still 42, unchanged — SPOT stockout issue
  has not recurred). **Whoever continues this: any FUTURE `EXIT_STATUS=137` should be treated as the DERIBIT landmine
  class first** (check the shard's date range for a >1GB `DERIBIT/perpetual/trades` file before assuming a new/different
  cause) and fixed by adding `DERIBIT` to that relaunch's `--exclude-venues`, `--workers` back to 24 (no need to reduce
  it — that lever doesn't help this failure mode).
- **2026-07-27T07:05Z — same check-in, continued: 2nd genuine completion + 1 more DERIBIT-landmine OOM confirmed +
  fixed, playbook holding.** `cs10-10d` finished cleanly (`EXIT_STATUS=0`, 15,920/15,920 files, 550 patched, 300,876
  rows changed via `catalogue_marker_peel`, `STOP-ON-SURPRISE` bounds ok, 0 errors) — the 2nd real completion alongside
  `cs1-1r`. Separately, `cs9-3r` (one of the wave-1 `--workers 24` recoveries) also came back `EXIT_STATUS=137` —
  checked its date range (2025-05-02..2025-06-15) BEFORE assuming a new cause, per the standing instruction, and found
  the exact same signature: a 2.33GB `DERIBIT/perpetual/trades/XRP_USDC-23MAY25-3D1-C.parquet` (day=2025-05-15) —
  confirms the DERIBIT-landmine class is real and recurring, not a one-off. Relaunched immediately per the now-known
  playbook: `cs9-3e`, `--exclude-venues HYPERLIQUID:ASTER:DERIBIT`, `--workers 24`, `e2-standard-16`, `ON_DEMAND` — no
  fresh diagnosis needed this time, the playbook just worked. **Fleet at 07:08Z**: 41 RUNNING, 8 total `EXIT_STATUS`
  objects seen so far (2 genuine `=0`, 6 `=137` OOM — all 6 OOM shards now relaunched with DERIBIT excluded), 0 new SPOT
  preemptions. Continuing to poll at sensible intervals.
- **2026-07-27T07:20Z (scheduled 30-min check-in) — issue doc filed for the DERIBIT finding; 3rd genuine completion; 2
  more DERIBIT-landmine OOMs confirmed + fixed via the playbook.** Filed
  `issues/deribit_dated_option_trades_perpetual_misclassification_2026_07_27.md` (checked first — neither
  `deribit_combo_perpetual_partition_move_2026_07_21.md` nor the Finding-8/10 spot/perpetual-collision class in
  `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` cover this; different symbol shape, different failure
  mode) per the findings-triage rule — this is a genuine data-correctness bug this migration works around, not fixes,
  and needs its own follow-up (writer-side root-cause, exhaustive census, backfill/reclassify pass). **Fleet poll**:
  `cs7-1d` finished cleanly (`EXIT_STATUS=0`, 72,064/72,064 files, 1,874 patched, `STOP-ON-SURPRISE` ok, 0 errors) — 3rd
  genuine completion (`cs1-1r`, `cs10-10d`, `cs7-1d`). `cs9-4r` came back `EXIT_STATUS=137`; checked its date range
  (2025-06-16..2025-07-29, day=2025-07-01) BEFORE assuming a new cause per the standing rule — found the same signature
  (1.26GB `XRP_USDC-4JUL25-2D25-C.parquet`) — relaunched as `cs9-4e` with `--exclude-venues HYPERLIQUID:ASTER:DERIBIT`,
  `--workers 24`, same as the established playbook; no fresh diagnosis needed. **Running total**: 3 genuine completions,
  7 DERIBIT-landmine OOMs hit and fixed (`cs8-1`, `cs8-5`, `cs10-2`, `cs10-3` ×2, `cs9-3`, `cs9-4`), 0 SPOT preemptions
  since the ON_DEMAND pivot. Fleet at ~40 RUNNING. Continuing to poll at sensible intervals toward all-42-terminal.
- **2026-07-27T07:50Z — apparent `cs7-2d`/`cs6-1d` throughput deceleration investigated properly (per the
  async-wait-discipline "healthy-looking but actually stuck" concern), confirmed NORMAL VARIANCE, not degradation.** The
  operator flagged a real-looking pattern from the last few check-ins' file-count deltas (`cs7-2d`'s per-window gain
  shrinking ~6x). Pulled each shard's FULL `run.log` (not just the latest line) rather than re-reporting the same two
  data points. Findings: (1) **byte-throughput held flat/stable** through the "slow" window — `cs7-2d` ~24.5-25.1MB/s
  cumulative-and-instantaneous both ways, `cs6-1d` ~31.0-31.3MB/s — while `files/sec` cumulative average declined only
  because the AVERAGE FILE SIZE in this stretch of the corpus is genuinely bigger (~7MB/file recent vs. ~4.2MB/file
  overall for `cs7-2d`); (2) **zero real errors** — 0 `ERROR` lines in either log, and the only `WARNING`s (259 / 263
  respectively) are ALL the same generic 30s "no progress in poll window" soft-check, not the tool's actual fatal
  hard-wedge path (never triggered); grepping for `429`/throttle/timeout/retry found no genuine hits (the apparent
  matches were false positives on numbers like `429129` catalogue-row counts); (3) **direct SSH process check** on both
  VMs confirmed the migration process genuinely alive and working — `cs7-2d` PID 7725 at 207% CPU / 279min accumulated
  CPU time, `cs6-1d` PID 7769 at 200% CPU / 271min — light load averages (2.57/1.78/1.85 on 16 cores) consistent with
  the already-documented I/O-bound-not-CPU-bound profile, no thread pileup. `cs6-1d` has in fact continued advancing
  normally since the flagged snapshot (68% done as of this check). **Conclusion: this was a genuine
  file-size-distribution effect in this part of the DERIBIT-excluded corpus, not the class of silent degradation the
  async-wait-discipline rule warns about — no fix applied, none needed.** Standard fleet poll this cycle: still 40
  RUNNING, 42 preemption-ops (unchanged), same 10 `EXIT_STATUS` objects as the last several checks — no new completions
  or OOMs to action via the DERIBIT playbook this cycle.
- **2026-07-27T08:15Z-08:55Z — operator challenged the deceleration re-diagnosis with a specific number (0.22 files/sec,
  25x below canary); rigorous re-check confirms per-file THROUGHPUT IS FINE, but uncovers a much more serious REAL
  problem: a systemic zombie-VM class (9-10 confirmed) that the routine check-ins had been missing entirely.** **Part 1
  — the throughput math, resolved.** Computed TRUE sustained files/sec for 5 shards two INDEPENDENT ways (the script's
  own internal `elapsed` clock vs. real GCS-log wall-clock timestamps) — both agree exactly: `cs7-2d`=5.571/s,
  `cs6-1d`=7.567/s, `cs2d`=3.620/s, `cs5-1d`=5.466/s, `cs9-4e`=5.699/s — all in the SAME range as the original ~5.5
  files/sec/VM canary, no 25x gap anywhere. **Root cause of the alarming "0.22/sec" figure**: the flagged sub-window
  (`cs7-2d` 44,200→49,000) was assumed to span "roughly 6 hours" (counting check-in MESSAGES × their nominal "~30-min"
  label), but the shards' own real log timestamps show it actually spanned **25.1 real minutes** (07:39:02→08:04:09) —
  the "~30-min check-in" cadence label has NOT corresponded to real 30-minute wall-clock gaps in this session; check-ins
  have arrived much faster in real time than their nominal label. At the REAL 25-min span, the rate is 3.185 files/sec —
  close to the shard's own cumulative average, not an alarming outlier. **Part 2 — while investigating, found something
  genuinely serious the throughput re-check alone would have missed**: doing a full-fleet staleness sweep (comparing
  every running shard's LAST `Progress:` log line against real wall-clock "now", not just the 2-3 shards originally
  flagged) surfaced **10 shards silently hung at the OS/VM level** — `cs7-5d`, `cs8-2d`, `cs8-4d`, `cs8-6d`, `cs9-5r`,
  `cs9-6r`, `cs8-3r`, `cs10-4d`, `cs10-1d`, plus a redundant already-superseded zombie `cs8-1d2` — each confirmed via
  TWO independent checks: (a) log completely silent (including the heartbeat daemon, which pings every ~60s) for 1-2.5+
  hours while GCE still reported the instance `RUNNING`; (b) direct SSH timeout (`exit=124`) on EVERY one, re-verified
  against a KNOWN-HEALTHY VM (`cs7-2d`, which SSH'd instantly) to rule out an SSH-access problem on my end rather than
  the VMs. Serial-console inspection on a sample found real system-level distress signatures, not clean process kills:
  `cs9-5r` logged `systemd-resolved: Under memory pressure, flushing caches` followed by a network anomaly; `cs9-6r`
  showed `DHCP lease lost` / route-drop timeouts — consistent with severe memory pressure destabilizing the whole VM
  (not just the migration process) rather than the OOM-killer cleanly killing one process (the `rc=137` signature
  already documented above). **Working theory (not fully proven)**: this is likely the SAME giant-file/memory-pressure
  class already root-caused for DERIBIT, just manifesting as a total system hang instead of a clean `SIGKILL` depending
  on how fast the allocation spike hits relative to the kernel OOM-killer's reaction — the script's own internal "wedged
  worker" warning is powerless here since a truly hung VM stops writing ANY log lines, including that warning. **This is
  exactly the "looks healthy on shallow inspection" trap the coordinator + CLAUDE.md's async-wait-discipline rule warn
  about** — `gcloud compute instances list` reporting `RUNNING` was not sufficient evidence of health; only a real
  staleness-vs-wallclock comparison plus a direct SSH/serial-console check caught it. **All 10 fixed**: deleted each
  hung VM and relaunched fresh with the identical date range, `ON_DEMAND`, `e2-standard-16`,
  `--exclude-venues HYPERLIQUID:ASTER:DERIBIT` (DERIBIT excluded defensively on all of these, not just the ones with
  confirmed landmine files, given the plausible shared root cause) — new names `cs7-5f`, `cs8-2f`, `cs8-4f`, `cs8-6f`,
  `cs9-5f`, `cs9-6f`, `cs8-3f`, `cs10-1f`; **`cs10-4` (261,903 files, by far the single largest surviving shard) was
  additionally SPLIT in two** (`cs10-4a` 2026-01-17..01-30, `cs10-4b` 2026-01-31..02-13) to reduce this specific failure
  mode's blast radius on the biggest remaining shard. **Also found 2 more genuine completions** during the sweep that
  the routine check-ins had missed: `cs10-8d` (90,506/90,506, `EXIT_STATUS=0`, 1 isolated per-file `error` noted but
  non-fatal) and `cs6-5d` (89,084/89,084, `EXIT_STATUS=0`, clean) — bringing the genuine-completion count to **6**
  (`cs1-1r`, `cs10-10d`, `cs7-1d`, `cs10-9r`, `cs10-8d`, `cs6-5d`). **Honest re-baselined ETA**: the original "~5.4h"
  figure was a FLEET-AVERAGE-throughput number (total files ÷ aggregate fleet files/sec) — it does not model "time until
  ALL 42 are done," which is gated by the SLOWEST/BIGGEST surviving shard, not the average. The largest shards now
  running (e.g. `cs10-5d` at 201,581 files, cumulative rate ~5.4/s) project to **~10.4h of their OWN runtime** — these
  VMs started ~05:40Z, so realistic completion is more like **~16:00Z**, i.e. roughly **7 more real hours from this
  checkpoint (08:55Z)**, not the original ~5.4h estimate — mainly because per-shard completion time was never actually
  bounded by the fleet average, compounded by the zombie-hang cycles costing 1-2.5h of wall-clock delay per affected
  shard before detection. **Process fix going forward**: every check-in must now include a REAL staleness sweep
  (last-progress-timestamp vs. wall-clock now, flagging anything >45min stale) across the WHOLE fleet, not just
  spot-checking 2-3 shards — this is now the standing check-in procedure, not optional.

- **2026-07-27T~12:00Z (pre-compact checkpoint, coordinating interactive session)** — durability checkpoint before a
  context-compaction boundary in the driving session; NOT a stopping point for the campaign itself, which continues
  unattended in GCE regardless of this session's context state.
  - **Live snapshot at checkpoint time** (fresh
    `gcloud compute instances list --filter="name~canonical-migration-cefi-content-apply"`, project
    `central-element-323112`): **23 VMs still RUNNING** (`cs10-3e/4a/4b/5d`, `cs2d`, `cs3-2d`, `cs4-3d`, `cs5-1d/2d`,
    `cs6-2d/3r`, `cs7-3d/4d/5f`, `cs8-1e/2f/3f/5e/6f`, `cs9-1d/2e/3e/4e`) — down from 42 total launched, consistent with
    real ongoing completions (not independently re-confirmed via `EXIT_STATUS` objects at this exact moment — that
    re-verification is the first thing any resumed check should do). Zero visible distress signals in this snapshot (no
    new preemption-count movement checked this pass).
  - **Todos 1-2-3(Scripts3/4) done; Script 1 (this fleet) is the only remaining piece of todo 3.** Todos 4 (mostly done,
    live-refetch proof still owed — see its own checkbox note) and 5 remain after Script 1 finishes.
  - **Continuity mechanism (session-internal, will NOT survive a genuinely fresh session/new conversation — only
    survives a same-session `/compact`)**: a background monitoring sub-agent has been resumed every ~30-60min via
    `SendMessage` throughout this dispatch, paired with a `ScheduleWakeup` timer (currently armed, ~30-60min cadence)
    that re-invokes the driving session to trigger the next resume. **If this exact mechanism is gone (new session, or
    the agent/timer didn't survive)**: resuming monitoring from scratch just means re-running the same live
    `gcloud compute instances list` filter above,
    `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/<vm>/run.log` per VM for progress, and checking
    for `EXIT_STATUS` objects under each VM's `vm-logs/` prefix for genuine completions — the campaign's state lives in
    GCE + GCS, not in this session's memory. Do NOT re-launch any `cs*` VM still `RUNNING`.
  - **Lessons worth not re-learning** (see full detail in the entries above, condensed here): (1) a "%X/hour" progress
    comparison across check-ins is worthless unless computed from REAL log timestamps, not assumed interval labels — the
    mid-session "25x slowdown" scare was a wall-clock-assumption bug, not a real regression, and cost a full diagnostic
    detour to rule out; (2) GCE `status=RUNNING` is not liveness — a whole-VM OS-level freeze (memory pressure) can
    silence even the heartbeat daemon for hours while GCE reports healthy; only externally-read signals (GCS heartbeat
    blob / uploaded run.log mtime, read from OUTSIDE the VM) reliably catch that class, never an in-VM watchdog (it dies
    with the same freeze); (3) always trace a claimed "X doesn't invoke Y" through the FULL execution path (host
    launcher → GCE startup-script → actual wrapper) before concluding an absence — grepping only the top-level launcher
    script for `vm-exec-with-gcs-tee.sh` gave a false negative this session (it IS invoked, one hop downstream via a
    shared startup script) and had to be corrected twice after being asserted in a committed doc.
  - **Companion work this session, all independently verified pushed** (not just self-reported): the
    `migration_vm_hung_detection_monitoring_gap_2026_07_27.md` issue doc (6 todos, all implemented and shipped this
    session across `deployment-api`/`deployment-service`/`market-tick-data-service`) plus 3 further issue docs it spun
    off for genuinely separate gaps found along the way (`vm_launcher_class_b_no_stall_kill_gap_2026_07_27.md`,
    `deployment_api_inventory_alert_gate_ondemand_only_2026_07_27.md`,
    `relaunch_stalled_vm_no_checkpoint_resume_gap_2026_07_27.md`) — none of that work is at risk; every commit cited in
    those docs was independently re-verified live on `origin/live-defi-rollout` (`git merge-base --is-ancestor`) as part
    of this same checkpoint, not trusted from sub-agent self-reports.
  - **git state at checkpoint**: every repo touched this session (`unified-trading-pm`, `instruments-service`,
    `market-tick-data-service`, `deployment-service`, `deployment-api`) is `ahead=0` of `origin/live-defi-rollout` —
    nothing uncommitted or unpushed anywhere. The only untracked files present (`plans/audit/results/*_2026_06_28.*`)
    predate this session and are not mine — left untouched per the foreign-WIP rule.

- **2026-07-27T~13:20Z (post-`/compact` resume) — fresh fleet check: 18/42 still RUNNING (5 more clean completions since
  the pre-compact snapshot: `cs5-2d`, `cs6-3r`, `cs8-1e`, `cs9-3e` all `EXIT_STATUS=0`). One genuine casualty found and
  fixed: `cs7-4d` exited `137` at 116,200/129,599 files (89.7% done) — its own command excluded `HYPERLIQUID:ASTER` but
  **not `DERIBIT`**, and its date range (2024-01-25..2024-03-18) sits inside the DERIBIT dated-options OOM window
  diagnosed earlier this session — this shard simply predates that fix being applied fleet-wide, not a new bug.
  Relaunched as `canonical-migration-cefi-content-apply-055803-cs7-4d-r2` with
  `MIGRATION_EXTRA_ARGS="--exclude-venues DERIBIT:HYPERLIQUID:ASTER"` (same playbook as the prior DERIBIT casualties);
  confirmed RUNNING and past discovery (128,129 files, 54 days x 36 venue/pipeline_mode pairs) within ~4 min of launch.
  **New operational finding surfaced while relaunching**: the launcher warned all 4 code tarballs
  (`market-tick-data-service`/`unified-api-contracts`/`unified-trading-library`/`deployment-service`) were STALE
  relative to repo HEAD — meaning every "floating"-pin VM launched since some earlier point (including this session's
  own `market-tick-data-service@54817bc1` PROGRESS.json-checkpoint fix, landed 10:27 UTC) had been silently pulling
  **pre-fix code** despite the source commit being pushed and green. Ran
  `create-code-tarballs.sh --include market-tick-data-service --include unified-api-contracts --include unified-trading-library --include deployment-service`
  to republish (completed ~12:19 UTC, manifests now point at current HEADs modulo normal concurrent-slot drift on
  `unified-api-contracts`, which is expected multi-agent churn, not a gap). **Caveat honestly recorded**: `cs7-4d-r2`
  itself likely still raced the republish and ran the pre-fix tarball anyway (its own run.log shows processing starting
  ~12:17:30 UTC, before the 12:19:15 UTC republish completed) — this does NOT matter for correctness here since the
  DERIBIT exclusion was passed as an explicit CLI flag on the command line (independent of which tarball SHA is
  running), but it DOES mean this specific relaunch will NOT checkpoint to `PROGRESS.json` if it dies again; a future
  relaunch of `cs7-4d-r2` itself would still replay from day one. Every VM launched from now on picks up the fresh
  tarball. **Lesson**: a floating-tarball VM launch and a code republish are NOT ordered relative to each other —
  launching a VM does not itself trigger a republish, so a source fix can sit merged-and-green for hours while every VM
  in flight (and any new one launched before someone remembers to republish) keeps running the old code. **Not a novel
  finding** — this is the SAME gap already tracked in
  `/plans/active/issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md` (two prior
  independent hits the same day, features-service + sports-features-purge); added this occurrence as a corroborating
  finding there and bumped its "default `LC_TARBALL_FRESHNESS=enforce`" todo P2→P1 given it's now a 3rd same-day hit,
  rather than fix the default mid-campaign (not the right moment to flip a workspace-wide launch gate while other shards
  are in flight).

- **2026-07-27T~13:35Z — fleet check after a session interruption (battery cut mid git-push retry loop; no work lost,
  the interrupted commit was still sitting safely uncommitted in the working tree on resume).** Fresh count: **14 shards
  still RUNNING** (`cs10-3e/4b/5d`, `cs3-2d`, `cs4-3d`, `cs5-1d`, `cs6-2d`, `cs7-3d(finishing)/5f`, `cs8-3f/6f`,
  `cs9-1d/2e/4e`, `cs7-4d-r2`) — **28/42 shards clean-complete** (5 more since the last snapshot: `cs10-4a`, `cs2d`,
  `cs8-2f`, `cs8-5e`, `cs7-3d`, all confirmed `EXIT_STATUS=0`). `cs7-4d-r2` (the DERIBIT-excluded retry) is healthy at
  36,200/128,129 files (28%) and — confirmed via its own `run.log` — IS writing
  `[[VM_PROGRESS]] last_completed_date=... monotonic=true` checkpoints, meaning it picked up the fresh (post-`54817bc1`)
  tarball despite the earlier-suspected race; it now has real crash-resilience its predecessor never had. No new
  casualties, no new stale-tarball hits, no wedged-worker warnings escalating past the known-benign noise pattern.
  **Committed via the pathspec form (`git commit -m "..." -- <2 files>`) after this session's own git-commit skill
  diagnosed the actual cause of ~9 consecutive "branch drift"/foreign-content collisions this cycle: a still-alive
  background sub-agent from earlier in this session (a "review role" agent, visible via `[slot-2·laptop]`-authored
  commits with unrelated content — `/codex/02-data/prediction-data-types-catalog.md`,
  `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`) sharing this SAME un-isolated working tree, not a truly
  foreign concurrent slot** — both of its commits were legitimate, independently verified content (one already
  corroborated by `mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md`'s own Update 6), so nothing was discarded, just
  not bundled into my own commit. **Lesson for future sessions**: spawning monitoring/review sub-agents without
  `isolation: "worktree"` means they share this git tree and WILL occasionally interleave commits under the same slot
  identity — expected, not a bug, and the pathspec commit form (`git commit -m ... -- <my files>`) is the clean way
  through it instead of a stash-restore dance.

- **2026-07-27T~14:15Z — operator follow-up on the "does crash resilience cover all VM runs" question, shipped
  `deployment-service@02ac568`.** Corrected an earlier claim: `RelaunchBackfillVm` (the OOM/exit-137 actuator) itself
  has no machine-escalation logic, but `escalation.py::_recover_backfill_vm()` ALREADY did (shipped 2026-06-23, sourced
  from `launch_budget_registry.MEMORY_TIER_LADDER`, capped at `n2-highmem-32`/256GB — exactly matching the operator's
  stated cap) — I had looked at the wrong abstraction layer. Two REAL gaps found and fixed this cycle: (1) a successful
  escalated-memory OOM relaunch previously left NO human-visible trace of why the VM OOM'd in the first place
  (`route_finding` stayed on the quiet `auto_recover` tier) — now also files an idempotent-per-(vm-prefix, day)
  "investigate OOM root cause" issue doc, without changing the tier/paging behavior; (2) `RelaunchStalledVm` (the
  watchdog-kill actuator) had zero checkpoint-resume logic at all, unlike `RelaunchPreemptedVm` — per operator direction
  ("stale vms should be watchdog killed and relaunched if they weren't complete"), ported the core
  monotonic-checkpoint-resume + force-run-no-checkpoint-pages logic (NOT the tarball-repin machinery, a separate
  preemption-specific concern) across `heartbeat_stall_watcher.py` (reads `LAUNCH_PARAMS.json`/`PROGRESS.json` only on a
  genuine STALL verdict), `escalation.py::_recover_stalled_vm()`, and `relaunch_stalled_vm.py`. 12 new tests, full QG
  forced-fresh (bypassing the green content-sentinel via `QG_SENTINEL_DISABLE=true` to get a genuine re-run, not a skip)
  — 2889 passed, 0 failed. Shipped via quickmerge (code, not docs) — `02ac568` on `live-defi-rollout`, `ahead=0`.

- **2026-07-27T~14:10Z (scheduled check-in) — 12/42 shards still RUNNING** (`cs10-3e/4b/5d`, `cs3-2d`, `cs4-3d`,
  `cs6-2d`, `cs7-4d-r2/5f`, `cs8-3f/6f`, `cs9-1d/2e`). **31/42 clean-complete** (3 more since the last snapshot:
  `cs5-1d`, `cs7-3d`, `cs9-4e`, all confirmed `EXIT_STATUS=0`). No new casualties. `cs7-4d-r2` (the DERIBIT-excluded
  retry) healthy at 54,600/128,129 files (42.6%), steady ~8.3 files/sec, checkpoint still writing. Nothing to relaunch
  this cycle.

- **2026-07-27T~14:50Z (scheduled check-in) — 8 VMs still RUNNING** (`cs10-4b/5d`, `cs3-2d`, `cs4-3d`, `cs7-4d-r2`,
  `cs8-6f`, `cs9-1d/2e`). 4 more clean completions since the last snapshot (`cs10-3e`, `cs6-2d`, `cs7-5f`, `cs8-3f`, all
  confirmed `EXIT_STATUS=0`). No new casualties. `cs7-4d-r2` healthy at 72,600/128,129 files (56.7%), steady ~8.0
  files/sec. **Running-count caveat**: a full `gsutil ls` of this campaign's `vm-logs/` prefix returned 105 distinct
  VM-instance names (not 42) — this session's own "N/42" framing tracks _currently-running instances_ cycle-over-cycle,
  not a precise total-shard denominator; the extra names are earlier canary/preemption-retry attempts
  (`-r`/`-d2`/bare-numbered) already superseded by a later-suffixed relaunch under the SAME logical shard, not new
  uncovered work. Spot-checked a handful of the old bare-numbered/retry names for a buried non-zero exit predating this
  session's monitoring — found only already-known/already-handled DERIBIT-class 137s from earlier waves (already covered
  in this doc's own OOM-playbook entries above), nothing new. Did not do a full 105-way reconciliation (scope creep
  beyond this cycle's job — the currently-RUNNING list plus per-drop exit-code checks is the operationally sufficient
  signal); noting this here so a future reader isn't confused by the running-count arithmetic not summing to a clean 42.
  Nothing to relaunch this cycle.

- **2026-07-27T~15:25Z (scheduled check-in) — 6 VMs still RUNNING** (`cs10-5d`, `cs3-2d`, `cs4-3d`, `cs7-4d-r2`,
  `cs8-6f`, `cs9-1d`). 2 more clean completions (`cs10-4b`, `cs9-2e`, both confirmed `EXIT_STATUS=0`). No new
  casualties. `cs7-4d-r2` healthy at 88,200/128,129 files (68.8%), steady ~7.9 files/sec. Fleet is converging — down to
  6 shards. Nothing to relaunch this cycle.

- **2026-07-27T~15:40Z — operator ETA question surfaced a genuine casualty: `cs9-1d` frozen since 09:33 UTC (6+ hours),
  `gcloud` still reporting it `RUNNING`.** Its `run.log` (last INFO Progress at 09:31:01, 25,200/152,700 files, 16.5%)
  AND the authoritative host-level sidecar heartbeat blob (`vm-heartbeat/…cs9-1d.txt`) BOTH stopped updating at the
  identical timestamp (~09:33) — the whole VM froze at the OS level, not just the worker (the "GCE RUNNING ≠ alive"
  class already documented in this doc's own lessons). No `PROGRESS.json` checkpoint existed (this VM predates
  `54817bc1`) and it wasn't a SPOT preemption (`compute.operations.list` for `compute.instances.preempted` on this VM
  returned empty) — a genuine host-level hang, not reclaimed capacity. Deleted it and relaunched as
  `canonical-migration-cefi-content-apply-055803-cs9-1d-r2` with the same
  `--start-date 2025-02-02 --end-date 2025-03-17` scope; caught+republished a stale `unified-api-contracts` tarball
  before it could matter (mtds/UTL/ deployment-service were already fresh from earlier fixes). **ETA to full drain,
  given current real throughput**: `cs10-5d` (98.5%, 5.5 files/sec) ~9min; `cs4-3d` (92.6%, 3.7/sec) ~48min; `cs3-2d`
  (87.5%, 3.1/sec) ~85min; `cs7-4d-r2` (72.7%, 7.8/sec) ~75min; `cs8-6f` (52%, 3.9/sec) ~6.5h — **the long pole**;
  `cs9-1d-r2` just restarted (its dead predecessor ran at only 1.8 files/sec on this exact date range before freezing,
  the slowest of the whole fleet — if it holds that rate over its full 152,700-file scope, this could be the true long
  pole at potentially 20+ hours, though idempotent-skip should make the RE-scan of its already-processed 25,200 files
  fast, not full-cost). Honest read: 4 of 6 shards finish within ~1.5h; `cs8-6f` and `cs9-1d-r2` are the real unknowns
  and could run several hours past that — will re-baseline this estimate against measured throughput on the next
  check-in rather than assert a single number now.

- **2026-07-27T~16:32Z (scheduled check-in) — 3 VMs RUNNING** (`cs3-2d`, `cs7-4d-r2`, `cs8-6f`). `cs10-5d`/`cs4-3d` both
  confirmed clean (`EXIT_STATUS=0`). **`cs9-1d-r2` OOM'd (exit 137)** at only 5,600/159,332 files — its
  `bytes_read`/file ratio (~19MB/file average, driven by a handful of enormous files) matches the DERIBIT dated-options
  giant-file class already diagnosed earlier this campaign, and this shard had NEVER had `--exclude-venues` applied
  (unlike `cs7-4d-r2`, which already excludes it). Relaunched as
  `canonical-migration-cefi-content-apply-055803-cs9-1d-r3` with `--exclude-venues DERIBIT`; caught + republished 2
  stale tarballs (`unified-api-contracts`, `deployment-service`) before they could matter. Checked all 3 currently-
  running VMs for the new frozen-but-RUNNING failure class (per the operator's ask last cycle) — all 3 have fresh
  `run.log` activity within 1-3 minutes of the check, no freeze. **ETA re-baseline**: `cs3-2d` (95.6%, 3.1 files/sec)
  ~30min; `cs7-4d-r2` (87.1%, 7.3/sec) ~38min; `cs8-6f` (58.1%, 3.9/sec) ~5.7h — still the confirmed long pole;
  `cs9-1d-r3` just restarted with DERIBIT now excluded, too early to rate — if it settles near `cs7-4d-r2`'s
  post-exclusion rate (~7/sec) it'd be ~6.3h, but this is a rough guess pending real throughput data.

- **2026-07-27T~17:57Z — operator asked whether the confirmed long pole (`cs8-6f`, ~5.7h ETA) could be resharded to
  finish in under an hour instead. Yes — resharded it.** `cs8-6f` had no `PROGRESS.json` checkpoint (predates the fix)
  and its date-range shard (`2024-12-19..2025-02-01`, 45 days, already excludes `HYPERLIQUID:ASTER:DERIBIT`) isn't
  processed in strict date order, so there was no clean "resume from X%" cut point. Killed it and split the FULL 45-day
  range into 8 sub-shards of ~6 days each (`cs8-6f-p0`..`cs8-6f-p7`), each launched with the SAME
  `--exclude-venues HYPERLIQUID:ASTER:DERIBIT`; idempotent-skip means the ~60% already migrated by the killed VM costs
  each sub-shard only a fast metadata-skip, not full reprocessing. All 8 confirmed `RUNNING`. Caught + republished a
  `deployment-service` tarball that had drifted stale again since the last republish (a different slot pushed a new
  commit in between) — this is now the 4th same-day hit of the tarball-staleness gap already tracked + P1-bumped in
  `features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md`. At 8-way parallelism, even at the
  ORIGINAL single-VM's blended 3.9 files/sec (a lower bound — each VM now has less competing I/O and only needs to
  scan+skip a fraction of the corpus, so real throughput per shard should be comparable or better), 8×3.9≈31 files/sec
  aggregate vs. ~75,470 files remaining ≈ ~40min — should land the whole range well under an hour, matching the
  operator's ask. Did NOT apply the same resharding to `cs9-1d-r3` yet (just relaunched, no throughput data to judge
  whether it's actually a long pole) — will reshard it too if its rate stays slow on the next check-in.
