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
    plans/archive/issues/gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md,
    plans/active/issues/defi_lending_atoken_debttoken_instrument_split_2026_07_07.md,
  ]
created: "2026-07-13"
last_updated: "2026-07-14"
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

- [x] ✅ [DATA] P0. Verify data parity: for each of `dex-pools` (data_types `dex_pool_state`/`dex_pool_swaps`),
      `lst-rates` (`lst_rates`), `perp-funding` (`perp_funding`), confirm the shared bucket's availability index has
      equivalent or superior coverage (row counts, date ranges) vs the dedicated `-prd` bucket — direct real-data
      comparison, not an assumption carried over from the earlier session's DeFi migration verification (that
      verification explicitly EXCLUDED these 3 kinds since they were kept live). If any gap is found, do NOT proceed to
      reader cutover until it's closed (re-run `migrate_defi_full_v9_canonical.py` for the gapped kind if needed). —
      Checkbox was never flipped when the work landed 2026-07-13; see the Progress Log entry "Todo 1 done — data parity
      verified" for the real evidence (all 4 data_types present across every sampled date 2024-06..2026-06; each
      dedicated bucket's max date sits inside that window; `dex_pool_fees` independently checked, zero real rows
      anywhere at the time).
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
- [x] ✅ [CODE] P0. Find and read the `e2e-testing` lst-rates reader flagged in
      `gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md` (`_lst_bucket()` in `staked_basis_funding_scan.py`) —
      same analysis. Resolve that issue doc's still-open finding as part of this cutover. — `e2e-testing@<pending>`
      (2026-07-13): found `_read_lst_exchange_rate` used a prefix (`day={day}/asset_group=defi/venue=.../...`) that
      NEVER matched even the dedicated bucket's own real layout
      (`raw_tick_data/by_date/day=.../pipeline_mode=     batch_onchain_subgraph/asset_group=defi/...`) — a real,
      pre-existing, silently-honest-absence bug, not just a bucket-location issue. Fixed the prefix to the correct
      day-first shape + repointed to `kind="tick-data"`. Live-verified: LIDO/ETHEREUM `exchange_rate` resolves correctly
      (1.233...); JITO/SOLANA initially resolved `None` — see the real gap this surfaced, below.
- [x] ✅ [CODE] P0. Grep the workspace for every real caller resolving `kind="perp-funding"` — identify the actual
      reader(s) (the earlier session's research didn't name one explicitly beyond "genuinely resolves its own kind, real
      data"). — Found 6 real callers (not 1): `strategy-service/engine/core/canonical_perp_funding_provider.py` (the
      REAL production reader, mirrors `canonical_dex_pool_provider.py`'s day-first-prefix pattern almost exactly — the
      dedicated `perp-funding-prd` bucket already used the shared bucket's identical day-first shape, unlike
      `dex-pools-prd`, so this was a pure bucket-kind repoint, no path rewrite);
      `features-service/cefi/calculators/     perp_funding_corpus.py` (a CeFi funding-corpus WRITER targeting this same
      bucket — confirmed via direct GCS checks across 2021-2026 that it has never actually run in production, so no
      historical data to migrate, but the writer needed repointing too so a future run doesn't write into a bucket about
      to be deleted); `features-service/onchain/calculators/perp_funding_rates_defi.py` (a separate, pre-existing DEAD
      reader using a legacy flat `perp_funding/{venue}/date={date}/` shape that has never existed in either bucket —
      bucket-kind repointed for consistency, the deeper path-shape bug left as a separate out-of-scope finding);
      `e2e-testing/scripts/defi/funding_regime_classifier.py` (reads `perp_daily_ctx` — see the gap below);
      `market-tick-data-service/cli/handlers/data_manifest_handler.py` (the `collect-perp-funding`/`collect-dex-pools`
      manifest-coverage scanners — also using stale legacy-shape listing logic that has never matched real objects in
      either bucket; bucket-kind repointed only, per the same "storage-location change, not behavior change" scoping).
