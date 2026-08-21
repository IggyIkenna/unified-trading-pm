---
doc_type: plan
title: DeFi distinct-values canonical cleanup — purge legacy/phantom manifest rows, fix live writers, execute canon-swap, verify UI/API clean
summary: >-
  Client-facing deliverable — the deployment UI/API distinct-values panel for DeFi must show ONE canonical value set
  per axis (venue/chain/instrument_type/data_type). Live census 2026-08-21 found 22 EVM chain-glued venue rows that are
  pure manifest phantoms (zero backing GCS objects, 100% fake "captured"), 4 Solana glued venues written by a
  still-LIVE writer bug, legacy data_types (dex_pools/dex_swaps/rate_indices), POOL casing regrowth, and blanket
  perp_funding/derivative_ticker honest-absence stamps on non-perp venues. This plan purges/migrates them, root-fixes
  the writers/seeders so they don't regrow, executes the already-shipped N5r/N6r manifest canon-swap on a VM, and
  regenerates the coverage rollup so the panel verifies clean. Operator rulings 2026-08-21 — physical merge now; full
  autonomy incl. proof-gated deletes; human plan.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos:
  [
    market-tick-data-service,
    instruments-service,
    deployment-service,
    unified-api-contracts,
    deployment-api,
  ]
scope: [engineer]
tags: [defi, canonicalisation, manifest, distinct-values, migration, data-correctness]
related:
  [
    /plans/active/issues/defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md,
    /plans/active/issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md,
    /plans/active/issues/b21_distinct_values_noncanonical_live_2026_08_18.md,
    /plans/active/issues/b21_defi_venue_5_unregistered_perp_dex_2026_08_19.md,
    /plans/active/issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md,
    /plans/active/data_pipeline_completion_2026_08_21.md,
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
  ]
created: 2026-08-21
last_updated: 2026-08-21
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
assigned_role: data_engineering
effort: max
context_scope:
  [
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/honest-coverage-model.md,
    market-tick-data-service/market_tick_data_service/scripts/defi_manifest_venue_itype_canon_swap.py,
    market-tick-data-service/market_tick_data_service/scripts/defi_manifest_drain_gate.py,
    deployment-service/scripts/vm/launch-defi-manifest-projection-vm.sh,
    deployment-api/deployment_api/routes/data_status/_distinct_values.py,
    instruments-service/scripts/measure_honest_coverage.py,
  ]
drift_direction: advance-code
---

# DeFi distinct-values canonical cleanup (2026-08-21)

> **Codex SSOTs**: /codex/02-data/defi-canonical-naming-ssot.md (bare venue + separate chain= is canonical; combined
> PROTOCOL-CHAIN is legacy) · /codex/02-data/four-surface-reconciliation-procedure.md ·
> /codex/02-data/gcs-and-manifest-delete-safety-protocol.md · /codex/02-data/honest-coverage-model.md.
>
> **Operator rulings (2026-08-21, this session)**: (1) physical merge NOW, not read-path cosmetics; (2) FULL autonomy
> incl. deletes where the five-part proof / phantom-verification passes (overrides the human-only default for this
> cleanup); (3) this is a human (NA) plan; (4) zero-content rows (empty_confirmed / phantom "captured" with no object)
> under NON-canonical venue spellings are purge targets too — the manifest must only carry canonical venues, because
> legacy rows pollute the distinct-values panel and the coverage denominator.
>
> **Explicit NON-goals**: perp_funding vs derivative_ticker are NOT duplicates — ruled 2026-07-15/2026-08-08 and
> code-verified 2026-08-21 (independent fetches; only 60.7% match for HYPERLIQUID; features-service is hardwired
> venue-by-venue to one or the other with no fallback). Do NOT merge them. The 6-venue CARRY_BASIS_PERP defi-bucket
> home (BINANCE-FUTURES etc.) is operator-ACCEPTED (2026-08-20) and live-read by CanonicalPerpFundingProvider — do NOT
> purge; disposition is todo 13.

## Evidence base (live census 2026-08-21, slot-3 session)

