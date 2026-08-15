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

## Session 2 findings (2026-08-15, slot 22) — dispatched todo 2 ("migrate the three unique gaps")

Investigated the todo below ("Migrate the three unique gaps into their current canonical destinations") directly against
LIVE GCS state (read-only, via UTL `get_storage_client` — no `gsutil`/raw walk). Findings, per sub-part:

**(a) + (b) Aave V3 `2022-03-12…2022-10-31` (evm-defi-prd) / `marinade` mSOL LST (solana-defi-prd) — CANNOT VERIFY,
source buckets no longer exist.** `client.list_buckets()` confirms `evm-defi-prd-central-element-323112` and
`solana-defi-prd-central-element-323112` do not exist in the project today — they were deleted in the 2026-07-10 "bucket
estate cleanup" (`deployment-service/configs/cloud-providers.yaml` line ~117: "Confirmed zero callers workspace-wide...
buckets... were empty and deleted in the same cleanup"). That yaml comment asserts the buckets were **empty** at
deletion time — if true, the Aave/marinade ranges the 2026-06-08 audit flagged as "unique" were either already
migrated/never uniquely there, or the "confirmed empty" claim didn't specifically re-check those two ranges before an
irreversible bucket delete. No `_index/audit/*` artifact anywhere in `market-data-tick-defi-prd` mentions `evm`, `aave`,
`marinade`, or `solana_defi` (checked the full `_index/audit/` listing) — i.e. there is no record either confirming
these ranges were migrated OR confirming they were re-verified before the 07-10 deletion. **This cannot be resolved by
further investigation from this session — the source data (if it ever existed) is gone with the bucket.** Flagging as a
genuine data-correctness/audit-trail gap, not attempting a migration that has no source to read from.

**(c) KAMINO DEX pools + Solana `lending_indices` (market-data-tick-defi-prd legacy prefixes) — RESOLVED, nothing to
migrate.** Two independent checks: (1) the exact prefixes the todo names, top-level `dex_pools/` and `lending_indices/`
(the PRE-canonical path shape, distinct from the current `data_type=dex_pool_state/` / `data_type=lending_indices/`
segments), have **zero objects** in `market-data-tick-defi-prd-central-element-323112` today — confirmed via
`list_blobs(prefix=...)`. (2) `market-data-tick-defi-prd`'s own audit trail
(`_index/audit/kamino_solend_lending_fabrication_pending_delete.parquet`, 10,472 rows, `venue=KAMINO`, plus the
`_index/availability_index.parquet.kamino_lending_retire.bak` +
`availability_index.parquet.pre_lending_instrument_ type_restamp_apply_20260730T125527Z.parquet` backups) shows the
KAMINO/SOLEND `lending_indices` data this todo's source audit (2026-06-08) had flagged as "unique, needs migrating" was
independently found to be **FABRICATED** (wrong `claimed_day` vs `true_date`, wrong `instrument_type=lending` vs the
corrected `solana_lending`) and was already relabeled/retired on **2026-07-30** — six weeks before this dispatch, by a
later and more thorough pass than the original audit. There is nothing unique or real left to migrate for KAMINO
lending. (KAMINO DEX-pool-state specifically wasn't in that fabrication file — the separate
`dex_pools_fake_history_pending_delete.parquet` audit file covers ORCA/RAYDIUM fake history only — but since the legacy
top-level `dex_pools/` prefix this todo names has zero objects regardless of venue, there is no source path to migrate
FROM either way.)

**Net effect on the dispatched todo**: (c) is resolved-as-moot (no action needed, confirmed via live state); (a)/(b) are
NOT actionable by a worker — the source is gone, not merely hard to find. Filing per the "big finding" (data-correctness
/ SSOT-contradiction) HARD RULE rather than silently closing the todo. Did not attempt `--apply`/any GCS write — this
session was investigation-only, appropriate given both closed sub-parts turned out to need judgment about an
already-executed, irreversible deletion rather than a migration to perform.

## Recommended decision

- [ ] [OPERATOR] P1. **Re-scope the delete list.** `market-data-tick-defi{,-prd}` must be REMOVED from any future DeFi
      orphan-bucket delete list — it is the permanent canonical bucket, not a delete candidate, under the architecture
      that shipped 2026-07-10..07-16. Confirm this reading (or correct it, if a further architecture change since
      2026-08-14 has occurred) before any DeFi bucket-delete todo is re-dispatched. (repo: unified-trading-pm — plan-doc
      correction only)
- [x] ✅ [DATA] P1. **INVESTIGATED 2026-08-15 (slot 22) — see "Session 2 findings" above; not literally executable as
      scoped.** (c) KAMINO DEX pools + Solana `lending_indices` from the legacy top-level prefixes: RESOLVED-AS-MOOT —
      those prefixes hold zero objects in `market-data-tick-defi-prd` today, and the underlying KAMINO/SOLEND
      `lending_indices` data this todo's source audit flagged was independently found FABRICATED and already
      retired/relabeled 2026-07-30 (pre-dates this dispatch). (a) Aave V3 `2022-03-12…2022-10-31` from `evm-defi-prd`
      and (b) `marinade` mSOL LST from `solana-defi-prd`: NOT ACTIONABLE — both source buckets were deleted in the
      2026-07-10 bucket-estate cleanup (confirmed via `list_buckets()`, neither exists in the project); no audit-trail
      record confirms these specific ranges were migrated or re-verified before that deletion. No further worker action
      is possible without either (i) an operator-confirmed reading of the 07-10 cleanup's own verification scope (was it
      project-wide "zero callers" only, or did it also re-check historical archived ranges?), or (ii) a
      GCS/Cloud-Logging admin-activity check for the buckets' pre-deletion object count — deferred to the follow-up todo
      below rather than attempted here (no code/script exists to act on; this was an investigation task). Repo:
      market-tick-data-service / instruments-service. Owner: vm-defi. parent_epic: defi_master.
- [ ] [OPERATOR] P2. **Decide whether the Aave 2022-03..10 / marinade mSOL gap (Session 2 findings above) needs a GCP
      Cloud-Logging admin-activity check for the 2026-07-10 deletion of `evm-defi-prd`/`solana-defi-prd`** (to confirm
      the buckets were genuinely 0 objects at delete time, not just "0 code callers") — or whether the 2026-06-08
      audit's "unique data" claim is itself accepted as stale/superseded, matching the pattern already found for
      KAMINO/SOLEND lending (fabricated, not unique). No GCS write proposed here. parent_epic: defi_master.
- [ ] [DATA] P2. **Only after both above are closed**: re-run the five-part delete proof
      (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §1) against the CORRECTED list — `solana-defi{,-prd}`
      / `evm-defi{,-prd}` / the 4 empty `*-test-*` DeFi buckets — and execute per §3a's reversibility-qualified
      autonomous path once each bucket's fresh soft-delete-retention check clears ≥7 days.
      `market-data-tick-defi{,-prd}` stays permanently off any delete list. Repo: instruments-service (or wherever the
      delete script/skill lives). Owner: vm-defi. parent_epic: defi_master.