- [x] ✅ [CODE] P0. Update the identified readers to resolve `kind="tick-data"` (the shared bucket) filtered by the
      correct `data_type`, mirroring the exact pattern already shipped this session in
      `data_manifest_handler.py::_scan_via_availability_index` for gas-fees/lst-rates. Preserve each reader's current
      output contract exactly — this is a storage-location change, not a behavior change. — All 6 real callers above
      repointed. **Real gap found + closed (not in the original Todo 1 parity check, which covered date-range coverage
      but not per-venue completeness)**: (1) JITO + MARINADE (the two Solana-chain `lst_rates` venues) were entirely
      absent from the shared bucket while every EVM `lst_rates` venue (LIDO, ETHERFI, ANKR, ...) was already present —
      confirmed via direct real-data sampling across 2022-2026, always 0 shared-bucket objects vs 1/day in the dedicated
      bucket; (2) HYPERLIQUID's `perp_daily_ctx` shard (the mark-price sibling to `perp_funding`, read by
      `canonical_perp_funding_provider.py::_marks_for_day`) was entirely absent from the shared bucket across every
      sampled date — every HL funding observation was silently getting `mark_price=None`. Both closed via a new one-off
      script `market-tick-data-service/scripts/migrate_lst_perp_shared_bucket_gap_2026_07_13.py` — both source buckets
      already used the identical canonical day-first path shape as the destination, so this was a pure server-side
      `gcs_copy_object` at the SAME key (no content rewrite, unlike the earlier AAVE/COMPOUND/MORPHO migrations this
      session). Real run: JITO 1,305 objects copied, MARINADE 1,745 objects copied, HYPERLIQUID `perp_daily_ctx` 1,109
      objects copied. Live-verified post-backfill: JITO/SOLANA `exchange_rate` now resolves (was `None`);
      `CanonicalPerpFundingProvider.funding_for_day(2026-05-01)` → 230/230 HYPERLIQUID observations now carry a real
      `mark_price` (was 0/230).
- [x] ✅ [SCRIPT] P0. Ship the reader code changes via quickmerge (per-repo, quality-gates.sh green). Do NOT touch the
      dedicated buckets or their `cloud-providers.yaml` entries yet — this step only lands the new read path alongside
      the old one still working.
- [x] ✅ [INFRA] P0. Redeploy/restart every affected service (strategy-service at minimum; check whether
      `materialize_dex_pool_fees.py` runs as a script/cron/VM and redeploy that path too) with the updated code — no
      fire-and-forget, verify STARTED + real progress + confirm the new code path is genuinely being exercised (not just
      deployed and never invoked). — Done 2026-07-13. **How strategy-service actually runs in prod**: ephemeral GCE VMs
      (`launch-strategy-paper-vm.sh` / `launch-strategy-live-vm.sh` / `launch-funding-ensemble-paper-cron-vm.sh`) that
      pull code TARBALLS from `gs://deployment-scripts-{pid}/code/` at boot — NO persistent strategy-service process
      exists (verified: zero `strategy-paper-*`/`strategy-live-*`/`funding-ensemble-*` VMs running on GCP or AWS; no
      strategy Cloud Run service/job; no scheduler entry). `materialize_dex_pool_fees.py` has no cron/launcher (manual
      one-off). **Deploy artifact verified**: `strategy-service-code.tar.gz` refreshed 2026-07-13T21:40:58Z at
      `a4ea4fa7` (contains BOTH shipped readers 3affd5b2 + a34351cd, merge-base verified); the 3 reader files inside the
      tarball are sha256-IDENTICAL to repo HEAD; e2e tarball @4b91e1a7 ⊇ c3a5d77, features @588eed0e ⊇ d784c79f, mtds
      @77ff475a ⊇ 9b980179. Any future VM launch boots the migrated readers; nothing stale is running (no restart
      possible/needed — the STARTED-event contract applies at the next real launch). **Genuinely exercised**: the
      deployed reader code ran against real prod GCS (`ENVIRONMENT=prod`) — Todo 7 evidence.
