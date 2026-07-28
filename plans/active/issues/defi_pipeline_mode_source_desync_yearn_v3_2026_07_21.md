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
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [data-correctness, defi, pipeline-mode, manifest, source-desync, yearn-v3, honest-coverage, vault-share-price]
related: [data_pipeline_reconciliation_defi_2026_07_20]
created: 2026-07-21
last_updated: 2026-07-28
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
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

- [x] 1. [DATA] P2. **DONE 2026-07-28 (slot-4) — NOT stale, active ongoing bug.** Scoped manifest read
      (`read_availability_index` with row-group filters, no new whole-corpus walk) shows the desynced pairing
      (`pipeline_mode=batch_onchain_rpc`, `source=onchain_subgraph`, `row_count=3`) on YEARN_V3/vault_share_price for
      EVERY day from 2026-06-21 through 2026-07-27 (today at read time), `attempted_at` timestamps ranging
      2026-07-22T18:39Z→2026-07-28T04:56Z — all postdate the handler's git-blame introduction
      (`9475e66b`, 2026-05-03T15:01:01Z) by 7+ weeks and are still being written daily. The ORIGINAL sampled row
      (day=2026-04-14) no longer exists in this desynced form — it was superseded on 2026-07-23 by a manifest-rebuild
      pass (`f2e3ad41`, "harden manifest rebuild to route 0-row shards to honest-absence") that backfilled a
      correctly-paired zero-row marker (`batch_onchain_subgraph`/`onchain_subgraph`, row_count=0) for that date. So the
      one row the audit sampled is resolved/superseded, but the bug that PRODUCED that pairing is the handler's own
      live write path and has been firing every single day since — this is an active-write-path bug, not a stale
      legacy row.
- [x] 2. [DATA] P2. **DONE 2026-07-28 (slot-4).** Scanned the full `vault_share_price` data_type (all 5 registered
      protocols, 7,476 manifest rows). Every protocol shows the identical desync: 37 rows each of
      `pipeline_mode=batch_onchain_rpc`+`source=onchain_subgraph` (desynced) vs. 952-2497 correctly-paired
      `batch_onchain_subgraph`+`onchain_subgraph` rows (the rebuilt zero-row markers from todo 1). Total: **185
      desynced rows** (37 × 5) across ETHENA, FRAX, MAKER, MORPHOVAULTS, YEARN_V3 — blast radius is the WHOLE handler,
      not just YEARN_V3, confirming this is one bug in the shared `vault_share_price_handler.py` write path, not a
      per-venue issue.
- [x] 3. [CODE] P2. **DONE 2026-07-28 (slot-4) via `defi_satellite_ao_dispatch_batch1_2026_07_25.md`
      (market-tick-data-service@\<sha\>) — shipped a DIFFERENT value than this todo's suggested `"onchain_rpc"`.**
      Root-caused WHY the handler passed blank `source=`: UAC `SOURCE_PRIORITY[("defi","vault_share_price")]` (
      `_source_priority_data.py:312`) registers **only** `["onchain_subgraph"]` — `is_valid_manifest_source("defi",
      "vault_share_price", "onchain_rpc")` returns `False`. Passing `source="onchain_rpc"` as this todo originally
      suggested would make `ManifestWriter._resolve_and_validate_source` raise `MissingSourceError` on every future
      write — caught + swallowed by `DefiManifestRecorder._emit_captured_add`'s try/except (D10 isolation), silently
      dropping the captured row from the manifest entirely. That is a WORSE regression than today's desynced-but-present
      row (verified live via `is_valid_manifest_source`/`valid_manifest_sources` — see todo 6). Shipped instead: every
      call site now passes `source="onchain_subgraph"` explicitly (the only currently-registered value, identical to
      what UAC's `default_source()` auto-stamp already produced — zero behavior change to written manifest rows),
      satisfying the crosscutting "`source=` required on `record_captured`" rule without introducing a write failure.
      A code comment at the constant's definition documents why `"onchain_rpc"` was NOT used and points here.
- [x] 4. [DECISION] P2. **RESOLVED 2026-07-28 — reframed by todo 1's finding.** Not a stale-legacy-row question (the
      sampled row is gone, superseded by rebuild). The real remediation decision is the UAC registry gap captured in
      NEW todo 6 below — routed there instead of the cutover register.
- [ ] 5. [DATA] P3. Append F10 to the reconciliation register per the audit's own §9 maintenance-contract note (the
      audit run flagged this as not-yet-registered and deferred it) — repo: unified-trading-pm,
      `/codex/02-data/non-canonical-path-inventory.md` or the register doc F10 belongs under.
- [ ] 6. [DATA] P1. **NEW 2026-07-28 (slot-4) — the genuine root-cause fix, cross-repo, needs a UAC-owner/operator
      decision, not done here.** Register `"onchain_rpc"` as a valid manifest source for `("defi",
      "vault_share_price")` in `unified-api-contracts/unified_api_contracts/canonical/crosscutting/_source_priority_data.py:312`
      — currently `["onchain_subgraph"]`, should genuinely reflect the RPC-only `convertToAssets` collection mechanism
      this handler has used since its 2026-05-03 introduction (no subgraph-based vault_share_price collector has ever
      existed in this codebase — grep-verified). Direct precedent: commit `6bf6012a` fixed the mirror-image bug for
      DeFi `mev_events`/FLASHBOTS (handler passed the wrong pipeline_mode string against an ALREADY-correct UAC
      registration; here it's the UAC registration itself that's wrong against an already-correct handler). Open
      decision for whoever picks this up: REPLACE `["onchain_subgraph"]` → `["onchain_rpc"]` outright (my
      recommendation — no genuine second source exists) vs. ADD `"onchain_rpc"` as a second source (would flip
      `source_required()` to `True` for this cell, forcing every future caller — including the 185 already-correct
      `batch_onchain_subgraph` zero-row-marker writers — to pass an explicit source or start raising). Once landed,
      flip `market-tick-data-service`'s `_VAULT_SHARE_PRICE_SOURCE` constant (`vault_share_price_handler.py`) from
      `"onchain_subgraph"` to `"onchain_rpc"` to match. Repos: unified-api-contracts (primary), market-tick-data-service
      (follow-up one-line flip).