- Defi `_index`: 161,763,515 defi rows. Census CSVs: session scratchpad `venue_census.csv` etc. (see Progress Log).
- **Class A — 22 EVM glued phantom venues** (`UNISWAP_V3-{ETHEREUM,ARBITRUM,BASE,OPTIMISM,POLYGON}`,
  `BALANCER-{6 chains}`, `CURVE-{AVALANCHE,ETHEREUM}`, `SUSHISWAP_V3-{BASE,AVALANCHE,ETHEREUM}`, `SUSHISWAP-ARBITRUM`,
  `CAMELOT_V3-ARBITRUM`, `PANCAKESWAP_V3-{BASE,ETHEREUM,BSC}`, `AERODROME_V3-BASE`): all `data_type=dex_pool_swaps`,
  `chain=""`, `instrument_id=NULL`, 100% capture_status=captured, `written_at` clustered 2026-08-03/04T07:2x (single
  bulk registration), **zero backing GCS objects** (prefix probes found no `venue={GLUED}/` prefix at all). Purge.
- **Class B — 4 Solana glued venues, LIVE writer bug**: `KAMINO-SOLANA`/`MARGINFI-SOLANA`/`SOLEND-SOLANA` (risk_params,
  real objects, e.g. `venue=KAMINO-SOLANA/chain=SOLANA/instrument_type=solana_lending/data_type=risk_params/`
  `KAMINO-SOLANA-SOLANA:SOLANA_LENDING:BONK.parquet`, last written 2026-08-14) + `SOLBLAZE-SOLANA` (lst_rates, 1,330
  rows, backing objects not found under expected defillama pipeline_mode — verify then purge-or-migrate). Fix writer,
  migrate objects, re-key manifest.
- **Class C — legacy axis values**: `dex_pools` 454,014 rows (re-retire; recurs via rebuild rescans of live legacy
  objects — needs a scan guard), `dex_swaps` 3,460,714 rows (REAL legacy-only content in 22/24 venue-chain pairs — NOT
  a blanket rename; content migration is gated), `rate_indices` 25,478, `POOL` uppercase 10,204,983 rows (canon-swap
  re-keys; MDPS root fix shipped @94215e9cd9 — confirm landed), blank instrument_type 5,620,899 rows + Python-None
  3,296 rows, blanket perp_funding/derivative_ticker stamps across ~90 non-perp defi venue-chain combos.
- **Distinct-values surface**: `GET /data-status/distinct-values/defi` reads the nightly honest-coverage rollup
  (`coverage.json`) raw-by-design (drift detector); the panel only reflects cleanup after the rollup regenerates.

## Todos

- [ ] [SCRIPT] P0. 1. **MTDS writer fix — Solana glued-venue double-glue.** Find the writer emitting
      `venue={PROTOCOL}-SOLANA` + `chain=SOLANA` + filename `{PROTOCOL}-SOLANA-SOLANA:...` for solana_lending
      `risk_params` (KAMINO/MARGINFI/SOLEND) and check the SOLBLAZE lst_rates path for the same class. Fix to bare
      `venue={PROTOCOL}` + `chain=SOLANA` + canonical id `{PROTOCOL}-SOLANA:{ITYPE}:{SYM}` per
      defi-canonical-naming-ssot. QG green + quickmerge. (repo: market-tick-data-service)
- [ ] [SCRIPT] P1. 2. **Rebuild-scan legacy-path guard.** `rebuild_defi_manifest.py` scan re-registers retired legacy
      data_type objects (`dex_pools` re-registered 2026-08-12 after 2026-08-05 retirement). Add a durable
      skip-legacy-vocabulary guard (retired data_types + glued defi venue segments) so retirements stick. QG +
      quickmerge. (repo: market-tick-data-service)
- [ ] [DATA] P0. 3. **Purge Class-A 22 glued phantom venues.** Safe-idempotent + self-justified per operator ruling
      (2): rows are phantom `captured` with verified-zero backing objects; per-venue prefix re-verification runs
      IMMEDIATELY before each delete inside the same tool run (delete-safety §phantom path; prefix_tpls must cover the
      glued shape). Use the existing IS/MTDS reconcile tooling — never a hand-rolled index rewrite. Evidence: per-venue
      before/after row counts. (repos: instruments-service, market-tick-data-service)
- [ ] [DATA] P0. 4. **Re-retire `dex_pools` legacy rows (454,014)** with the shipped retirement tool; record count;
      gate on todo 2 landing first so it cannot re-regrow. (repo: market-tick-data-service)
