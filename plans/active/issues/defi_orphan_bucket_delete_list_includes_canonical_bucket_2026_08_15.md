---
doc_type: issue
title: >-
  defi_operator_ruling_ao_dispatch_2026_08_15.md todo 2's delete list names market-data-tick-defi{,-prd} — that is now
  the PERMANENT canonical DeFi bucket, not a legacy orphan; also the Aave/marinade/KAMINO unique-gap migration has NOT
  landed (no code/script evidence anywhere)
summary: >-
  Dispatched to verify whether the "unique-gap migration" (Aave V3 2022-03-12..2022-10-31, solana-defi `marinade` mSOL
  LST, market-data-tick-defi KAMINO DEX pools + Solana lending_indices — defi_migration_audit_log_2026_07_24.md line
  522-529) had landed, then execute the delete of `market-data-tick-defi{,-prd}` / `solana-defi{,-prd}` /
  `evm-defi{,-prd}` if confirmed. Found two independent blockers: (1) the migration has NOT landed — zero code/script
  evidence anywhere in the workspace (no migrator `BucketSpec`, no one-off backfill script, no manifest-audit completion
  note); (2) the delete list itself is stale — `market-data-tick-defi{,-prd}` is the PERMANENT canonical DeFi tick-data
  bucket today (2026-07-10..07-16 bucket estate cleanup retired the dedicated per-data_type buckets and consolidated
  every DeFi writer onto it), not a legacy duplicate — this was already independently flagged as a prediction in
  `plans/active/issues/defi_migration_dedicated_bucket_architecture_retired_2026_08_14.md`'s "Recommended decision" #2
  and this session confirms it. Executing the dispatched delete as originally scoped would have destroyed the live
  canonical DeFi tick-data bucket. NOT executed.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, delete-safety, bucket-naming, migration, ssot-contradiction, stale-doc, data-correctness, orphan-bucket]