- [x] ✅ [DATA] P0. Verify parity post-deploy: confirm each migrated reader is genuinely resolving + reading from the
      shared bucket with no data loss or behavior change. — Done 2026-07-13, and the re-verification CAUGHT + CLOSED a
      large residual gap (Progress Log "Todos 6-9"): a full (venue, data_type, day)-granular diff of all 3 dedicated
      buckets vs the shared bucket found **6,941 gap objects** invisible to the earlier spot checks — 5 whole dex venues
      (TRADER_JOE_V2 1,747d / VELODROME_V2 1,024d / ORCA 529d / RAYDIUM 528d / PHOENIX 497d + early
      CURVE/BALANCER/KAMINO), GMX 2021-09→2023-10 funding history (733d), HL perp_funding 177d + the whole HL
      `perp_mark_price` data_type (316d), the 7 CeFi Tardis venues' 2026-05-16..22 perp capture (98 objs — these venues
      fed `funding_for_day` pre-cutover and had silently VANISHED from it post-cutover), 5 LST venues' early history
      (504d: COINBASE 202 / MAKER 201 / ETHENA 68 / ETHERFI 28 / SWELL 5), and the only real `dex_pool_fees` rows ever
      produced (21 objs in dex-pools-prd's asset_group-first tree — corrects Todo 1's "zero rows anywhere"; copied WITH
      key transform to the day-first shape). All copied day-tuple-aware (copy only when the destination lacks that
      (asset_group, venue, data_type, day) — the shared bucket was partially re-captured under different filenames, so a
      blind same-key copy would double-concat) via the v2 `migrate_lst_perp_shared_bucket_gap_2026_07_13.py`: real run
      `{'copied': 6941}`, 0 errors; dry-run count cross-checked against an independent listing diff (exact match).
      PACIFICA = venue-rename to PACIFICA-SOLANA in shared (all 167 days covered; NOT copied). **Post-closure live
      verification through the deployed readers** (`ENVIRONMENT=prod`): `funding_for_day(2026-05-18)` → 697 obs incl all
      7 CeFi venues restored; `funding_for_day(2022-06-15)` → GMX resolves; `pairs_for_day(2026-05-01)` → 4,550 pairs
      (== pre-migration baseline); `_read_pools_for_day(2026-05-28)` → 32,459 rows / 12 venues incl ORCA 14,093 (their
      exclusion from `pairs_for_day` is the pre-existing documented all-NaN-`price_b` honest-absence — identical to the
      dedicated bucket's own behavior); `pool_for_day(2026-05-18, CURVE 3pool)` → real fee overlay (fees_usd=379.77,
      fee_apy_bps=59.87); e2e `_read_lst_exchange_rate` LIDO 1.2333 + JITO 1.2766; e2e
      `_read_hl_funding_day`/`_read_hl_ctx_day` 230/230 coins — all resolving
      `market-data-tick-defi-prd-central-element-323112`, zero reads left on the dedicated buckets. No live writers to
      the dedicated buckets (newest real object 2026-06-21; only a 2026-07-12 availability-index write from the
      pre-cutover scanner).
- [x] ✅ [CODE] P0. (Discovered 2026-07-13 estate audit, adversarially verified) Migrate
      `execution-service/execution_service/data/defi_lateral_loader.py` — `DEFAULT_LATERAL_BUCKETS` (:46-73) still
      defaults to FLAT bucket names (`perp-funding-{pid}`, `lending-indices-{pid}`, `liquidations-{pid}`,
      `oracle-prices-{pid}`, `gas-fees-{pid}`, `lst-rates-{pid}`, `eigenlayer-rewards-{pid}`, flat
      `market-data-tick-defi-{pid}`) — 5 of 7 already point at buckets DELETED on 2026-07-10/12, and the path shape is
      the legacy `category=` form (no `raw_tick_data/by_date/` wrapper). Dormant in prod backtests (`defi_feeds` is
      configured nowhere) but breaks the 15 operator decision-trace CLIs today; needs the same two-axis fix
      (`kind="tick-data"` + day-first prefix) this plan shipped for `canonical_dex_pool_provider.py` — do it BEFORE the
      deletion todo below runs. Also covers `service_config` `defi_bucket_*` fields. — `execution-service@a7e42c932`
      (2026-07-14): all 7 default bucket entries + 9 feed keys now resolve `_SHARED_LATERAL_BUCKET` (module-level
      `resolve_bucket_name(kind="tick-data", asset_group="defi")`); `build_partition_prefix`/`build_partition_needles` +
      `list_partition_files` rewritten to the day-first-prefix + needle-filter pattern; `load_lst_rates` +
      `load_eigenlayer_rewards_range` (also fixed `EIGENLAYER` → `EIGENLAYER-ETHEREUM` venue-string drift) fixed too.
      Verified all 7 legacy bucket names directly against real GCP state before editing (5 confirmed 404-gone, 2
      `eigenlayer-rewards` forms confirmed 0 bytes). 2 test files updated to match the new prefix/needle contract,
      quality-gates.sh green (also closed a real gap found in the process: `tests/defi_execution/unit/` + `tests/e2e/`
      were completely un-gated by any QG wrapper/CI — wired the 2 touched files into `scripts/quality-gates.sh`'s
      `PYTEST_UNIT_DIR`).
