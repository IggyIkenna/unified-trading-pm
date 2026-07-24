---
doc_type: plan
title: MTDS venue onboarding + ops-hardening residuals — historical Progress Log (archive-bound record)
summary: >-
  Archive-bound extraction (2026-07-24 line-cap remediation) of the fully-completed, zero-open-todo Progress Log
  sections from plans/active/mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md, which was itself over the
  1000-line cap (~1238 lines, 45 open todos before this split). Content below is moved VERBATIM, in original
  chronological order: the sports E2E FINAL REPORT + independent LIVE re-certification (2026-06-19), the sports legacy
  DELETE execution + credential live-test, the tradfi IS-defs VM fan-out + close-out/LIVE-certification drive + honest
  NOT-100% list, the close-out continuation, the gas-fees FIX VERIFIED + sfi relaunch note, and the TradFi ICE/CME +
  DeFi EIGENLAYER legacy chain-tail fixes. No open todos live in this file — every still-open residual todo from the
  source sections stayed in the parent. This file is a record, not a work queue.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, e2e-testing, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [instruments, mtds, venue-onboarding, ops-hardening, backfill, manifest, sports, defi, tradfi, history, archive]
related:
  [
    /plans/active/mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md,
    /plans/active/instruments_mtds_subset_consistency_remediation_2026_06_17.md,
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: docs_reconciler
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [
    "plans/active/mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md (line-cap remediation,
    historical-section extraction, 2026-07-24)",
    "plans/active/issues/plan_line_cap_remediation_2026_07_23.md",
  ]
drift_direction: none
---

# MTDS venue onboarding + ops-hardening residuals — historical Progress Log (archive-bound record)

> **Extraction provenance (2026-07-24).** This file holds Progress Log sections extracted VERBATIM (no rewriting, no
> summarization) from `/plans/active/mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md`, which was over the
> 1000-line hard-fail cap (~1238 lines, 45 open todos) per
> `/plans/active/issues/plan_line_cap_remediation_2026_07_23.md`. Every section here was verified to carry **zero open
> (`- [ ]`) todo lines** at extraction time — all still-open residual todos stayed in the parent plan. This is a
> **record**, not a dispatched work queue: `status: complete`, `assigned_vm: NA`, `execution_scope: local-only`. Three
> original line ranges from the parent are concatenated here, in original order: L584-847 (sports FINAL REPORT +
> independent re-certification + legacy DELETE + credential live-test + tradfi IS-defs VM fan-out +
> close-out/LIVE-certification + honest NOT-100% list + close-out continuation), L892-913 (gas-fees FIX VERIFIED + sfi
> relaunch), L1074-1223 (TradFi ICE/CME legacy chain-tail + DeFi EIGENLAYER combined-venue legacy fix). For any
> still-open residual todo referenced anywhere in this record, see the parent plan.

## SPORTS E2E audit + remediation — FINAL REPORT (rule 9, autonomous run COMPLETE 2026-06-19)

Operator `/autonomous` 2026-06-19: full e2e sports audit+remediation for IS+MTDS + "make twins for ALL sports data
lacking one across both buckets so the operator-gated delete loses nothing". Delete stays operator-gated (never
executed). Concurrent agent af95b962 (IS coverage backfill) never collided — all my IS work was index-canonicalise +
object-copy, never a fetch; the IS `_index` stayed stale-stable (2026-06-11) throughout my writes.

**ALL deliverables COMPLETE + verified:**

| Area                              | Result                                                                                                                                                   | Evidence                                                                            |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Twin coverage IS (operator ask)   | 9,723 legacy odds-api instrument objects → ALL canonical-twinned, delete-safe                                                                            | UAC@2224818 + IS@308013f; `sports_legacy_oddsapi_twin_migration_2026_06_19.parquet` |
| Twin coverage MD (operator ask)   | 252,318 legacy objects ALL delete-safe (248,502 path + 3,116 content + 700 fanned-out); re-verify **3,816 TWIN-VERIFIED-SAFE / 0 MIGRATE-NEEDED / 100%** | e2e@1b07bcb; `sports_md_unmappable_verify_2026_06_19.parquet`                       |
| MTDS `_index` v9 + canonical      | 100% v9; null-league 32,707→0; blank 17,288→0; captured 202,087→346,498 (per-league grain recovered)                                                     | mtds@ba21ee5                                                                        |
| MTDS UNIBET/UNKNOWN remnants      | re-stamped batch_odds_api + league recovered                                                                                                             | mtds@ba21ee5                                                                        |
| MTDS GCS paths                    | canonical pipeline_mode= (raw) + processed (odds_horizon_bucket) verified                                                                                | recovery day-map                                                                    |
| IS `_index` v9                    | schema 100% v9; asset_group 100%; source 93.4% (UAC SSOT)                                                                                                | IS@5d7f6f0                                                                          |
| IS catalogue + MVP/total_universe | PASS — 789-league catalogue fresh; sports in TOTAL_UNIVERSE_AXES + MVP_SCOPE; universe_membership MVP⊆TOTAL                                              | sub-agent verify                                                                    |
| IS GCS paths                      | PASS — all 6 data_types resolve via candidate_parquet_paths()                                                                                            | sub-agent verify                                                                    |
| Shard-atom (D)                    | PASS — (data_type, league_id, date) identical IS/MTDS/data-status/UI                                                                                     | data_status_axis_matrix.py:70,105                                                   |
| Credentialed (SFI/Transfermarkt)  | scaffolds+tests confirmed; BLOCKED-CREDENTIALS ask filed                                                                                                 | ping slot_1.md                                                                      |

**Forced-tradeoff / non-obvious decisions made under autonomy (rule 1/9):**

1. **Plan claim corrections** (both surfaced + fixed honestly): (a) "9,723 unmappable/superseded, MIGRATE-FIRST=0" was
   WRONG — they were genuinely-unique odds-api instrument data (canon venue=odds_api was empty_confirmed-only to
   2020-06-05) → migrated, not abandoned. (b) "instruments-store `_index` v9-canonical for ALL 5 AGs — DONE" OVERCLAIMED
   — it ran only blank/dedup; the v9-COLUMN populate was never run for ANY AG → done for sports here, fleet-wide gap
   filed under the source-provenance plan.