- [ ] [DATA] P0. 5. **Migrate Class-B Solana glued objects to canonical.** Bounded (hundreds of objects): UTL
      `gcs_copy_object` to `venue={BARE}/chain=SOLANA/...` + canonical filename, re-key the manifest rows, then delete
      legacy objects (reversibility-qualified: verify `gcs_bucket_soft_delete_retention_seconds() >= 604800` first;
      content-equality proof per copied object). SOLBLAZE-SOLANA rows: verify backing objects under the vocabulary the
      writer actually emits before verdict — purge-as-phantom only on a confirmed-absent probe. (repos:
      instruments-service, market-tick-data-service)
- [ ] [DATA] P1. 6. **Purge blanket perp_funding/derivative_ticker honest-absence stamps on non-perp defi venues**
      (empty_confirmed/expected_unattempted rows on LST/DEX/lending venues that structurally cannot have perp data) AND
      root-fix the expected-universe seeder / capability declaration so they don't reseed. KEEP: carry-basis 6-venue
      rows (operator-accepted), HYPERLIQUID/EXTENDED/LIGHTER perp rows (todo 13). (repos: unified-api-contracts,
      instruments-service)
- [ ] [INFRA] P0. 7. **Launch the N5r/N6r projection VM** (`deployment-service/scripts/vm/
      launch-defi-manifest-projection-vm.sh`, shipped @99b46b9f2d) — no defi rebuild VM is running (verified 2026-08-21,
      GCE list), so the 2026-08-10 blocker is clear. Verify STARTED + progress + terminal state; record the swap
      plan-mode ADD/REMOVE delta here and in the owning issue doc. (repo: deployment-service)
- [ ] [SCRIPT] P0. 8. **Drain-gate + apply + post-verify the canon-swap** (`--drain-gate` → snapshot →
      `--apply-prod --confirm-prod-write` on the VM) per
      /plans/active/issues/defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md todo (e) — same safety
      construction (snapshot rollback path, stale_remaining=0, canon_missing=0, no captured→failed mass flip). Sequence
      AFTER todos 3-5 manifest mutations complete (drain requires quiet index). Flip the issue doc's checkbox with the
      same evidence. (repo: market-tick-data-service)
- [ ] [SCRIPT] P0. 9. **Regenerate the honest-coverage rollup + verify the panel clean.** Re-run
      `measure_honest_coverage.py` (or trigger its nightly job) post-mutations; re-derive
      `/data-status/distinct-values/defi` via the production functions; verify: zero glued `PROTOCOL-CHAIN` venue
      values, zero `dex_pools`, single-cased instrument_types, no phantom venues. Record the before/after distinct
      counts (108 venues → target ≤ ~70 canonical). (repos: instruments-service, deployment-api)
- [ ] [SCRIPT] P1. 10. **Blank/None instrument_type diagnosis** (5,620,899 blank across 71 venues + 3,296 None across
      16): classify by (venue, data_type) writer, decide per-class backfill-or-accept, execute the clear cases. (repos:
      market-tick-data-service, instruments-service)
- [ ] [SCRIPT] P2. 11. **Consumer alignment residuals**: MDPS `_DEFI_DEX_VENUE_SEGMENTS` hand-maintained legacy
      combined-form literals (orchestration_scanner.py:88-113) — remove once GCS carries no combined-form objects;
      MTDS preflight combined-form vocabulary (preflight.py:292-296) — verify against post-swap manifest;
      optional defensive fold in measure_honest_coverage. (repos: market-data-processing-service,
      market-tick-data-service, instruments-service)
- [ ] [SCRIPT] P2. 12. **`rate_indices` (25,478 rows) migration to `lending_indices`** — same treatment class as
      dex_pools; verify content vs canonical twin first. (repo: market-tick-data-service)
- [ ] [OPERATOR] P2. 13. **Boundary disposition**: HYPERLIQUID/ASTER/EXTENDED/LIGHTER perp rows + the 4 `*-FUTURES`
      carry-basis venues remain visible in the DeFi distinct values. SSOT classes on-chain perp CLOBs as cefi, but the
      defi-bucket carry-basis home is operator-accepted and live-read. Decide: accept + register as expected exceptions
      (badge canonical, document) vs re-home the corpus to the cefi bucket (large migration). Until ruled, they stay.
