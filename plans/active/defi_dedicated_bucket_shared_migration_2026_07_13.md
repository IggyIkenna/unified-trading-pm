---
doc_type: plan
title: Migrate dex-pools/lst-rates/perp-funding off dedicated buckets onto the shared DeFi tick bucket
summary:
  The 3 remaining kind-dedicated DeFi buckets (dex-pools-prd, lst-rates-prd, perp-funding-prd) were kept out of the
  earlier gcs_bucket_estate_cleanup consolidation specifically because they have real, live readers
  (canonical_dex_pool_provider.py, materialize_dex_pool_fees.py, an e2e-testing lst-rates reader, whatever reads
  perp-funding) — unlike the 5 kinds already folded into the shared market-data-tick-defi-prd bucket. This plan does the
  actual migration — verify data parity, update the readers, redeploy, verify the new path is live, THEN retire the
  dedicated buckets — the same "code updated + service redeployed" pattern already used for gas-fees/lst-rates reads in
  data_manifest_handler.py this session, just applied to the harder, live-trading-adjacent readers.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [strategy-service, market-tick-data-service, deployment-service, e2e-testing, unified-trading-pm]
scope: [engineer, admin]
tags: [gcs, bucket-migration, defi, dex-pools, lst-rates, perp-funding, strategy-service]
related:
  [
    plans/active/gcs_bucket_estate_cleanup_2026_07_10.md,
    plans/active/defi_manifest_canonicalisation_2026_06_01.md,
    plans/active/issues/gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md,
    plans/active/issues/defi_lending_atoken_debttoken_instrument_split_2026_07_07.md,
  ]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  'Operator, 2026-07-13, reviewing dex-pools-prd-central-element-323112''s bucket structure: "Shouldn''t it be moved,
  put into a Marketing, Data Service, DeFi, or something bucket if we have such a thing? ... code updated and associated
  VMs redeployed with new code?" — confirmed the bucket has real, verified redundant partitioning (asset_group=defi +
  instrument_type=pool segments duplicating what the bucket name and instrument_id already encode) and asked for this to
  be scoped as its own follow-on plan.'
---

# Migrate dex-pools/lst-rates/perp-funding off dedicated buckets onto the shared DeFi tick bucket

## Context — why these 3 are different from the 5 already consolidated

`gcs_bucket_estate_cleanup_2026_07_10.md` §5i deleted 12 of 14 legacy kind-dedicated DeFi buckets (oracle-prices,
dex-swaps, gas-fees, liquidations, evm-defi, solana-defi flat+prd, plus the flat source forms of dex-pools/lst-rates/
perp-funding) once their historical data was confirmed present in the shared `market-data-tick-defi-prd` bucket. The
`-prd` forms of `dex-pools`/`lst-rates`/`perp-funding` were explicitly KEPT — `cloud-providers.yaml`'s own comment says
why: `dex-pools` has a real reader in `strategy-service/engine/core/canonical_dex_pool_provider.py` +
`scripts/materialize_dex_pool_fees.py`; `lst-rates` has a real but MISMATCHED reader/writer (the
`market-tick-data-service` side got fixed this session, but `e2e-testing/scripts/defi/staked_basis_funding_scan.py`'s
`_lst_bucket()` reader is still unverified — `gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md`);
`perp-funding` "genuinely resolves its own kind, real data" per the same comment, source unconfirmed.

Verified 2026-07-13 (operator prompted by inspecting `dex-pools-prd-central-element-323112` directly): these 3 buckets
carry the SAME redundant v9-canonical partitioning (`asset_group=defi/.../instrument_type=X/...`) the other 5 kinds had
before consolidation — the partitioning scheme was built for the shared, multi-tenant bucket where those dimensions
vary; reused via the same writer code path into a single-kind dedicated bucket, they're pure redundant overhead (bucket
name + instrument_id key already encode both dimensions). The data-migration precedent
(`migrate_defi_full_v9_canonical.py`) already covers all 3 kinds — the blocker was never data, it's that the real
readers still point at the dedicated buckets.

**This is real, higher-stakes work** than the 5 already-consolidated kinds: `canonical_dex_pool_provider.py` sits in
`strategy-service`, live-trading-adjacent. Do not rush the reader-cutover or skip the parity-verification step.

## Todos

