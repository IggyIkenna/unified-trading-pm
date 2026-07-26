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

- [ ] [BACKEND] P0. **Fix the DERIBIT `instrument_id` missing-quote defect, then rebuild `prod/catalog.parquet`.** The
      canonical symbol must ALWAYS be `BASE-QUOTE` (operator ruling 2026-07-18, overriding the `BASE[_QUOTE]`
      optional-quote decision in `instrument_id_format_canonicalization_2026_07_08.md`). Verified live: **265,538 of
      425,160 catalogue rows (62%) — ALL DERIBIT (263,950 OPTION + 1,588 FUTURE)** — drop the quote
      (`raw=AVAX_USDC-1APR26` → `DERIBIT:FUTURE:AVAX@LIN-20260401`, must be `…AVAX-USDC@LIN…`; `BTC-5APR19-3250-C` →
      `DERIBIT:OPTION:BTC@INV-…`, must be `…BTC-USD@INV-…`). DERIBIT-only (every other venue already carries the quote).
      Fix the DERIBIT adapter/builder to always emit `BASE-QUOTE@MARGIN_TYPE[-YYYYMMDD][-STRIKE-C|P]` (USDC linear / USD
      inverse), then rebuild `prod/catalog.parquet` (coordinated ~38-min prod op). **Self-justified, no `[OPERATOR]`
      tag** per `task_template.md` finding Q (operator ruling 2026-07-25, cefi.2/cefi.3): the design pass floated an
      instant-rollback-via-GCS-object-versioning justification, but bucket versioning is NOT independently confirmed in
      this pass, so this uses finding Q's other basis instead — prior explicit operator approval (the 2026-07-18 ruling
      that this exact fix gates the Track-1 cutover) plus per-script validation (the adapter/builder fix ships behind
      its own passing unit tests before the catalogue rebuild runs against it). This GATES todo 3 below (else the
      cutover bakes the quote-less form into all four surfaces). Repo: instruments-service. **Done when**: the fixed
      adapter/builder emits the quote for 100% of DERIBIT rows on a fresh catalogue build (0 missing-quote DERIBIT ids),
      the Phase-−1 verify gate is extended to also assert ZERO missing-quote ids fleet-wide (the pre-existing gate only
      checked 0 `:PERP:` + `instrument_id==canonical_instrument_id`), and both are cited with the shipping commit.
      Source: `cefi_consolidated_closeout_2026_07_18.md` (Operator dispositions, DERIBIT quote fix).
- [ ] [SCRIPT] P0. **Execute the remaining on-disk GCS content rename for `:PERP:` → `:PERPETUAL:`** (374,272 manifest
      rows already resolved via Script 3's `resolve_canonical`, `instruments-service@555ddf1c` — this todo is ONLY the
      remaining on-disk GCS object rename + symbol decompose, e.g. `ASTER:PERP:CLUSDT` → `ASTER:PERPETUAL:CL-USDT@LIN`;
      it explicitly EXCLUDES the separate MTDS writer-side fix for future captures, which ships alone as
      `cefi_consolidated_native_ao_extract_2026_07_25.md`'s own todo 7 — do not re-do that work here). Extends Script
      2/3. **Self-justified, no `[OPERATOR]` tag** per `task_template.md` finding O/Q: reuses the
      already-dry-run-validated `resolve_canonical` rename pattern from Script 2/3 — the same idempotent
      copy→verify→delete shape already proven safe in production for the KRAKEN-SPOT and DERIBIT renames documented in
      `cefi_4surface_migration_execution_log_2026_07_24.md`. Repos: market-tick-data-service, instruments-service.
      **Done when**: a fresh run of `scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py` shows 0
      `:PERP:`-form instrument_id rows remaining in the live cefi manifest/GCS content, and a `--dry-run` re-run of the
      rename script confirms 0 further planned changes (idempotency). Source: `cefi_consolidated_closeout_2026_07_18.md`
      (Track 8, `:PERP:` → `:PERPETUAL:` rewrite).
- [ ] [PM] P0. **Execute the minutes-gap hybrid cutover (Track 1) — the operator-approved drain + `--apply` of the
      4-script canonical-ID migration.** Requires todo 1 (DERIBIT fix) and todo 2 (PERP on-disk rename) above to have
      landed first in this sequential chain — Track 8's own audit found the cutover `--apply` would otherwise bake
      ~1.48M non-canonical rows (blank-itype-driven bare-wire, `:PERP:`, missing-quote, COMBO) into the canonical
      surfaces as if resolved. Vehicle: `plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md` (+
      blueprint `_cefi_canonical_blueprint_2026_07_17.md`) — Phase A (code) ✅, Phase B (deploy) ✅, Phase C (4 scripts
      dry-run-validated) ✅; this todo is Phase D/E (drain + `--apply`). **No `[OPERATOR]` tag** — already ruled
      self-justifying per cefi.2/cefi.3 (finding Q): the migration is explicitly operator-approved in principle and
      every constituent script is individually dry-run-validated. Repos: instruments-service, market-tick-data-service.
      **Done when**: the operator's `ADAF0:USTF0.parquet` is canonical on all four surfaces (GCS filename / parquet
      `instrument_id` column / manifest key / reader), verified live; each of the 4 scripts' `--dry-run` re-run asserts
      0 further changes (idempotency); flip this todo AND `cefi_residual_followups_after_honest_done_2026_07_17.md`'s
      own Phase-1/2 todos, citing the shipping evidence in both places. Source:
      `cefi_consolidated_closeout_2026_07_18.md` (Track 1). > **⚠️ Cross-link gate (D1 instrument_type-column UPPERCASE
      migration, 2026-07-20 ruling)**: this `--apply` > (`complete_cefi_manifest_canonical_dedup_2026_07_17.py`) is the
      script that rewrites the manifest > `instrument_type` COLUMN to UPPERCASE (its own docstring's delta (iv),
      "`instrument_type` COLUMN drift... > lowercase/aliased -> canonical"). Per >
      `plans/archive/issues/honest_coverage_harness_instrument_type_case_break_on_d1_migration_2026_07_20.md` (resolved,
      archived) > (todo 4), this `--apply` MUST NOT run until that issue's case-insensitivity fix to the Honest-Coverage
      v2 > harness (`instruments-service/scripts/measure_honest_coverage.py` — shipped > `instruments-service@867b68f6`,
      2026-07-25, QG green) has landed and is proven green — otherwise the > cutover silently craters coverage.json for
      every migrated cefi shard the moment this todo runs. That > normalisation has shipped; this todo is now UNBLOCKED
      on that specific dependency.
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
