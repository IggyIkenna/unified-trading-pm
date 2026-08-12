---
doc_type: issue
title:
  "Cross-cutting manifest-canonicalisation findings + per-AG CF-state assessment (2026-07-11 /autonomous) — 2 shared
  bugs root-caused & fixed (schema_version-as-string, audit-tool _probe_paths backup-descent); precise per-AG
  remaining-work map for cefi/defi/tradfi/sports so each can be driven to E7-green + E8-delete applying prediction's
  proven lessons"
summary:
  "While driving the prediction manifest-canonicalisation to E7-GREEN + E8/E8b legacy-bucket deletes, two CROSS-CUTTING
  bugs affecting ALL migrated AGs were root-caused and fixed: (1) the shared v9 populator
  (populate_v9_index_columns_inplace.py) only rewrote NON-'9' schema_version rows to int 9, so rows already stored as
  the STRING '9' survived the str-guard and left the column mixed-object — which breaks readers doing schema_version >=
  9 (int compare) and makes CF-1 audit falsely RED on cefi/defi/tradfi (FIXED: forces int64 dtype); (2) the CF-audit's
  _probe_paths descended into _migration_backup/ (only _index/_vm_staging/snapshots were excluded), sampling a
  non-partitioned backup parquet and reporting false CF-2-paths/CF-3-partition RED on every AG (FIXED pm PR#928: skips
  ALL _-prefixed meta trees). Fresh CF-audits of all 5 AG canonical surfaces give the precise remaining-work map below.
  CF-8 (available_at absent, written_at proxy) is RED on ALL AGs and is a separate lookahead concern
  (predictions_lookahead_and_reader_migration_2026_06_20.md), not a per-AG blocker. **ADJUDICATED 2026-07-14
  (doc-reconciliation verify-rerun-2, findings 152/154/196): the per-AG 'remaining work' table's physical-relabel /
  rebuild / CF-audit claims are STALE for sports/tradfi/defi (all independently confirmed DONE + GCS-reverified
  2026-07-12) and tradfi's Era-B 242,210 chain-rows is a design-adjudicated non-issue, not remaining work; cefi is NOT
  adjudicated (no fresh CF-audit found). Legacy-BUCKET delete (a distinct axis from in-bucket duplicate cleanup, which
  is done) remains genuinely open for all four AGs — see the 'Adjudication 2026-07-14' section for the full per-claim
  evidence.**"
status: open
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-library, unified-trading-pm]
scope: [engineer]
tags: [manifest, canonicalisation, cf-audit, schema-version, cross-cutting, findings]
related:
  [
    /plans/archive/2026_07/prediction_manifest_canonicalisation_2026_06_01.md,
    /plans/archive/2026_07/cefi_manifest_canonicalisation_2026_06_01.md,
    /plans/archive/2026_07/defi_manifest_canonicalisation_2026_06_01.md,
    /plans/archive/2026_07/tradfi_manifest_canonicalisation_2026_06_01.md,
    /plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md,
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
  ]
created: 2026-07-11
author: unknown
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
archive_exempt: true # BRIDGE 2026-08-12: clearing the stale locked_by:live-defi-rollout placeholder (operator ruling, option B, see /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md) immediately surfaces this doc as 0-open-todos archive-eligible. Per that ruling's explicit scope ("do NOT auto-archive in this same pass"), archival is deferred to a separate follow-on pass. Bridged via the sanctioned flip-then-mv two-commit pattern documented in scripts/plan-hygiene/check_archive_candidates.sh -- drop this line + git mv to plans/archive/[issues/] in that follow-on pass.
locked_by:
locked_since:
source:
  ["/autonomous 2026-07-11 prediction canonicalisation drive — surfaced 2 cross-cutting bugs + per-AG CF-audit state"]
resolved_by:
context_scope:
  [
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    market-tick-data-service/scripts/one_offs/verify_legacy_bucket_decommission_precondition.py,
  ]
---

# Cross-cutting manifest-canonicalisation findings (2026-07-11 /autonomous)

> Companion to the 5 per-AG `*_manifest_canonicalisation_2026_06_01.md` plans + the master catalogue. Written after
> driving PREDICTION to full completion (E7-green manifest content + E8 tick-bucket delete + E8b instruments-store
> migrate+delete). Records the two shared bugs that were root-caused & fixed here, and the precise per-AG CF-state so
> cefi/defi/tradfi/sports can each be finished applying the same proven playbook.

