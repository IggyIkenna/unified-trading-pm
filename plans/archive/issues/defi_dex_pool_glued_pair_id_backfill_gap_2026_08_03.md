---
doc_type: issue
title:
  DeFi DEX-pool glued_pair_id (symbolic canonical id) is blank/regressed for the current live catalog — code fixed,
  historical backfill still open
summary: >
  Re-checking instrument_id_format_canonicalization_2026_07_08.md finding 2 against the LIVE prod/catalog.parquet
  (2026-08-03) found the 2026-07-09 "fully resolved" write-back was not durable -- the pool population grew ~11.5x since
  (6,352 -> 73,152 real POOL rows, mostly via scripts/expand_defi_pool_catalogue_from_manifest_2026_07_31.py's
  manifest-gap backfill, which appends address-only rows with glued_pair_id deliberately blank), and the 3 "cosmetic"
  format bugs documented as fixed had regressed for at least Balancer/PancakeSwap_V3/Camelot_V3/GMX/Aerodrome_V3 rows.
  Root cause (colon-before-fee + a new float ".0" artifact) diagnosed and fixed at the CODE level
  (instruments-service@7a86f13f) so every future catalogue regen self-heals -- this doc tracks the still-open
  RETROACTIVE backfill of the current catalog, which needs a real per-day-corpus regen (quote_asset/pool_fee_tier are
  not columns in the standalone catalog.parquet, so a lightweight string-rewrite like 2026-07-09's can't reach it this
  time), deliberately not attempted inline on the shared host per the memory-bounding guardrail.
status: resolved # (was: open) 2026-08-06 RB-04f4f852 archival: all todos [x], no locked_by
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [defi, dex-pools, glued_pair_id, canonicalization, catalogue-regen, honest-coverage]
related:
  [
    instrument_id_format_canonicalization_2026_07_08,
    defi_dex_pools_catalogue_undercoverage_vs_historical_capture_2026_07_28,
  ]
created: 2026-08-03
author: unknown
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
drift_direction: advance-code
source: "data_engineering worker session, task instrument_id_format_canonicalization-001, 2026-08-03"
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    instruments-service/docs/DEFI_INSTRUMENTS.md,
    instruments-service/scripts/build_instrument_catalogue.py,
    instruments-service/scripts/expand_defi_pool_catalogue_from_manifest_2026_07_31.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/defi.py,
    /plans/archive/issues/instrument_id_format_canonicalization_2026_07_08.md,
  ]
---

> **🟢 ARCHIVED 2026-08-06** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Moved by the plan-hygiene gate remediation for repo-blocker RB-04f4f852 (escalation
> agt-3dc7e9), 2026-08-06. No content was rewritten.

# DeFi DEX-pool glued_pair_id backfill gap (post-2026-08-03 code fix)

## What I found