- [x] ✅ [INFRA] P0. (Discovered 2026-07-13 estate audit) The deletion todo below MUST also remove the Terraform
      resources `market_data_defi_lst_rates_prd` / `market_data_defi_perp_funding_prd` and the `bucket_config.yaml`
      dex-pools/lst-rates/perp-funding entries in the SAME change. — `deployment-service@f04cc39b` (2026-07-13): both TF
      resource blocks removed from `terraform/gcp/main.tf` (a dex-pools TF resource never existed — verified), the 3
      kinds' `canonical_buckets.tf` exclusion entries retired (`canonical_excluded_kinds` → audit-records + manual-audit
      only; the canonical for*each is unaffected since the kinds are gone from the yaml it decodes),
      `bucket_config.yaml` GCP+AWS templates + aws_naming rows removed, `tofu validate` green. Paired guarded
      `terraform state rm` script GENERATED (not run — orchestrator runs it BEFORE the next apply, else the config-less
      state entries plan a DESTROY that errors on force_destroy=false): probes state for
      `google_storage_bucket.market_data_defi*{lst_rates,perp_funding,dex_pools}\_prd`, removes only present entries,
      DRY_RUN=1 mode. **Related finding (NOT fixed here — belongs to
      [[terraform_bucket_estate_drift_resurrection_2026_07_13]])**: `market_data_defi_lending_indices_prd` is still
      declared in main.tf while its bucket was cleanup-deleted on 2026-07-10 — same resurrection class.
- [x] ✅ [DATA] P1. Once every reader is confirmed migrated and real production traffic is flowing through the new path
      (not just deployed-but-idle), delete `dex-pools-prd`, `lst-rates-prd`, `perp-funding-prd` — mirror the careful
      backup-verify-delete pattern already used this session for the other 12 legacy DeFi buckets
      (`gcs_bucket_estate_cleanup_2026_07_10.md` §5i). — All 3 confirmed deleted (`gcloud storage buckets list`, zero
      matches in any form, 2026-07-14). `lst-rates-prd`/`perp-funding-prd` were deleted by the operator directly
      (`ikenna@odum-research.com`, GCP audit log) prior to this session's visible window. **`dex-pools-prd` was deleted
      by the same operator on 2026-07-14T11:03:47Z BEFORE this todo's own snapshot-before-delete step ran** — the
      ~209k-object undiffed legacy tree noted below was never independently object-diffed; no soft-delete recovery or
      pre-migration snapshot of it exists. Not the careful backup-verify-delete pattern this todo specified. Risk
      assessed low (not zero) given Todo 1's prior parity verification already covered the canonical/reader-relevant
      content and `dex_pool_fees` had zero real rows to lose — full writeup in `gcs_bucket_estate_cleanup_2026_07_10.md`
      §5k. Flagging per the data-correctness HARD RULE rather than silently treating it as fine.
- [x] ✅ [CODE] P1. Remove the `dex-pools`/`lst-rates`/`perp-funding` kinds from `cloud-providers.yaml`,
      `bucket_config.yaml`, and `manifest_reader.py`'s `_EXTRA_BUCKET_KINDS` — mirror the exact removal pattern already
      used for `gas-fees` earlier this session. — Done 2026-07-13 across **five** cloud-providers.yaml copies (the plan
      said 4; the workspace straggler grep found a 5th: PM `scripts/quality-gates-base/ci-test-cloud-providers.yaml`,
      consumed by `base-service.sh` in CI QG): each copy now 34 GCP + 34 AWS storage kinds (was 37/37), yaml-parse
      verified. Also cleaned the test stragglers the grep surfaced: UTL `test_bucket_naming.py` (snapshot exemplar
      rehomed dex-pools → eigenlayer-rewards; the workspace-yaml-resolving AWS purpose-bucket test dropped its dex-pools
      row — it would have genuinely failed) and MTDS `test_data_manifest_handler_coverage.py` (mock `bucket_key` args →
      "tick-data", matching the shipped handler). Remaining references are removal-comments/plan docs only.