## Two CROSS-CUTTING bugs — root-caused & FIXED this session

### 1. `schema_version` stored as STRING `'9'` (not int 9) — breaks reader int-comparison + false CF-1 RED

- **Symptom**: CF-audit reports `CF-1 [RED] v9=0/N (0.0%)` on cefi/defi/tradfi even though the value-distribution shows
  `'9'` at ~100%. The canonical `_index` `schema_version` column is `dtype=object` holding the string `'9'`.
- **Why it's a REAL bug, not cosmetic**: the UTL native writer types `schema_version: int = MANIFEST_SCHEMA_VERSION`
  (`unified_trading_library/manifest_writer/_rows.py`), and readers gate on
  `date_df["schema_version"] >= MANIFEST_SCHEMA_VERSION` (`_queries.py`) — a **str-vs-int comparison** that raises /
  misbehaves against string `'9'`.
- **Root cause**: `market_tick_data_service/scripts/populate_v9_index_columns_inplace.py` computed
  `not_v9 = df["schema_version"].apply(lambda v: str(v) != "9")` then set only `df.loc[not_v9] = 9`. Rows already stored
  as the STRING `'9'` pass the `str(v) != "9"` guard → never rewritten → column stays mixed-`object` → parquet stores
  string.
- **FIX (shipped, MTDS, landed on live-defi-rollout)**: append
  `df["schema_version"] = pd.to_numeric(df["schema_version"]).astype("int64")` after the bump. Every future `--apply`
  emits canonical int schema_version.
- **Existing-manifest remediation**: prediction's `_index` was normalised in-place (int64) → CF-1 GREEN.
  cefi/defi/tradfi `_index`es still hold string `'9'` and will be corrected when their migration re-runs the fixed
  populator (OR via a targeted `pd.to_numeric(...).astype("int64")` normalisation of the one
  `_index/availability_index.parquet` — snapshot first; prediction's normalisation script pattern is in that plan's
  Progress Log).

### 2. CF-audit `_probe_paths` descended into `_migration_backup/` → false CF-2-paths/CF-3-partition RED

- **Symptom**: every AG showed `CF-2-paths [RED]` / `CF-3-partition [RED]` even when the actual data objects are
  canonically partitioned (`raw_tick_data/by_date/day=…/pipeline_mode=…/asset_group=…/venue=…/data_type=…/`).
- **Root cause**: `cf_manifest_audit_2026_06_01.py::_probe_paths` excluded only `_index`/`_vm_staging`/`backfill-logs`/
  `snapshots`, NOT `_migration_backup/` (or `_migration_backups/`, `_backups/`) — so the shallow descent picked the
  alphabetically-first child `_migration_backup/…/<non-partitioned>.parquet` and reported no `pipeline_mode=`/
  `asset_group=`.