- [ ] [SCRIPT] P2. 14. **`dex_swaps` → `dex_pool_swaps` content migration** (3.46M rows, real legacy-only content) —
      execute per /plans/active/issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md under its
      five-part proof gating; not a blanket rename. (repo: market-tick-data-service)
- [ ] [SCRIPT] P2. 15. **Post-phase codex audit**: update defi-canonical-naming-ssot (phantom-registration class,
      Solana double-glue gotcha), update/flip the owned checkboxes in the related issue docs, fix any doc that misled
      during this work. (repo: unified-trading-pm)

## Progress Log

- **2026-08-21 ~15:15 London (todos 1+2 CODE-COMPLETE, ship pending)** — mtds@d188fb2e (LOCAL commit, 10 files
  +557/-29; NOT yet on LDR — quickmerge dirty-deps-blocked, see choke point below). Root causes: (1)
  `_lending_grain.py:141-145` `_PROTOCOL_TO_CANONICAL_VENUE` mapped kamino_lending/solend/marginfi to GLUED
  `X-SOLANA` venues — feeds risk_params/lending_indices handlers; `write_defi_rows`'s `build_canonical_instrument_id`
  glues AGAIN → double-glued path+id; fixed to bare. (2) `solana_lst_archival.py:737,757` SOLBLAZE-SOLANA → bare
  SOLBLAZE. (3) `canonical_write.py:85` `_normalize_venue` docstring falsely claimed glue-stripping — corrected. (4)
  NEW `_rebuild_defi_retired_guard.py` wired into `rebuild_defi_manifest.py` scan: skips RETIRED
  `dex_pools` (dex_swaps deliberately EXCLUDED — real content) + double-glued-id detector via UAC
  `split_glued_venue_chain`. 18 new/updated tests. QG: own tests green; 1 fail + 1 collection error from unrelated
  same-day peer commit f7cdd18b (sports registry / pipeline_e2e_check) — peer sessions are actively shipping
  fixes/skip-marks for exactly those.
