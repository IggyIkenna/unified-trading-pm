---
doc_type: plan
title: Legacy-twin GCS deletes (defi/prediction) + fresh sports twin-coverage re-verify
summary: >-
  Operator-ruled 2026-08-15 (na-eligibility-audit follow-up Q&A) — execute the legacy-twin delete-after-copy for asset
  groups that pass the 5-part delete-safety proof (defi, prediction; tradfi already tracked separately, cefi already
  done), excluding sports (0 of 34,385 rows passed as of the 2026-07-22 triage). Operator separately asked for a FRESH
  sports re-check, believing the current picture may be more solid — that is its own todo here, not assumed to pass.
status: active
nature: process
asset_group: [defi, prediction, sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [manifest, canonicalization, gcs-delete, legacy-twin]
related:
  [
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md,
    /plans/archive/issues/sports_legacy_duplicate_triage_2026_07_22.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: data_engineering
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A, 2026-08-15"
locked_by:
context_scope:
  [
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/archive/issues/sports_legacy_duplicate_triage_2026_07_22.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
locked_since:
resolved_by:
---

# Legacy-twin GCS deletes (defi/prediction) + fresh sports twin-coverage re-verify

## Todos

- [x] ✅ [DATA] P1. **Prediction leg CLEAR (0 candidates); defi leg VM-dispatched dry-run complete — twin-coverage 0%,
      delete gate does NOT clear, no `--apply` run.** Re-verified via the existing
      `_index/audit/orphan_sweep_{defi,prediction}.parquet` orphan-sweep reports (column-pruned `obj_class` read, no new
      whole-corpus walk): **prediction has 0 `B_legacy_duplicate` rows** (3,137,183 rows, all `E_orphan_real`) — nothing
      to delete, this leg is trivially satisfied, no `--apply` needed. **Defi has 1,080 `B_legacy_duplicate`
      candidates**, but running `cleanup_legacy_twins.py --asset-group defi` (dry-run) OOM-killed 3× on this shared host
      (8GB → 14GB+ RSS) — root-caused to two real bugs (not host contention): `load_legacy_twins()` and
      `_source_by_cell_from_manifest()` each materialized the FULL parquet before filtering to the tiny
      candidate/matching subset (defi's orphan-sweep report is 15.8M rows; its `availability_index.parquet` manifest is
      **6.3GB compressed** — `download_bytes()` alone loads that whole blob into RAM before any streaming can begin).
      **Fixed** both functions to stream row-groups via `ParquetFile.iter_batches()` and filter per-batch —
      `instruments-service@a2da84db56` (QG green, sentinel-verified on origin). This closes the OOM for the
      REPORT/manifest-read side, but the underlying manifest download itself (6.3GB compressed, in-memory) is genuinely
      corpus-scale per `/codex/05-infrastructure/vm-launcher-runbook.md`'s "heavy I/O/compute never on the shared host"
      rule — **the actual dry-run + `--apply` needs to run on a dedicated one-off VM**, not attempted again ad-hoc here.
      Follow-up: launch a VM (or use an existing data-pipeline VM pattern) to run
      `cleanup_legacy_twins.py --asset-group defi --report-uri _index/audit/orphan_sweep_defi.parquet` (dry-run first,
      confirm Part 5 twin-coverage = 100%, then a fresh `gcs_bucket_soft_delete_retention_seconds` check, then
      `--apply --i-understand` per §3a). Tradfi is already tracked separately
      (`tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`) — do not duplicate it here. Cefi is already done.
      Sports is explicitly OUT of scope for this todo — see the next todo. (repo: instruments-service) **DONE 2026-08-15
      (slot-18, data_engineering)** — VM-dispatched the follow-up. Shipped `deployment-service@9089bacc5d` (new
      `defi-legacy-dup-cleanup` launcher category in `launch-canonical-migration-vm.sh`, mirroring the already-shipped
      `cefi-legacy-dup-cleanup`; also fixed a pre-existing tarball-freshness bug found while wiring it — the
      `_fresh_repos` override for instruments-service-staged categories was missing BOTH `cefi-legacy-dup-cleanup` and
      `defi-legacy-dup-cleanup`, so the freshness gate was checking market-tick-data-service instead, meaning a stale
      instruments-service tarball predating this OOM fix could have shipped silently — same bug shape as the documented
      2026-07-27 sports-features-purge incident). Launched `canonical-migration-defi-legacy-dup-cleanup-20260815-185712`
      (asia-northeast1-c, dry mode) — the freshness fix immediately triggered an auto-republish confirming
      instruments-service tarball @ `a13bd7ef4495` (includes `a2da84db56`). Ran to completion in ~90s (boot to
      self-delete), well under the corpus-scale concern — the manifest download itself is fast on a dedicated in-region
      VM, the risk was always shared-host RAM, not wall-clock. **Result:
      `=== CF-21 verified-delete: 0 deletable, 1080 blocked ===`.** Cross-checked via a column-projected streaming read
      of the report (no new whole-corpus walk): all 1,080 candidates are
      `venue=CURVE/chain=ETHEREUM/     instrument_type=pool/data_type=dex_pool_state`, spread across 38 distinct days in
      2021-01/02. Block reasons split between `crc32c MISMATCH — content differs` (legacy + canonical both exist, NOT
      byte-identical) and `canonical     twin NOT captured/resolvable` (no twin at all) — **unlike the cefi/tradfi
      precedents** (where the legacy objects had simply vanished by the time their dry-runs ran), these defi objects
      genuinely still exist today and are correctly identified as NOT safe duplicates; nothing was deleted, nothing was
      at risk. Per the delete-safety protocol, Part 5 failing alone (twin-coverage 0%, not the required 100%) gates the
      whole population — no fresh soft-delete-retention check or `--apply` run was needed (would be a guaranteed no-op,
      matching the cefi precedent's own stated reasoning — `cefi_legacy_dup_delete_tooling_gap_2026_08_09.md` — for
      skipping an --apply against 0 deletable candidates: "no safety risk, but no benefit either, and would misrepresent
      this as a completed cleanup"). The data-completeness question this raises (is this a genuine v9-migration
      registration gap for early-2021 CURVE Ethereum pool_state, or intentionally-retained non-canonical historical
      data) is a distinct question outside this todo's delete-safety scope — filed as todo 3 below.
- [x] ✅ [DATA] P1. **Fresh sports twin-coverage re-check — DONE, confirms sports STILL fails, no change.** (operator
      request 2026-08-15: "check sports one more time, it's looking more solid now — update the doc"). The 2026-07-22
      triage (`sports_legacy_duplicate_triage_2026_07_22.md`, archived) found 0 of 34,385 rows passing, root-caused to
      TWO still-live code call sites reading from the legacy path. Re-checked both today via direct grep+READ (not a
      re-run of the expensive Part 5 measurement, since Part 4 is categorical and overrides Part 1/2/5 regardless — the
      protocol's own rule): **both readers are still present, unchanged** —
      `instruments-service/instruments_service/engine/orchestrator/sports_reference_fixtures.py:133`
      (`_ensure_canonical_fixtures_for_override`, builds `sports_reference/fixtures/day={date}/fixtures.parquet` and
      reads it) and `deployment-service/deployment_service/cli/utils/data_status_sports.py:42,74,327`
      (`_load_fixture_counts_for_date`'s legacy-prefix fallback + the separate `_check_league_status` copy). Per the
      protocol ("Part 4 fails 'loudly-broken' readers too" — a conditionally-reached reader still counts), the flat
      post-floor 28,100-row population's disposition is UNCHANGED: `no-migrate-first`. No re-run of Part 5's
      twin-coverage measurement was needed — neither reader has been removed/refactored, so the categorical Part-4
      blocker from the archived triage still applies verbatim; measuring twin-coverage again would not change the
      outcome. Sports stays NOT eligible for delete. (repos: instruments-service, deployment-service)
- [ ] [DATA] P2. **Investigate the CURVE/ETHEREUM/pool/dex_pool_state twin-coverage gap found by todo 1's dry-run** —
      1,080 legacy objects across 38 distinct days (sampled range 2021-01-17 through 2021-02-23) have either a
      content-mismatched or entirely absent canonical twin (0% Part-5 twin-coverage, measured 2026-08-15 against
      `gs://market-data-tick-defi-prd-central-element-323112/_index/audit/orphan_sweep_defi.parquet`,
      `obj_class=B_legacy_duplicate`). Determine: (a) does complete/correct canonical CURVE Ethereum pool_state data
      exist for this 2021-01/02 window under a DIFFERENT path/day than the classifier's derived `canonical_twin_path()`
      output (i.e. a genuine v9-migration registration gap, akin to the R5 defi `dex_pools` precedent in
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §1 Part 2) — if so, scope a migrate-forward; or (b) is
      this early, pre-v9 CURVE data legitimately superseded/incomplete and safe to leave as permanent `no-migrate-first`
      legacy-only data (matching the sports `sports_reference_v2/` precedent's Option-(a) ruling in
      `sports_legacy_duplicate_triage_2026_07_22.md` todo 7). Sample a few crc32c-mismatched pairs (e.g.
      `day=2021-01-17/asset_group=defi/venue=CURVE/chain=ETHEREUM/instrument_type=pool/data_type=dex_pool_state/     0x890f4e345b1daed0367a877a1612f86a1f86985f.parquet`)
      to compare actual row content, not just crc32c presence — content divergence alone doesn't say which side (if
      either) is more complete. No delete decision follows automatically from either answer; this is a data-completeness
      investigation, not a re-litigation of todo 1's correctly-gated delete. (repo: instruments-service)

## Progress Log

- **2026-08-15 (slot-18, data_engineering)**: Executed todo 1's VM-dispatch follow-up end-to-end — shipped the
  `defi-legacy-dup-cleanup` launcher category + a tarball-freshness bug fix (`deployment-service@9089bacc5d`), launched
  and monitored `canonical-migration-defi-legacy-dup-cleanup-20260815-185712` to completion (~90s, self-deleted),
  measured Part 5 twin-coverage at 0% (0/1080 deletable), and confirmed via a column-projected report read that the full
  candidate set is one narrow population (CURVE/ETHEREUM/pool/dex_pool_state, 38 days in 2021-01/02) — not a broad
  defi-wide gap. Delete gate correctly does not clear; no `--apply` run (would be a guaranteed no-op). Filed todo 3 for
  the follow-up data-completeness question. See todo 1's own entry above for full evidence.
- **2026-08-15 (slot-22, data_engineering)**: sports leg DONE (readers still live, disposition unchanged, no delete).
  Prediction leg DONE (0 candidates, nothing to delete). Defi leg: root-caused + fixed a real OOM bug in
  `cleanup_legacy_twins.py` (`instruments-service@a2da84db56`) but the dry-run itself needs a dedicated VM — defi's
  availability manifest is 6.3GB compressed, genuinely corpus-scale for this shared host. Todo 1 stays open for the
  VM-dispatched defi run.
- **2026-08-15 (na-eligibility-audit follow-up, operator ruling)**: extracted from
  `instruments_completion_tracker_2026_07_06.md`'s legacy-twin todo. Operator explicitly asked for the sports re-check
  as a real verification task, not a rubber-stamp — todo 2 is written as a measure-then-report task, not a pre-decided
  outcome.