- **FIX (shipped, pm PR#928)**: skip ALL `_`-prefixed meta trees generically (data partitions never start with `_`).
  After the fix, prediction correctly reads CF-3-partition GREEN.
- **Residual note**: CF-2-paths can still read RED when the probe samples `processed_candles/` (MDPS candle scheme
  validly omits `asset_group=` — the per-AG bucket name encodes the AG; raw_tick DOES carry it). This is a
  check-altitude nuance, not a data gap — do NOT "fix" it by stamping `asset_group=` into candle paths.

## Per-AG CF-state (fresh audits 2026-07-11, `market-data-tick-<AG>-prd`)

> **⚠️ ADJUDICATED 2026-07-14 (doc-reconciliation verify-rerun-2, findings 152/154/196) — this table's "remaining work"
> column is STALE for physical relabel / rebuild / CF-audit on sports, tradfi, and defi.** See the "Adjudication
> 2026-07-14" section below the table for the full per-claim evidence; row cells are annotated in place `(was: …)`
> rather than silently rewritten.

| AG             | rows  | manifest-content CFs                                                                                     | remaining work to E7-green → E8-delete                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| -------------- | ----- | -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **prediction** | 755k  | **ALL GREEN** (CF-1/2/3/4/5/6/7/13/Era-B)                                                                | ✅ DONE. E8 tick-delete executing; residual audit REDs = CF-2-paths candle-scheme + CF-8 (both cross-cutting, not data gaps).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **sports**     | 1.80M | CF-1/3/4/5/Era-B **GREEN**; CF-7 has `ODDS`/`odds` + `ODDS_MOVEMENT`/`odds_movement` **case-drift**      | **STALE 2026-07-14 (finding 196).** CF-7 case-normalise ran (multiple touches). Physical relabel VM EXECUTED 2026-07-12 (E3+E4 fleet, 16 VMs exit_code=0) — CF-3-partition GREEN on `market-data-tick-sports-prd`, confirmed in 5+ independent audits 2026-07-13→07-14. (was: "physical relabel VM (objects lack `pipeline_mode=` segment → CF-3-partition)".) Genuinely still open: CF-8 `available_at` backfill (captured-row-specific gap, in-progress) + a small L6-legacy-only residual (28-140 cells, mostly accepted-phantom) — these, not physical relabel, gate E8 delete of `market-data-tick-sports` today.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| **defi**       | 27.4M | CF-4 near-green (2,477 blank), CF-5 GREEN, Era-B GREEN; CF-1 string-schema; physical paths               | **STALE 2026-07-14 (finding 196).** Physical relabel CONFIRMED DONE + GCS-verified 2026-07-12 — `market-data-tick-defi-prd`'s `raw_tick_data/by_date/day=2022-06-01/` shows populated `pipeline_mode=batch_onchain_rpc/`+`pipeline_mode=batch_onchain_subgraph/` partitions under `asset_group=defi/`; canonical index confirmed comprehensive (27.4M rows) via direct inspection (`data_completion_to_100_all_ag_2026_06_21.md` §C0e). (was: "physical relabel VM".) Legacy dedicated-per-kind buckets operator-authorized + 12/14 DELETED 2026-07-12 (1 deferred pending a live VM). Genuinely still open: apply schema_version int; populate 2,477 blank source; the SEPARATE raw_tick_data legacy-twin-bucket delete (still `BLOCKED-OPERATOR-DECISION`, grouped with tradfi/pred).                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| **cefi**       | 7.22M | CF-1 string-schema; **CF-4 source 54% blank (3.9M)**; CF-5 189,665 untyped; **Era-B 521,513 chain-rows** | **NOT ADJUDICATED — no fresh 2026-07 CF-audit re-run found for cefi; these data-content claims (CF-4/CF-5/Era-B) are UNCHANGED, do not treat as stale.** One narrower sub-claim IS stale: cefi's in-bucket legacy-duplicate cleanup is done ("9.98 TB / 1,077,672 legacy-shape objects deleted", operator-authorized, `instruments_mtds_subset_consistency_remediation_2026_06_17.md:462,1148`). **CORRECTED 2026-08-02 (operator ruling on `plan_reconcile_parked_operator_decisions_2026_08_02.md` § 1e, option A): the SEPARATE standalone legacy bucket (`market-data-tick-cefi-central-element-323112`, no `-prd`) — this row previously said "still holds real content as of 2026-07-10, NOT deleted" — is in fact DELETED, 2026-07-14, per `cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md:78-80` and `cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md:218-220`, i.e. before this row's own 2026-07-10 snapshot went stale. cefi's E8 whole-bucket delete is DONE — defi/tradfi/sports E8 deletes are unaffected by this correction and remain open.** Source backfill, CF-5 typed-reason, Era-B chain→trades reclassify, and schema int remain live todos pending cefi's own fresh CF-audit. |
| **tradfi**     | 5.09M | CF-1 string-schema; CF-4 near-green (14,003 blank); **Era-B 242,210 chain-rows**                         | **STALE 2026-07-14 (finding 196).** Physical relabel CONFIRMED DONE — CF-3-partition GREEN, re-confirmed in 6+ independent sessions 2026-07-08→07-13; G4 `--apply` DONE + GCS re-verified 2026-07-12 (`pipeline_mode=` partitions confirmed present for real dates, `migration_verification_orphan_safety_2026_06_10.md:719-721`). **Era-B 242,210 chain-rows is NOT remaining work — EXPLICITLY ADJUDICATED as a non-issue** (tradfi's bundle-grain design; the audit tool's "must be 0" premise doesn't hold; re-confirmed unchanged across 5+ sessions 2026-07-08→07-13). (was: "Era-B chain→trades; ... physical relabel; E8".) Genuinely still open: a 13,971-row (0.27%) v4 schema/source tail from an ACTIVELY-RUNNING backfill fleet (fleet-drain-gated, not a bulk historical gap) + the legacy-twin bucket delete (`BLOCKED-OPERATOR-DECISION`, hard-stop, unchanged) + the RESUME-runbook (still gated, see finding-154 note in `migration_verification_orphan_safety_2026_06_10.md`).                                                                                                                                                                                                                             |

**CF-8 (available_at)** is RED on ALL five AGs (column absent, `written_at` proxy present). This is a shared
point-in-time/lookahead concern owned by `predictions_lookahead_and_reader_migration_2026_06_20.md`, NOT a per-AG E7
blocker.

## Adjudication 2026-07-14 (doc-reconciliation verify-rerun-2, findings 152/154/196)

> Written in response to a cross-doc adjudication checking whether this doc's per-AG claims survive events that
> post-date it (2026-07-11): sports E3+E4 v9 migration EXECUTED 2026-07-12; a fresh 4-AG legacy-dup audit 2026-07-13
> (`unified-trading-pm@194b7d542`); tradfi's Era-B adjudication re-confirmed through 2026-07-13; TradFi G4 apply
> GCS-reverified 2026-07-12.

**Per-claim verdict (finding 196 — this doc's own "remaining scope" framing, § below):**

- **"physical relabel" (objects lacking `pipeline_mode=` in the `-prd` bucket) — STALE for sports/tradfi/defi, NOT
  adjudicated for cefi.** Confirmed DONE + independently re-verified via CF-3-partition GREEN reads (sports, tradfi) and
  direct GCS partition inspection (defi, tradfi). This is a DIFFERENT axis from legacy-bucket deletion — this doc's own
  "Remaining scope is VM-scale" paragraph below conflated the two; corrected there and in the table above.
- **"rebuild + CF-audit" — STALE for sports/tradfi (audited to exhaustion, 5-10+ independent re-runs each through
  2026-07-14), largely stale for defi (C0e consolidator-verify 2026-07-12), NOT adjudicated for cefi.**
- **"legacy-bucket delete" — STILL-LIVE for all four (sports/defi/tradfi/cefi), for a narrower reason than "relabel not
  done".** Two distinct axes must not be conflated: (a) in-`-prd`-bucket legacy-SHAPE duplicate objects (audited by
  `e2e-testing/scripts/defi/audit_legacy_gcs_dup_delete_list.py`) — >99% cleaned for defi/tradfi/sports/pred (fresh
  2026-07-13 audit: 2.88M→6,434 residual objects) and DONE for cefi (9.98 TB, done earlier); (b) the SEPARATE standalone
  legacy BUCKET each AG's own E8 step targets (e.g. `market-data-tick-sports`,
  `market-data-tick-cefi-central-element-323112`) — genuinely NOT yet deleted for any of the five AGs, each gated on
  either operator sign-off (defi/tradfi/pred/cefi: hard-stop, never-autonomous) or AG-specific residual gates (sports:
  CF-8 + L6-legacy-only).
- **tradfi's Era-B 242,210 chain-rows — MISFRAMED, not "remaining work".** Design-adjudicated non-issue (tradfi's
  bundle-grain data model), unchanged across every 2026-07 re-audit. cefi's 521,513 Era-B chain-rows has received NO
  such adjudication — do NOT assume the same exception; treat as still-live pending cefi's own fresh audit.

