---
doc_type: issue
title: >-
  defi_migration_audit_log_2026_07_24.md's "dedicated per-data_type bucket" migration target was retired by the
  2026-07-10..07-16 bucket estate cleanup — the open REDIRECT/9th-spec/delete-after todos in that doc are stale
summary: >-
  Dispatched to redirect 4 DeFi live handlers (dex_swaps_handler, solana_defi_handler, evm_defi_handler,
  aggregator_route_handler) from a shared "orphan" bucket onto dedicated per-data_type migrated buckets
  (dex-pools-prd/dex-swaps-prd/lending-indices-prd/perp-funding-prd/lst-rates-prd/oracle-prices-prd/etc.), per
  defi_migration_audit_log_2026_07_24.md's 2026-06-08 audit trail. Live investigation found the redirect target itself
  no longer exists: `deployment-service/configs/cloud-providers.yaml` documents a "bucket estate cleanup"
  (`gcs_bucket_estate_cleanup_2026_07_10`, `defi_dedicated_bucket_shared_migration_2026_07_13`) that ran 2026-07-10
  through 2026-07-16 and RETIRED every dedicated per-data_type DeFi bucket kind (dex-pools, dex-swaps, lending-indices,
  perp-funding, lst-rates, oracle-prices, gas-fees, eigenlayer-rewards, evm-defi, solana-defi) after confirming zero
  live callers — every real writer/reader/scanner had already converged on the single shared
  `market-data-tick-defi-{env}-{pid}` bucket (yaml kind `market-data`, consumer alias `tick-data`), differentiated by
  the `data_type=` path segment instead of by bucket. Direct code read confirms all 4 "orphan" handlers in the redirect
  todo already call `get_write_bucket_name("market_data", "defi")` / `resolve_bucket_name(kind="market-data",
  asset_group="defi")` — bit-identical to the call every "already migrated" handler (dex_pools_handler,
  lending_indices_handler, lst_rates_handler) makes. The redirect's premise (dedicated buckets are the canonical target)
  is the OPPOSITE of the architecture that actually shipped; no code change is possible or needed for that todo. This
  also makes several OTHER open todos in the source doc suspect — flagged here rather than silently resolved, since
  re-triaging them needs a human/judgment read of the doc, not a mechanical fix.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, bucket-naming, migration, ssot-contradiction, stale-doc]
related:
  [
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/active/defi_satellite_ao_dispatch_batch13_2026_08_13.md,
    /plans/active/defi_satellite_ao_dispatch_batch13_2026_08_13_finalize.md,
  ]
created: 2026-08-14
author: sub-agent (Claude Code session, dispatched via defi_satellite_ao_dispatch_batch13_2026_08_13.md's REDIRECT todo)
parent_epic: defi_master
priority: P2
assigned_vm: NA
execution_scope: local-only
estimate_class: research
assigned_role:
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-14
locked_since:
context_scope:
  [/plans/active/defi_migration_audit_log_2026_07_24.md, /codex/05-infrastructure/bucket-isolation-model.md]
source: >-
  defi_satellite_ao_dispatch_batch13_2026_08_13.md's "[SCRIPT] P2. Redirect the 4 DeFi live handlers..." todo (Source:
  plans/active/defi_migration_audit_log_2026_07_24.md).
---

# defi_migration_audit_log_2026_07_24.md's dedicated-bucket architecture was retired — several open todos are stale

## What I found

The batch13 task assigned to me was: "Redirect the 4 DeFi live handlers (dex_swaps_handler, solana_defi_handler,
evm_defi_handler, aggregator_route_handler) that still write to non-migrated legacy buckets onto their dedicated
migrated-bucket targets", sourced from `defi_migration_audit_log_2026_07_24.md`'s open `[SCRIPT] P1` "REDIRECT the 4
DeFi live handlers" todo (that doc's line ~528). That todo's premise, verbatim from the 2026-06-08 audit trail
verbatim-extracted into the doc: 4 handlers write to a shared legacy "orphan" bucket (`market-data-tick-defi`, kind
`market-data`) while the "correct" migrated destination is a set of DEDICATED per-data_type buckets (`dex-pools-prd`,
`dex-swaps-prd`, `lending-indices-prd`, `perp-funding-prd`, `lst-rates-prd`, `oracle-prices-prd`, plus `gas-fees-prd`/
`liquidations-prd`/`aggregator-routes-prd` added later in the same doc).

Reading the CURRENT live code + config (2026-08-14) shows this premise is now false:

1. **`deployment-service/configs/cloud-providers.yaml`** (the SSOT `resolve_bucket_name`/`get_write_bucket_name` load)
   has NO entries for `dex-pools`, `dex-swaps`, `lending-indices`, `perp-funding`, `lst-rates`, `oracle-prices`,
   `gas-fees`, `eigenlayer-rewards`, `evm-defi`, or `solana-defi` as bucket kinds. Each removal is dated + rationale'd
   inline:
   - `REMOVED 2026-07-10 (bucket estate cleanup, [[gcs_bucket_estate_cleanup_2026_07_10]])`: dex-swaps, evm-defi,
     solana-defi, lending-indices, oracle-prices, liquidations — "Confirmed zero callers workspace-wide... every writer
     for these DeFi reference-data types resolves `get_write_bucket_name("market_data", asset_group="defi")` instead
     (the shared `market-data-tick-defi-{env}-{pid}` bucket)."
   - `gas-fees REMOVED 2026-07-12` — last real caller repointed to `kind="tick-data"`.
   - `eigenlayer-rewards REMOVED 2026-07-16` — its only caller repointed to `kind="tick-data"`.
   - `dex-pools + lst-rates + perp-funding REMOVED 2026-07-13 ([[defi_dedicated_bucket_shared_migration_2026_07_13]])` —
     "every real reader/writer/scanner migrated to `kind="tick-data"`... every (venue, data_type, day) shard verified
     present there (6,941 gap objects backfilled), dedicated buckets retired."