2. **MD 700 genuine gap**: the prior "all 3,816 TWIN-VERIFIED-SAFE (58,910 sampled)" was a 6-file sample; the FULL
   verifier found 700 genuinely-unique 2022-2023 odds objects on days with ZERO canonical content → fanned out (not
   declared safe on a sample).
3. **3 captured-preservation bugs** caught by adversarial pre-apply verification before the MTDS recovery `--apply`
   (existing_keys captured-only + supersede; processed/ root; footystats `league=`/lowercase-`odds`) — would have
   wrongly emptied ~21k real captured cells.
4. **Source-column scope split**: sports IS source backfilled now (UAC SSOT); the live-writer auto-stamp + cefi/tradfi/
   defi backfill homed under the named cross-cutting `data_source_provenance_all_asset_groups_2026_06_01.md` (the source
   RED-gap owner) — not a sports deferral.

**Remaining open (all properly homed — NO sports-data-correctness deferral):** (1) FLEET-WIDE IS v9 for the OTHER AGs
(source-provenance plan); (2) BLOCKED-CREDENTIALS SFI/Transfermarkt validate-rotate (operator-gated, the only sanctioned
deferral; scaffolds+tests shipped); (3) catalogue mvp numeric-league-id P3 cosmetic fix. **Operator action: (a) the
operator-gated DELETE of the now-fully-twinned sports legacy objects across both buckets; (b) validate/rotate the 2
sports API keys.** Nothing else to pick up.

### SPORTS — independent LIVE re-certification (2026-06-19, verify-not-redo dispatch)

A follow-up dispatch (verify the prior sports drive, finish any remainder, certify 100% twin-coverage). Read-only
re-verified EVERY claim against the LIVE prd buckets (no redo — all prior work confirmed APPLIED + correct). **Material
update vs the FINAL REPORT: the operator-gated DELETE has since been EXECUTED** (e2e-testing@0f1d761 + idempotent
fixup), so the legacy objects are GONE and the only remaining "operator action" is the credential validate/rotate.

| Check (live)                                  | Result                                                                                                                                                                                                        | How verified                                                                               |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| MTDS sports `_index` league-recovery APPLIED  | ✅ captured **346,498** (== projection), captured-null-league **0**, blank-status **0**, NULL-source **0**, schema_version **100% v9**                                                                        | direct read `market-data-tick-sports-prd/_index/availability_index.parquet`                |
| IS sports `_index` v9 column-populate APPLIED | ✅ schema **100% v9** (2,606,663 rows), asset_group **100% sports**, source **93.4%** (171,227 blank = SSOT-unmapped retired/catalog data_types — honest), blank-status **0**, captured **659,693** preserved | direct read `instruments-store-sports-prd/_index/availability_index.parquet`               |
| IS 9,723 odds-api twin-migration              | ✅ 9,723/9,723 mapped (0 unmapped), 7,721 unique twins (5,719 MIGRATED + 4,004 MIGRATED-UNION, 2,368,129 rows, no row loss); twin sample 25/25 present on disk                                                | `sports_legacy_oddsapi_twin_migration_2026_06_19.parquet` + `gcs_describe` sample          |
| MD sports twin coverage                       | ✅ 252,318 ALL delete-safe (248,502 path-twin `canonical_twin_verified` + 3,816 content-twin `TWIN-VERIFIED-SAFE`, the 700 MIGRATE-NEEDED fan-out re-verified 0)                                              | `legacy_dup_delete_list_sports.parquet` + `sports_md_unmappable_verify_2026_06_19.parquet` |
| Legacy DELETE executed (BOTH buckets)         | ✅ IS legacy sample 0/25 still present (deleted, permanent), MD per-object `gcs_describe` twin re-verify before each delete                                                                                   | e2e-testing@0f1d761 `delete_sports_legacy_twinned_2026_06_19.py`                           |
| captured-preserved throughout                 | ✅ MTDS 202,087→346,498 (per-league grain explode, never lost); IS 659,693 unchanged                                                                                                                          | both `_index` reads                                                                        |

**Delete-ready manifest — SPORTS row (now HISTORICAL — already deleted):** IS 9,723 legacy odds-api instrument objects
(0.146 GB) + MD 252,318 legacy objects (4.78 GB) — all twin-verified, operator-authorized, **DELETED 2026-06-19**. No
agent delete performed in this dispatch (delete was already done by the operator-authorized run).

**Sports is FOLDED INTO 100% twin-coverage on both buckets** — every captured cell is backed by a canonical-path object,
every legacy object had a verified canonical twin before deletion, and both `_index` are 100% v9. The 2 remaining open
sports todos are non-blocking + correctly homed (BLOCKED-CREDENTIALS SFI/Transfermarkt + P3 catalogue-mvp cosmetic). No
codex contract changed (the league-recovery brought live data INTO compliance with the already-documented sports shard
atom `(asset_group=sports, venue/source, data_type, league_id, day)` in `availability-manifest-and-data-status.md`).