**RESUME-runbook readiness (finding 154, `migration_verification_orphan_safety_2026_06_10.md:728-731`)**: G4 `--apply`
is verified DONE for all 5 AGs, but the runbook's own precondition text requires BOTH "every AG `--apply`
complete+verified" AND "the new manifests are consolidated" before resuming the 48 paused GCP schedulers + 26 AWS rules.
Tradfi specifically is NOT fully consolidated (the same 13,971-row / 0.27% v4 schema tail above, from an
actively-running backfill fleet) — `tradfi_v9_stage1_finish_2026_07_06.md`'s own RESUME-runbook todo stays
`BLOCKED-PREREQUISITES` for exactly this reason, sequenced after the fleet-drain+re-stamp task. The
`migration_verification_orphan_safety` line only surfaces the FIRST precondition (G4 verified) as met without flagging
the second (consolidated) is not — see that doc's own correction below. cefi/defi/sports/pred are not separately
confirmed clean on the "consolidated" precondition either (no fresh audit found either way beyond tradfi's) — treat
RESUME-runbook readiness as unconfirmed fleet-wide, not just tradfi-gated.

**master_data_canonicalisation_migration_catalogue (finding 152)**: its own Gate-State Board (refreshed 2026-07-12, G4
🟢 all 5 AGs, RESUME-runbook text unchanged/still correctly conditional) was checked against this adjudication and found
ALREADY ACCURATE — no correction needed there; the staleness was confined to this cross-cutting doc's per-AG table
above.

## Recurring-bug playbook (prediction's proven lessons → apply per AG)

1. **schema_version → int** (bug #1 above; populator now fixed — re-run or normalise the `_index`).
2. **CF-15 live-path templates** — the phantom reconciler only enumerated `pipeline_mode=batch_<source>/` prefixes and
   false-phantomed LIVE-captured cells at `live_<source>/` paths. FIXED in `possible_manifest`
   (`_canonical_pipeline_mode_prefixes` now emits batch AND live prefixes per non-legacy source, uac@83ed5765). Any AG
   with live captures benefits; re-run `--unphantom-only --apply` if an AG shows spurious `attempted_failed[phantom_…]`.
3. **Phantom bundle-atom exemption** — manifest-only bundle atoms (`MANIFEST_ONLY_BUNDLE_DATA_TYPES`) must be EXEMPT
   from the object-existence phantom check (they have no on-disk path segment). Prediction's
   `prediction_canonical_question_group` was wiped before this; check each AG for manifest-only atoms before an
   `--apply` phantom pass.
4. **data_type case-drift + exact-dup collapse** — e.g. prediction had `MARKET_LIFECYCLE` as an EXACT case-drift
   duplicate of `market_lifecycle` (same 2,280 keys) → drop uppercase; sports has `ODDS`/`odds`. Normalise data_type to
   canonical-lowercase and collapse dups (verify key-membership first, don't blind-relabel).
5. **Vestigial blank-`data_type` rows** — malformed atoms (an atom requires a data_type). Prediction had 17 → dropped.
6. **Era-B chain rows** — `options_chain`/`futures_chain` data_type must be 0 (chains write `data_type=trades` with the
   chain distinction in `instrument_type`). cefi 521k needs this reclassify (unadjudicated, still-live). **tradfi's 242k
   is NOT this class (was: "tradfi 242k need this reclassify") — ADJUDICATED 2026-07-14 (finding 196) as a
   design-exception non-issue** (tradfi's adjudicated bundle-grain data model; the audit tool's "must be 0" premise does
   not hold for it; re-confirmed unchanged across 5+ sessions 2026-07-08→07-13, see the "Adjudication 2026-07-14"
   section above). Do not reclassify tradfi's Era-B rows on the strength of this playbook item.
7. **CF-4 source population** — `record_captured(source=…)` is required; cefi has 54% blank. Backfill from the
   `pipeline_mode` `{mode}_{source}` or the venue→source map.
8. **Physical-path relabel is a VM `--apply`** — objects lacking `pipeline_mode=`/`asset_group=` segments require the
   migrator's operational relabel run (fleet-drain-gated), not a manifest-only fix. **UPDATE 2026-07-14 (finding 196):
   this has now RUN and is CONFIRMED DONE for sports (E3+E4 fleet, 2026-07-12) and tradfi/defi (GCS-reverified
   2026-07-12) — CF-3-partition GREEN on all three's `-prd` surfaces.** (was: "objects lacking … segments (sports)
   require …" implying sports was still pending — sports's own relabel is done; only cefi's is unadjudicated.)

## Remaining scope is VM-scale (documented, not a descope)

> **⚠️ CORRECTED 2026-07-14 (doc-reconciliation verify-rerun-2, findings 152/154/196) — see "Adjudication 2026-07-14"
> above for the full evidence.** (was: "Each of cefi/defi/tradfi/sports still needs its operational migrator `--apply`
> (physical relabel) + rebuild + CF-audit + legacy-bucket delete — hours-long, fleet-drain-gated VM runs" — this blanket
> framing conflated two different axes and is STALE for the relabel/rebuild/CF-audit portion on sports/tradfi/defi.)

**Physical relabel + rebuild + CF-audit is DONE for sports, tradfi, and defi** (E3+E4 fleet 2026-07-12 for sports; G4
apply + GCS-reverify 2026-07-12 for tradfi/defi; each independently CF-3-partition-GREEN-confirmed through 2026-07-14).
**cefi is NOT adjudicated either way** — no fresh 2026-07 CF-audit re-run was found for it; its data-content gaps
(CF-4/CF-5/Era-B) stand as originally recorded.

**Legacy-bucket delete remains genuinely open for ALL FOUR** (cefi/defi/tradfi/sports) — but this is now a narrower,
better-understood gap than "physical relabel not done": the in-`-prd`-bucket legacy-duplicate cleanup is essentially
complete (>99% for defi/tradfi/sports/pred per the fresh 2026-07-13 audit; done earlier for cefi), while the SEPARATE
standalone legacy BUCKET each AG's own E8 step targets has not been deleted for any AG — gated on operator sign-off
(defi/tradfi/pred/cefi, hard-stop) or AG-specific residual closure (sports: CF-8 + L6-legacy-only). `populate_v9` fix +
the audit-tool fix + this playbook remove the shared blockers; the per-AG data-content fixes (cefi Era-B/source/CF-5,
defi source/schema-int) are code+rebuild work still homed in each AG's tracking doc.

## Todos

- [x] ✅ [DATA] P1. **Legacy-bucket delete (defi/tradfi/sports) ~~+ cefi CF-audit adjudication~~** — the standalone
      legacy bucket each remaining AG's own E8 step targets (defi/tradfi/sports) remains genuinely undeleted~~, and
      cefi's CF-4/CF-5/Era-B data-content claims are NOT ADJUDICATED (no fresh 2026-07 CF-audit re-run found for
      cefi)~~. **cefi's own legacy-bucket delete is DONE (corrected 2026-08-02, see the cefi table row above) — dropped
      from this todo's AG list.** **STALE (na-eligibility-audit 2026-08-03)** — the cefi CF-audit adjudication half is
      ALSO done, not "unaffected and still open" as the 2026-08-02 correction claimed:
      `cross_cutting_satellite_ao_dispatch_batch1_     2026_07_26.md`:465 (DONE 2026-08-01, slot-6, data_engineering)
      ran a fresh `cf_manifest_audit.py` against the live `market-data-tick-cefi-prd-central-element-323112` manifest
      and confirmed CF-1/CF-3/CF-4/CF-5/Era-B all GREEN for cefi (`market-tick-data-service@c2ae82e0`, 9,662,116 rows,
      independently re-verified post-apply) — this is exactly the named CF-4/CF-5/Era-B adjudication this todo asked for
      (CF-8/CF-2-paths stay RED but were already explicitly out of that todo's scope, tracked separately). **RESOLVED
      2026-08-08 (operator, NA-corpus blocker digest round 5, id=57 — "execute it, but only after verifying zero live
      callers first"): all 3 remaining buckets are ALREADY GONE — nothing to execute.** Zero-live-callers check done
      first as instructed: grepped the FULL workspace (all repos, not just unified-trading-pm) for
      `market-data-tick-{defi,tradfi,sports}` — every application-code hit is a comment/docstring narrating history
      (e.g. `market-data-processing-service/.../build_continuous_engine.py:116-118` documents a prior
      `resolve_bucket_name(kind="market-data-tick-tradfi")` call that ALWAYS raised `BucketNamingError`, never worked),
      Terraform `gcs_volumes` blocks use the bare name only as a local mount LABEL (the real `bucket =` value
      interpolates the env-tiered project-suffixed name), and the 3 bare names are not registered `bucket_template`s
      anywhere in `cloud-providers.yaml` (registry already superseded) — **zero live callers, confirmed**. Then checked
      current existence, fresh (not assumed — the doc's own table already flagged tradfi as suspect-already-deleted):
      `gcloud storage buckets describe gs://market-data-tick-{defi,tradfi,sports}` → **all 3 return a clean `404` (not a
      permission-denied ambiguity)**, and a project-level
      `gcloud asset search-all-resources --scope=projects/central-element-323112     --asset-types=storage.googleapis.com/Bucket --query="name:market-data-tick-"`
      cross-check lists only the canonical `-{ag}-{env}-central-element-323112` shaped buckets — **none of the 3 legacy
      bare names exist in this project.** Nothing to delete; this todo's "still pending" framing was stale (matches the
      tradfi discrepancy already flagged in this doc's own table: tradfi's flat bucket was independently confirmed
      deleted 2026-07-14 in `tradfi_legacy_bucket_deleted_without_also_legacy_migration_2026_07_26.md`, and defi/sports
      have evidently since followed the same path, untracked). **One residual finding**: a dormant one-off script,
      `market-tick-data-service/scripts/cleanup_may4_bait_sentinels.py` (lifecycle=oneoff, marked "Delete-when: after
      prod-run verified complete" but still present), hardcodes these exact 3 legacy bucket names in an
      `ASSET_GROUP_BUCKET` map — not a live caller (only reachable via manual `--apply`), but should be deleted as dead
      code alongside this finding; flagged for market-tick-data-service, not actioned here (out of this session's edit
      scope).

## Progress Log

- **plan-reconcile 2026-08-02 § 1e — RULED, option A**: operator confirmed cefi's legacy bucket
  (`market-data-tick-cefi-central-element-323112`) was deleted 2026-07-14, correcting this doc's prior "remains
  genuinely undeleted" claim (stale as of the 2026-07-10 snapshot it was based on). See the cefi table row + Todos
  section above for the applied correction.
- **na-eligibility-audit 2026-08-02** (re-confirms 2026-07-30; content unchanged since; NOTE its cefi legacy-bucket
  claim was the live contradiction parked for operator ruling above, now resolved): KEEP-NA, valid —
  `locked_by: live-defi-rollout`; the remaining defi/tradfi/sports legacy-bucket deletes are documented as 'hard-stop,
  never-autonomous' operator sign-off.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: reviewed, still accurate — refreshed marker (6 entries).
- **na-eligibility-audit 2026-08-04**: KEEP-NA, valid — sole open `[DATA]` P1 todo is a legacy-bucket delete for
  defi/tradfi/sports, explicitly gated in-doc on operator sign-off ("hard-stop, never-autonomous" per the delete-safety
  protocol) — a genuine human-only gate, not a judgment-free bounded task. The 2026-08-03 inline annotation resolves
  only the CEFI CF-audit-adjudication half; the bucket-delete half remains open and correctly NA.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — reaffirms 2026-08-04 (unchanged): sole open todo is a
  whole-bucket GCS delete for defi/tradfi/sports, explicitly "hard-stop, never-autonomous" per delete-safety protocol.
- **context-scout 2026-08-07**: refreshed context_scope (3 entries) — the sole open todo is now purely the
  defi/tradfi/sports legacy-bucket delete (cefi's half + the CF-audit adjudication are both done), so trimmed to the
  delete-safety protocol, the master catalogue (per-AG gate tracking), and the standalone
  `verify_legacy_bucket_decommission_precondition.py` tool built exactly for this precondition. Dropped the CF-audit
  tooling (`cf_manifest_audit.py`, `populate_v9_index_columns_inplace.py`) — that work is closed — and
  `cf_manifest_audit_first_full_rollup_findings_2026_07_26.md`, which is not actually cited anywhere in this doc's body
  text (the doc's own resolution note cites a _different_ doc,
  `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`, for the same CF-audit-adjudication evidence — flagged as a
  stale-candidate finding, not corrected here).
- **na-eligibility-audit 2026-08-07 (cross-cutting tranche)**: KEEP-NA, valid — reaffirmed, unchanged. Sole open todo
  (whole-standalone-bucket GCS delete for defi/tradfi/sports) is explicitly 'hard-stop, never-autonomous' operator
  sign-off per the delete-safety protocol; `locked_by: live-defi-rollout` noted, not touched.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (3 entries), still accurate.
- **2026-08-12** — `locked_by`/`locked_since` cleared (corpus-wide fix, operator ruling Option B, interactive session
  2026-08-12; see /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md). This doc has
  0 open todos, so clearing the placeholder lock immediately makes it archive-eligible. Per the ruling's explicit scope
  ("do NOT auto-archive in this same pass"), archival itself is deferred to a separate follow-on pass; bridged with
  `archive_exempt: true` (the sanctioned flip-then-mv two-commit pattern documented in
  `scripts/plan-hygiene/check_archive_candidates.sh`) so this commit doesn't trip the archive-candidates pre-commit
  gate. The follow-on pass should drop `archive_exempt` and `git mv` this doc to `plans/archive/[issues/]`.
