---
doc_type: issue
title:
  "DeFi manifest pipeline_mode<->source desync on YEARN_V3 vault_share_price (pipeline_mode=batch_onchain_rpc,
  source=onchain_subgraph) — breaks the SOURCE-AWARE {mode}_{source} invariant; filed as the audit's own flagged
  follow-up"
summary: >-
  Found by the /data-pipeline-reconciliation defi run (2026-07-20, finding F10,
  data_pipeline_reconciliation_defi_2026_07_20.md §4+§9). The YEARN_V3/ETHEREUM/yield_bearing/vault_share_price manifest
  row sampled on day=2026-04-14 carries pipeline_mode=batch_onchain_rpc but source=onchain_subgraph — the two axes
  disagree on the same row, which breaks the SOURCE-AWARE `{mode}_{source}[_{transport}]` partition scheme
  (/codex/02-data/pipeline-mode-partition.md) that requires them to be derived together. The audit report explicitly
  lists F10 as "not in the register as defi-scoped rows ... flagged as follow-up" (§9) and this repo's task instructed
  filing it as its own issue since the audit run itself did not. A code read of the CURRENT
  market-tick-data-service/cli/handlers/vault_share_price_handler.py shows every record_captured call stamps
  pipeline_mode via the literal `pipeline_mode_for_source("onchain_rpc", ...)` and never passes a `source=` kwarg at all
  (defaults to blank per `DefiManifestRecorder.record_captured`'s `source: str = ""`), which does not by itself produce
  `source=onchain_subgraph` — so the sampled row is most likely a STALE row from a prior collector generation that the
  current RPC-based handler has not reconciled, compounded by the current handler's own separate gap (never stamping
  `source=` explicitly, against the crosscutting "source= is required on record_captured" rule). Both need a
  data-engineering pass; neither was fixed here (docs-hygiene-only task).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [data-correctness, defi, pipeline-mode, manifest, source-desync, yearn-v3, honest-coverage, vault-share-price]
related: [data_pipeline_reconciliation_defi_2026_07_20]
created: 2026-07-21
author: unknown
last_updated: 2026-08-11
archive_exempt: true
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "/data-pipeline-reconciliation defi run 2026-07-20 (finding F10), day=2026-04-14 four-surface sample; filed 2026-07-21
  per the audit's own §9 follow-up flag (not yet its own issue at audit time); code-verified against the current
  market-tick-data-service vault_share_price_handler.py + _defi_manifest.py"
resolved_by:
context_scope:
  [
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/_source_priority_data.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/vault_share_price_handler.py,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/02-data/non-canonical-path-inventory.md,
    /plans/audit/results/data_pipeline_reconciliation_defi_2026_07_20.md,
  ]
---

# DeFi manifest pipeline_mode<->source desync on YEARN_V3 vault_share_price

> **Follow-up filing, not a new discovery.** The reconciliation audit itself already surfaced this as F10 and explicitly
> flagged it as not yet tracked as its own issue (§9: "F10 ... not in the register as defi-scoped rows ... flagged as
> follow-up"). This doc is that follow-up.

## The exact finding (quoted verbatim from the audit)

`data_pipeline_reconciliation_defi_2026_07_20.md` §4 (Typed findings table):

```
| F10 | pipeline_mode↔source desync | MEDIUM | YEARN_V3 row `pipeline_mode=batch_onchain_rpc` but
`source=onchain_subgraph` | S3 | scoped read | NO | breaks SOURCE-AWARE `{mode}_{source}` invariant |
```

Same report, §3 (four-surface shard table, row 5, `day=2026-04-14`):

```
| 5 | YEARN_V3/ETHEREUM/yield_bearing/vault_share_price (canonical spelling) | OK | NOT-READ |
NOTE blank `instrument_id`, rows nan; **pm↔source desync** (`pm=batch_onchain_rpc` src=`onchain_subgraph`) |
OK (6 rows) | — |
```

Same report, §9 (Inventory reconcile — "Reality→register (new)"):

> "F10 (pipeline_mode↔source desync) and F6 (expected-universe `pool` vs writer `solana_amm_pool` vocab desync ...) are
> not in the register as defi-scoped rows; both should be appended by the register's maintenance contract (not done in
> this read-only run — flagged as follow-up)."

(F6 already got its own issue doc — `defi_expected_universe_solana_pool_instrument_type_vocab_desync_2026_07_20.md`. F10
had not, until this doc.)

## Why it matters

