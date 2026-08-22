---
doc_type: issue
title: "TradFi post-full-backfill reconciliation (2026-08-17) — residual findings not fixed inline"
summary: >-
  Findings from the tradfi_phase_d_terminal_gate_2026_07_24.md P1 post-full-backfill reconciliation run
  (data_pipeline_reconciliation_tradfi_2026_08_17.md / _candles_2026_08_17.md) that are NOT already tracked in an
  existing plan/issue doc and were not small+clear enough to fix inline within this run. Two of the 2026-07-24 run's
  three escalated findings are now resolved (ICE/KRX provenance mis-stamp, FX manifest instrument_id 0%->72.4%); this
  doc tracks what remains: the FX ohlcv_24h provenance-mislabel residual (unchanged since 07-24), the FX manifest
  "ticks"-literal residual (983->670, not zero), continued `_quarantine/` growth (>=400K->>=500K, capped), a new
  unregistered `_migration_backup_2026_07_25/` location, a small multi-token-equity-symbol id gap, a low-severity
  `instrument_type=UNKNOWN` census entry, and phantom-audit staleness (count grew 10x, 18 days stale). None of these
  rise to data-correctness/cross-repo/SSOT-contradiction severity individually.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm, unified-api-contracts]
scope: [engineer]
tags: [reconciliation, tradfi, manifest, provenance, quarantine, phantom-audit]
related: [tradfi_phase_d_terminal_gate_2026_07_24, tradfi_fx_provenance_and_manifest_id_defects_2026_07_24]
created: 2026-08-17
author: data-pipeline-reconciliation (tradfi post-full-backfill checkpoint)
priority: P2
parent_epic: security_and_cross_cutting_master
source:
  "Filed as the required issue-doc half of tradfi_phase_d_terminal_gate_2026_07_24.md's P1 todo
  ('Post-full-backfill reconciliation RUN checkpoint') — see
  plans/audit/results/data_pipeline_reconciliation_tradfi_2026_08_17.md and its candles-layer sibling for the full
  evidence and methodology behind each item below."
execution_scope: local-only
resolved_by:
drift_direction: advance-docs
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
context_scope:
  [
    /plans/audit/results/data_pipeline_reconciliation_tradfi_2026_08_17.md,
    /plans/audit/results/data_pipeline_reconciliation_tradfi_candles_2026_08_17.md,
    /plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md,
    /plans/archive/issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch16_2026_08_17.md,
    /codex/02-data/non-canonical-path-inventory.md,
  ]
---

# TradFi post-full-backfill reconciliation (2026-08-17) — residual findings

## What I found

Full evidence and methodology in `plans/audit/results/data_pipeline_reconciliation_tradfi_2026_08_17.md` (raw-tick)
and `..._candles_2026_08_17.md`. Summary of what's tracked here (items already covered by an existing plan/issue —
e.g. the chain-bundle sampler reverse-derivation gap, `tradfi_chain_bundle_reverse_derivation_ao_dispatch_2026_08_16.md`
— are NOT duplicated in this doc):

1. **FX `ohlcv_24h` provenance mis-stamp — unchanged since 2026-07-24.** 28.1% of captured FX `ohlcv_24h` rows
   (1,008/3,591) still stamp `source=databento` against the SSOT's Yahoo-only routing for FX daily bars. The sibling
   ICE/KRX mis-stamp from the same 07-24 finding is now fully resolved (0 databento rows on either venue's daily
   cell) — FX is the one piece not yet fixed.
2. **FX manifest `instrument_id` "ticks"-literal residual.** The 2026-08-04 backfill
   (`market-tick-data-service@c86016f6`) raised well-formed FX manifest ids from 0% to 72.4%, but 670 rows (down from
   983 on 07-24, not zero) still carry the literal `"ticks"` bundle-filename leak instead of a real
   `FX:SPOT_PAIR:XXX-USD` id.
3. **`_quarantine/` continues growing, still not uncapped-measured.** 146,288 (07-21) -> >=400,000 (07-24) ->
   >=500,000 capped (08-17, this run's 500K enumeration cap was hit in 41s without exhausting the 60s time budget,
   meaning the true population is materially above 500K). Three consecutive reconciliation runs have re-flagged this
   without an uncapped measurement or feeder-process investigation ever happening.
4. **New unregistered top-level location `_migration_backup_2026_07_25/`** — 20,000+ objects / 2.35+ GB capped (true
   size likely higher), not in `/codex/02-data/non-canonical-path-inventory.md`. Provenance not investigated this
   run.
5. **Multi-token equity symbols with an embedded space in the id.** `NYSE:EQUITY:BRK B-USD` (19 rows) and
   `NYSE:EQUITY:BF B-USD` (19 rows) — legitimate Class-B share symbols, but the canonical id grammar has no defined
   join convention for a multi-token wire symbol. 38 rows measured; other venues not exhaustively checked.