- **2026-08-21 ~15:15 London (execution state)** — Todo 3 purge apply RUNNING (Kleene-mask fix applied to
  `purge_evm_glued_phantom_venue_defi_rows_2026_08_21.py` — non-Kleene or_/and_ nulled the whole mask on NULL-chain
  rows; consolidator cron PAUSED for the write, resume after terminal verdict). Todo 7 projection VM launch attempt 2
  ABORTED at the tarball-freshness gate (dirty UAC checkout). **Single choke point: co-occupant sessions' uncommitted
  WIP in slot-3 UAC (`venue_instrument_type_axis.py`, actively being QG'd by its owner) + UTL (`ledger/run_writer.py`)
  blocks ALL of: MTDS ship (d188fb2e), IS seeder-fix ship, deployment-service launcher ship, and the VM tarball
  publish.** Dep-clean watcher armed (60s poll, 45min cap) → on fire: relaunch VM + retry all three quickmerges.
  Purge agent also left `scripts/one_offs/rekey_solana_glued_venue_defi_rows_2026_08_21.py` (task-5 manifest re-key,
  untracked) — run after task-3 completes + copies verified.

- **2026-08-21 (slot 3, interactive + /autonomous)** — Plan created from a 4-agent live census (manifest census /
  distinct-values trace / plans census / UAC+consumer audit). Key numbers in § Evidence base. Census artifacts in the
  session scratchpad (`venue_census.csv`, `datatype_census.csv`, `instrumenttype_census.csv`, `chain_census.csv`,
  `perp_census.csv`, `defi_distinct_values_result.json`). VM fleet check: no defi rebuild VM running; canon-swap
  unblocked. Operator rulings recorded in the banner. perp_funding vs derivative_ticker settled as NOT-duplicates
  (code-verified; see banner).
- **2026-08-21 ~14:00Z (todo 6 root-fix half)** — Root cause of the blanket perp stamps FOUND + half-shipped. (1)
  Primary: `instruments-service/scripts/enumerate_expected_universe.py::_yield_v2_defi_pre_launch_rows` Class-2 loop
  cross-joined every `PROTOCOL_LAUNCH_DATES` entry (126 chain-protocol tuples) × ALL defi data_types incl.
  perp_funding/derivative_ticker with ZERO capability check. (2) Secondary: UAC
  `market_data_categories.py::valid_data_types_for_venue_instrument_type` unmapped-protocol fallback returned the
  cross-protocol UNION, leaking perp_funding via the `spot_pair` union — **fix SHIPPED
  unified-api-contracts@4b06013aea** (defi-scoped exclusion + 2 tests; QG 13445 passed, 2 pre-existing unrelated
  fails). IS seeder fix (capability-derived `_defi_perp_capable_protocols()` gate + 2 tests) is code-complete,
  QG-passed locally, but quickmerge Stage-1 dep validation is HARD BLOCKED: two unrelated peer sessions hold
  uncommitted WIP in this slot's UAC (`venue_instrument_type_axis.py` DERIBIT fix) + UTL (`ledger/run_writer.py`)
  checkouts — PROTECTed per liveness rule; re-attempt the IS quickmerge once peers land. Stops-seeding population: 71
  of 72 protocols × chains × {perp_funding, derivative_ticker} (ASTER kept — capability-declared; HYPERLIQUID /
  EXTENDED / LIGHTER untouched by construction). Reverse finding (report-only): `DATA_TYPES_BY_ASSET_GROUP["defi"]`
  declares perp_funding/derivative_ticker but no defi-axis venue capability produces them — inert axis declarations,
  belongs to the b21/orthogonality thread.
- **2026-08-21 ~14:00Z (in-flight)** — Todo 3 phantom purge forward-apply RUNNING + todo 5 Solana migration copy pass
  2 RUNNING (purge worker, background jobs with wake-loops). Todo 1 writer fix code-complete, QG queued behind the
  saturated host-wide QG governor (Monitor armed). Todo 7 projection VM: first launch attempt FAILED, launcher fix in
  QG, relaunch pending (worker driving).
- **2026-08-21 ~14:40 London — SESSION-LIMIT interruption (resets 16:40 London). RESUME STATE (lossless):** the purge
  and VM sub-agents were API-terminated mid-flight; verified NO orphaned process is mutating the manifest (ps clean;
  the only heavy host processes are a slot-2 peer quickmerge shipping adjacent DeFi handler fixes — it also skip-marks
  `test_defi_prefix_parser_handles_multi_hyphen_protocol_keys`, a pre-existing UAC `parse_defi_venue` multi-hyphen
  failure directly adjacent to this plan's glued-venue scope; see
  `/plans/active/issues/mtds_defi_prefix_parser_multi_hyphen_solana_native_2026_08_21.md`). Per-todo resume state,
  scratch evidence in the session scratchpad: **Todo 3** — dry-run + full-reverify done (`task3_purge_dryrun.log`,
  `task3_full_reverify.log`); forward-apply NOT completed (216-byte `task3_forward_apply.log`): the worker found a
  REAL bug in its pyarrow mask before applying — `pc.equal(chain, "")` on a NULL chain yields null and non-Kleene
  `pc.or_`/`pc.and_` propagate it through the mask; the fix was unverified at termination. Re-verify the mask
  (null-safe: use `pc.is_null` OR Kleene logic) against the dry-run counts BEFORE any apply. **Todo 4** — no evidence
  of execution; not started. **Todo 5** — SOLBLAZE-SOLANA confirmed PHANTOM (absence re-verified across writer
  vocabularies, `task5_solblaze_reverify.log`/`task5_solblaze_absent.csv` → purge rows with todo 3); copy pass 1 done
  (`task5_copy.log`, plan `task5_copy_plan.csv` 142KB), pass 2 started (`task5_copy_pass2.log` 313B) — re-verify copy
  completeness against the plan CSV, then manifest re-key, then retention-qualified legacy deletes. **Todo 1** —
  writer-fix worker ALIVE at interruption: QG queued ~57min behind the saturated host governor (host cap 7, peer-slot
  runs), Monitor armed on the QG log terminal marker; ship + report pending. **Todo 6** — UAC half SHIPPED
  (@4b06013aea); IS half code-complete in the IS working tree, quickmerge dep-gate blocked on peer WIP in UAC
  (`venue_instrument_type_axis.py` et al.) + UTL (`ledger/run_writer.py`) — re-attempt when peers land. **Todo 7** —
  VM NOT launched; launcher fix was in QG at ~98% when the worker was terminated; deployment-service working tree
  holds the fix — verify QG, quickmerge, launch, then todo 8 sequencing (apply only after todos 3-5 mutations land +
  drain gate green).