`/codex/02-data/pipeline-mode-partition.md` defines the manifest/GCS partition scheme as SOURCE-AWARE:
`{mode}_{source}[_{transport}]` — `pipeline_mode` is meant to be _derived from_ the vendor `source`
(`pipeline_mode_for_source(source, mode)`), not an independent field. A row where `pipeline_mode=batch_onchain_rpc` but
`source=onchain_subgraph` means the two axes were stamped from **different, disagreeing inputs on the same manifest
row** — exactly the invariant the partition scheme exists to prevent. This is a MEDIUM-severity manifest data-quality
defect (same class as F6, F9 — see the audit's §10 verdict: "two manifest data-quality defects (F6 vocab-desync, F10
pm↔source, plus F9 row_count)"), not a fleet-blocker: `delete_elig=NO`, single-day/single-venue sample, not a red
quality gate.

## Code-verified lead (found while filing, not yet root-caused to completion)

Read `market-tick-data-service/market_tick_data_service/cli/handlers/vault_share_price_handler.py` (the current YEARN_V3
vault-share-price collector) end-to-end:

- Every `record_captured` / `record_failed` / `record_zero_rows` call in that file stamps
  `pipeline_mode=pipeline_mode_for_source("onchain_rpc", Mode(self.runtime.mode.value))` — a **literal hardcoded
  `"onchain_rpc"`** string, at lines 299, 307, 588, 610, 618 (`record_failed`/`record_zero_rows`) and 588
  (`record_captured`, the one that emits captured rows). This matches the audit's observed
  `pipeline_mode= batch_onchain_rpc` half of the row.
- The single `record_captured` call in this file (line 581-589) does **NOT** pass a `source=` kwarg at all.
  `DefiManifestRecorder.record_captured` (`_defi_manifest.py:406-417`) defaults `source: str = ""` — it flows straight
  through `_emit_captured_add` → `self._writer.add(..., source=source)` with **no fallback/derivation to
  `"onchain_subgraph"`** anywhere in that class. So the CURRENT handler code, as written today, cannot itself be the
  origin of a `source=onchain_subgraph` value on a row it writes — it would write blank `source=""` instead.
- Conclusion (not yet confirmed against the live manifest, hence a todo below, not a closed root cause): the sampled row
  is most likely a **stale row from a prior collector generation** (an older generic on-chain-subgraph-based collector
  that predates this dedicated RPC-based `vault_share_price_handler.py`), never reconciled/overwritten since.
  Separately, and regardless of that: the CURRENT handler's own failure to pass `source=` explicitly is itself a live
  gap against the crosscutting rule "`source=` is required on `record_captured`" (CLAUDE.md § data/manifest domain) — it
  should be stamping an explicit vendor source (e.g. `"onchain_rpc"`, matching the pipeline_mode) rather than relying on
  the blank default.

## Todos