6. **New `instrument_type=UNKNOWN` census entry** — 4,142 rows, all `venue=CME, data_type=ohlcv_1m,
   capture_status=attempted_failed`. No captured data affected; not seen in the 07-24 non-standard-value census.
7. **`phantom_audit_latest.json` count grew 10x and is stale.** 1,635 @2026-07-14 (07-24 report) -> 16,997
   @2026-07-30 (this run), now 18 days stale as of 2026-08-17. Not itself evidence of a live defect (a published,
   not-re-derived number), but the growth + staleness together warrant a fresh run.
8. **`venue=BARCHART` vocabulary residual, still unchanged 4 consecutive reconciliation runs.** 9,119
   `empty_confirmed` rows, removed from `VENUES_BY_ASSET_GROUP["tradfi"]` 2026-06-24, `max(attempted_at)=2026-07-07`
   (not re-touched since), still present in the manifest vocabulary.
9. **The `manifest_dedup_2026_07_10/` register-patch line is still unapplied after 3 reconciliation runs flagging
   it** (07-21, 07-24, 08-17 — see the raw-tick report's Phase 2 register-patch stanza).

## Why it matters

None of these individually rise to the "big finding" / operator-notify bar (data-correctness / cross-repo / SSOT
contradiction) — they're all small-volume, single-repo, already-diagnosed-enough-to-act-on items. Collectively they
represent the genuinely-remaining residual after this checkpoint run, distinct from the two already-tracked open
items (chain-bundle sampler reverse-derivation, `tradfi_chain_bundle_reverse_derivation_ao_dispatch_2026_08_16.md`;
the sector/micro-contract GCS convergence migration, same doc's sibling todo) that this run deliberately did not
duplicate.

## Recommended decision

No operator decision needed for items 1, 2, 4, 5, 6, 8, 9 (bounded, worker-determinable engineering fixes). Item 3
(`_quarantine/` growth) needs a VM-scale uncapped measurement before any disposition beyond `unknown` — a normal
engineering-latitude choice, not an authority-level call. Item 7 is a one-line "re-run the audit" action.

## Todos

- [x] ✅ [DATA] P1. EXTRACTED 2026-08-17 (na-eligibility-audit, tradfi tranche, dispatch agt-071b5c) →
      `tradfi_satellite_ao_dispatch_batch16_2026_08_17.md` Todo 1. Root-cause + fix the FX `ohlcv_24h`
      `source=databento` mis-stamping — the remaining piece of the 2026-07-24 G2 finding after ICE/KRX were already
      fixed. Re-stamp the 1,008 affected historical rows once fixed. (repo: market-tick-data-service)
- [x] ✅ [DATA] P2. EXTRACTED 2026-08-17 (na-eligibility-audit, tradfi tranche, dispatch agt-071b5c) →
      `tradfi_satellite_ao_dispatch_batch16_2026_08_17.md` Todo 2. Finish the FX manifest `instrument_id`
      "ticks"-literal backfill residual (670 rows) — the 2026-08-04 restamp (`market-tick-data-service@c86016f6`) did
      not cover this sub-population; extend it or run a targeted follow-up CAS-apply. (repo: market-tick-data-service)
- [x] ✅ [DATA] P1. EXTRACTED 2026-08-17 (na-eligibility-audit, tradfi tranche, dispatch agt-071b5c) →
      `tradfi_satellite_ao_dispatch_batch16_2026_08_17.md` Todo 3. Re-measure `_quarantine/` with an uncapped,
      time-boxed VM walk (heavy-I/O rule — VM, not interactive) and identify the feeding process; either drain it
      faster or confirm the growth is a bounded, expected side-effect. (repo: market-tick-data-service or
      deployment-service)
- [x] ✅ [DOCS] P3. EXTRACTED 2026-08-17 (na-eligibility-audit, tradfi tranche, dispatch agt-071b5c) →
      `tradfi_satellite_ao_dispatch_batch16_2026_08_17.md` Todo 4. Confirm the provenance of
      `_migration_backup_2026_07_25/` and add a disposition line to `/codex/02-data/non-canonical-path-inventory.md`
      (register-patch stanza already drafted in `data_pipeline_reconciliation_tradfi_2026_08_17.md` Phase 2). (repo:
      unified-trading-pm)
- [ ] [DATA] P3. Apply the dot-join convention for multi-token equity symbols (e.g. `BRK B` -> `BRK.B`) and re-stamp
      the affected rows (`NYSE:EQUITY:BRK B-USD` / `BF B-USD`, 38 rows measured). Per D132 ruling (2026-08-22): dot-join
      — matches standard ticker convention; zero corpus precedent existed, this was the operator's naming call.
      (repo: unified-api-contracts + market-tick-data-service)
- [x] ✅ [DATA] P3. EXTRACTED 2026-08-17 (na-eligibility-audit, tradfi tranche, dispatch agt-071b5c) →
      `tradfi_satellite_ao_dispatch_batch16_2026_08_17.md` Todo 5. Investigate the 4,142
      `venue=CME, instrument_type=UNKNOWN, data_type=ohlcv_1m, attempted_failed` rows. (repo:
      market-tick-data-service)
- [x] ✅ [DATA] P3. EXTRACTED 2026-08-17 (na-eligibility-audit, tradfi tranche, dispatch agt-071b5c) →
      `tradfi_satellite_ao_dispatch_batch16_2026_08_17.md` Todo 6. Run a fresh tradfi phantom audit — published
      count is 18 days stale and grew 10x since the last measurement. (repo: market-tick-data-service)
- [x] ✅ [DOCS] P3. EXTRACTED 2026-08-17 (na-eligibility-audit, tradfi tranche, dispatch agt-071b5c) →
      `tradfi_satellite_ao_dispatch_batch16_2026_08_17.md` Todo 7. Clean up the `venue=BARCHART` residual (9,119
      `empty_confirmed` rows, unchanged 4 consecutive reconciliation runs since removal from the vocabulary
      2026-06-24). (repo: market-tick-data-service or unified-api-contracts)
- [x] ✅ [DOCS] P3. EXTRACTED 2026-08-17 (na-eligibility-audit, tradfi tranche, dispatch agt-071b5c) →
      `tradfi_satellite_ao_dispatch_batch16_2026_08_17.md` Todo 8. Apply the `manifest_dedup_2026_07_10/`
      register-patch line to `/codex/02-data/non-canonical-path-inventory.md` — proposed 07-21, re-flagged 07-24,
      re-flagged again 08-17, never applied. (repo: unified-trading-pm)

## Progress Log

- **2026-08-17**: filed by the `/data-pipeline-reconciliation --asset-group tradfi` post-full-backfill checkpoint run
  (`tradfi_phase_d_terminal_gate_2026_07_24.md` P1). Two doc-coverage findings (venue=FRED undocumented, the ratified
  CME/CBOE null-instrument_id chain-bundle carve-out) were fixed inline in
  `.claude/skills/data-pipeline-reconciliation/reference-tradfi.md` in the same commit as this doc, not tracked here.
- **na-eligibility-audit 2026-08-17** (tradfi tranche, dispatch agt-071b5c) [body-hash:ddfe2c490493c7bc]: RECLASSIFY, per-todo split. 8 of this
  doc's 9 todos are bounded/worker-determinable engineering fixes (root-cause+fix / mechanical backfill-extend /
  documentation+register-patch / diagnostic-with-clear-target-population / re-run-existing-tooling shapes, several
  with precedent already shipped this week on the sibling ICE/KRX finding or the 2026-08-04 restamp) — conflict-checked
  clean (grepped `plans/active/*.md` + `issues/*.md` for every item's distinctive terms; the 2 near-hits found,
  `tradfi_phase_d_terminal_gate_2026_07_24.md` and `tradfi_satellite_ao_dispatch_batch13_2026_08_13.md`'s KRW-USD
  `pipeline_mode` restamp, are confirmed different ground on inspection — the former is this doc's own parent
  pointing back here, the latter is a different axis (`pipeline_mode`/storage-location, not `source=`-field
  provenance) already-done for one FX pair only, explicitly scoped out of widening to others) — extracted to
  `tradfi_satellite_ao_dispatch_batch16_2026_08_17.md` Todos 1-8 (see checkboxes above). **Todo 5 (multi-token equity
  symbol join convention, `BRK B` -> `BRK-B`/`BRK.B`) stays KEEP-NA, deliberately NOT extracted despite this doc's own
  "Recommended decision" section listing it as bounded** — picking between undecided naming conventions with no
  existing corpus precedent (checked: no multi-token-ticker convention exists anywhere in codex/UAC) is a genuine
  design call per the AO-dispatch-scope-eligibility bar, not a worker-determinable fact; the source doc's own
  optimism on this one item is not taken at face value per this skill's explicit "stay skeptical of a todo's own
  self-framing" guidance. Doc stays `assigned_vm: NA` for this remaining item (per-todo split — the doc itself is
  never whole-doc-reclassified when a mix like this exists).
- **context-scout 2026-08-17**: populated context_scope (5 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **2026-08-22 — ruling D132 (Share-class symbol convention)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Dot-join — matches standard ticker convention; zero corpus precedent exists, so this
  is the operator's naming call. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