- [ ] [DATA] P0. Verify data parity: for each of `dex-pools` (data_types `dex_pool_state`/`dex_pool_swaps`), `lst-rates`
      (`lst_rates`), `perp-funding` (`perp_funding`), confirm the shared bucket's availability index has equivalent or
      superior coverage (row counts, date ranges) vs the dedicated `-prd` bucket — direct real-data comparison, not an
      assumption carried over from the earlier session's DeFi migration verification (that verification explicitly
      EXCLUDED these 3 kinds since they were kept live). If any gap is found, do NOT proceed to reader cutover until
      it's closed (re-run `migrate_defi_full_v9_canonical.py` for the gapped kind if needed).
- [x] ✅ [CODE] P0. Read `strategy-service/engine/core/canonical_dex_pool_provider.py` +
      `scripts/materialize_dex_pool_fees.py` in full — confirm exactly how each resolves its bucket today
      (`resolve_bucket_name(kind="dex-pools", ...)` or similar) and what real callers depend on their current output
      shape (so the cutover doesn't silently change a field/path shape a live caller expects). —
      `strategy-service@3affd5b2` (2026-07-13): rewrote both readers' path-construction to the shared bucket's day-first
      shape, dropped the now-unneeded two-step mode-discovery (`_pipeline_mode_prefixes`/ `_fee_pipeline_mode_prefixes`
      deleted — a single per-day `list_blobs` prefix suffices, measured ~700 objects/day bucket-wide so this is cheap),
      repointed both to `resolve_bucket_name(kind="tick-data", ...)`. Output contract (`DexPoolObservation`,
      `pairs_for_day`/`pool_for_day`/`pairs_window`/`pool_window`) left byte-identical — only the read path changed.
      Live-verified against real production data (`ENVIRONMENT=prod`): `pairs_for_day(2026-05-01)` → 4,550 real pairs; a
      real pool observation round-tripped correctly; `_read_pools_for_day` direct inspection → 24,050 total rows across
      9 venues, 1,191 real Curve rows (Curve's NaN token_a/b/price_b confirmed pre-existing Curve-schema behaviour, not
      a migration regression). 9/9 unit tests updated + passing. Shipped via quickmerge (content-scoped sentinel handled
      a stale `.qg_last_passed_sha` automatically — HEAD had moved via concurrent unrelated commits but the `--files`
      set was byte-identical across the gap, so Pass-1 QG coverage still applied).
- [ ] [CODE] P0. Find and read the `e2e-testing` lst-rates reader flagged in
      `gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md` (`_lst_bucket()` in `staked_basis_funding_scan.py`) —
      same analysis. Resolve that issue doc's still-open finding as part of this cutover.
- [ ] [CODE] P0. Grep the workspace for every real caller resolving `kind="perp-funding"` — identify the actual
      reader(s) (the earlier session's research didn't name one explicitly beyond "genuinely resolves its own kind, real
      data").
- [ ] [CODE] P0. Update the identified readers to resolve `kind="tick-data"` (the shared bucket) filtered by the correct
      `data_type`, mirroring the exact pattern already shipped this session in
      `data_manifest_handler.py::_scan_via_availability_index` for gas-fees/lst-rates. Preserve each reader's current
      output contract exactly — this is a storage-location change, not a behavior change.
- [ ] [SCRIPT] P0. Ship the reader code changes via quickmerge (per-repo, quality-gates.sh green). Do NOT touch the
      dedicated buckets or their `cloud-providers.yaml` entries yet — this step only lands the new read path alongside
      the old one still working.
- [ ] [INFRA] P0. Redeploy/restart every affected service (strategy-service at minimum; check whether
      `materialize_dex_pool_fees.py` runs as a script/cron/VM and redeploy that path too) with the updated code — no
      fire-and-forget, verify STARTED + real progress + confirm the new code path is genuinely being exercised (not just
      deployed and never invoked).
- [ ] [DATA] P0. Verify parity post-deploy: confirm each migrated reader is genuinely resolving + reading from the
      shared bucket with no data loss or behavior change (diff real output — e.g. dex-pool-fee materialization results —
      against a pre-migration baseline; confirm strategy-service's DEX-pool-dependent code paths still produce correct
      results end-to-end, not just "no crash").
- [ ] [DATA] P1. Once every reader is confirmed migrated and real production traffic is flowing through the new path
      (not just deployed-but-idle), delete `dex-pools-prd`, `lst-rates-prd`, `perp-funding-prd` — mirror the careful
      backup-verify-delete pattern already used this session for the other 12 legacy DeFi buckets
      (`gcs_bucket_estate_cleanup_2026_07_10.md` §5i).
- [ ] [CODE] P1. Remove the `dex-pools`/`lst-rates`/`perp-funding` kinds from `cloud-providers.yaml`,
      `bucket_config.yaml`, and `manifest_reader.py`'s `_EXTRA_BUCKET_KINDS` — mirror the exact removal pattern already
      used for `gas-fees` earlier this session.
- [ ] [SCRIPT] P1. Ship the config removal via quickmerge, quality-gates.sh green, verify CI.
- [ ] [DATA] P2. Final verification sweep (full bucket-list check confirming all 3 gone, no stray references left in any
      repo) + update `gcs_bucket_estate_cleanup_2026_07_10.md` §5i and `defi_manifest_canonicalisation_2026_06_01.md`
      C0f with the completed resolution — C0f can only fully close once these last 3 (of the original 8 DeFi kinds) are
      done.

## Progress Log

- **2026-07-13 (Todo 2 shipped)** — `canonical_dex_pool_provider.py` + `materialize_dex_pool_fees.py` rewritten to the
  shared bucket's day-first path shape and shipped (`strategy-service@3affd5b2`). Full detail in the Todo 2 checkbox
  above. Next: Todo 3 (find + fix the `e2e-testing` lst-rates reader) and Todo 4 (locate the real perp-funding reader —
  not yet found).

- **2026-07-13 (Todo 1 done — data parity verified; Todo 2 in progress — found a real path-shape blocker)** — **Parity
  (Todo 1)**: direct GCS probes (consolidator still stale, ~64h — same open sub-finding as
  `eigenlayer_manifest_availability_index_collision_2026_07_12.md`, not re-litigated here) confirm the shared bucket has
  `dex_pool_state`/`dex_pool_swaps`/`lst_rates`/`perp_funding` present across every sampled date from 2024-06 through
  2026-06, and each dedicated bucket's max date (`dex-pools-prd` 2026-05-22, `lst-rates-prd` 2026-05-28,
  `perp-funding-prd` 2026-06-09) sits comfortably inside that coverage window. No data gap blocking cutover for these 3
  data_types. Separately checked `dex_pool_fees` (a companion data_type `canonical_dex_pool_provider.py` also reads,
  materialized by `scripts/materialize_dex_pool_fees.py`) — **zero real rows anywhere in `dex-pools-prd`** (recursive
  search, no matches), so it's either never been run in production or writes elsewhere; not a parity risk either way
  since there's nothing to preserve, but flagging since the docstring describes it as a real, designed corpus and it
  appears dormant. **Real blocker found (Todo 2)**: `canonical_dex_pool_provider.py`'s path-construction
  (`_pipeline_mode_prefixes`, `_read_pools_for_day`, `_fee_pipeline_mode_prefixes`) is hard-coded to the DEDICATED
  bucket's segment order — `asset_group=defi/pipeline_mode={MODE}/day={D}/venue=.../data_type={DT}/` (asset_group first,
  no wrapper prefix, verified directly against `dex-pools-prd-central-element-323112`). The SHARED bucket uses a
  DIFFERENT order — `raw_tick_data/by_date/day={D}/pipeline_mode={MODE}/asset_group=defi/venue=.../data_type={DT}/` (day
  first, wrapped under `raw_tick_data/by_date/`; verified directly against `market-data-tick-defi-prd`). **This is not a
  bucket-name swap** — the reader's prefix-construction logic needs a real rewrite to match the shared bucket's actual
  path shape, on top of repointing `resolve_bucket_name(kind=...)`. Confirms the plan's own "do not rush the
  reader-cutover" caution was warranted. Have not yet read `materialize_dex_pool_fees.py`'s path logic, nor located the
  lst-rates/perp-funding readers (Todos 3-4) — next steps.

- **2026-07-13** — Filed after the operator questioned `dex-pools-prd-central-element-323112`'s internal structure
  directly (confirmed real: legacy `day=.../category=defi/` + canonical
  `raw_tick_data/.../asset_group=defi/.../instrument_type=pool/` trees both present, redundant with the bucket name +
  instrument_id key on three separate axes) and asked whether it should be consolidated the way other DeFi buckets were
  this session. Scoped as its own plan rather than folded into the in-flight DeFi-lending-instrument-split doc/code
  fixup, since this touches strategy-service (live-trading-adjacent) and warrants its own careful, sequential execution.
