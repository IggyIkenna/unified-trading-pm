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
  (codex/02-data/pipeline-mode-partition.md) that requires them to be derived together. The audit report explicitly
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
last_updated: 2026-07-21
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

`codex/02-data/pipeline-mode-partition.md` defines the manifest/GCS partition scheme as SOURCE-AWARE:
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

- [ ] 1. [DATA] P2. Confirm the stale-row hypothesis — read the live YEARN_V3/ETHEREUM/yield_bearing/vault_share_price
      manifest rows' `attempted_at`/`available_at` timestamps and compare against `vault_share_price_handler.py`'s
      git-blame introduction date; if the desynced row predates the handler, this is a stale/orphaned row, not an
      active-write-path bug (repo: market-tick-data-service, scoped manifest read only — no new whole-corpus walk).
- [ ] 2. [DATA] P2. Measure blast radius beyond the single sampled row — scan the defi manifest for any row where
      `pipeline_mode` implies one vendor source (via `pipeline_mode_for_source` reverse-mapping) while the row's own
      `source` column names a different vendor, scoped to YEARN_V3 first then all `vault_share_price`-data_type venues
      (repo: market-tick-data-service).
- [ ] 3. [CODE] P2. Fix `vault_share_price_handler.py` to pass an explicit `source=` on every `record_captured` /
      `record_failed` / `record_zero_rows` call, consistent with the `"onchain_rpc"` already passed to
      `pipeline_mode_for_source` — closing the crosscutting "`source=` required" gap for this handler (repo:
      market-tick-data-service).
- [ ] 4. [DECISION] P2. If todo 1 confirms stale legacy rows (not an active-write bug), rule on remediation: leave the
      legacy row as an accepted historical artifact (annotate the cutover register) vs. a targeted manifest correction
      pass — do not blind-pick; this is manifest-absence/correction semantics territory per the workspace's
      data-pipeline-correctness rule (repo: unified-trading-pm, `codex/02-data/canonical-cutover-register.md`).
- [ ] 5. [DATA] P3. Append F10 to the reconciliation register per the audit's own §9 maintenance-contract note (the
      audit run flagged this as not-yet-registered and deferred it) — repo: unified-trading-pm,
      `codex/02-data/non-canonical-path-inventory.md` or the register doc F10 belongs under.