related:
  [
    /plans/active/defi_operator_ruling_ao_dispatch_2026_08_15.md,
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/active/issues/defi_migration_dedicated_bucket_architecture_retired_2026_08_14.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-08-15
author: data_engineering (slot 27)
last_updated: 2026-08-15
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.5
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  ["defi_operator_ruling_ao_dispatch_2026_08_15.md todo 2 (dispatched task
  defi_operator_ruling_ao_dispatch-e5203df5b8c2), 2026-08-15"]
depends_on: []
context_scope:
  [
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/active/issues/defi_migration_dedicated_bucket_architecture_retired_2026_08_14.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    market-tick-data-service/market_tick_data_service/scripts/_migrate_defi_classify.py,
  ]
---

# DeFi orphan-bucket delete list includes the current canonical bucket; unique-gap migration unconfirmed

## What I found

Dispatched task `defi_operator_ruling_ao_dispatch-e5203df5b8c2` (todo 2 of
`defi_operator_ruling_ao_dispatch_2026_08_15.md`): verify the "unique-gap migration" referenced at
`defi_migration_audit_log_2026_07_24.md` line 575-577 has landed, then execute the DELETE of
`market-data-tick-defi{,-prd}` / `solana-defi{,-prd}` / `evm-defi{,-prd}` if confirmed, else report what's missing.

**1. The unique-gap migration has NOT landed — no code/script evidence anywhere.**

The referenced todo (`defi_migration_audit_log_2026_07_24.md` line 522-529, still `- [ ]` open) asks to
VERIFY-then-MIGRATE three unique data ranges into their canonical destinations before any legacy delete:

- (a) `evm-defi-prd` Aave V3 `2022-03-12…2022-10-31` → backfill into the lending destination
- (b) `solana-defi-prd` `marinade` (mSOL LST) → migrate if unique
- (c) `market-data-tick-defi-prd` KAMINO DEX pools + Solana `lending_indices` → migrate if unique

Checked for completion evidence:

- `market-tick-data-service/market_tick_data_service/scripts/_migrate_defi_classify.py`'s `BucketSpec` registry has 9
  entries (`dex-pools`, `dex-swaps`, `lending-indices`, `perp-funding`, `lst-rates`, `oracle-prices`, `gas-fees`,
  `liquidations`, `aggregator-routes`) — none targets the Aave 2022-03..10 range, `marinade`, or KAMINO specifically.
- `grep -rl "marinade\|MARINADE"` and `grep -rl "KAMINO\|kamino"` over
  `market-tick-data-service/market_tick_data_service/scripts/` — zero hits.
- No file matching `*aave*2022*` / `*unique_gap*` / `*unique-gap*` exists anywhere in the workspace (a one-off backfill
  script, the todo's other suggested implementation route, was never written).
- `defi_migration_audit_log_2026_07_24.md`'s own Progress Log has no entry recording this migration as done, and the
  todo itself is still open (`- [ ]`, unchanged since 2026-06-08).

**Verdict: NOT CONFIRMED.** No evidence — code, script, or manifest-audit record — that the Aave 2022-03..10 range,
`marinade`, or KAMINO DEX pools were ever migrated into a canonical destination.

**2. Independently, the delete list itself is stale — `market-data-tick-defi{,-prd}` is now the PERMANENT canonical
bucket, not a legacy duplicate.**

`plans/active/issues/defi_migration_dedicated_bucket_architecture_retired_2026_08_14.md` (filed 2026-08-14, still open)
already found: the 2026-07-10..07-16 "bucket estate cleanup" (`gcs_bucket_estate_cleanup_2026_07_10`,
`defi_dedicated_bucket_shared_migration_2026_07_13`) retired every dedicated per-data_type DeFi bucket kind
(`dex-pools`, `dex-swaps`, `lending-indices`, `perp-funding`, `lst-rates`, `oracle-prices`, `gas-fees`,
`eigenlayer-rewards`, `evm-defi`, `solana-defi`) from `deployment-service/configs/cloud-providers.yaml` after confirming
every real writer had already converged on the single shared `market-data-tick-defi-{env}-{pid}` bucket (differentiated
by the `data_type=` path segment instead of by bucket). That issue doc's own "Recommended decision" #2 explicitly
flagged this exact delete-after-migration todo as needing re-reading against the current architecture before dispatch —
flagged, not yet acted on, until this dispatch surfaced it live.

Direct consequence: `market-data-tick-defi{,-prd}`, the FIRST bucket pair in the dispatched delete list, is the
architecture's PERMANENT canonical home for every DeFi tick data_type today — not a duplicate/legacy bucket. Executing
the dispatched delete as scoped would have destroyed the live canonical bucket for the entire DeFi asset_group.
`solana-defi{,-prd}` and `evm-defi{,-prd}` remain plausible legacy-orphan candidates (their bucket-kind entries were
removed from the yaml SSOT, meaning no current writer targets them) — but per part 1 above, they still hold the UNIQUE,
unmigrated Aave/marinade/KAMINO data, so even those two are not yet delete-eligible under Part 5 of
`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` (the legacy-copied-not-moved invariant: never delete a
legacy object without a content-verified canonical twin).

## Why it matters

This is exactly the failure mode `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` exists to prevent: a delete
instruction whose premise (which bucket is "legacy" vs "canonical") had gone stale between when the source audit was
written (2026-06-08) and when the delete was dispatched (2026-08-15), via an intervening architectural decision
(2026-07-10..07-16) that inverted which bucket is which. Had this task executed the delete literally as scoped, it would
have destroyed `market-data-tick-defi{,-prd}` — the live, currently-written canonical bucket for every DeFi market-data
type — a data-correctness incident on the scale this workspace treats as a "big finding" requiring operator
notification, not a routine cleanup.

## Recommended decision

- [ ] [OPERATOR] P1. **Re-scope the delete list.** `market-data-tick-defi{,-prd}` must be REMOVED from any future DeFi
      orphan-bucket delete list — it is the permanent canonical bucket, not a delete candidate, under the architecture
      that shipped 2026-07-10..07-16. Confirm this reading (or correct it, if a further architecture change since
      2026-08-14 has occurred) before any DeFi bucket-delete todo is re-dispatched. (repo: unified-trading-pm — plan-doc
      correction only)
- [ ] [DATA] P1. **Migrate the three unique gaps into their current canonical destinations** (re-scoped against the
      single-bucket model — the old "dedicated bucket" destinations named in the source todo, `lending-indices-`/
      `lst-rates-`/`dex-pools-`, no longer exist as separate buckets; the destination is now `market-data-tick-defi-prd`
      under the correct `data_type=`/`venue=` segments): (a) Aave V3 `2022-03-12…2022-10-31` from `evm-defi-prd` → the
      canonical `lending_indices` data_type shard for those dates; (b) `marinade` mSOL LST from `solana-defi-prd` → the
      canonical `lst_rates` data_type shard, confirmed absent there first; (c) KAMINO DEX pools + Solana
      `lending_indices` from `market-data-tick-defi-prd`'s legacy `dex_pools/`/`lending_indices/` top-level prefixes →
      the canonical `dex_pool_state`/`lending_indices` data_type shards, confirmed absent there first (sampled
      ORCA/RAYDIUM were already found present in the old dedicated buckets per
      `defi_consolidated_closeout_2026_07_18.md` line 385-386 — KAMINO/SOLEND were confirmed ABSENT there, i.e.
      genuinely unique and at risk). Repo: market-tick-data-service (extend `_migrate_defi_classify.py` or a one-off
      backfill, either targeting the current single-bucket destination). Owner: vm-defi. parent_epic: defi_master.
- [ ] [DATA] P2. **Only after both above are closed**: re-run the five-part delete proof
      (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §1) against the CORRECTED list — `solana-defi{,-prd}`
      / `evm-defi{,-prd}` / the 4 empty `*-test-*` DeFi buckets — and execute per §3a's reversibility-qualified
      autonomous path once each bucket's fresh soft-delete-retention check clears ≥7 days.
      `market-data-tick-defi{,-prd}` stays permanently off any delete list. Repo: instruments-service (or wherever the
      delete script/skill lives). Owner: vm-defi. parent_epic: defi_master.