- [x] 1. [DATA] P2. **DONE 2026-07-28 (slot-4).** Confirmed/REFUTED via a read-only scan against the LIVE prod defi
      manifest (`market-tick-data-service@50fb82cf`,
      `scripts/one_offs/defi_vault_share_price_pipeline_mode_source_desync_scan_2026_07_28.py`, using
      `read_availability_index(bucket, columns=[...], filters=[("data_type","==","vault_share_price")])` — one
      predicate-pushdown read, no new whole-corpus walk). **Result: the stale-row hypothesis is REFUTED.**
      YEARN_V3/ETHEREUM desync rows' `attempted_at` values run through 2026-07-28T01:11:07Z — POSTDATING
      `vault_share_price_handler.py`'s git-blame introduction (commit `9475e66b`, 2026-05-03T15:01:01Z) — so these are
      NOT legacy/orphaned rows from a prior collector generation; they are being written by the CURRENT RPC handler
      right now. Root cause (verified live against the UAC registry, not assumed):
      `SOURCE_PRIORITY[('defi',     'vault_share_price')] = ['onchain_subgraph']` is the ONLY registered external source
      for this cell (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/_source_priority_data.py:312`),
      so `default_source()`/`source_required()`
      (`unified_api_contracts.canonical.crosscutting._source_priority_provenance`) auto-stamp
      `source='onchain_subgraph'` on EVERY write to this cell — before AND after todo 3's fix below — regardless of
      whether the row was actually fetched via subgraph or RPC. The `pipeline_mode<->source` combination is a STRUCTURAL
      consequence of the single-source write-time provenance gate, not evidence any specific row is wrong. Full per-row
      detail in the plan's flip note (`plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md`).
- [x] 2. [DATA] P2. **DONE 2026-07-28 (slot-4), same scan as todo 1.** Blast radius: 7,476 total `vault_share_price`
      rows in the manifest; **185 desync rows (2.5%)**, spread EVENLY across **5 venues** (37 rows each) — ETHENA, FRAX,
      MAKER, MORPHOVAULTS, YEARN_V3 — all sharing the identical
      `(pipeline_mode=batch_onchain_rpc,     source=onchain_subgraph)` pair. All 5 venues are written by the same
      `vault_share_price_handler.py` (the vault registry's 5 protocol groups), confirming this is a
      handler-wide/cell-wide structural artifact, not a YEARN_V3-specific bug.
- [x] 3. [CODE] P2. Fix `vault_share_price_handler.py` to pass an explicit `source=` on every `record_captured` /
      `record_failed` / `record_zero_rows` call, consistent with the `"onchain_rpc"` already passed to
      `pipeline_mode_for_source` — closing the crosscutting "`source=` required" gap for this handler (repo:
      market-tick-data-service). — already covered by defi_satellite_ao_dispatch_batch1_2026_07_25.md (see that doc for
      execution).
- [x] 4. [DECISION] P2. **RESOLVED 2026-07-30, differently than either option this todo posed — not a second-source
      addition.** `unified-api-contracts@8c506575` ("fix(defi): register onchain_rpc as vault_share_price's true
      SOURCE_PRIORITY source") swapped `SOURCE_PRIORITY[('defi','vault_share_price')]` from `["onchain_subgraph"]` to
      `["onchain_rpc"]` — a single-source RENAME to match the handler's actual RPC-only collection mechanism, not the
      "register a second source" design call this todo originally posed (that path was overtaken by events: the Phase-4
      writer invariant, `d7b3ed7d` 2026-07-26, started hard-rejecting the pipeline_mode<->source mismatch, silently
      dropping every ETHENA/FRAX/MAKER/MORPHOVAULTS/YEARN_V3 captured manifest row from ~2026-07-28 onward, forcing a
      same-day fix rather than a deferred multi-source design decision). Verified live 2026-08-08 against
      `unified-api-contracts/unified_api_contracts/canonical/crosscutting/_source_priority_data.py:344-357` — the code
      comment there cites this exact todo and confirms the rename rationale.
- [x] 5. [DATA] P3. **DONE 2026-07-26** — appended to `/codex/02-data/canonical-cutover-register.md` §2 (line 136) via
      `defi_satellite_ao_dispatch_batch2_2026_07_26.md` (`unified-trading-pm@0c4172c31`), closing the audit's own §9
      maintenance-contract follow-up flag. — repo: unified-trading-pm.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - todo 4 is an explicit [DECISION] on adding a second
  SOURCE_PRIORITY source (multi-source cell + backfill call); todo 5 targets codex
- **context-scout 2026-08-01**: populated context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries, was 6) — dropped the archived batch1 dispatch doc
  (its only cited todo, #3, is already shipped); remaining set covers the two still-open items (todo 4 [DECISION], todo
  5 register-append).
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA valid (prior verdict re-affirmed) —
  todo 4 remains an explicit `[DECISION]` on adding a second SOURCE_PRIORITY source (multi-source cell + backfill on
  7,476 existing rows); todo 5 is a minor P3 that doesn't outweigh it. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — re-confirmed independently; no content change
  since the 2026-08-04 audit (context-scout metadata only, per git log). Todo 4 remains an explicit `[DECISION]` on a
  second SOURCE_PRIORITY source; todo 5 (register-append, P3) doesn't outweigh it. Doc stays `assigned_vm: NA`.
- **2026-08-08 (doc-hygiene, digest close-out)**: Closed todo 4 — already resolved by `unified-api-contracts@8c506575`
  (2026-07-30), a single-source rename of `SOURCE_PRIORITY[('defi','vault_share_price')]` to `["onchain_rpc"]`, not a
  second-source addition. Confirmed live against the current file (`_source_priority_data.py:344-357`) before flipping.
  Todo 5 (F10 register-append) left untouched — genuinely still open, out of this pass's scope.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA-STALE (already-duplicated), not reclassified —
  the sole remaining open item (todo 5, "Append F10 to the reconciliation register") is ALREADY an open todo in the
  active `defi_satellite_ao_dispatch_batch10_2026_08_06.md` (`status: active`), whose own text reads "Sync a stale
  checkbox: `defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md`'s Todo 5 ... is unchecked but the substance
  already shipped 2026-07-26." Reclassifying this doc now would open a second, redundant dispatch path the moment
  batch10 executes its own copy of the same fix. Correct owner is batch10; this doc's checkbox stays as the citation
  anchor per this corpus's own convention. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA-STALE (already-duplicated) re-confirmed — batch10's own
  citation todo (lines 154-158) still active and unshipped; also independently re-confirmed by
  `defi_satellite_ao_dispatch_batch11_2026_08_09.md`'s same-day conflict-check. Doc stays `assigned_vm: NA`.
- **2026-08-11 (slot-7, batch10 item 7)**: Todo 5 flipped `[x]` — F10 register-append substance shipped 2026-07-26
  (`unified-trading-pm@0c4172c31`, register §2 line 136), verified live before flipping. `archive_exempt: true` set as
  the flip-then-mv bridge (`check_archive_candidates_only_mode_no_flip_then_mv_exemption_2026_08_09.md`) — the `git mv`
  archival to `plans/archive/issues/` follows in the immediately-next commit.