- [x] ✅ [DATA] P2. **Residual sports MTDS bookmaker-`trades` pipeline_mode/source mislabel — re-stamped 559 cells** —
      DONE 2026-06-19 (mtds@41c990a `restamp_sports_bookmaker_trades_pipeline_mode_2026_06_19.py --apply`). Surfaced
      during the re-certification: the league-recovery's `defective_mask = (captured & null_league) | blank_status`
      never touched captured cells that ALREADY had a per-league `league_id` but a wrong `pipeline_mode`. Of 50,497
      captured `data_type=trades` cells carrying `pipeline_mode=batch_api_football`, GCS-verified that **49,938 are
      CORRECT** — their object genuinely lives under
      `…/pipeline_mode=batch_api_football/…/data_source=ODDS_API/venue={V}/     league_id={L}/…/data_type=trades/`
      (api_football's pipeline ingests odds-api-sourced bookmaker odds; the pipeline_mode label matches the object), and
      only **559 were genuinely mislabeled** (object lives ONLY under `batch_odds_api`, verified ABSENT under
      `batch_api_football`). Re-stamped only those 559 → `pipeline_mode=batch_odds_api` + `source=odds_api` (day-map
      distinguishes the two via `batch_api_football in     modes`). ROW-PRESERVING — captured **346,498 → 346,498** (0
      lost). Post-apply verify: trades captured pipeline_mode = 167,779 odds_api + 49,938 api_football, source perfectly
      consistent with pipeline_mode, null-league 0, null-source 0, schema 100% v9. Snapshot
      `pre_sports_bookmaker_restamp_20260619_130152`. — market-tick-data-service

## SPORTS legacy DELETE executed (operator-authorized 2026-06-19) + credentials live-tested

> Operator 2026-06-19: "do these delete" + "check if [the keys] work". Both actioned.

- [x] ✅ [INFRA] P1. **Operator-authorized DELETE of the fully-twinned sports legacy objects (BOTH buckets)** — DONE
      2026-06-19 (e2e-testing@a893f1c `delete_sports_legacy_twinned_2026_06_19.py --apply`). Per-object
      `gcs_describe_object` twin re-verification before EACH delete (safety invariant, not prefix-match); 0
      SKIP_TWIN_MISSING. **Authoritative post-delete verify: IS 0/9,723 + MD SAFE 0/248,502 + MD content 0/3,816
      remaining** = all 262,041 legacy objects deleted. Reclaimed **~4.81 GB** (IS 0.142 + MD-SAFE 4.451 + MD-content
      0.212 GB). Recoverability: MD bucket = **7-day soft-delete** (recoverable); IS bucket soft-delete DISABLED =
      PERMANENT (every IS twin gcs_describe-verified present before its permanent delete). cefi MD legacy (9.98 TB) was
      deleted earlier; sports completes the sports-bucket legacy cleanup. — e2e-testing
- [x] ✅ [DATA] P2. **SFI + Transfermarkt keys LIVE-TESTED (operator "check if they work")** — DONE 2026-06-19. Both
      secrets hold the SAME valid RapidAPI key (`22380b4a…`); both APIs return HTTP 403
      `{"message":"You are not subscribed to this API."}`. **Root cause = RapidAPI SUBSCRIPTION GAP, not a bad/expired
      key** (control: api-football `c820a404…` + footystats `b1d5bc90…` are distinct keys with working subscriptions).
      NOT agent-fixable (subscribing to a paid RapidAPI plan = operator action). **Operator: SUBSCRIBE the account to
      `soccer-football-info` + `transfermarkt-football-data-api`, or swap the TM secret to an Apify `apify_api_*` token
      (adapter auto-detects).** Stays BLOCKED-CREDENTIALS (subscription, not rotation). — ping slot_1.md UPDATE. —
      instruments-service [BLOCKED-CREDENTIALS]

### Progress Log — tradfi IS-defs VM fan-out (2026-06-19, operator "use more servers")

The serial single-host tradfi IS-definition backfill (CBOE@2023-06, NASDAQ@2024-08, NYSE-not-started; gating Step-2c v9

- B1 catalogue) was replaced with a 9-VM sharded fleet for ~9x wall-clock speedup. Stopped the local serial runners
  (`dbeq_is_defs_backfill.sh` slot6, `cfe_vx_is_definitions.sh`, `tradfi_backfill_then_v9_monitor.sh` wrapper). Launched
  `deployment-service/scripts/vm/launch-tradfi-is-defs-sharded.sh` (new, shellcheck-clean, lifecycle:campaign) → 9 GCE
  VMs `instr-backfill-tradfi-{cboe-a/b/c,nasdaq-a/b,nyse-a/b,cme-a/b}-20260619-141559` (asia-northeast1-c,
  e2-standard-4, run-ts 20260619-141559), each a disjoint (venue, date-window) shard over 2010-06-19→2026-06-19,
  `VM_VENUE` scoped to the 3 paid datasets (CME/NASDAQ/NYSE/CBOE; ICE/FX excluded — off the Databento billing
  allowlist), `MANIFEST_PER_VM_SHARDS=true`, unique `VM_NAME`, `VM_SHUTDOWN_ON_COMPLETION=true`, `VM_CHUNK_DAYS=30`.
  Reuses the proven `instruments-backfill` task in `setup-data-pipeline-vm.sh` (tarball `instruments-service-code` @
  e1ec379 == local HEAD). T+10min verify (14:23Z): all 9 RUNNING + chunk-loop progressing. BEFORE tradfi-IS `_index`
  (12471 rows): schema_v9=13.8%, source≈0%, asset_group ABSENT. Post-fleet sequence (pending VM self-shutdown):
  consolidator Cloud Run Job `uts-prod-manifest-consolidator-instruments-tradfi` →
  `populate_is_index_v9_2026_06_19.py --asset-group tradfi --apply` (row-preserving, aborts if captured drops) →
  `build_instrument_catalogue.py --asset-group tradfi` → delete VMs.

### Progress Log — close-out drive + LIVE certification (2026-06-19, autonomous)

**VM diagnosis (4 running at 19:30Z; freshness = per-VM SHARD update, NOT the lagging GCS log-tee):**

- `instr-backfill-tradfi-cme-b` — **WORKING**, climbing (date=2021-07-14 of its 2020-01-01→2026-06-19 window). The 8
  sibling tradfi IS-def shards (cboe-a/b/c, nasdaq-a/b, nyse-a/b, cme-a) **already self-deleted**
  (`VM_SHUTDOWN_ON_COMPLETION`) — only CME-b remains. Genuine multi-year CME GLBX.MDP3 daily-definitions backfill → many
  hours ETA.
- `af-backfill` (sports MTDS api-football coverage) — **WORKING**, log fresh 19:33Z (multi-season league sweep; many
  `Fetched 0 teams` = off-season/no-data, normal honest absence).
- `mtds-gas-fees` (defi gas_fees 2021→2026 multi-chain RPC) — **WORKING** (initially misread as stalled: GCS log-tee
  uploader lagged at 17:51Z, but the per-VM SHARD updated 19:37Z, local log live at date=2021-02-12, 247 shard entries
  climbing). The `ManifestConsolidatorStaleError` for `gas-fees-central-element-323112` is a NON-FATAL warning ("keeping
  previous membership set") — writes continue; root cause is that bucket has **no consolidator Cloud Run job** (only a
  2026-05-20 `_index`), which does NOT block the backfill. Load ~0.05 = RPC-bound, not hung. Long backfill.
- `sfi-backfill-chunk-2of4` — **DELETED** (no-op). sshd-dead (port 22 backend fail), log frozen 3h21m, wrote ZERO data
  (no SFI per-VM shard, no SOCCER_FOOTBALL_INFO objects). Root cause = **BLOCKED-CREDENTIALS** (SFI RapidAPI 403 "not
  subscribed", operator-only fix, already journaled). Siblings 1/3/4-of-4 already terminated. Stopped pure cost/zero
  output.

**LIVE CERTIFICATION MATRIX (read 19:40-19:50Z, CANONICAL `-prd` buckets via `resolve_bucket_name`; prediction canonical
= `-pred-prd`, NOT the stale legacy-flat `-prediction-` buckets):**

| AGÃTYPE                       | rows      | v9%      | pmode% | src% | ag%   | captured  | empty(honest) | failed(fillable) | expU      | honest-cov% |
| ----------------------------- | --------- | -------- | ------ | ---- | ----- | --------- | ------------- | ---------------- | --------- | ----------- |
| cefi IS                       | 36,084    | 100      | 100    | 100  | 100   | 36,062    | 0             | 22               | 0         | 99.9        |
| defi IS                       | 75,081    | 100      | 100    | 100  | 100   | 75,081    | 0             | 0                | 0         | 100         |
| tradfi IS                     | 13,727    | **37.6** | 36.3   | 24.4 | **0** | 13,385    | 342           | 0                | 0         | 100         |
| sports IS                     | 4,069,112 | 100      | 97.8   | 91.2 | 97.6  | 659,697   | 2,269,970     | 112,049          | 1,027,396 | 36.7        |
| prediction IS (`-pred-prd`)   | 791       | 100      | 100    | 100  | 100   | 791       | 0             | 0                | 0         | 100         |
| cefi MTDS                     | 3,872,296 | 96.6     | 85.5   | 85.5 | 96.6  | 1,311,984 | 1,276,223     | 801,975          | 482,114   | 50.5        |
| defi MTDS                     | 6,165,919 | 100      | 100    | 100  | 99.8  | 368,605   | 3,483,771     | 6,185            | 2,307,358 | 13.7        |
| tradfi MTDS                   | 1,938,910 | 99.7     | 75.1   | 74.9 | 99.1  | 102,936   | 1,007,650     | 10,013           | 818,311   | 11.1        |
| sports MTDS                   | 920,230   | 100      | 100    | 100  | 100   | 346,498   | 573,568       | 164              | 0         | 100         |
| prediction MTDS (`-pred-prd`) | 41,809    | 96.5     | 96.5   | 93.9 | 93.9  | 16,918    | 24,503        | 50               | 338       | 97.8        |

**expected_unattempted present (4th state materialised):** defi MTDS 2.31M, cefi MTDS 482K, tradfi MTDS 818K, sports IS
1.03M, prediction MTDS 338. IS-side defi/cefi/tradfi/prediction = 0 expU (IS is a finite listed-universe, not a
could-exist grid — captured≈total is correct there).

**NOT-100% honest reasons (no false 100% claims):**

- **tradfi IS 37.6% v9 / 0% ag = the ONE open cell** — awaits CME-b finish →
  `populate_is_index_v9 --asset-group tradfi --apply` → `build_instrument_catalogue --asset-group tradfi`. IN PROGRESS.
- **Low honest-cov% on defi/tradfi/cefi MTDS (13.7/11.1/50.5) = expected_unattempted dominating, BY DESIGN** — the huge
  could-exist universe (every IS-listed instrument Ã every post-genesis day) is honest absence, not failure. captured is
  real; expU is the 4th-state working.
- **cefi MTDS 801,975 attempted_failed = BILLING-BLOCKED** (operator: cefi tick backfill paused on vendor billing). The
  fillable re-run is operator-gated.
- **sports IS 112,049 failed + 36.7% honest-cov** = the honest sports universe (SFI/TM BLOCKED-CREDENTIALS 403 +
  off-season fixtures); mostly honest absence. af-backfill running to raise captured.
- **sports IS 91.2% src** = 171,227 blank-source rows = SSOT-unmapped retired/catalog data_types (journaled honest).

### Delete-ready manifest (2026-06-19, OPERATOR-FACING — no agent delete performed this session)

Per-AG certified delete-lists (`_index/audit/legacy_dup_delete_list_{ag}.parquet` MTDS +
`instruments_store_legacy_delete_list_{ag}.parquet` IS), classification = per-object `gcs_describe`-verified canonical
twin (SAFE-TO-DELETE) vs no-twin (MIGRATE-FIRST, NOT delete-safe):

| List                     | total     | SAFE-TO-DELETE        | MIGRATE-FIRST | status                                                                                                            |
| ------------------------ | --------- | --------------------- | ------------- | ----------------------------------------------------------------------------------------------------------------- |
| cefi MTDS                | 1,077,687 | 1,077,672             | 15            | legacy-flat twins; cefi MD 9.98 TB already deleted earlier; these 1.08M are the residual flat-shape dups          |
| defi MTDS                | 352,234   | 346,902               | **5,332**     | 5,332 MIGRATE-FIRST = no canonical twin yet → NOT delete-safe (migrate first)                                     |
| tradfi MTDS              | 1,706,332 | 1,705,230             | **1,102**     | 1,102 MIGRATE-FIRST not delete-safe                                                                               |
| sports MTDS              | 252,318   | 248,502               | 3,816         | **ALREADY EXECUTED 2026-06-19** (3,816 content-twin verified safe at delete time) — list is pre-delete/historical |
| pred MTDS                | 573,451   | 573,451               | 0             | all twin-verified safe (canonical = `-pred-prd`)                                                                  |
| sports IS                | 9,723     | (UNMAPPABLE→migrated) | —             | **ALREADY EXECUTED 2026-06-19** (odds-api twins migrated then legacy deleted)                                     |
| cefi/defi/tradfi/pred IS | 0         | —                     | —             | no legacy IS dups listed                                                                                          |

**Delete-SAFE NOW (operator may delete; agent did NOT):** cefi MTDS 1,077,672 + defi MTDS 346,902 + tradfi MTDS
1,705,230 + pred MTDS 573,451 legacy-flat objects (all `gcs_describe`-verified canonical twin present). Plus the
**prediction legacy-flat BUCKETS** `instruments-store-prediction-…` (stale 2026-06-08) + `market-data-tick-prediction-…`
are SUPERSEDED by canonical `-pred-prd` (which is live + 100%/97.8% certified) — candidate for bucket-level delete, but
a per-object twin-walk on those two buckets has NOT been run this session, so they are CANDIDATE not CERTIFIED.

**NOT delete-safe (MIGRATE-FIRST first):** defi MTDS 5,332 + tradfi MTDS 1,102 objects have no canonical twin → must be
copied to canonical path BEFORE their legacy copy is deletable. **Caveat: the lists above are the LAST-COMPUTED
snapshot; sports + cefi-MD + sports-IS deletes already EXECUTED, so re-run the per-AG rescan twin-verify before any new
delete to refresh classification (fail-safe: stale list over-lists MIGRATE-FIRST, never under-flags an unsafe delete).**

**[✅ RESCAN DONE 2026-07-13 — see "Fresh audit 2026-07-13 (operator-ordered)" section ~L473-524.** The caveat above was
acted on: defi MTDS + tradfi MTDS SAFE-TO-DELETE (346,902 + 1,705,230, this table's "Delete-SAFE NOW" row) are confirmed
GONE from live GCS — deleted sometime before 2026-07-13 (undocumented in this plan; process-hygiene follow-up filed in
the fresh-audit section, not a data-safety concern given the exact SAFE-list match). pred MTDS 573,451 is likewise gone.
Remaining legacy for defi/tradfi is EXACTLY this table's MIGRATE-FIRST column (5,332 / 1,102, byte-identical) —
unchanged, still tracked below, still not delete-safe on THIS simple path-derivation audit (the separate content-aware
verifier already covers most of it, see "Migration unmappable residue" above). sports/pred legacy = 0.]\*\*

### Honest NOT-100% list (final, no false claims)

1. **tradfi IS v9 = the ONE genuinely-open cell** (37.6% v9, 0% asset_group) — gated on `instr-backfill-tradfi-cme-b`
   (CME GLBX.MDP3 daily-defs 2020→2026, ~108 days/h, **ETA ~17h from 19:48Z**). On its TERMINATION the close-out runs:
   consolidator → `populate_is_index_v9 --asset-group tradfi --apply` →
   `build_instrument_catalogue --asset-group tradfi` → verify 100% v9. Tracked waiter armed (`/tmp/wait_cme_b.sh`). NOT
   a code/decision blocker — pure backfill wall-clock.
2. **cefi MTDS 801,975 attempted_failed = BILLING-BLOCKED** (operator: cefi tick vendor billing paused). Fillable re-run
   is operator-gated, not agent-fixable.
3. **sports IS 36.7% honest-cov + 112,049 failed** = SFI/Transfermarkt **BLOCKED-CREDENTIALS** (RapidAPI 403
   not-subscribed)
   - off-season fixture honest absence. af-backfill running to raise api-football captured. Operator: subscribe SFI/TM.
4. **defi/tradfi MTDS low honest-cov (13.7/11.1%) = expected_unattempted BY DESIGN** — huge could-exist universe (every
   IS instrument Ã every post-genesis day) is honest absence (the 4th state working), not pipeline failure. captured is
   real.
5. **prediction MTDS 96.5% v9 / 93.9% src** — near-complete; 50 failed + 338 expU residual. Not a blocker.
6. The **legacy-flat `_index` reads (prediction 0% v9, etc.) were a measurement artifact** — the CANONICAL
   `-prd`/`-pred-prd` buckets (what `resolve_bucket_name` returns + what readers/writers use) are the certified ones in
   the matrix above.

**Bottom line: 4 of 5 AGs (cefi, defi, sports, prediction) are CERTIFIED on canonical buckets (IS 100% v9; MTDS
96.5-100% v9). tradfi IS is the single open cell, gated purely on a ~17h backfill (operator already accelerated via the
9-VM shard fleet; 8 shards self-completed). No code, no decision, no un-run agent op remains for the certified AGs.**

## Close-out continuation (2026-06-19 ~20:20Z) — Progress Log

- **MTDS fallback-import ratchet 3→2 SHIPPED** (operator ask): `no_fallback_imports_baseline.yaml` lowered;
  `check_no_fallback_imports.py` confirms `market-tick-data-service: 2 (== baseline)` PASS; MTDS tree has no uncommitted
  `.py` (count durable on committed tree). **PM@953bc18fc** on LDR → standing PR #432 → main. Locks the import-pattern
  improvement against regression.
- **batch+LIVE smoke matrix DONE** (af55592b): `e2e-testing@c92d50f` harness, 3401 cells Ã 5 AGs — **754 batch-pass / 0
  fail; 339 L1-wired / 0 live-fail; 135 symmetric / 0 divergent**; real Binance-spot live tick verified L2. Wired
  repeatable as MTDS QG STEP 5.88b. Plan `batch_live_smoke_matrix_2026_06_19.md` (PM@d74e2899a). Honest gaps:
  non-Binance L2 = sandbox-egress-blocked (schema-only); TradFi-Databento + Sports-Odds-API live = blocked-credentials.
- **SFI CONFLICT DEFINITIVELY RESOLVED** — the _new_ `soccer-football-info-api-key` works: sfi-backfill-chunk-3of4 log
  shows **HTTP 200 ("Fetched 50 leagues")**, filters to 4 mapped prediction-leagues, writes **empty `{}` for off-season
  historical dates** (2023-02-26/27) = **honest-absence, NOT 403/blocked-credentials**. The earlier close-out conclusion
  ("403 not-subscribed / permanently dead") was the OLD dead VM/key, now superseded. Sports IS stays 100% v9; off-season
  empties are correct 4th-state absence.
- **gas-fees re-launch VERIFIED CLIMBING** on the fixed log-streamer (BSC gas blocks, 2021 dates, 200 pts/chain/day) —
  the operator-flagged "log frozen" was the pre-fix streamer lag, now resolved (VM-observability fix live).
- **CME-b (tradfi IS v9, the ONE open cell)**: `instr-backfill-tradfi-cme-b-20260619-141559` RUNNING + writing CME
  instruments to canonical `instruments-store-tradfi-prd`. **Main-loop-owned tracked waiter `b3e05u4d6` armed** (5-min
  poll of VM state + hourly climbing-metric breadcrumb + 2h-flat stall-trip + 20h cap). On terminal → re-invokes main
  loop to run: consolidator → `populate_is_index_v9 --asset-group tradfi --apply` →
  `build_instrument_catalogue --asset-group tradfi` → verify tradfi IS 100% v9. (Replaces the sub-agent-owned waiter
  that died when its parent came to rest — per CLAUDE.md "main loop owns the waiter".)
- **State**: 4/5 IS at 100% v9 (canonical buckets); tradfi IS the single open cell on a ~17h backfill. Residuals are
  operator-gated (cefi MTDS billing; Extended placeholder; Kalshi RSA-PSS wire; ~7 bespoke launchers) or
  honest-absence-by-design (low defi/tradfi MTDS coverage = expected_unattempted 4th state).

## gas-fees FIX VERIFIED + sfi relaunch (2026-06-19 ~21:18Z) — Progress Log

- **Foreign TF blocker RESOLVED by its owner** — `paper_week_determinism_scheduler.tf`'s duplicate `blrs_image` local
  was removed (now reuses `local.blrs_image` from `audit03_cron_provisioning.tf`). `tofu validate` clean. (No edit by me
  to the foreign file.)
- **gas-fees consolidator cron APPLIED + FIX VERIFIED.** Targeted `tofu apply` (2 add / 0 change / 0 destroy) created
  `uts-prod-manifest-consolidator-gas-fees` (Cloud Run job) + `uts-prod-manifest-consolidator-gas-fees-cron` (`*/1`).
  Ran the job once to seed a fresh index. Relaunched `mtds-gas-fees-20260619-211114`, which is now **past the exact
  preflight that crashed the prior run** — log shows ETHEREUM gas sampling + BSC block resolution for 2021-01-01/02 with
  **no `ManifestConsolidatorStaleError` and no traceback**. Root cause (missing consolidator coverage) is genuinely
  closed.
- **sfi — HTTP-layer hang ruled OUT; relaunched to reproduce-or-clear.** The SFI adapter base
  (`instruments-service/.../adapters/sports/adapters/base.py`) ALREADY sets a bounded `aiohttp.ClientTimeout`
  (`_HTTP_TOTAL_TIMEOUT` + sock bounds) and retries `asyncio.TimeoutError` — so a stalled SFI request CANNOT hang the
  worker forever. The earlier 46-min freeze is therefore NOT a missing-timeout bug; candidates are an
  orchestration-layer stall, a log-tee daemon death (work continued, only logging froze), or the chunk having
  effectively completed. Relaunched chunk-parallel 4 (`run-id 20260619-211603`; chunk 3of4 = 2023-02-26..2024-09-23,
  spanning the prior 2023-02-27 freeze date). Tracked waiter watches 3of4 cross 2023-02-27: **advance = transient
  (systemic fix = the already-filed silent-worker watchdog); re-freeze at the same point = a date/data-specific
  reproducer to root-cause** (NOT HTTP). Honest status: sfi root cause is NOT yet pinned to a code defect — relaunch is
  the reproduce-or-clear step, not a claimed fix.

## TradFi ICE/CME pre-cutover legacy chain-tail — PRESERVE+RESHAPE — DONE (2026-07-13, operator ruling)

> **🟡 PARTIALLY SUPERSEDED (2026-07-14, operator ruling — ICE descope)**: the ICE half of this section's "PRESERVE AND
> RESHAPE, never delete" ruling was explicitly OVERRIDDEN one day later by the operator's ICE-descope ruling ("delete
> the 9 but for dollar index we're gonna use the daily yahoo finance"): the 9 preserved ICE `futures_chain` canonical
> objects on `day=2025-01-06` (BRENT, COCOA, COFFEE, COTTON, DOLLARINDEX, GASOIL, ORANGEJUICE, SUGAR, WTI) were DELETED
> 2026-07-14 as part of the ICE non-`ohlcv_24h` purge (market-tick-data-service@fffd7f82
> `scripts/purge_tradfi_ice_non_24h_2026_07_14.py`; manifest rows reclassed
> `empty_confirmed[EXPECTED_NO_PROVIDER_COVERAGE]`, snapshot `_index/snapshots/pre_ice_purge_2026_07_14.parquet`). DXY's
> forward path is the Yahoo `ohlcv_24h` route (`ICE:INDEX:DXY-USD`). The CME half (40 futures_chain + 6 options_chain
> objects) is UNAFFECTED — CME stays in-subscription and preserved.

> Operator ruling 2026-07-13: the tradfi "LEGACY shape D" (pre-hive instrument-key,
> `day={D}/data_type={DT}/{class}/{VENUE}/{file}`) `futures_chain`/`options_chain` objects the generic
> `audit_legacy_gcs_dup_delete_list.py` classifies `MIGRATE-FIRST` (`reason=no_venue_or_data_type_in_path`) include ICE
> softs/Brent data captured BEFORE the 2026-06-18 3-dataset Databento subscription lockdown dropped ICE
> (`/codex/02-data/tradfi-databento-sourcing-ssot.md`) — non-refetchable. Ruling: PRESERVE AND RESHAPE, never delete.

**Live-verified count (two independent full-corpus rescans agree, 2026-07-02 and 2026-07-13 — bucket confirmed stable):
55 objects, not the ballpark "~64" first quoted** — `futures_chain` MIGRATE-FIRST = 49 (9 ICE: BRENT, COCOA, COFFEE,
COTTON, DOLLARINDEX, GASOIL, ORANGEJUICE, SUGAR, WTI — all `day=2025-01-06`; + 40 CME: 30 symbols on `day=2025-01-06` +
AUD repeated on 9 more dates) + `options_chain` MIGRATE-FIRST = 6 (CME: ES, EW1, EW2, EW3, EW4, NQ, `day=2025-01-06`).
10 distinct days total: 2025-01-06, 2025-01-10, 2025-11-02/03/04/06/07/08/09/10.

**DECISIVE FINDING — the generic audit's `MIGRATE-FIRST`/`twin_exists=False` verdict was a PATH-PARSING ARTIFACT, not a
real gap (same class of false-negative the 2026-06-18 unmappable-residue diagnosis already documented for this AG).**
`audit_legacy_gcs_dup_delete_list.py`'s twin-check can't parse this bare "LEGACY shape D" grammar (no `venue=`/
`data_type=` hive keys) well enough to CONSTRUCT the correct candidate canonical path (which needs an inserted
`underlying=` bundle segment), so it never actually probed for a twin. Using the parser `rebuild_tradfi_manifest.py`
already ships for exactly this shape (`_parse_prehive_path`) to build the REAL candidate canonical path revealed: **53
of the 55 objects already had a verified canonical twin** (server-side copy made 2026-06-27, `gcs_describe_object`
`last_modified` confirms) with **exact parquet-footer row-count parity** (spot-verified programmatically, not sampled —
173,632 legacy rows == 173,632 canonical rows across all 55). The manifest ALSO already carried
`capture_status=captured`/`source=databento`/`pipeline_mode=batch_databento` for all 55 target
`(date, venue, instrument_type, data_type, underlying)` cells (batch-verified against the live `_index`, not assumed).
The remaining 2 objects (CME AUD `futures_chain` on 2025-11-02 + 2025-11-08, both weekend dates) are genuine 0-row
honest-empty files — nothing to preserve (matches the workspace's established "0-byte/0-row legacy = honest no-data,
delete-safe once confirmed empty" precedent).

**Action taken**: market-tick-data-service@(uncommitted this session)
`scripts/reshape_tradfi_ice_cme_legacy_chain_tail_2026_07_13.py` — reuses `rebuild_tradfi_manifest.py`'s
`_parse_prehive_path`/`_derive_pm_and_source`/`_emit_bundled_shard_row` verbatim (no reimplementation); idempotent
(skips a copy/manifest-write when the canonical twin + manifest row already exist — true for 53/55); the 2 zero-row
objects were confirmed genuinely 0-row (footer read) then deleted directly (no data lost). **Result: all 55 legacy
objects deleted (twin-verified first); 0 remain at the legacy paths (live re-list confirms); the 53 real-data cells'
canonical objects + manifest rows were untouched (already correct) — the operation was effectively a
verify-then-delete-the-now-redundant-legacy-duplicate, since the actual RESHAPE had already happened on 2026-06-27.**
Before/after: 55 legacy objects → 0; 53 canonical twins (pre-existing, row-parity verified) + 2 honest-empty (no twin
needed) = 55/55 accounted for; manifest captured-count unaffected (no new writes — all 55 cells were already
`captured`).

- [x] ✅ [DATA] P1. **TradFi ICE/CME pre-cutover legacy chain-tail — live-verify + reshape + delete-legacy — DONE
      2026-07-13.** 55 objects (not ~64) live-verified across 2 independent rescans; 53/55 already had a
      row-parity-verified canonical twin (2026-06-27) + captured manifest row (path-parsing artifact in the generic
      audit, not a real gap); 2/55 were genuine 0-row honest-empty. All 55 legacy duplicates deleted post-twin-verify; 0
      data lost. — market-tick-data-service `scripts/reshape_tradfi_ice_cme_legacy_chain_tail_2026_07_13.py`

## DeFi EIGENLAYER combined-venue (`venue=EIGENLAYER-ETHEREUM`) legacy + mis-shaped-canonical-twin — VERIFY + DELETE — DONE (2026-07-13, operator "fix now" ruling)

> Operator ruling 2026-07-13: the legacy shape
> `day=.../venue=EIGENLAYER-ETHEREUM/instrument_type=restaking/ data_type=rewards/ticks.parquet` (~597 objects) AND its
> computed "canonical" twin (same combined venue under `pipeline_mode=batch_onchain_subgraph` in the prd bucket) BOTH
> violate `/codex/02-data/defi-canonical-naming-ssot.md` (NEVER the combined PROTOCOL-CHAIN venue overload —
> `venue=EIGENLAYER` + `chain=ETHEREUM` as separate hive keys). Mid-session scope update from the coordinator (fresh
> legacy-dup audit, PM@194b7d542): the generic defi legacy bulk (5,332 MIGRATE-FIRST objects) was already
> migrated+deleted by a separate process — this EIGENLAYER population is its own, separately-tracked residue,
> live-verified independently below.

**Live-verified populations (before any action, buckets confirmed mid-flux):**

- Legacy env-less bucket `market-data-tick-defi-central-element-323112`: **597 objects** at
  `raw_tick_data/by_date/day={D}/pipeline_mode=batch_onchain_rpc/asset_group=defi/venue=EIGENLAYER-ETHEREUM/ instrument_type=restaking/data_type=rewards/ticks.parquet`,
  day range 2024-08-15→2026-04-07, all created **2026-05-19** (same day as the handler shard-key fix below — a stale
  one-time backfill run, not a recurring write).
- PRD bucket `market-data-tick-defi-prd-central-element-323112`: **597 mis-shaped "canonical" twins**, same combined
  venue + labels, under `pipeline_mode=batch_onchain_subgraph`, all created **2026-06-18** (the generic
  v9/unmappable-residue migration-era window) — the exact copy the operator flagged as "equally wrong."
- **Decisive finding**: a FULLY correctly-split twin
  (`venue=EIGENLAYER/chain=ETHEREUM/instrument_type=staking/ data_type=eigenlayer_rewards/rewards.parquet`) already
  existed for **597/597 days** in the prd bucket under the same `pipeline_mode=batch_onchain_subgraph` (plus in the
  legacy bucket under both `batch_onchain_rpc` and a bare/no -pipeline_mode form) — written by the ALREADY-FIXED live
  handler. Same signature as the TradFi ICE/CME section above: verify-then-delete-the-now-redundant-legacy-duplicate,
  not a from-scratch reshape/migration.
- **Row-count parity** (parquet-footer read, all 597 pairs, not sampled): **596/597 exact match**; 1 day (2026-04-07)
  where the correct-shape twin is a strict superset (44 rows vs 21) — captured-preserved-or-higher holds everywhere,
  zero data-loss risk from deleting the wrong-shaped side.
- **Manifest check**: both buckets' `_index/availability_index.parquet` (prd 27.45M rows / legacy 1.91M rows;
  column-projected `pyarrow.dataset` + `pc.field("venue").isin(...)` predicate-pushdown read — never a full-corpus load,
  per single-walk/OOM-avoidance discipline) carry **zero rows** for the combined `venue=EIGENLAYER-ETHEREUM` — the
  mis-shaped objects were never manifested (orphan stray objects), so no manifest row correction was needed,
  object-level delete only.

**Snapshots** (before any delete, server-side `gcs_copy_object`):
`gs://market-data-tick-defi-prd-central-element-323112/_index/snapshots/pre_eigenlayer_venue_chain_fix_2026_07_13.parquet`
(445,220,744 bytes) +
`gs://market-data-tick-defi-central-element-323112/_index/snapshots/pre_eigenlayer_venue_chain_fix_2026_07_13.parquet`
(20,717,472 bytes).

**Action taken**: deleted all **1,194** mis-shaped objects (597 legacy `batch_onchain_rpc` + 597 prd
`batch_onchain_subgraph`, both combined-venue) via UTL `gcs_delete_object` (never subprocess gsutil), thread-pooled —
**1,194/1,194 OK, 0 errors**. Post-delete live re-verify used direct `gcsfs.exists()` per-object checks (NOT gsutil's
recursive `**...**` glob — that glob gave an inconsistent/unreliable match count mid-session for multi-segment patterns,
a real gotcha, not trusted for the final verdict): **0/597 remain** at either wrong-shaped path in either bucket;
**597/597 correct-shape canonical twins remain intact**, untouched, in the prd bucket.

**Writer-source check** (`rg EIGENLAYER-ETHEREUM` across instruments-service + UAC registries): the CURRENT live writer
(`market-tick-data-service/market_tick_data_service/cli/handlers/eigenlayer_rewards_handler.py`) already emits the
fully-split canonical shape —
`write_defi_rows(rows, venue="EIGENLAYER", chain="ETHEREUM", instrument_type=InstrumentType.STAKING, data_type="eigenlayer_rewards", ...)`
— confirmed by direct source read; `canonical_write.py`'s enrichment step OVERWRITES any row-level
`venue`/`data_type`/`instrument_id` the row dicts carry (the `_parse_claims`/`_parse_season1_transfers` row-dict
literals still say `"venue": "EIGENLAYER-ETHEREUM"` — dead code, clobbered before write, cosmetic only, not a live bug).
Zero grep hits for a `venue="EIGENLAYER-ETHEREUM"` writer callsite workspace-wide. UAC's
`defi_venues.py`/`venue_adapter_keys.py`/`venue_mapping.py`/ `defi_venue_capabilities.py` combined-form entries are the
INSTRUMENT/CATALOG-KEY convention (same family as `instrument_key="EIGENLAYER-ETHEREUM:GOVERNANCE_TOKEN:EIGEN"`) — a
separate namespace from the GCS storage-PATH `venue=`/`chain=` hive keys this SSOT governs; not a path writer, no fix
needed there. **Verdict: writer already fixed** — `market-tick-data-service@b3a15d894cfa6c13698fac817425cfc0a6fa25bf`
(2026-05-19, "fix(eigenlayer): align \_EIGENLAYER_DATA_TYPE with parquet path + fix docstring"). The 1,194 deleted
objects were a stale artifact from before/around that fix (legacy side) and from the mid-2026-06 generic
v9-canonicalisation pass that copied them into the prd bucket without reshaping (mis-shaped "canonical" twin, prd side)
— **no current re-litter path exists.**

**Two adjacent findings surfaced, logged but OUT OF SCOPE for this fix** (ambiguous/wider blast radius, per
findings-triage — not fixed this session):

1. `market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/canonical_write.py::_normalize_venue()`
   docstring claims it "strips any trailing -CHAIN suffix" but the code only uppercases (no actual split) — a latent
   landmine IF a future caller ever passes an already-combined venue string directly (confirmed zero current callers do,
   for EIGENLAYER or any other venue checked). Docstring/code mismatch, not itself a live bug today.
2. The prd manifest carries **1,139 rows**
   `(venue=EIGENLAYER, chain=ETHEREUM, instrument_type=restaking, data_type=rewards, pipeline_mode=batch_onchain_subgraph, capture_status=attempted_failed)`
   — an OLD label-pairing (pre-b3a15d894), already-split-venue manifest cluster, all `attempted_failed`. Unrelated to
   the combined-venue-path bug fixed here; resembles this SSOT's documented gotcha #3 (`expected_unattempted` seeded
   pre-canonical) but with venue already split — needs its own root-cause pass.

- [x] ✅ [DATA] P0. **EIGENLAYER combined-venue (`venue=EIGENLAYER-ETHEREUM`) legacy + mis-shaped-canonical-twin —
      live-verify + twin-verify + delete — DONE 2026-07-13.** 597 legacy
      (`market-data-tick-defi-central-element-323112`, `batch_onchain_rpc`) + 597 mis-shaped "canonical" twin
      (`market-data-tick-defi-prd-central-element-323112`, `batch_onchain_subgraph`) — both
      `venue=EIGENLAYER-ETHEREUM/instrument_type=restaking/data_type=rewards`, violating
      `/codex/02-data/defi-canonical-naming-ssot.md`. A correctly-split twin
      (`venue=EIGENLAYER/chain=ETHEREUM/instrument_type=staking/data_type=eigenlayer_rewards`) already existed for
      597/597 days (596 exact row-count parity + 1 strict superset); manifest carried ZERO rows for the combined venue
      (orphan objects, no manifest correction needed). Snapshotted both bucket manifests first, deleted all 1,194
      mis-shaped objects via `gcs_delete_object`, live re-verified 0/597 remain + 597/597 correct twins intact. Writer
      already fixed (`market-tick-data-service@b3a15d894`, 2026-05-19); no re-litter path found. Two adjacent findings
      logged (out of scope): `_normalize_venue()` docstring/code mismatch in `canonical_write.py`; 1,139 pre-existing
      `attempted_failed` manifest rows with old label-pairing. — unified-trading-pm (docs-only; no code change needed,
      data-only op)