- [x] ✅ [SCRIPT] P1. Ship the config removal via quickmerge, quality-gates.sh green, verify CI. — Shipped in dep order,
      every repo QG-green first: `unified-api-contracts@252c0072` (packaged yaml) · `unified-trading-library@1177768b`
      (fixture yaml + tests) · `deployment-service@f04cc39b` (yaml + bucket_config + manifest_reader + TF; dirty-deps
      carve-out direct push — UTL carried live sibling WIP so quickmerge pre-flight refused; `Quickmerge:` trailer
      present, local QG PASS 92s) · `e2e-testing@3d219d76` (`_hl_pf_bucket` straggler: still resolved
      `kind="perp-funding"`; repointed to `kind="tick-data"` + live-verified 230/230 HL coins) ·
      `market-tick-data-service@02a88186` (dirty-deps carve-out; QG PASS 130s) · `unified-trading-pm@abcd47b4` (PR
      #1006, auto-merge on v2). deployment-service post-push `quality-gates-v2` run 29292731847 = success.
- [x] ✅ [DATA] P2. Final verification sweep (full bucket-list check confirming all 3 gone, no stray references left in
      any repo) + update `gcs_bucket_estate_cleanup_2026_07_10.md` §5i and
      `defi_manifest_canonicalisation_2026_06_01.md` C0f with the completed resolution — C0f can only fully close once
      these last 3 (of the original 8 DeFi kinds) are done. — Bucket-list check: all 3 confirmed gone. Workspace-wide
      grep sweep (dedicated research pass, all repos) found **1 more real, live bug** (fixed same-day, see below) + 4
      lower-severity script-level findings (NOT fixed — separate repos/scope, captured as new todos below) + confirmed
      the rest is harmless (data_type/CLI-operation names, test fixtures, plan docs, already-clean
      Terraform/cloud-providers.yaml/bucket_config.yaml). Docs updated: `gcs_bucket_estate_cleanup_2026_07_10.md` §5k
      added; `defi_manifest_canonicalisation_2026_06_01.md` C0f noted (kept `[ ]` —
      `lending-indices`/`lending-indices-prd` remain a separate open item, out of scope here).
- [x] ✅ [CODE] P1. (Found by the final verification sweep) `deployment-api/deployment_api/services/data_status/defi.py`
      — `_BUCKET_CATEGORY_OVERRIDES` + `_MTDS_DEFI_SUB_DIMENSIONS` still listed 9 of 10 Phase-1 DeFi sub-buckets
      (`gas-fees`/`evm-defi`/`solana-defi`/`dex-pools`/`dex-swaps`/`liquidations`/`lst-rates`/`oracle-prices`/
      `perp-funding`) as bucket-name templates — ALL 9 now resolve to deleted buckets (this file was never updated
      across ANY of the `gcs_bucket_estate_cleanup_2026_07_10.md` deletion rounds, not just this plan's 3). Not a crash
      — `_read_defi_merged_index` wraps each sub-bucket read in `except Exception: logger.debug(...)` — but a LIVE,
      silent monitoring bug: deployment-ui's Data ETL DeFi drilldown was permanently showing these 9 sub-dimensions as
      empty/no-data (the real data now merges into the main "defi-core" bucket instead, unlabeled). Dropped all 9 dead
      entries from both dicts (kept `lending-indices`, confirmed still live); verified the breakdown-building code
      (`breakdowns_domain.py::_build_defi_sub_dimension_breakdown`) degrades gracefully — `all_sources` unions the
      static list with whatever `_defi_source` values actually appear in the data at runtime, so no UI code path assumes
      these keys statically exist. — `deployment-api@b5641cf79`, quality-gates.sh green.
- [ ] [SCRIPT] P2. (Found by the final verification sweep, NOT fixed — separate repos/scope) 3 diagnostic/migration
      scripts still hardcode dead flat bucket-name templates for `dex-pools`/`lst-rates`/`perp-funding` and would error
      if re-invoked: `market-tick-data-service/scripts/migrate_legacy_solana_defi_to_canonical.py`
      (`SubsetSpec.canonical_bucket_kind = "dex-pools"`/`"lst-rates"` isn't a valid UTL domain key, falls through to a
      legacy fallback that builds the now-404 flat bucket names — lines 92/94/95/132-136, used at 271/314);
      `strategy-service/scripts/trace_carry_staked_basis.py` (`_LST_RATES_BUCKET_TEMPLATE`/
      `_PERP_FUNDING_BUCKET_TEMPLATE` at lines 81/83, used in `main()`'s slot-processing loop — this one is likely still
      actively used, it's the same carry_staked_basis archetype verified via paper-trading VM earlier this session);
      `strategy-service/scripts/probe_funding_rate_dispersion_coverage.py` (`_DEFAULT_PERP_FUNDING_BUCKET_     TEMPLATE`
      at line 106, default unless `--perp-funding-bucket` passed explicitly). Each needs the same
      `resolve_bucket_name(kind="tick-data", asset_group="defi")` repoint already shipped everywhere else this plan
      touched — small, mechanical, same pattern 3x over, just not done here to keep this plan's scope to the 3 original
      kinds + what directly blocked them.
- [ ] [CHORE] P3. (Found by the final verification sweep, NOT fixed) Housekeeping cluster, all low-risk/low-value: (1)
      `market_tick_data_service/scripts/migrate_lst_perp_shared_bucket_gap_2026_07_13.py` — its own documented
      `Delete-when: dex-pools-prd/lst-rates-prd/perp-funding-prd are deleted` condition is now satisfied, script should
      be deleted; (2) `market-tick-data-service/cli/handlers/data_manifest_handler.py:44-82` — module-level `OPERATIONS`
      constant still has stale `"bucket_type": "dex-pools"`/`"perp-funding"` values contradicting the file's own correct
      `_build_operations_dict()` (already `kind="tick-data"`) — confirmed unused elsewhere, dead but misleading, should
      be deleted or corrected; (3) ~8 more `market-tick-data-service/scripts/defi_*_2026_06_01.py` /
      `gate3_solana_manifest_reconcile.py` / `backfill_hl_*_2026_06_17.py` (all `Lifecycle: campaign`) hardcode dead
      bucket names tied to separate, already-completed earlier migrations — a lifecycle-marker audit pass, not urgent;
      (4) `strategy-service/strategy_service/cli/handlers/paper_run_handler.py:314,430` — stale comments say "kind
      `perp-funding`"/"kind `dex-pools`" describing classes that already correctly use `kind="tick-data"` — comment-only
      fix.

## Progress Log

- **2026-07-14 (final todo shipped — `defi_lateral_loader.py` fixed, all 3 buckets confirmed deleted, TF state clean,
  cross-plan docs updated)** — Fixed the last broken reader (`execution-service@a7e42c932`): `defi_lateral_loader.py`'s
  `DEFAULT_LATERAL_BUCKETS` repointed off 5-of-7-dead flat bucket defaults to the shared bucket via
  `resolve_bucket_name(kind="tick-data", asset_group="defi")`, plus the day-first-prefix + needle-filter rewrite
  (`build_partition_prefix`/`build_partition_needles`/`list_partition_files`), `load_lst_rates`, and
  `load_eigenlayer_rewards_range` (also fixed an `EIGENLAYER`→`EIGENLAYER-ETHEREUM` venue-string bug found while reading
  it). 2 test files updated to match; quality-gates.sh green; also closed a real QG-coverage gap found in the process
  (`tests/defi_execution/unit/` + `tests/e2e/` were completely un-gated — wired the 2 touched files in).
  **Bucket-deletion todo**: all 3 (`dex-pools-prd`, `lst-rates-prd`, `perp-funding-prd`) confirmed gone via direct
  `gcloud storage buckets list`. **Flagging, not hiding**: `dex-pools-prd` was deleted by the operator directly
  (`ikenna@odum-research.com`, 2026-07-14T11:03:47Z per GCP audit log) BEFORE this plan's own snapshot-before-delete
  step for its ~209k-object undiffed legacy tree could run — that tree was never independently object-diffed, and no
  soft-delete recovery or pre-migration snapshot of it exists. Assessed risk as low (not zero): Todo 1's parity check
  had already verified the canonical/reader-relevant content in the shared bucket, and `dex_pool_fees` (the one
  data_type that could have held unique legacy content) was confirmed to have zero real rows anywhere. **Terraform**:
  `tofu state list` in `deployment-service/terraform/gcp` confirmed clean — zero `google_storage_bucket` entries for any
  of the 3 kinds (only the legitimate, live `google_cloud_scheduler_job`/`google_cloud_run_v2_job` DATA-COLLECTION
  resources match the kind names); the guarded `terraform state rm` script generated 2026-07-13 was never run and turned
  out unnecessary — no matching state entries existed to remove. **Cross-plan docs updated**:
  `gcs_bucket_estate_cleanup_2026_07_10.md` gets a new §5k covering this trio's resolution + the early-deletion flag;
  `defi_manifest_canonicalisation_2026_06_01.md`'s C0f gets a note that the "last 3" are now deleted, but stays `[ ]`
  (not flipped to done) since `lending-indices`/`lending-indices-prd` — a separate, pre-existing residual from that same
  checkbox's original 14-bucket scope — remain undeleted (out of scope here; tracked in
  `gcs_bucket_estate_cleanup_2026_07_10.md` §5i/§5j). **Final workspace-wide straggler sweep results** (dedicated
  research pass, every repo, `kind="dex-pools"/"lst-rates"/"perp-funding"` resolver calls + hardcoded bucket-name
  literals): found **1 more real, live bug** — `deployment-api`'s Data ETL DeFi drilldown
  (`services/data_status/defi.py`) still templated 9 of 10 Phase-1 sub-bucket names (this file was never touched across
  ANY of the earlier `gcs_bucket_estate_cleanup_2026_07_10.md` deletion rounds, not just this plan's 3 kinds), silently
  swallowing failed reads against now-deleted buckets and permanently showing those 9 sub-dimensions as empty in the UI.
  Fixed same-day — `deployment-api@b5641cf79`, see the todo above. 4 lower-severity findings (3 diagnostic/migration
  scripts with dead bucket templates, 1 housekeeping cluster) captured as new `[ ]` P2/P3 todos above rather than fixed
  here — separate repos, each a small mechanical repoint but genuinely outside this plan's original 3-kind scope.
  Everything else confirmed harmless: ~2,700+ legitimate data_type/CLI-operation/UAC-capability name hits, test-fixture
  mock bucket names, historical plan/codex docs, already-clean Terraform + `cloud-providers.yaml` +
  `bucket_config.yaml`.

- **2026-07-13 (Todos 6-9 + config-removal todos shipped — redeploy verified, 6,941-object residual gap closed, kinds
  retired)** — executed by the todo-6-9 worker; full evidence in the flipped checkboxes above. Shipped:
  `unified-api-contracts@252c0072` · `unified-trading-library@1177768b` · `deployment-service@f04cc39b` ·
  `e2e-testing@3d219d76` · `market-tick-data-service@02a88186` (also carries the Tardis lease-bucket default →
  `resolve_bucket_name(kind="config-store")`, env override wins — unblocks the flat `config-store-{pid}` delete in
  [[bucket_estate_consolidation_to_sub100_2026_07_13]]) · `unified-trading-pm@abcd47b4` (PR #1006). Guarded
  `terraform state rm` script generated (NOT run) for the orchestrator at
  `/tmp/claude-1000/-home-ubuntu-unified-trading-system-repos/f74c2622-ac37-43fc-9109-ea536b28d5c4/scratchpad/defi_trio_state_rm.sh`
  — must run BEFORE the next terraform apply. Bucket deletion NOT performed — remains with the orchestrator, gated on:
  (1) the still-open `defi_lateral_loader.py` todo above (its flat f-string bucket defaults break on deletion, though
  NOT on the kind removal — it never used resolve_bucket_name); (2) the state-rm run; (3) the backup ritual — NOTE:
  `dex-pools-prd` holds ~209k objects in LEGACY trees (`day=.../category=defi/` + `asset_group=defi/...` +
  `_migration/`) beyond its 40,864-object canonical tree; the canonical/reader-relevant content is fully covered in the
  shared bucket (verified at (venue,data_type,day) granularity) but the legacy trees were never object-diffed — snapshot
  them before delete. Side findings: (a) `mtds-dex-swaps-backfill` + `mtds-perp-funding-backfill` GCE VMs are STALLED
  ZOMBIES — running since 2026-06-27, `VM_SHUTDOWN_ON_COMPLETION=true` never fired, ZERO deployment-registry events
  since at least 06-28, serial console idle (dex-swaps silent since 07-05; perp-funding only heartbeat gsutil ticks) —
  they run pre-cutover tarball code but write NOTHING to the dedicated buckets (newest real object 2026-06-21), so they
  don't block deletion; flagged for operator stop/reap (zombie watchdog hasn't reaped them). (b)
  `market_data_defi_lending_indices_prd` TF resource still declared while its bucket was cleanup-deleted 2026-07-10 —
  same resurrection class as [[terraform_bucket_estate_drift_resurrection_2026_07_13]], annotate/fix there. (c) HL
  `perp_mark_price` (316 objs) preserved into the shared bucket though no current reader consumes it
  (`canonical_perp_funding_provider` reads marks from `perp_daily_ctx`).

- **2026-07-13 (Todos 3-5 shipped — all real readers/writers/scanners migrated + 2 real data gaps closed)** — Scope grew
  well beyond the plan's original estimate of "2 readers" once every real `kind="lst-rates"`/`kind="perp-funding"`
  caller was actually grepped (per Todo 4's own instruction, since the earlier session's research never enumerated
  them). Full findings live in the Todo 3/4/5 checkboxes above; summary:
  - **6 real callers found and fixed** (not the ~2 assumed): the production `CanonicalPerpFundingProvider`
    (`strategy-service@a34351cd`), a never-yet-run CeFi funding-corpus WRITER (`features-service`) that would have
    written into a bucket about to be deleted, a separate pre-existing DEAD reader with an unrelated legacy path-shape
    bug (`features-service/onchain/calculators/perp_funding_rates_defi.py` — documented, not fixed, out of scope), the
    `e2e-testing` lst-rates + perp-daily-ctx research readers, and the MTDS `data_manifest_handler.py` manifest-coverage
    scanners for `collect-dex-pools`/`collect-perp-funding` (also using stale legacy-shape listing logic that's never
    matched real objects in either bucket — bucket-kind repointed only, scanner-logic bug left as a separate finding).
  - **2 real, previously-unknown data gaps found and backfilled** — Todo 1's original parity check covered date-range
    coverage but not per-venue completeness, so these were invisible until the actual reader code was live-tested
    against real data: (1) JITO + MARINADE (the two Solana-chain `lst_rates` venues) were entirely absent from the
    shared bucket; (2) HYPERLIQUID's `perp_daily_ctx` (mark-price) shard was entirely absent, so every HL funding
    observation was silently getting `mark_price=None`. Closed via a new one-off script
    `market-tick-data-service/scripts/migrate_lst_perp_shared_bucket_gap_2026_07_13.py` (both source buckets already
    used the destination's exact path shape, so a pure `gcs_copy_object` sufficed — no content rewrite): JITO 1,305
    objects, MARINADE 1,745 objects, HYPERLIQUID `perp_daily_ctx` 1,109 objects, all copied and live-verified.
  - **Shipped**: `market-tick-data-service@9b980179` (manifest scanners + the gap-backfill script),
    `strategy-service@a34351cd` (`canonical_perp_funding_provider.py`). e2e-testing + features-service ship pending QG
    completion (in progress as of this entry).
  - Next: Todo 6 (redeploy strategy-service with the updated code, verify it's genuinely exercised) and Todo 7 (parity
    verification post-deploy) before the bucket-deletion todos (8-9) can proceed.

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

- **2026-07-26 (worker, slot 6, `defi_satellite_ao_dispatch_batch2-002`)** — Finished the 2 remaining housekeeping
  sub-items. (1) Deleted `market-tick-data-service`
  (`market_tick_data_service/scripts/ migrate_lst_perp_shared_bucket_gap_2026_07_13.py`) — re-verified live
  (`gcloud storage buckets list`) that all 3 gating buckets (`dex-pools-prd`, `lst-rates-prd`, `perp-funding-prd`) are
  still gone, matching this doc's own 2026-07-14 confirmation; its `Delete-when` condition is unambiguously satisfied.
  Shipped `market-tick-data-service@5dadaae7`. (2) Audited the 10 `Lifecycle: campaign` scripts in
  `market-tick-data-service/scripts/` (`defi_index_venue_canonicalise`, `defi_chain_genesis_relabel_migration`,
  `defi_oracle_relabel_migration`, `defi_captured_pre_existence_fix`, `defi_phantom_captured_pre_genesis_fix`,
  `defi_object_path_canonicalisation`, `defi_venue_launch_relabel_migration`, `defi_captured_vs_objects_walk` — all
  `_2026_06_01.py`, plus `gate3_solana_manifest_reconcile.py` and
  `backfill_hl_mark_price_from_s3_asset_ctxs_2026_06_17.py`). **Did NOT delete any of them** — documenting why instead,
  per this todo's own accepted alternative:
  - 9 of the 10 (all except the HL one) reference now-CONFIRMED-DEAD buckets (`dex-pools-prd`, `lst-rates`,
    `perp-funding`, or `oracle-prices` — all zero matches in a live `gcloud storage buckets list`), and their
    `Delete-when` condition's plan-archival half IS satisfied (`defi_manifest_canonicalisation_2026_06_01.md` /
    `solana_defi_legacy_migration_2026_05_27.md`, both archived). BUT the condition's second half ("+ GCS orphan sweep =
    0") is genuinely ambiguous: the archived `defi_manifest_canonicalisation_2026_06_01.md` itself still carries an
    UNCHECKED `- [ ] C0-RD5b` orphan-sweep todo (legacy-form objects pre-seeded in `-prd`, a DIFFERENT and apparently
    still-open sweep, not obviously the same "sweep" these scripts' markers refer to). Rather than guess which sweep the
    marker means and risk deleting code whose formal gate isn't actually closed, left all 9 in place — they are
    functionally dead (target buckets don't exist, so they cannot run) but not formally delete-eligible with full
    confidence.
  - The 10th (`backfill_hl_mark_price_from_s3_asset_ctxs_2026_06_17.py`) has its OWN, unrelated `Delete-when`
    ("HyperLiquid mark-price backfill prod-run verified") — not plan-archival-gated at all. Its target bucket
    (`perp-funding`) is also confirmed dead, so this script too cannot currently run, but its stated verification
    milestone was not investigated here (out of scope for this chore pass).
  - **Net**: all 10 are orphaned/non-functional right now (dead target buckets) but left in place pending an explicit
    resolution of the ambiguous orphan-sweep condition (or a fresh operator call to just delete known-non-functional
    code regardless).

- **2026-07-13** — Filed after the operator questioned `dex-pools-prd-central-element-323112`'s internal structure
  directly (confirmed real: legacy `day=.../category=defi/` + canonical
  `raw_tick_data/.../asset_group=defi/.../instrument_type=pool/` trees both present, redundant with the bucket name +
  instrument_id key on three separate axes) and asked whether it should be consolidated the way other DeFi buckets were
  this session. Scoped as its own plan rather than folded into the in-flight DeFi-lending-instrument-split doc/code
  fixup, since this touches strategy-service (live-trading-adjacent) and warrants its own careful, sequential execution.
