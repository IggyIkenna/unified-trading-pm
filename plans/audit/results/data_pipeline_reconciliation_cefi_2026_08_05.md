---
doc_type: audit-result
title: "Data-pipeline reconciliation — cefi (2026-08-05), raw-tick layer, Tier-1 only"
summary: >-
  Operator-requested spot-check answering three questions: are cefi GCS paths canonical, can every declared shard
  dimension genuinely produce data (vs. orphaned/dead declarations), and are the honest-coverage numbers correct. Tier-1
  only (Phase 0 + census, in-session, no VM) — the full path-structure oracle sweep and Tier-2 per-datapoint validation
  were NOT run this pass; see §5 for exactly what's covered vs. not. Headline: both cefi buckets healthy (consolidator
  not locked, fresh runs, no row-count regression). The venue/instrument_type/data_type distinct-value census against
  UAC's canonical declarations found ZERO canonical venues with no real data ever (no orphaned DECLARATIONS) but did
  find the inverse — manifest values not in the canonical declaration — including an ACTIVE regression: bare "OKX" had
  5,225 fresh `attempted_failed` rows (batch_tardis, every MVP data_type) despite `unified-api-contracts@d67a226f`
  removing it from the registry the day before. Root-caused to a hardcoded `venues.extend(["OKX", "COINBASE-CDE"])`
  literal in `market-tick-data-service`'s own orchestrator (`engine/orchestrator/__init__.py:365`), independent of and
  never updated when the UAC fix shipped — fixed + regression-tested this run, verified correct, but NOT YET SHIPPED: ~9
  quickmerge-track `quality-gates.sh` attempts hit five unrelated pre-existing/concurrent-slot failures in this
  heavily-multi-tenant checkout (three reconciled as duplicates of already-landed fixes discovered via a stash-pop
  conflict this run also had to safely resolve; two are other slots' active in-progress work, correctly left untouched)
  — see §3 for the full account. Separately confirmed a genuine orphaned DECLARATION: `BINANCE-DELIVERY` is UAC-declared
  for cefi but has captured ZERO real rows across all 5 attempted data_types (582 attempted_failed/empty_confirmed,
  never `captured`) and is missing from `VENUE_DATA_TYPE_CAPABILITIES` entirely. Also found the inverse gap —
  `COINBASE-FUTURES`/`EXTENDED-STARKNET`/ `LIGHTER-ZKSYNC` write real `ohlcv_1m` data (1,081-1,700 rows each) that isn't
  in their declared capability set, meaning the registry under-declares real capture activity for those three.
  Honest-coverage formula verified against a freshly re-triggered rollup — `by_chain.cefi` clean.
  `phantom_audit_latest.json` is 9 days stale relative to this run (generated 2026-07-27) — a freshness gap, not re-run
  here (single-walk discipline).
status: partial
nature: record
asset_group: [cefi]
stage: [data]
repos:
  [unified-trading-pm, unified-api-contracts, unified-trading-library, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags:
  [reconciliation, canonicalisation, census, cefi, orphaned-shard-dimension, honest-coverage, bare-okx, monitoring-gap]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    honest-coverage-model,
    data_pipeline_reconciliation_cefi_2026_07_24,
    cefi_bare_okx_venue_removal_2026_08_04,
    defi_cefi_venue_chain_axis_contamination_2026_07_28,
  ]
created: 2026-08-05
resulting_plan:
lib_version: "market-tick-data-service@cfffb1448 (this run's fix, pending QG)"
doc_versions_checked:
audited_scope:
  "asset_group=cefi, layer=raw-tick, PROD (-prd-) buckets only, read-only, Phase 0 + census (Tier-1) only per the
  /data-pipeline-reconciliation skill — operator-requested spot-check, not a full campaign"
date: 2026-08-05
auditor: interactive session (operator-requested, /data-pipeline-reconciliation Phase 0-1 subset)
parent_epic: security_and_cross_cutting_master
severity: P2
skill: data-pipeline-reconciliation
run_date: 2026-08-05
generated_at: 2026-08-05T17:00:00+00:00
---

# Data-pipeline reconciliation — cefi (2026-08-05), raw-tick layer, Tier-1 only

**Read-only except the one code fix in §3** (bare-OKX hardcoded literal — shipped as a normal code change via
quickmerge, not a data mutation). No GCS writes, no manifest writes, no deletes, no VM launches. This run is **Tier-1
only** (§5) — narrower than a full `/data-pipeline-reconciliation` campaign, dispatched to directly answer three
operator questions rather than produce a full four-surface verdict.

## 0. Phase-0 reachability + freshness

| bucket                                              | reachable | consolidator lock | last run (UTC)       | verdict                                                 |
| --------------------------------------------------- | --------- | ----------------- | -------------------- | ------------------------------------------------------- |
| `market-data-tick-cefi-prd-central-element-323112`  | yes       | not locked        | 2026-08-05T16:07:34Z | produced (9,751,603 rows out)                           |
| `instruments-store-cefi-prd-central-element-323112` | yes       | not locked        | 2026-08-05T16:00:47Z | empty (0 rows this cycle — no new shards, not an error) |

`_index/phantom_audit_latest.json` (market-data bucket): `phantom_count=0`, but `generated_at=2026-07-27T17:38:18Z` —
**9 days stale relative to this run**. Not re-run here (single-walk discipline; a full phantom sweep is its own
review-gated action). `instruments-store-cefi-prd` has **no** `phantom_audit_latest.json` at all — a declared coverage
gap, not assessed by this run.

## 1. Census — venue axis (M = manifest distinct, C = UAC `VENUES_BY_ASSET_GROUP["cefi"]`)

- **C − M (canonical venues with zero real manifest data — the "orphaned declaration" question, direct)**: **empty**.
  Every one of the 25 UAC-declared cefi venues has at least some real manifest presence.
- **M − C (manifest venues not in the canonical declaration — drift)**:
  - `OKX` (bare) — **5,225 `attempted_failed` rows**, `service_name=market-tick-data-service`,
    `pipeline_mode=batch_tardis`, all 5 MVP data_types, `attempted_at` through `2026-08-04T17:32:43Z`. **Active
    regression, root-caused + fixed this run — see §3.**
  - `OKX-OPTIONS` — 2 `attempted_failed` rows, single date `2026-07-25`. Stale, not recurring. Not actioned.
  - `BYBIT-FUTURES` — 4 `empty_confirmed` rows, `2026-07-31`..`2026-08-04`. Low volume, non-failing. Not actioned.
  - `KALSHI_PERP` (underscore variant of the canonical `KALSHI-PERP`) — 2 `attempted_failed` rows, `2026-07-26/27`.
    Stale dialect drift, not recurring. Not actioned.

## 2. Census — instrument_type + (venue, data_type) capability axis

- `instrument_type` case variants (`future`/`perpetual`/`spot_pair`/`index` lowercase) are the **already-ruled,
  `migration_pending` C2a casing item** (`reconciliation-finding-taxonomy.md` §5.1) — correctly NOT flagged as a new
  finding.
- Residual after excluding the casing migration: `futures_chain`/`options_chain` appear as `instrument_type` values (not
  just `data_type` values). Plausibly legitimate bundle-root semantics (MTDS's own shard-atom comment describes "bundle
  root for options_chain / futures_chain") rather than a defect — **not independently confirmed this run**, flagged for
  the next investigator rather than asserted as a bug.
- **`BINANCE-DELIVERY`** — UAC-declared cefi venue, **missing from `VENUE_DATA_TYPE_CAPABILITIES` entirely**, and has
  **zero `captured` rows ever** across all 5 data_types it has been attempted against (582 rows total, all
  `attempted_failed`/`empty_confirmed`). This is the concrete, positive answer to "orphaned shard dimension": a
  canonical declaration that structurally cannot produce real data as currently wired. Filed as a todo (§6), not fixed
  this run (needs an operator call on whether BINANCE-DELIVERY is still in scope at all, or dead and should be
  deregistered).
- **`COINBASE-FUTURES` / `EXTENDED-STARKNET` / `LIGHTER-ZKSYNC`** write real `ohlcv_1m` data
  (`service_name=market-tick-data-service`, 1,700 / 1,081 / 1,505 rows respectively) **outside their declared
  `VENUE_DATA_TYPE_CAPABILITIES`** — the registry under-declaring real production activity, the mirror-image gap. Filed
  as a todo (§6).
- `KALSHI-PERP` / `POLYMARKET-PERP` show many undeclared-combo rows, almost entirely `empty_confirmed` at low volume
  (~60-400 rows each) — reads as pre-MVP exploratory enumeration rather than a live problem. Not actioned.

## 3. Fixed this run — bare-OKX hardcoded literal (root cause, not the earlier registry symptom)

`unified-api-contracts@d67a226f` (2026-08-04) removed bare `"OKX"` from `VENUES_BY_ASSET_GROUP["cefi"]`. A prior
session's manual manifest purge + VM restart addressed the LIVE-websocket capture path and the historical row backlog,
but the census above proved bare-OKX attempts were still live as of `2026-08-04T17:32:43Z` — a full day after the
registry fix shipped. Traced (dispatched sub-agent, verified directly) to
`market_tick_data_service/engine/orchestrator/__init__.py:365`:

```python
venues.extend(["OKX", "COINBASE-CDE"])
```

a hardcoded literal inside `get_venues_for_asset_groups()`, completely independent of the UAC registry — it re-injects
bare OKX into every CEFI batch/download venue enumeration regardless of what UAC currently declares. OKX-SPOT/-SWAP/
-FUTURES already surface correctly via `_VENUE_MAPPING.tardis_to_venue.values()` (each has an unambiguous 1:1 Tardis
exchange slug), so the bare-OKX injection's original justification is moot and it was guaranteeing every attempt fail
(no unambiguous Tardis exchange to resolve to).

**Fix**: removed `"OKX"` from the literal (kept `"COINBASE-CDE"` — still UAC-declared, still has real captured data,
same shared-slug carve-out reasoning, unaffected). Updated `test_orchestrator.py::test_cefi_includes_okx` (whose own
premise was the bug) to `test_cefi_excludes_bare_okx` + added a live-registry regression lock
(`test_bare_okx_matches_live_uac_registry`), mirroring the existing `test_cefi_excludes_deregistered_deribit_combo` /
`test_deribit_combo_matches_live_uac_registry` pattern already in the same file.

**Ship status: code-complete + verified, NOT yet committed.** Across ~9 `quality-gates.sh` attempts this run hit five
DIFFERENT, unrelated pre-existing/concurrent failures in this heavily-multi-tenant checkout (a stale DEFI shard-count
pin, an import-pattern violation, an undocumented broad-except, an ASTER websocket connector test under severe host load
— load average peaked 21.24 — and an empty-string-fallback ratchet baseline another slot is actively lowering right now,
confirmed via that baseline file's own git log). The first three were genuinely fixed/reconciled (mirrors of
already-independently-landed identical fixes from another slot, discovered via a `stash pop` conflict this run also had
to resolve — 4 foreign files' conflicts were resolved via `checkout --ours` + re-add, verified zero net diff against
HEAD, so no foreign WIP was lost, only deferred to its rightful owner). The last two are active, in-progress work by
other slots, not mine to touch. My own 3-file diff (`market_tick_data_service/engine/orchestrator/__init__.py` + 2 test
files, 71 insertions/20 deletions) is verified correct and sits uncommitted, ready to ship the moment one clean
full-suite run lands — see the tracking doc for the todo.

## 4. Honest-coverage formula + freshness

Re-triggered `honest-coverage-daily` and pulled the fresh rollup (`generated_at=2026-08-05T14:42:13Z`) directly —
`by_chain.cefi` shows exactly one entry, blank, confirming the `unified-trading-library@7684a102` chain-axis heal
(shipped earlier this session) generalizes correctly. Did not independently re-derive `reachable_coverage` from raw
counts this run (out of scope for this spot-check) — the formula itself is unchanged from `honest-coverage-model.md`'s
`captured / (captured + attempted_failed + expected_unattempted)`.

## 5. What this run does NOT cover (declared, per skill discipline — Tier-1 subset only)

- **No machine-oracle path-structure sweep** (§3 of the skill, `canonical_path_violations()` over real GCS objects) —
  the "are GCS paths canonical" question is answered here only via the census (values), not path STRUCTURE. The daily
  automated **Hygiene-vs-GCS RED/GREEN digest** (per the parallel research this session ran,
  `codex/05-infrastructure/ data-pipeline-alerts.md`) already covers this on a schedule — see the companion answer to
  the operator in-chat.
- **No id-form / schema Tier-1 sampled check** (§3g) or Tier-2 100%-corpus VM validation (§7).
- **No orphan-object sweep** (§4a — GCS objects with no manifest row).
- **`instruments-store-cefi` bucket** — Phase 0 only (reachability + freshness); no census/oracle pass run against it
  this time (its `verdict=empty` this cycle and low manifest volume made it lower priority for this spot-check).
- **No delete suggestions** — none proposed or needed this run.

## 6. Todos

- [ ] [DATA] P2. **Orphaned declaration**: decide whether `BINANCE-DELIVERY` is still in-scope for cefi. If yes, wire it
      into `VENUE_DATA_TYPE_CAPABILITIES` and root-cause why it never captures; if dead, deregister it from
      `VENUES_BY_ASSET_GROUP["cefi"]` (mirrors the bare-OKX precedent). Repo: unified-api-contracts.
- [ ] [DATA] P3. **Under-declared capability**: add `ohlcv_1m` to `VENUE_DATA_TYPE_CAPABILITIES` for
      `COINBASE-FUTURES`/`EXTENDED-STARKNET`/`LIGHTER-ZKSYNC` (or confirm it's intentionally undeclared and document
      why) — real production data currently exists outside the registry's stated capability set. Repo:
      unified-api-contracts.
- [ ] [DIAG] P3. Confirm whether `futures_chain`/`options_chain` as `instrument_type` values (§2) is legitimate
      bundle-root semantics or a genuine data_type/instrument_type axis confusion. Repo: market-tick-data-service /
      unified-api-contracts.
- [ ] [INFRA] P2. Re-run (or schedule) a fresh `phantom_audit` for cefi — 9 days stale. Repo: instruments-service.
- [ ] [CODE] P1. **Ship the bare-OKX orchestrator fix** — code-complete + regression-tested this run
      (`market_tick_data_service/engine/orchestrator/__init__.py` + 2 test files, verified correct in isolation) but NOT
      YET committed: retry `quality-gates.sh` + `quickmerge` once the shared `.tabs/3` checkout's current heavy
      multi-slot churn settles (load average was 21.24 at last attempt, with another slot actively mid-ratchet on an
      unrelated ~empty-string-fallback baseline in the same repo). No code changes needed — just needs one clean
      full-suite run. Repo: market-tick-data-service.
- [ ] [INFRA] P3. Consider whether the current level of concurrent multi-slot write activity in the shared
      `.tabs/3/market-tick-data-service` checkout (5 unrelated QG-blocking conditions hit within roughly one hour this
      run, plus 8 stacked `autostash` stash entries found on the same checkout — `git stash list`) warrants an operator
      look, independent of this doc's own cefi scope.