2. **`_KIND_ALIASES["tick-data"] = "market-data"`** (`unified_trading_library/cloud_interface/bucket_naming.py:108`) —
   `tick-data` and `market-data` resolve to the byte-identical bucket name. There is exactly ONE DeFi tick-data bucket
   today: `market-data-tick-defi-{env}-{pid}`.
3. **Direct code read of the 4 "orphan" handlers** — all 4 already call the shared-bucket resolver, not a legacy one:
   - `dex_swaps_handler.py:164` — `resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="defi")`
   - `solana_defi_handler.py:483` — `get_write_bucket_name("market_data", "DEFI")`
   - `evm_defi_handler.py:545` — `get_write_bucket_name("market_data", "defi")`
   - `aggregator_route_handler.py:490` — `get_write_bucket_name("market_data", "defi")` Compare the "already migrated"
     handlers the audit doc claims are correct: `dex_pools_handler.py:640`, `lending_indices_handler.py:657`,
     `lst_rates_handler.py:331/383/420/484` — every one calls `get_write_bucket_name("market_data", "defi")` (or the
     `asset_group="DEFI"` case-insensitive equivalent). **All 8 handlers resolve the identical bucket name.** There is
     no divergence left to redirect.
4. **The migrator's `_SPECS` dest bucket is a hardcoded literal, disconnected from the yaml SSOT**:
   `migrate_defi_full_v9_canonical.py:325` — `base_prd = f"{stem}-prd-{project_id}"` — bypasses
   `resolve_bucket_name`/yaml entirely. `aggregator-routes` (added as the migrator's 9th spec in
   `_migrate_defi_classify.py`, per batch13's already-checked item 6) does not and never did appear in
   `cloud-providers.yaml` — its computed dest bucket `aggregator-routes-prd-{pid}` is not a provisioned GCS bucket under
   the current architecture.

## Why it matters

The redirect todo cannot be completed as scoped — its target (dedicated per-data_type buckets) does not exist and was
deliberately retired by a LATER, closed-out architectural decision that went the opposite direction (consolidate onto
one shared bucket, differentiate by `data_type=` path segment). The goal the todo was actually chasing — "stop DeFi
handlers from writing to divergent buckets" — is already TRUE today, just achieved by the opposite mechanism (retire the
dedicated buckets, not redirect handlers onto them).

This also puts a shadow over several OTHER still-open todos in `defi_migration_audit_log_2026_07_24.md`, all premised on
the same retired dedicated-bucket model:

- The **gas-fees manifest-rebuild-scope P1 todo** (doc, "MANIFEST-REBUILD SCOPE GAP") assumes `rebuild_defi_manifest`
  needs to rebuild manifests over 7 SEPARATE dedicated `-prd-` buckets — those buckets don't exist; the manifest for
  every DeFi data_type already lives in the one shared bucket's `_index`.
- The **delete-after-migration P1 todo** (doc, "DELETE the duplicate/legacy DeFi orphan buckets AFTER...") lists
  `market-data-tick-defi{,-prd}` itself as a delete-AFTER-redirect candidate — but that is now the PERMANENT canonical
  bucket, not a legacy one to delete. This todo's target has inverted.
- The **aggregator-routes 9th migrator spec** (batch13's already-checked item 6, this doc's `_migrate_defi_classify.py`
  registration) targets a dest bucket (`aggregator-routes-prd-{pid}`) that was never provisioned — its own `--apply`
  step (if ever run) would fail or silently create an orphan bucket outside the yaml SSOT.
- The **VERIFY-then-MIGRATE unique orphan gaps P1 todo** (evm-defi 2022-03..10 Aave range, solana-defi `marinade`,
  market-data-tick-defi KAMINO/lending) may still be valid on its own terms (verifying whether OLD legacy-bucket data
  has a live-bucket twin), but its migration TARGET language ("into `lending-indices-`" / "into `lst-rates-`") needs
  re-reading against the current single-bucket model before anyone dispatches it.

None of this is a data-correctness bug today — the live write path is fine (confirmed: all 8 handlers converge on one
bucket). It's a stale-doc / SSOT-contradiction hazard: an agent picking up any of the above todos without first
independently re-verifying the bucket architecture (as this investigation had to do) would burn real time chasing a
target that doesn't exist, or worse, could `--apply` a migration write into a hand-rolled bucket name outside the
provisioning SSOT.

## Recommended decision

1. **The REDIRECT todo (this dispatch)**: mark resolved-as-moot in `defi_migration_audit_log_2026_07_24.md` — no code
   change needed, evidenced by this issue doc. (Handled by `defi_satellite_ao_dispatch_batch13_2026_08_13_finalize.md`
   todo 1's evidence-reconciliation pass — cite this issue doc there.)
2. **Gas-fees manifest-rebuild-scope + delete-after-migration + aggregator-routes-9th-spec todos**: need a human/
   judgment re-read against the current bucket architecture before further dispatch — recommend the next
   `/na-eligibility-audit` or `/ag-closeout-audit` defi-tranche pass (or a direct operator ruling) either strikes them
   as moot or rewrites them against the single-bucket model. Left as `assigned_vm: NA` here rather than resolved, since
   striking a still-open P1 todo needs the doc owner's confirmation, not a unilateral edit from an unrelated dispatch.
3. No GCS/bucket state change is proposed or required by this issue doc itself — purely a doc-accuracy finding.