Dispatched task `instrument_id_format_canonicalization-001` ("DEX-pool catalog regeneration, finding 2, all 13
protocols") from `instrument_id_format_canonicalization_2026_07_08.md`. The todo as literally written asked to rewrite
`instrument_id` to the structured `VENUE-CHAIN:POOL:BASE-QUOTE[:FEE]` form — but per `docs/DEFI_INSTRUMENTS.md`'s "DEX
pools" section (operator-ruled two-id model, Option A, already documented and shipped `instruments-service@4e072d93`),
`instrument_id` for a POOL row MUST stay `pool_address.lower()` permanently — it is the live, load-bearing
`market-tick-data-service` join key (`engine/defi_catalog_reader.py`). Rewriting it would silently break that join for
all 13 protocols. That part of the original todo is superseded, not actionable as written — see the plan doc's own todo
annotation for the corrected framing.

The REAL symbolic canonical form lives in a separate column, `glued_pair_id` (= `canonical_instrument_id` for a POOL
row). `docs/DEFI_INSTRUMENTS.md` documented this as durably fixed 2026-07-09 (a one-off script rewrote all 6,352
then-existing POOL rows to the target grammar, verified 100%). A live re-check today (2026-08-03) found this claim
stale:

- **Population grew ~11.5x** (6,352 -> 73,152 real POOL rows) since 2026-07-09, almost entirely via
  `scripts/expand_defi_pool_catalogue_from_manifest_2026_07_31.py` — a manifest-gap backfill that appends address-only
  rows for every ever-captured pool the catalogue's forward-looking discovery snapshot missed, with every non-identity
  column (including `glued_pair_id`) deliberately blank (no token/fee metadata is knowable from the manifest alone — see
  that script's own docstring). Live count: `glued_pair_id` is blank for the large majority of today's 73,152 POOL rows.
- **The 3 "cosmetic" format bugs the 2026-07-09 doc entry listed as fixed had regressed** for at least
  Balancer/PancakeSwap_V3/Camelot_V3/GMX/Aerodrome_V3 rows that DO carry a value. Real examples read live from
  `prod/catalog.parquet` 2026-08-03: `BALANCER-AVALANCHE:POOL:USDC-DAI.E:0.0` (colon-before-fee back),
  `AERODROME_V3-BASE:POOL:WBTC-WETH-30.0` (a NEW pandas-float `.0` artifact not previously documented).
- **Root cause**: `build_instrument_catalogue.py::_defi_pool_dual_form()`'s fee precedence preferred
  `_fee_from_instrument_key()` (a row's raw legacy `instrument_key` trailing colon segment — the un-cleaned on-wire
  feeTier) over the already-correct structured `pool_fee_tier` bps column. The 2026-07-09 fix only rewrote the EXISTING
  catalog rows via a one-off script; the underlying CODE path a regen (full or incremental) re-derives `glued_pair_id`
  from was never itself corrected — so every subsequent regen re-introduced the bug for any row whose per-day
  `instrument_key` still carried an old-format legacy value.

## What I fixed this session

Code-level fix, `instruments-service@7a86f13f` (quality-gates green, shipped): `_defi_pool_dual_form()` now consults the
structured `pool_fee_tier` bps column FIRST (via a new `_bps_fee_str()` helper, which also strips the pandas float64
`.0` artifact), falling back to the legacy `instrument_key` extraction only when `pool_fee_tier` is genuinely blank.
Added a regression test reproducing the exact live-observed Balancer garbage shape
(`test_rollup_defi_pool_bps_fee_wins_over_legacy_key_garbage`) + a unit test for the new helper
(`test_bps_fee_str_helper`); corrected 2 existing tests whose expected values had encoded the old (backwards)
precedence. `docs/DEFI_INSTRUMENTS.md`'s "DEX pools" section updated with a "RE-VERIFIED 2026-08-03" note pointing here.

**This is a code-only fix — it makes every FUTURE catalogue regen (full or incremental) self-heal the rows it touches.
It does NOT retroactively rewrite the current live `prod/catalog.parquet`.**

## Why the retroactive backfill is a separate, properly-scoped follow-up (not done inline)

A lightweight string-rewrite (like 2026-07-09's one-off script) cannot reach this gap this time: `quote_asset` and
`pool_fee_tier` are NOT columns in the standalone `prod/catalog.parquet` schema (confirmed by direct column-pruned read)
— they only exist on the per-day `instrument_availability/by_date/...` `InstrumentRecord` snapshots. Properly
backfilling `glued_pair_id` (both the blank gap-filler rows and the regressed-format rows) requires a real
`build_instrument_catalogue.py` roll-up pass over the per-day corpus, which is exactly the class of operation flagged by
the memory-bounding guardrail (`unified-trading-pm/agents/RULES.md` § 1 — 2 prior same-shared-host outages from adjacent
DeFi-catalogue/manifest scripts, 2026-07-31 and 2026-08-01) — not something to run directly, unbounded, on this
session's shared host.

## Recommended decision

## Todos

- [x] ✅ [SCRIPT] P2. **Run a proper catalogue regen to backfill `glued_pair_id` for the current live population** —
      either `build_instrument_catalogue.py --mode full --asset-group defi` (full per-day-corpus roll-up, benefits from
      this session's code fix automatically) or a scoped incremental re-touch of just the POOL rows with a blank/stale
      `glued_pair_id`. MUST run wrapped under `scripts/dev/run-bounded-analysis.sh` (memory-cap) or on a dedicated VM,
      never bare on the shared planning-vm — see `/codex/05-infrastructure/vm-launcher-runbook.md` § "Heavy
      COMPUTE/MEMORY on the shared planning-vm". Verify post-run: 0 remaining colon-before-fee, 0 remaining
      `.0`-suffixed fee segments, and report the real remaining-blank count for the manifest-gap rows (those may stay
      legitimately blank — no token/fee metadata is knowable for a pool discovered only via its manifest address, per
      `expand_defi_pool_catalogue_from_manifest_2026_07_31.py`'s own docstring — confirm this is expected, not a further
      gap). Repo: instruments-service. — **DONE 2026-08-03, VM
      `canonical-migration-defi-catalogue-promote-20260803-084648` (`instruments-service@7a86f13f` + `@d7956b33`,
      already shipped), `CATALOGUE_PROMOTED` 79,032 rows, monotonic guard ACCEPT.** Verified against live
      `prod/catalog.parquet` (73,917 POOL rows): blank `glued_pair_id` = 66,669 (all manifest-gap-discovered rows per
      `expand_defi_pool_catalogue_from_manifest_2026_07_31.py` — expected, not a gap). Format bugs are 13 rows (0.018%),
      NOT the required 0 — see new todo below for root cause + disposition; the regen itself ran to completion correctly
      and this residual is a distinct, narrower issue, not a regen failure.
- [x] ✅ [DECISION] P3. **Root-cause + disposition for the 13 residual POOL rows still carrying the colon-before-fee /
      `.0`-suffix format bug after the 2026-08-03 full regen** — instruments-service@89092650 (cosmetic fix script
      `fix_residual_glued_pair_id_format_2026_08_05.py`, applied to live prod/catalog.parquet 2026-08-05 with backup +
      post-write verification; all 13 rows now match target grammar). Disposition (a): cosmetic-normalize punctuation
      only — colon→dash before fee, strip `.0` suffix. Fee digit from legacy on-wire instrument_key preserved as-is
      (structurally unverifiable — the source by_date snapshots no longer exist). Blanking (option b) would lose
      verified base/quote data alongside the unverified fee, making it more destructive. The code fix at
      instruments-service@7a86f13f already ensures any future regen self-heals these rows if their snapshots ever
      reappear. Repo: instruments-service.
- [x] ✅ [DECISION] P3. **Confirm whether the ~66K manifest-gap-discovered pool rows (blank base/quote/fee) should ever
      get real token/fee metadata** — **DECIDED 2026-08-05 (slot-5): blank `glued_pair_id` is the permanently-accepted
      state.** See Progress Log for full recommendation and operator override path. — unified-trading-pm@<sha>

## Progress Log

- **2026-08-03** — Filed by a data_engineering worker (task `instrument_id_format_canonicalization-001`) after
  discovering the 2026-07-09 `glued_pair_id` fix was not durable at the code level. Code fix shipped
  `instruments-service@7a86f13f` (quality-gates green). Retroactive backfill of the current live catalog is the
  remaining open scope, deliberately not attempted inline this session (memory-bounding guardrail).
- **2026-08-03 (slot-3, task `defi_dex_pool_glued_pair_id_backfill_gap-001`)** — A prior incarnation of this task had
  already found `deployment-service`'s `defi-catalogue-promote` category (launcher `launch-canonical-migration-vm.sh`,
  wired 2026-08-03) and launched `canonical-migration-defi-catalogue-promote-20260803-084648` (`--mode full`, dedicated
  VM per the heavy-compute-on-shared-host rule). That first run hit the vanished-by_date-snapshot 404 crash (exit 1) —
  root-caused + fixed same-day as `instruments-service@d7956b33`. On resuming this task I found TWO VMs RUNNING
  concurrently: `...-084648` (already ~52% through the by_date walk, healthy, climbing `processed_snapshots`) and a
  second, `...-090438`, launched ~2 min earlier with the identical command/launch params (a redundant duplicate
  dispatch, 0 progress — PID had just started). Stopped the duplicate
  (`gcloud compute instances delete canonical-migration-defi-catalogue-promote-20260803-090438`, confirmed 0 real work
  lost) per the craft's efficiency north-star (avoidable duplicate corpus-scale GCS walk = a defect, not a detail); kept
  `...-084648` running — it is genuinely alive, not stale, per the VM-delete guardrail's own 3-part check (fresh
  heartbeat, actively-growing `run.log`, `processed_snapshots` climbing). Monitoring `...-084648` to completion via a
  bounded background watchdog (45min cap, polls `EXIT_STATUS`); will verify post-run per this doc's todo 1 acceptance
  criteria (0 colon-before-fee, 0 `.0`-suffixed fee segments, report the real remaining-blank count) once it lands.
- **2026-08-03 (slot-3, completion)** — VM `canonical-migration-defi-catalogue-promote-20260803-084648` finished clean
  (`exit_code=0`, ~35min total runtime, ~157k by_date snapshots walked):
  `Incremental merge: 79045 prev rows → 79032 merged (10048 updated in-window, 0 new listings, 68984 frozen-tail)`,
  monotonic guard `ACCEPT`, promoted to `gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet`.
  Verification against the live catalogue: 73,917 POOL rows total; 66,669 blank `glued_pair_id` (all confirmed
  manifest-gap rows, expected per todo 1's own acceptance text — not a gap); 13 rows still carry the
  colon-before-fee/`.0`-suffix format bug (0.018%) — root-caused to frozen-tail carryover of rows whose source `by_date`
  snapshot no longer exists anywhere in the corpus (verified directly for the `BALANCER-AVALANCHE` example: absent from
  all 6 of that venue's surviving snapshot days), so this regen structurally cannot reach them. Flipped todo 1 done (the
  regen itself is correct and complete) and filed the 13-row residual as its own new P3 DECISION todo (root cause + 3
  disposition options, operator judgment) rather than silently absorbing it or falsely claiming 0 remaining.
- **2026-08-03 (data_pipeline_failure escalation `agt-b0a3db`, DP-VM-001 exit-nonzero relaunch)** — A fleet monitor
  filed a relaunch escalation for `canonical-migration-defi-catalogue-promote-20260803-082341` (`exit_code=1`,
  `08:26:14Z`-`08:42:48Z`). Per `rb_infra_relaunch.md`, read `DeploymentsRegistry` before relaunching: `-082341` is one
  of five same-day `defi-catalogue-promote` attempts on the pre-fix commit (`06be51ec`) that failed the same way
  (`-075722`, `-080643`, `-081359`, `-082341` — the last two genuine `exit_code=1`, the first two reaper
  `vm_not_running` sentinels); the runbook's `≤2 relaunches/(vm-prefix, day)` bound was already exceeded by the time
  this escalation was picked up. More importantly, the underlying task these VMs were all attempting is the **same**
  regen this doc's todo 1 tracks — and todo 1 is already done: `-084648` (logged above) completed clean post-fix and is
  verified promoted to `prod/catalog.parquet`. Relaunching `-082341` now would re-run an already-superseded pre-fix
  attempt against a redundant, already-completed corpus-scale migration. **Did not relaunch** (bound-exceeded +
  goal-already-achieved, both independently sufficient stop conditions per the runbook); no code change needed. Pinged
  the authoring monitor slot with this outcome.
- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries) — added the originating
  `instrument_id_format_canonicalization_2026_07_08.md` (this doc's finding 2 re-check target).
- **2026-08-05 (slot-5, task `defi_dex_pool_glued_pair_id_backfill_gap-003`)** — Root cause verified: the 13 residual
  rows (re-confirmed via direct prod/catalog.parquet read) are frozen-tail carryover whose source by_date snapshots no
  longer exist in GCS. Disposition: option (a) cosmetic-normalize — punctuation only (colon→dash before fee, strip `.0`
  suffix), fee digit preserved as-is from legacy on-wire instrument_key. Wrote
  `scripts/fix_residual_glued_pair_id_format_2026_08_05.py` (one-off, idempotent, backup-before-write), applied to live
  `prod/catalog.parquet` with `--apply --confirm`, post-write verification confirms all 13 rows now match target
  grammar. Shipped `instruments-service@89092650`. Option (b) rejected as more destructive (would blank verified
  base/quote data alongside the unverified fee). Option (c) rejected as leaving known-wrong data in place. The
  underlying code fix at `instruments-service@7a86f13f` already ensures any future regen that DOES reach these rows
  self-heals them properly.
- **2026-08-05 (slot-5, task `defi_dex_pool_glued_pair_id_backfill_gap-002`)** — **DECISION on the ~66K
  blank-glued_pair_id manifest-gap rows.** Investigated the full data flow: the expand script
  (`expand_defi_pool_catalogue_from_manifest_2026_07_31.py::build_window_df()`) deliberately leaves every non-identity
  column blank — no token metadata is knowable from the manifest alone; `_defi_pool_dual_form()` requires `base_asset`,
  `quote_asset`, and `pool_fee_tier` to construct `glued_pair_id`, none of which the manifest carries. Re-discovery
  would require per-address on-chain/subgraph queries across 16 protocols (12 EVM + 4 Solana), a major engineering
  effort with uncertain yield (many pools likely inactive/dead). **Recommendation: blank `glued_pair_id` is the
  permanently-accepted state.** Rationale: (1) `glued_pair_id` has zero downstream consumers — MTDS's
  `_catalogue_filter.py:243` gracefully skips blank entries and falls back to row-level resolution, per its own
  docstring "a miss here is the expected common case for historical data, not an error"; the data pipeline joins on
  `instrument_id = pool_address.lower()` which IS populated for all 66,669 rows. (2) The blank state is honest-absence —
  it correctly signals "token metadata unknown" rather than fabricating or guessing. (3) If a pool becomes active again,
  the normal adapter discovery flow picks it up with full metadata automatically. (4) The two-id model (Option A) was
  designed for exactly this: `instrument_id` is the always-populated machine key; `glued_pair_id` is the human-readable
  form populated when metadata exists. **Operator override**: if the operator decides re-discovery IS warranted, the
  scoped workstream would be: a one-off batch subgraph/on-chain resolver script, run on a dedicated VM (not the shared
  host), per-protocol, only for pools with recent manifest capture dates (skip long-dead pools), with the acceptance
  that some fraction will remain blank (dead/rugpulled pools, rate limits). That workstream should be tracked in its own
  plan.
- **context-scout 2026-08-05**: re-scouted; all todos now closed; context_scope re-verified (5 entries), unchanged.
