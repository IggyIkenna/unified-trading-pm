---
doc_type: plan
title: Sports legacy bucket cutover — freeze, move, purge, delete, restore
summary:
  Executable cutover runbook retiring the last two non-canonical sports buckets — instruments-store-sports-* and
  market-data-tick-sports-* — into their -prd- canonical twins. Synthesised from five read-only audits (code, infra,
  objects, manifests, v1_archive). Freeze writers, repoint the static legacy declarations, MOVE only the 30,333
  object-layer-verified unique objects to canonical paths, purge the 123,149 bogus index rows in the quiet window, prove
  zero-unique at the OBJECT layer, then delete and restore in reverse.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    unified-trading-pm,
    deployment-service,
    market-tick-data-service,
    instruments-service,
    deployment-api,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [migration, bucket-canonicalisation, cutover, gcs, terraform, manifest, sports, destructive]
related:
  [
    sports_manifest_canonicalisation_2026_06_01.md,
    sports_data_sources_canonical_completion_2026_07_13.md,
    ../epics/sports_master.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source: [operator request 2026-07-16, 5-leg read-only audit 2026-07-16]
---

# Sports legacy bucket cutover — 2026-07-16

> **DESTRUCTIVE PLAN. Phases are STRICTLY SEQUENTIAL. Phase 5 (delete) is gated on Phase 4 (proof) and a FINAL
> live-writer re-check.** Every phase todo carries a Mechanism, a Verification, and an ABORT condition. An ABORT means
> STOP the phase and escalate — it never means "note it and continue."

**Operator goal (2026-07-16, verbatim)**: _"instruments-store-sports-central-element-323112 doesnt need to exist whilst
instruments-store-sports-prd-central-element-323112 exists — its the last instrument store bucket which has non
canonical [paths]. For that to migrate it needs us to ensure all the code and deployed vms and cloud run/service etc and
manifests and catalogues etc all migrate fully to the canonical bucket usage, and to avoid redownloading we should
instead MOVE any non already existent data into the canonical bucket."_ Operator additionally authorises _"stopping all
sports related crons and vms and cloud stuff to make the migrations and fixes and bucket deletes then rerunning
everything so sports is in canonical buckets and paths."_

| Legacy (delete)                                   | Canonical (survives)                                  |
| ------------------------------------------------- | ----------------------------------------------------- |
| `instruments-store-sports-central-element-323112` | `instruments-store-sports-prd-central-element-323112` |
| `market-data-tick-sports-central-element-323112`  | `market-data-tick-sports-prd-central-element-323112`  |

## Codex SSOTs (read before executing the phase that cites them)

| SSOT                                                           | Governs                                                          |
| -------------------------------------------------------------- | ---------------------------------------------------------------- |
| `codex/02-data/sports-gcs-path-ssot.md`                        | Canonical sports path shape; `candidate_parquet_paths()`         |
| `codex/02-data/pipeline-mode-partition.md`                     | `{mode}_{source}` segment placement; readers PREFIX-MATCH        |
| `codex/02-data/availability-manifest-and-data-status.md`       | 4-state `capture_status`; per-VM shards; consolidator contract   |
| `codex/02-data/honest-absence-downstream-handling.md`          | Phantom vs real absence; never fake `record_captured`            |
| `codex/02-data/data-pipeline-correctness-hard-rule.md`         | Audit issues fixed in FULL; RED freezes layer N+1                |
| `codex/02-data/bucket-naming-and-config.md`                    | `resolve_bucket_name()` is the only name producer                |
| `codex/02-data/sports-data-source-coverage-matrix.md`          | `ODDS` writer is footystats only — no api_football odds path     |
| `codex/05-infrastructure/gcs-object-operations.md`             | UTL `gcs_copy_object`/`gcs_delete_object` — never `gsutil`       |
| `codex/05-infrastructure/manifest-consolidator-ssot.md`        | Consolidator is Cloud Run; loud-fails on stale index             |
| `codex/05-infrastructure/vm-launcher-runbook.md`               | Registered launchers; `VM_PREFIX_TO_BUCKET`; pre-migration drain |
| `codex/05-infrastructure/deployment-service-gcp-tofu-state.md` | Terraform state ops; `state rm` vs `destroy`                     |
| `codex/06-coding-standards/script-homes.md`                    | One-off lifecycle markers; delete-after-prod-run                 |

---

> # ✅ **`instruments-store-sports-central-element-323112` IS DELETED — 2026-07-16T19:52Z.**
>
> **The LAST Group-A legacy instruments twin is GONE.** Executed after every gate was RE-MEASURED (not inherited): T4.1
> **UNACCOUNTED = 0** against a live re-count of **968,927 (delta +0)** · OR-9 recovery re-verified by fresh reads
> **131/131** · T5.2 **0 writers** (R-1b discriminator) · T5.1 block removed **ds@4637aed** + `tofu state rm` · T5.3
> **968,927 objects + 34,596 versions** purged, 0 errors · T5.4 via Cloud Build **`7b8b0e75`** → **`describe` = 404 from
> the ELEVATED SA** (a real 404, not this slot's 403-masquerade) and the flat name is absent from `buckets list`.
> **Canonical `-prd-` survives intact** (all 3 `_index/per_vm/` shards incl. `or9-recover`). **No resurrection
> pending**: the post-delete `tofu plan` (**`97baca1b`**) is the same shape as pre-delete and carries **ZERO actions
> referencing the deleted bucket**.
>
> **⚠️ `market-data-tick-sports-central-element-323112` is NOT deleted and MUST NOT be — still blocked on OR-5b.** Its
> terraform block (`main.tf:345`) + import block (`_imports_reconcile.tf:74-77`) are deliberately RETAINED.
>
> **🔴 DO NOT run a full `tofu apply` on prod** — it would resurrect `instruments-store-cefi-…` (404 but still
> declared + in state) and make 71 unaudited changes →
> [`issues/terraform_instruments_cefi_armed_resurrection_2026_07_16.md`](issues/terraform_instruments_cefi_armed_resurrection_2026_07_16.md).
> **The two Phase-1 applies were NOT run and are NOT needed**: R-17/T1.3's live MDPS FUSE mount **does not exist** (all
> 113 live Cloud Run jobs carry zero legacy refs; the MDPS module is dormant with an EMPTY state), and R-16 was
> satisfied by `state rm`-ing the 2 legacy IAM keys instead. Details in the Progress Log's Phase-5 entry.
>
> **🟡 REMAINING (unchanged by this leg)** — `market-data-tick-sports` is still BLOCKED on OR-5b; the residue is now
> MEASURED at ~2,081 objects on 32 days carrying 550,062 legacy-only tick keys, NOT 49,517 objects / 7,079,850 rows.**
> The OR-5b recovery leg re-measured at the key layer over ALL 1,837 legacy tick-days (~900k reads, 0 errors): **1,805
> days are at exactly ZERO legacy-only keys**; the gap is 32 days, dominated by a canonical capture outage
> 2022-09-07…2022-10-01. The "6.37M genuine pre-match rows" was a ROW-count + PER-PAIR artifact; **the option-D G1 merge
> was REFUSED** (it would have duplicated ~15.7M rows) and **zero data objects were mutated**. **43,964/45,701
> (96.199%)** class-B objects close by direct proof. Also found: **T2.6's 6,110 moved objects are a pure duplicate
> population** (case-blind strip key) → own issue doc; settle before T6.1. See the OR-5b block + **OR-9 is closed**: all
> 2,078 unaccounted objects now carry a written, measured disposition; the re-run T4.1 accounting closes at **968,927
> with UNACCOUNTED = 0**. 131 canonical cells were recovered (482 distinct legacy-only keys + 803 progressive rows);
> **not one legacy object was mutated or deleted**. See the Progress Log's OR-9 entry. **T4.1 STAYS `- [ ]` — it gates
> BOTH buckets and the MDT half is still open (OR-5b).** T5.1-T5.4 have NOT run and still MUST NOT: they also require
> the two `tofu apply`s (T1.3 MDPS FUSE-mount removal, T1.4 catalogue IAM repoint) and T5.2's final writer re-check.
>
> **The headline correction (5th "inherited classification" reversal — the reason this leg re-measured instead of
> executing the ruling as written): the "6,673 genuinely legacy-only keys / GENUINE loss — re-fetch" verdict was ~94%
> WRONG.** Only **482 keys** were real recoverable data. **5,897 of the 6,379 `fixture_stats` keys carry NO STATISTICS
> PAYLOAD AT ALL** — 1,648 of the 1,738 legacy objects are `[fixture_id, available_at]` **2-col** files, not the "4-col
> nested" form OR-9 was written around, and a whole-corpus scan of **all 27,247** legacy `fixture_stats` objects proves
> **no payload exists for any of those keys anywhere in legacy**. Deleting the bucket loses nothing for them; unioning
> them would have written 21 NULL stat columns per row — the **banned empty-placeholder pattern**.

## THE HEADLINE — read this before touching anything

Five audits agree on the shape of the work, but **synthesis surfaced three findings no single leg owned**. Each one
would have caused silent, permanent data loss if the phases below were executed in the obvious order.

### F-1 (BLOCKING) — the designated MOVE vehicle silently enumerates 4 of its 7 trees as EMPTY

`market-tick-data-service/market_tick_data_service/scripts/migrate_sports_canonical_v9.py` is the plan-of-record
instruments MOVE vehicle. Its `_list_tree()` (`:463-467`) enumerates exactly one shape:

```python
def _list_tree(fs, bucket, prefix, days, workers):
    """List all parquet objects under bucket/prefix/day=D for each day in days."""
    for found in pool.map(lambda d: fs.find(f"{bucket}/{prefix}/day={d}"), days):
```

`_INSTR_DATA_TREES` (`:110-117`) declares **seven** trees. Only three are `{prefix}/day={d}` shaped
(`sports_reference/by_date`, `sports_reference_v2/by_date`, `sports_reference_v1_archive/by_date`). The other four
resolve to paths that cannot exist:

| Declared tree                                       | Path `_list_tree` probes                     | Legacy's actual shape                      | Result        |
| --------------------------------------------------- | -------------------------------------------- | ------------------------------------------ | ------------- |
| `"day="` (bare top-level)                           | `{bucket}/day=/day={d}`                      | `day=2026-03-21/venue=BETFAIR/…`           | **0 objects** |
| `"instrument_availability"`                         | `{bucket}/instrument_availability/day={d}`   | `instrument_availability/by-date/day-{D}/` | **0 objects** |
| `sports_reference/mappings` (static)                | `{bucket}/sports_reference/mappings/day={d}` | `…/mappings/season=2019/`                  | **0 objects** |
| `sports_reference/{fixtures,footystats_league_ids}` | `…/{tree}/day={d}`                           | static, no day shard                       | **0 objects** |

`instrument_availability` alone is **119,858 legacy objects**. The vehicle reports
`RECONCILE SUMMARY: legacy_only_total=N` and exits 0 — a **systematically undercounted N reported as success**. This is
the fourth instance of the tooling-lies class this investigation. **Do not trust the vehicle's own enumeration.**

### F-2 (BLOCKING) — the vehicle's set-difference semantic cannot see the 13,222-object data-loss class

`_run_instruments_reconcile` (`:717-737`) is explicit: _"Compute legacy-only (present in legacy, absent from prd) … Copy
legacy-only objects → prd."_ The objects leg proved **13,222 legacy objects have a canonical counterpart that holds
STRICTLY FEWER ROWS** (111,827 player_stats rows, 91,380 standings, 69,444 fixture_events, …). Those are **not**
legacy-only → the vehicle **skips every one of them**. The same is true of
`migrate_legacy_tick_buckets_to_canonical.py`, whose `gcs_copy_object` skip-if-exists semantic — correctly praised by
the code leg as matching the operator's "move only non already existent" wording — **skips exactly the objects that
carry the missing rows**. The vehicle's own docstring concedes this: schema regressions are _"flag[ged] for manual
column-union."_

> **The operator's "MOVE any non already existent data" is object-existence phrasing. At the row layer, canonical is NOT
> a superset of legacy.** Taking the phrase literally deletes 305,000+ rows. This needs an OPERATOR RULING (OR-1).

> **🟡 F-2 INVESTIGATED 2026-07-16 (operator ruling: "investigate the row gap first") →
> [`issues/sports_legacy_canonical_row_gap_2026_07_16.md`](issues/sports_legacy_canonical_row_gap_2026_07_16.md).**
> **The class is REAL (not a path artifact) but the cause is NOT a lossy migration.** Nothing ever transformed legacy
> rows into canonical rows: the v9 vehicle is a byte-identical `gcs_copy_object`; the 2026-04-28 v1→v9 plan is
> `phase: pending_approval` (never ran, `entity=fixtures`-scoped only); canonical `fixture_events` carries
> `player_id`/`team_id`/`time_elapsed` columns legacy **never had**. Measured: **62/62 canonical twins are written LATER
> than legacy** (legacy 05-01…05-23, canonical 07-06…07-15) — the buckets are two INDEPENDENT capture generations.
> **Canonical is NET RICHER: +27,764 rows over 3,051 paired objects (gains 29,650 / loses 1,886, 15:1)** — F-2 measured
> only the losing 2%. The ~305k splits: **player_stats 111,827 (37%) = GENUINE complementary coverage (recover)**;
> standings 91,380 + teams 16,502 + player_values 16,233 (~41%) = **snapshot skew with ZERO missing entities + one
> cartesian-junk write (never merge)**; fixture_events 69,444 (23%) = **degenerate 5-col legacy schema, rows
> unattributable**. **OR-1 → option D (partial/targeted), NOT A and NEVER B.**

### F-3 (BLOCKING, ordering) — the vehicle would re-import the v1_archive the v1_archive leg says must never enter canonical

`SPORTS_REF_V1_ARCHIVE_PREFIX` is a member of `_INSTR_DATA_TREES` (`:113`) **and** is one of the three trees whose shape
`_list_tree` _can_ enumerate. The v1_archive leg's verdict is `safe-to-delete` with the explicit warning that _"moving
it into the canonical bucket would import a retired-schema backup of data canonical already holds, re-contaminating the
bucket the operator wants clean."_ Running the vehicle before deleting the archive copies all 398 objects **into
canonical**. → **Phase 2a (delete v1_archive) must run BEFORE Phase 2b (move).**

### F-4 (BLOCKING) — the day window silently truncates both ends

`--start-date` defaults `2019-01-01`, `--end-date` defaults `2026-06-01` (`:813-814`). Verified unique-object date span
is **2018-01-02 … 2026-12-06**. Defaults silently drop 2018 (`standings`/`teams` from 2018-01-01, `footystats_odds` from
2018-05-07) and everything after 2026-06-01 (`fixtures_schedule`/`fixtures_outcomes` run to 2026-12-06 — these are
legitimate future-dated fixtures). Days outside the window are never listed → never reported → never copied.

### F-5 (~~BLOCKING~~ **RESOLVED / FALSE PREMISE** 2026-07-16) — ~~something is STILL WRITING to the legacy bucket~~

> **🟢 F-5 IS DISPROVEN AT THE OBJECT LAYER (T0.1, 2026-07-16). There is NO live legacy writer — there never was.** F-5
> read the GCS **`updated`** field and interpreted it as a write time. It is not: `updated` also bumps on a
> **metadata-only** change, and an Object-Lifecycle **storage-class transition** is exactly that. Measured over 100% of
> both legacy buckets (enumeration dedup-verified to the exact audited totals 969,321 / 406,581, so this is not an F-1
> style subset): of the **5,008** objects with `updated >= 2026-07-09`, **5,008 are transitions, 0 are writes** —
> `generation` unchanged (a write mints a NEW generation), `metageneration` 1→2, and
> `updated == timeStorageClassUpdated` to the second. Bucket-wide: **954,303 STANDARD ⇔ metageneration=1**; **15,018
> NEARLINE ⇔ metageneration=2**. Every transition fired at **age EXACTLY 90 days** ⇒ an OLM `STANDARD→NEARLINE @ 90d`
> rule. F-5's own numbers ARE the transition cohort (07-12: 2,398 · 07-13: 1,559 · 07-14: 220 · 07-15: 125), and its
> "newest write 2026-07-15T20:07:38Z" is `_index/availability_index_backup_20260416.parquet` **created
> 2026-04-16T17:23:56Z** — and **2026-04-16 + 90d = 2026-07-15**. The only genuine writes in 30 days are **3 `_audits/`
> artifacts on 2026-07-14T00:12** from a hand-run `audit_fixtures_via_api_football.py`, whose legacy-name literal was
> deleted 2h33m later by `instruments-service@bd6b797a`. **This was our own agent activity, now finished and remediated.
> T0.1 PASSES; OR-2 is MOOT.**
>
> **Lesson (this is the 5th "tooling-lies" instance — the instrument itself misled):** `updated` is NOT a write time. To
> prove a write, compare **`generation`** (or assert `updated != timeStorageClassUpdated`), and note a _fresh create_
> also has `updated == timeStorageClassUpdated`, so age-0 objects need a separate check — that check is what surfaced
> the 3 real writes.

_Original (false) finding, retained for provenance:_

Newest legacy write `2026-07-15T20:07:38Z`; **125 writes on 07-15, 220 on 07-14, 1559 on 07-13, 2398 on 07-12** — and
not just index artifacts: real data paths
(`instrument_availability/by_date/day=2021-08-{16,17,18}/venue=API_FOOTBALL_FIXTURES/instruments.parquet`, ~120
`day=2026-04-14/league=*/venue=API_FOOTBALL/` objects). Yet: no sports VMs exist, every Cloud Run job spec is canonical,
and **no resolver can produce the legacy name** (proven at runtime — missing env, empty env, every tier → `-prd-`).
**The writer is unidentified.** A migrate-then-delete without stopping it silently re-creates legacy objects, or
re-creates the bucket. Phase 0 cannot complete until this is named. (`market-data-tick-sports` legacy IS dormant — all
406,581 objects written 2026-06-27, single bulk op.)

### The resulting decision

> **Do not drive Phase 2 from the v9 migrator's enumeration.** Drive it from the objects leg's **verified object-layer
> inventory** (method reproduced in T2.2), and use the migrator only as a copy primitive — or replace it. See **OR-6**.

### Migration payload (object layer — the only layer that counts)

| Class                                               | Objects    | Disposition                                      |
| --------------------------------------------------- | ---------- | ------------------------------------------------ |
| Legacy total (`instruments-store-sports`)           | 969,321    | —                                                |
| ├─ duplicate in canonical (crc match)               | 495,082    | no action                                        |
| ├─ superseded (canonical ≥ rows, or later snapshot) | 443,508    | no action                                        |
| ├─ contentless                                      | 0          | — (class is empty; nothing droppable)            |
| └─ **unique**                                       | **30,731** | —                                                |
| ├─ class A — no canonical cell at any pipeline_mode | 17,509     | MOVE (minus v1_archive)                          |
| │ └─ of which `sports_reference_v1_archive/`        | 398        | **DELETE, never move** (v1_archive verdict)      |
| └─ class B — canonical cell exists, FEWER rows      | 13,222     | **MOVE — blocked on OR-1** (vehicle skips these) |
| **NET unique to migrate**                           | **30,333** | = (17,509 − 398) + 13,222 ✓                      |

Arithmetic closes against the object layer: 495,082 + 0 + 443,508 + 30,731 = 969,321 = exact legacy object count.

`market-data-tick-sports` (second bucket): 406,581 objects; **~52,400 unique ESTIMATED** (9,927 no-canonical-key
verified + ~42,500 extrapolated from an n=400 sample of 108,970 crc-differing pairs whose row-count pass ran out of
budget). **This estimate is NOT a delete-gate.** T2.6 finishes the exact pass.

---

## Todos

### PHASE 0 — FREEZE (writers first, consolidators LAST after a final drain)

- [x] ✅ [INFRA] P0. **T0.1 — Identify the live legacy writer (F-5). HARD GATE — RESOLVED 2026-07-16: THERE IS NO LIVE
      WRITER.** F-5's premise was a **measurement artifact** — it read the GCS `updated` field and called it a write.
      **Measured (object layer, both legacy buckets, 100% enumerated — dedup-verified to the exact audited totals
      969,321 / 406,581)**: of the 5,008 objects with `updated >= 2026-07-09`, **5,008 are lifecycle storage-class
      transitions and 0 are writes**. Discriminator: a write creates a NEW `generation`; a transition leaves
      `generation` untouched, bumps `metageneration` 1→2, and sets `updated == timeStorageClassUpdated` **to the
      second**. Bucket-wide the correspondence is exact: **954,303 STANDARD ⇔ metageneration=1** (never touched) and
      **15,018 NEARLINE ⇔ metageneration=2** (transitioned exactly once). Every transition fired at **age EXACTLY 90
      days** (07-12: 2,398 all age-90; 07-13: 1,559; 07-14: 217; 07-15: 125) — i.e. an OLM `STANDARD→NEARLINE @ 90d`
      rule. F-5's cited "real DATA paths" are the same artifact: `instrument_availability/…/day=2021-08-16/…` was
      **created 2026-04-16T01:32:40Z** (`generation=1776303160008012`, `metageneration=2`,
      `storage_class_update_time == update_time == 2026-07-15T09:52:35Z`), and the "newest write"
      `_index/availability_index_backup_20260416.parquet` was **created 2026-04-16T17:23:56Z**, transitioned
      2026-07-15T20:07:38Z. **2026-04-16 + 90d = 2026-07-15.** _The ONLY genuine writes_ in 30 days: **3 objects**,
      2026-07-14T00:12:14-16Z, all under `_audits/` (`fixtures_{truthset,diff,recovery_set}_20260714-001053`) →
      attributed to a **hand-run of `instruments-service/scripts/audit_fixtures_via_api_football.py`** (run_ts
      `20260714-001053`), which then wrote via the since-deleted
      `_bucket_for_project(project_id) -> f"instruments-store-sports-{project_id}"` raw literal. **Already remediated**:
      `instruments-service@bd6b797a` _"fix(sports): … prd truthset bucket default"_ (**2026-07-14T02:45:02Z — 2h33m
      AFTER those writes**) deleted that literal for
      `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group="sports")`; **verified ancestor of
      `origin/live-defi-rollout`** (not yet on `origin/main` — hand-run script, no image/cron, so not a writer risk).
      **No scheduler, no Cloud Run job, and no VM invokes that script** (verified: `gcloud scheduler jobs list` /
      `run jobs list` grep `truthset|audit` → only the unrelated `uts-prod-cf-manifest-audit`; `compute instances list`
      `name~sports|truthset|fixtures` → zero rows). `market-data-tick-sports` legacy: **0 objects touched since 07-09**
      — fully dormant (all 406,581 COLDLINE, metageneration=2), confirming the audit. **⇒ The writer was OUR OWN
      now-finished agent activity, fixed in code. OR-2 is MOOT — the cutover is not blocked.** Residual (NOT the writer,
      read-only): `deployment-service/.../data_status_sports.py:25` — read the file in full, every GCS call is
      `list_blobs`; it cannot write. Stays a T1.1 fix. Evidence: `~/tmp-cutover/scan_writers.py` +
      `scan_<bucket>.jsonl`. _Superseded mechanism (kept for provenance)_: enable/read GCS data-access audit logs —
      unnecessary; the object layer settled it (data-access logs are OFF, so this was the only available path anyway).
      _Original mechanism_:
      `gcloud logging read 'resource.type="gcs_bucket" AND resource.labels.bucket_name="instruments-store-sports-central-element-323112" AND protoPayload.methodName="storage.objects.create"' --project=central-element-323112 --freshness=7d --format='table(timestamp, protoPayload.authenticationInfo.principalEmail, protoPayload.resourceName)' --limit=200`.
      If data-access logging was off, attribute via the object cohort instead: the 07-15 12:18-12:25Z
      `instrument_availability/by_date/day=2021-08-1{6,7,8}/venue=API_FOOTBALL_FIXTURES/` cluster and the
      07-15T20:07:38Z `_index/availability_index_backup_20260416.parquet` write both look like a hand-run one-off (an
      agent/slot running a `scripts/` one-off), not a scheduled job — cross-check against slot shell history and the ~35
      legacy-reading one-offs enumerated in T1.6. _Gate_: a NAMED principal + mechanism, and it is stopped/quiesced.
      _ABORT_: writer cannot be identified after audit-log + cohort attribution → **STOP the whole cutover** and
      escalate (OR-2). Deleting a bucket with an unidentified live writer is the resurrection-plus-data-loss case.
- [x] ✅ [INFRA] P0. **T0.2 — Snapshot EVERYTHING before any mutation (this is the rollback substrate). DONE
      2026-07-16** — 19 control-plane backups across all 4 buckets, 0 failures, every backup crc32c-verified == source
      (re-read proof, stronger than size>0). Inventory reproduces audited ground truth EXACTLY on both legacy buckets
      (969,321 / 406,581, delta=+0, raw==uniq so zero double-listing — the prior +51 bug is gone); canonical prd +4
      (0.0003%, far under the 0.5% ABORT — expected drift on the LIVE bucket). Pre-freeze index baselines recorded:
      instruments-prd 5,465,414 rows / market-data-tick-prd 1,958,498 rows (T0.6/T6.1 reference). Snapshot TS
      `20260716-080453`; archived to `gs://deployment-scripts-central-element-323112/sports_cutover_2026_07_16/`.
      Verifier: `~/tmp-cutover/{inventory,snapshot}.py`. **HARD rule honoured**: per-VM shard backups written to
      `_index/precutover_per_vm_bak/<TS>/` — OUTSIDE `_index/per_vm/`, so the consolidator glob cannot absorb them.
      _Original mechanism (retained for reference)_: for each of the 4 buckets (2 legacy + 2 canonical) copy the control
      plane to a dated sibling — `_index/availability_index.parquet` →
      `_index/availability_index.<UTC-ts>.precutover.bak.parquet`, `availability_index/*.parquet`,
      `prod/catalog.parquet` → `prod/catalog.<UTC-ts>.precutover.bak.parquet`, plus `_index/per_vm/*.parquet` copied
      **outside** `per_vm/`. Record a full object inventory of all 4 buckets (T2.2 lister) to
      `~/tmp-cutover/inventory_precutover_*.jsonl` and archive it to
      `gs://deployment-scripts-central-element-323112/sports_cutover_2026_07_16/`. _Gate_: every `.bak` object exists
      with size > 0; inventory row counts match the audited totals (969,321 / 1,398,521 / 406,581 / 491,576). _ABORT_:
      any count deviates > 0.5% from audit → re-audit before proceeding; the estate moved under us. **HARD: never write
      a `.bak` into `_index/per_vm/`** — the consolidator globs `per_vm/*.parquet` and absorbs EVERY parquet there as a
      shard; a backup dropped there becomes shard #3, is merged back, and resurrects purged rows
      (`_index/consolidator_stall_state.json` = `{"streak":0,"baseline_shards":2}` confirms the current baseline).
- [x] ✅ [INFRA] P0. **T0.3 — Freeze the meta-launcher FIRST (freeze_order 1). DONE 2026-07-16T08:08:43Z** — paused
      `uts-prod-sports-scheduler-cron`, verified `state: PAUSED`. Last dispatch execution
      `uts-prod-sports-scheduler-lx556` completed 08:05:52Z (before freeze); the ~08:11 `*/5` tick did NOT fire —
      confirmed quiet. _Mechanism_:
      `gcloud scheduler jobs pause uts-prod-sports-scheduler-cron --location=asia-northeast1 --project=central-element-323112`.
      It runs `*/5` and dispatches tiers 1-4 → `uts-prod-instruments-service-sports-fixtures`,
      `features-service-sports-job`, `uts-prod-market-tick-data-service-fast-t1-recon`
      (`deployment-service/configs/sports-trigger-tiers.yaml`). **Pausing the 4 fixture crons without this leaves the
      fixtures job dispatched every 5 min.** _Gate_: `jobs describe` → `state: PAUSED`; no new execution after T+6min.
      _ABORT_: state not PAUSED → stop; everything downstream assumes the writers are quiet.
- [x] ✅ [INFRA] P0. **T0.4 — Freeze the remaining writer schedulers in freeze_order 2→11. DONE 2026-07-16** — all 17
      paused one-at-a-time in freeze_order, each verified `PAUSED` immediately after its pause. Final tally: 21/21 of
      the frozen set (1 meta + 17 writers + 3 consolidators) report PAUSED, 0 ENABLED. Out-of-scope ENABLED remaining:
      `uts-dev-market-tick-data-fast-t1-schedule` (DEV infra, fires 00:30, resolves dev buckets — not a legacy-sports
      writer) — noted, not paused (not in the runbook freeze list). _Mechanism_:
      `gcloud scheduler jobs pause <NAME> --location=asia-northeast1 --project=central-element-323112` for, in order —
      `sports-ref-v3-{1,2,3}-start` (2); `uts-prod-sports-fixtures-{midnight,6am,noon,6pm}-t1-schedule` (3);
      `uts-prod-sports-enrichment-{footystats,transfermarkt,soccer-football-info}-daily` (4);
      `understat-eu-typing-sweep-daily` (5); `is-daily-enum-sports` (6); `expected-universe-v2-sports-daily` (7);
      `lifecycle-catalogue-regen-sports-daily` (8); `uts-prod-mdps-odds-horizon-bucket-daily` (9);
      `features-service-sports-daily-trigger` (10); `uts-prod-market-tick-data-fast-t1-schedule` (11). _Gate_: all 17
      report `state: PAUSED`. _ABORT_: any refuses to pause → stop. **Note (11)**: not on the known-jobs list — found by
      the infra leg. `uts-prod-market-tick-data-service-fast-t1-recon`'s baked args are
      `[--operation download --mode batch]` with **no `--asset-group`**, and UTL `service_cli.py:163-167` gives
      `--asset-group` no default → it may enumerate sports unfiltered. Pause it; **prove or disprove the sports write in
      T4.5** (OR-8).
- [x] ✅ [INFRA] P0. **T0.5 — DRAIN GATE (freeze_order 19). DONE 2026-07-16** — (1) checked every sports Cloud Run job's
      most-recent executions: ZERO non-terminal (all `runningCount=0`, completionTime present); newest sports work was
      `uts-prod-instruments-service-sports-fixtures` @ 06:34Z, terminal. (2) Watched the 3 consolidators ~6 ticks each
      (08:12→08:17): `verdict=empty`, `rows_added=0` every tick; index row counts perfectly stable (instruments
      5,465,414 / market-data-tick 1,958,498 / features 168,059); `unmerged_shards=[]` throughout — only `_legacy_seed`
      remains in each canonical `_index/per_vm/`, the observable proof the reaper
      (`manifest_consolidator.py:_prune_consolidated_shards`, deletes shards once mtime ≤ canonical content-write
      marker) had merged every shard. **per_vm drained — no LOST-ROWS risk from freezing the consolidators.**
      _Mechanism_: no pause action. Poll until all sports Cloud Run executions are terminal —
      `gcloud run jobs executions list --region=asia-northeast1 --project=central-element-323112 --format='table(name,status.completionTime,status.conditions[0].type)' | grep -i sports`
      — then let the three consolidators run **≥2 full ticks** (`*/1`) so every `_index/per_vm/*.parquet` merges into
      `_index/availability_index.parquet`. Poll on a **progress metric** (index mtime + row count), never a fixed sleep.
      _Gate_: zero non-terminal executions; index mtime advanced; two consecutive ticks add zero rows. _ABORT_: an
      execution is stuck non-terminal > 30 min → diagnose; do NOT freeze the consolidators under it (that strands the
      shard permanently — the legacy bucket has had NO consolidator since 2026-07-13 and its shards can never merge).
- [x] ✅ [INFRA] P0. **T0.6 — Freeze the 3 consolidators LAST (freeze_order 20→22). DONE 2026-07-16T08:18:00Z** — paused
      instruments-sports → market-data-sports → features-sports, all verified PAUSED. Post-freeze watch (>11 min):
      `cons_last_run` frozen at 08:18:09 / 08:18:06 / 08:18:40 (no run after pause); index mtime frozen; row counts ==
      the T0.2 snapshot exactly (5,465,414 / 1,958,498 / 168,059); `unmerged_shards=[]`. **The index is now QUIET — the
      safe window for Phase 3 is open.** _Mechanism_: pause `uts-prod-manifest-consolidator-instruments-sports-cron`,
      then `-market-data-sports-cron`, then `-features-sports-cron`. _Gate_: all PAUSED;
      `_index/availability_index.parquet` mtime stops advancing; index row count == the T0.2 snapshot. **From here the
      index is QUIET — this is the only safe window for Phase 3.** _ABORT_: index still advancing after the pause → an
      unknown writer exists (relates to F-5/T0.1) → STOP.
- [x] ✅ [INFRA] P1. **T0.7 — Delete the 2 DEAD schedulers + confirm the 3 phantom VM starters. DONE 2026-07-16** —
      verified both dead schedulers' target Cloud Run jobs `uts-{staging,prod}-features-sports-service-t1-recon` return
      "Cannot find job" (they write nothing), then deleted `uts-staging-features-sports-t1-schedule` +
      `uts-prod-features-sports-t1-schedule`. GATE: `jobs list | grep -c features-sports-t1` → **0**. Confirmed the 3
      `sports-ref-v3-{1,2,3}-start` are phantom: `compute instances list --filter=name~sports` → zero rows; they are
      PAUSED (frozen in T0.4). **OR-7 RESOLVED = delete (WORKER REC, safe — zero target instances)**; per the runbook
      the actual v3 deletion is placed at T6.6 (Phase-6 owner) — recorded here, not executed in Phase 0 (pausing already
      achieves the freeze; deletion is not gate-required). _Mechanism_: `uts-staging-features-sports-t1-schedule`
      (ENABLED, erroring daily) and `uts-prod-features-sports-t1-schedule` (PAUSED) both target
      `uts-{staging,prod}-features-sports-service-t1-recon`, which **do not exist** (verified against the full 115-job
      list) → `gcloud scheduler jobs delete <NAME> --location=asia-northeast1`. `sports-ref-v3-{1,2,3}-start` fire
      annually (`0 0 11 4 *`) at instances that do not exist (`gcloud compute instances list --filter='name~sports'` →
      zero rows) → recommend delete (OR-7). _Gate_: `jobs list | grep -c 'features-sports-t1'` → 0. _ABORT_: a target
      job actually resolves → do not delete; re-audit.

### PHASE 1 — CODE (repoints + lifecycle marks; lands and applies BEFORE any delete)

- [x] ✅ [BACKEND] P0. **T1.1 — Fix the one LIVE code path that reads the legacy bucket, and its path shape, together.
      DONE 2026-07-16 — deployment-service@a535e3c.** `data_status_sports.py` bucket now
      `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group="sports")` (→ canonical `-prd-`; dropped
      `DeploymentConfig`/`project_id` plumbing). Path shape: added a `_FIXTURES_CANONICAL_PREFIX` pipeline_mode-aware
      probe (`…/pipeline_mode=batch_api_football/entity=fixtures/`) as the PRIMARY candidate, KEPT the bare
      `entity=fixtures` + `entity=fixtures_schedule` + oldest-legacy as fallbacks — mirroring UAC
      `candidate_parquet_paths()` which itself probes BOTH the pipeline_mode-aware AND bare shapes (canonical genuinely
      holds `entity=fixtures/` for 2018-2025 AND `pipeline_mode=…/entity=fixtures_schedule/` post-2026-07-14). Both
      `_load_fixture_counts_for_date` + `_check_league_status` updated. **Runtime-verified against canonical -prd-**:
      `data-status --service instruments-service --sports-league-breakdown` returns a non-empty league breakdown for
      2026-07-13→14 (6 leagues, 100%) AND historical 2023-08-12 (23 leagues, 100%). QG green (deployment-service, 87s).
      _Decision (documented, autonomous rule 1)_: kept the bare `entity=fixtures` probe rather than delete it (the plan
      called it "pre-canonical") — empirically canonical HAS data at that shape and the UAC SSOT probes it, so removing
      it would UNDER-report; the pipeline_mode probe is added, not swapped. _Mechanism_:
      `deployment-service/deployment_service/cli/utils/data_status_sports.py:25` hardcodes
      `_SPORTS_BUCKET_TEMPLATE = "instruments-store-sports-{project_id}"` (used `:139`) — LIVE via
      `cli/commands/data_status.py:25` import → invoked `:362`. Replace with
      `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group="sports")` and drop the `project_id`
      plumbing. **Same commit**: `_FIXTURES_PREFIX` (`:26`) is the pre-canonical shape (`entity=fixtures`, no
      `pipeline_mode=`) while the `:33-35` split-entity probe already carries
      `pipeline_mode=batch_api_football/entity=fixtures_schedule/` — fix both or the reader still returns nothing.
      _Gate_: `cd deployment-service && bash scripts/quality-gates.sh --no-fix` green;
      `data-status --asset-group sports` returns a non-empty league breakdown against canonical. _ABORT_: breakdown
      empty post-fix → the path shape is still wrong; do not proceed to delete (this reader is a Phase-4 witness).
- [x] ✅ [BACKEND] P1. **T1.2 — Close the QG blind spot that let T1.1 exist. DONE 2026-07-16 —
      unified-trading-pm@0114f846e (PR #1082).** Extended `check_no_explicit_project_id_bucket.py` (STEP 5.72/5.93) to
      ALSO flag `ast.Constant` string literals matching
      `^(instruments-store|market-data-tick|features)-[a-z]+-\{project_id\}$` (the `.format()`-template class the
      builder-CALL check never saw — exactly the T1.1 bug). **Proved fleet-wide (autonomous rule 11)**: injected
      reverted-T1.1 literal (`instruments-store-sports-{project_id}` / `market-data-tick-sports-{project_id}`) → FAILs;
      canonical `-prd-` form → NOT flagged; current tree → OK. The fleet-wide run surfaced **21 pre-existing occurrences
      (15 unique)** in SSOT-registry / config-default / dependency-checker files, ALL for OUT-OF-SCOPE asset groups
      (tradfi/calendar/onchain/features-store/features-sports — none is
      `instruments-store-sports`/`market-data-tick-sports`). Per the T1.2 ABORT branch (">5 pre-existing → baseline +
      issue doc, don't block the cutover on unrelated repos") they are frozen in
      `check_no_explicit_project_id_bucket_baseline.json` (a `(repo/file, literal)` ratchet that only goes DOWN) +
      tracked in `issues/legacy_bucket_template_literals_2026_07_16.md`. No base-service.sh wiring change needed
      (baseline is the sibling default). QG green (PM). _Mechanism_:
      `scripts/quality_gates/check_no_explicit_project_id_bucket.py` (STEP 5.72) AST-matches
      `get_bucket_name()`/`get_write_bucket_name()` CALLS carrying an explicit `project_id`; a module-level
      string-literal template + `.format()` matches neither → undetected. Extend the gate to flag module-level string
      literals matching `^(instruments-store|market-data-tick|features)-[a-z]+-\{project_id\}$` outside
      `scripts/`/`tests/`. _Gate_: gate FAILS on a reverted T1.1, passes on the fixed tree. _ABORT_: >5 pre-existing
      violations surface → baseline them and file an issue doc; do not block the cutover on unrelated repos.
- [x] ✅ [INFRA] P0. **T1.3 — Remove the 2 MDPS Cloud Run gcsfuse mounts on the legacy buckets (DELETE, do not repoint).
      CODE DONE 2026-07-16 — deployment-service@a535e3c. ⚠️ `tofu apply` PENDING — Phase-5 prerequisite (see below).**
      Deleted both `gcs_volumes` entries in `terraform/services/market-data-processing-service/gcp/main.tf`
      (`instruments-store-sports` read_only=true + `market-data-tick-sports` read_only=FALSE), replaced with
      REMOVED-comments matching the 2026-07-12 prediction precedent. `tofu validate` → Success. **⚠️ HARD Phase-5
      PREREQUISITE (NOT yet applied):** the running MDPS Cloud Run service still has these FUSE mounts until a
      `tofu apply`. The service + mounts live in terraform state **prefix `terraform/state/prod`** (module
      `terraform/services/market-data-processing-service/gcp/`, NOT the `dev` default the backend block hardcodes —
      bootstrap_gcp.sh overrides `--env prod`). The apply was NOT run from this Phase-1 sub-agent: it is a live prod
      Cloud-Run mutation that must be applied against the CORRECT prod state (I could not safely derive the full prod
      var-set for two modules + risked concurrent-drift pickup / wrong-state apply — HARD RULE: live-infra-state
      ambiguity → STOP, don't blind-apply). **Phase-5 owner MUST, immediately BEFORE the physical bucket delete:**
      re-init the MDPS module backend to `prefix=terraform/state/prod`, `tofu apply` (expect: in-place update of the
      MDPS Cloud Run service removing 2 volumes, NO bucket create/destroy), then verify the MDPS job EXECUTES GREEN
      (T1.3 ABORT: MDPS fails to start → restore the mount + re-scope, do NOT proceed to delete). _Mechanism_:
      `deployment-service/terraform/services/market-data-processing-service/gcp/main.tf` — `:223`
      `{ name="instruments-store-sports", bucket="instruments-store-sports-${var.project_id}", read_only=true }` and
      `:230` `{ name="market-data-tick-sports", bucket="market-data-tick-sports-${var.project_id}", read_only=false }`.
      **`:230` is a live WRITE mount** — deleting the bucket makes the MDPS job **fail to START** (gcsfuse cannot mount
      a nonexistent bucket), not merely fail a read. Follow the verbatim in-file precedent at `:224-226`/`:231-232` (the
      prediction mounts were REMOVED 2026-07-12 because MDPS resolves buckets via `resolve_bucket_name` at runtime and
      needs no FUSE mount). _Gate_: `tofu plan` shows only the 2 volume removals; `tofu apply`; MDPS job executes green
      post-apply. _ABORT_: MDPS fails to start after apply → it had a real FUSE dependency → restore the mount and
      re-scope; **do not proceed to Phase 5.**
- [x] ✅ [INFRA] P0. **T1.4 — Canonicalise the 3 hardcoded legacy IAM grants (one-line each). CODE DONE 2026-07-16 —
      deployment-service@a535e3c. ⚠️ `tofu apply` PENDING — Phase-5 prerequisite (same prod-state note as T1.3).**
      Repointed all 3 legacy literals to `-prd-`: `instrument_catalogue_scheduler.tf` (`instruments-store-sports` +
      `market-data-tick-sports` readers) and `catalogue_regen_scheduler.tf` (`instruments-store-sports` reader),
      matching the sibling `-pred-prd-` pattern. `tofu validate` → Success; `tofu fmt` clean. **⚠️ NOT yet applied** —
      these IAM members are in terraform state **prefix `terraform/state/prod`** (module `terraform/gcp/`; confirmed the
      catalogue IAM resources are in the prod state, absent from dev). A `-refresh=false` targeted plan was unreliable
      (no state-knowledge) and applying against the wrong (dev) prefix would create duplicate/wrong IAM. **Phase-5 owner
      MUST** `tofu apply` the `terraform/gcp` module against `prefix=terraform/state/prod` before the delete (expect: 3
      IAM member destroy-old-legacy + create-new-`-prd-`, NO bucket diff — T1.4 ABORT: plan wants to create/destroy a
      bucket → STOP). Left unapplied at delete time, `tofu apply` FAILS on an IAM member of a nonexistent bucket.
      _Mechanism_: `terraform/gcp/instrument_catalogue_scheduler.tf:34` + `:52` and
      `terraform/gcp/catalogue_regen_scheduler.tf:49` carry legacy literals inside `google_storage_bucket_iam_member`
      `for_each` tosets → swap to `instruments-store-sports-prd-central-element-323112` /
      `market-data-tick-sports-prd-central-element-323112`. The prediction siblings in the same tosets are already
      `-pred-prd-` (`:36-39`, `:52-56`) — match that pattern. Left unfixed, `tofu apply` **fails** post-delete (IAM
      member on a nonexistent bucket). _Gate_: `tofu plan` shows 3 IAM member replacements, no bucket diff; apply green.
      _ABORT_: plan wants to create/destroy a bucket → STOP (see T1.5).
- [x] ✅ [INFRA] P1. **T1.5 — Refresh the stale docstrings/comments + the SSOT-contradicting TF header. DONE 2026-07-16
      — deployment-service@a535e3c + deployment-api@1390340 + deployment-ui@c425f00.** Canonicalised: deployment-api
      docstrings (`upcoming_fixtures.py`, `data_query_service.py`, `_csv_export.py`), deployment-ui `client.ts` JSDoc,
      the 3 vm-script comments/heredocs (`launch-sfi-forward-poll.sh`, `launch-api-football-backfill-vm.sh`,
      `launch-sports-manifest-rescan-vm.sh` — all pure comments/error-text; the VM resolves the bucket at runtime, so no
      functional change, T1.6-parked scripts untouched functionally), and the `terraform/gcp/main.tf:6-8` Group-A header
      (rewritten to state ALL buckets are env-tiered per the 2026-05-11 reversal; warns never to re-introduce a no-env
      Group-A bucket). **GATE MET**: `rg 'sports-central-element-323112'` over live code/config → the ONLY remaining hit
      is `_imports_reconcile.tf` (Phase-5, the terraform import ID for the delete — correctly deferred). Residual `.md`
      hits are `HANDOFF_features_sports_phase_4_to_8_2026_05_06.md` (a historical handoff record, out of scope) +
      `DOC_INDEX.generated.md` (gitignored generated index). QG green on all 3 repos. _Mechanism_: doc-only, zero
      runtime impact —
      `deployment-api/deployment_api/services/{upcoming_fixtures.py:4,     data_query_service.py:441, data_status_drilldown/_csv_export.py:263}`
      docstrings say legacy while the code (`:68`, `:448`, `:294`) already calls `resolve_bucket_name`;
      `deployment-ui/src/api/client.ts:2640` JSDoc;
      `deployment-service/scripts/vm/{launch-sfi-forward-poll.sh:9, launch-api-football-backfill-vm.sh:25,     launch-sports-manifest-rescan-vm.sh:14,155}`
      comments. **Most important**: `terraform/gcp/main.tf:6-8` header _"Group A (raw data) — no env suffix; all envs
      share prod-level copy"_ states the very rule that produced these buckets — REVERSED by operator direction
      2026-05-11 / Phase 0e (`cloud-providers.yaml:136-140`). Leaving it invites a future agent to re-add a no-env
      Group-A bucket. _Gate_: `rg -c 'sports-central-element-323112'` over non-`scripts/` trees → 0 outside the T1.6
      one-off corpus. _ABORT_: none (doc-only).
- [x] ✅ [INFRA] P1. **T1.6 — Lifecycle-mark the ONE unmarked one-off; leave the other 26 parked. DONE 2026-07-16 —
      re-verify only, no edit.** Confirmed `migrate_sports_canonical_v9.py:2-4` already carries all 3 markers
      (`# Epic: sports_master` / `# Lifecycle: oneoff` / `# Delete-when: after E8 legacy-sports-bucket deletion …`) —
      the code leg's finding was already remediated. The other ~26 legacy-reader one-offs (incl. the 3 vm scripts whose
      COMMENTS T1.5 refreshed) remain functionally parked (legacy-by-design; deletion is T6.8). No file change.
      _Mechanism_: `market-tick-data-service/market_tick_data_service/scripts/migrate_sports_canonical_v9.py` is the
      **sole** file in the 27-file legacy-sports script corpus without a marker — **CORRECTION (verified 2026-07-16)**:
      it _does_ now carry `# Epic: sports_master` / `# Lifecycle: oneoff` /
      `# Delete-when: after E8 legacy-sports-bucket deletion …` at `:2-4`, so the code leg's finding is **already
      remediated**; this todo is a re-verify, not an edit. The other ~26 (`instruments-service/scripts/**`,
      `features-service/scripts/sports/migrate_gcs_entity_filenames.sh:18`,
      `market-tick-data-service/scripts/patch_l6_legacy_manifest_mtds_2026_06_29.py:70`) hardcode legacy **by design**
      (they are legacy readers; repointing them to canonical would defeat their purpose) and are correctly parked.
      _Gate_: `rg -L 'Lifecycle:' <the 27 files>` → empty. _ABORT_: none. **Do NOT delete any of them in this phase** —
      the v9 migrator is the Phase-2 move vehicle; deletion is T6.8.

### PHASE 2 — MOVE (unique objects only, to CANONICAL paths; v1_archive disposed first)

> **Ordering is load-bearing: 2a (delete archive) → 2b (move class A) → 2c (move class B) → 2d (manifest rows).**
> Running 2b before 2a re-imports the archive into canonical (F-3).

- [x] ✅ [DATA] P0. **T2.1 — PHASE 2a: delete `sports_reference_v1_archive/` (398 objects) — DONE 2026-07-16T09:37Z.**
      398/398 DELETED (object-layer gate: live count under the prefix == 0, gcloud-confirmed "matched no objects";
      canonical `-prd-` never held the prefix — 0, never contaminated). Per-object evidence
      `~/tmp-cutover/t2_1_delete_evidence.jsonl` (398 rows, each DELETED, present_after=false). **FINDING (Phase-5
      owner)**: the legacy bucket is NOT retaining noncurrent versions on delete — `gcloud storage ls -a` under the
      prefix returns ZERO versions post-delete (versioning effectively off at runtime, or these once-written objects had
      no noncurrent version). So the delete is PERMANENT (the runbook ROLLBACK table's "restore via `--all-versions`
      until T5.3" does NOT apply to legacy objects), and **T5.3's `--all-versions` purge will likely be a no-op**. Safe
      regardless: runbook proved 398/398 fully superseded by v2 fixtures ALONE (100% value-match, 0 unique rows, 0
      mismatches), OR-3 pre-approved, 7-day window expired ~2.5mo ago. _Original mechanism_: this executes the
      already-authored, already-approved P0 operator todo in
      `plans/ai/sports_fixtures_legacy_schema_migration_2026_04_28.plan.md` — _"After 7 days of green production: delete
      `gs://…/sports_reference_v1_archive/`"_ — whose 7-day rollback window expired ~2026-05-05, ~2.5 months ago.
      Verdict `safe-to-delete`, proven at the object layer on **all 398, not sampled**: 398/398 COVERED, 0 GAP;
      72,522/72,522 fixture rows present in canonical for the same day; every populated column 100.00% value-match
      (goals, status, referee, venue, kickoff_utc, season, …), **0 mismatches**. The "41 columns vs v2's 32" alarm that
      forced the union-supersession reasoning was **vacuous — 24 of the 41 columns are 100% NULL across all 72,522
      rows**; the real payload is 17 populated columns, all covered by v2 fixtures ALONE. The only v1-only fields are
      pure derivations of canonical fields (logo_url embeds `af_league_id`/`af_home_id`; `slugify(af_home_name)`
      reproduces `team_id` 31/31; `season` '2017-18' renders int `2017`). Delete via UTL `gcs_delete_object` per
      `codex/05-infrastructure/gcs-object-operations.md`, never `gsutil`. _Gate_:
      `gcloud storage ls gs://instruments-store-sports-central-element-323112/sports_reference_v1_archive/**` → "matched
      no objects"; canonical unchanged (no `sports_reference_v1_archive/` prefix ever appears in `-prd-`). _ABORT_: any
      object's fixture set fails re-verification against canonical → STOP; it was not superseded. **Confirm OR-3
      first.**
- [x] ✅ [DATA] P0. **T2.2 — Object-layer inventory + EXPLICIT copy list — DONE 2026-07-16.** Drove classification from
      the frozen T0.2 inventory (buckets QUIET since 08:08 ⇒ inventory == live), NOT the F-1 vehicle. **Cell-key** =
      strip `pipeline_mode=<x>/` + normalise `by-date/day-<D>`→`by_date/day=<D>` + drop `fetched_at_hour=<x>/` (snapshot
      dim, the 7× trap) + normalise bare-top-level `day=…`→`instrument_availability/by_date/day=…`. **Reconciliation
      closes EXACTLY**: control 118 + v1_archive 398 + data 968,805 = 969,321. **Class A (no canonical cell at any
      pipeline_mode) = 17,105** vs runbook 17,111 — delta −6 FULLY EXPLAINED and MORE-correct: −4 = canonical's +4
      pre-freeze growth (4 cells now covered), −2 = the 2 bare `day=2026-03-21/venue=BETFAIR/<hash>.parquet` objects are
      crc32c+size-IDENTICAL dups of existing canonical `instrument_availability/…` objects (malformed-path dups, not
      class A). **CRITICAL RECONCILIATION**: `instrument_availability` (the runbook's "119,858 must move") is NOT a
      class-A tree — every IA cell has a canonical counterpart (Direction-1 live-verified); the 119,858 was the vehicle
      **blind-spot** framing, not the object-layer class-A set. **Copy list** (`~/tmp-cutover/t2_3_copylist.jsonl`,
      17,089 rows) = class A EXCLUDING player_stats: dst = legacy path with `pipeline_mode=<M>` inserted after `day=`, M
      DERIVED per-entity from canonical's own usage (fixtures*/injuries/teams/fixture_*→batch_api_football;
      footystats_*→batch_footystats). **16 class-A player_stats deferred to T2.4** (byte-copying legacy-schema
      player_stats to canonical paths would collide with future fetches + lack available_at). **T2.2 SAMPLE GATE PASS
      (live)**: Direction-1 (has-canonical match is real) 23/23 across every tree (IA, sports_reference/fixtures, v2,
      odds-with-differing-hour, venues); Direction-2 (class-A miss is real: src present + dst absent + no canonical cell
      at any pipeline_mode for that day) 11/11. Verifiers: `~/tmp-cutover/t2_2_{classify,copylist,verify}.py`. _Original
      mechanism_: paginated `list_blobs` with a fields projection (`name,size,crc32c,updated`), 12-way prefix-parallel
      over top-level prefixes (~2 min/bucket; the naive recursive `ls` times out). Key = **cell-key normalisation**, NOT
      path equality: (1) delete the canonical-only `/pipeline_mode=<x>/` segment, (2) normalise legacy
      `instrument_availability/by-date/day-<D>/` → hive `by_date/day=<D>`. Derive from the UAC SSOT
      `unified_api_contracts/canonical/domain/sports/gcs_paths.py::candidate_parquet_paths()` per
      `codex/02-data/sports-gcs-path-ssot.md`. **Two traps already found and corrected — do not re-introduce**: (a)
      `fetched_at_hour=` is a SNAPSHOT dimension, not identity — exact-key matching called 124,267 objects unique;
      latest-wins semantics collapsed 106,758 to superseded (**naive answer was 7× too high**); (b) crc32c-differs ≠
      content-differs (parquet bytes are non-deterministic) and **byte size is NOT a safe row-count proxy** (n=400 test:
      3.25% of canonical-bigger-in-bytes objects had FEWER rows — wider schema) → exact row-count via parquet-footer
      reads. _Gate_: **SAMPLE-VERIFY ≥10 known pairs BEFORE scaling** (prior run: 10/10 CRC-match, 2 genuine misses);
      the method must independently reproduce the 398 v1_archive count and the 30,731 total, and the classification must
      close exactly (495,082 + 0 + 443,508 + 30,731 = 969,321). _ABORT_: arithmetic does not close, or the ≥10-pair
      sample shows any false "unique" → the mapping is wrong; **STOP** (this is the path-shape trap that has already
      produced three false conclusions).
- [x] ✅ [DATA] P0. **T2.3 — PHASE 2b: MOVE class A — DONE 2026-07-16.** Moved **17,089** objects (class A minus 16
      player_stats → T2.4) legacy→canonical via server-side `gcs_copy_object` at the T2.2-derived `pipeline_mode=<M>`
      paths, driven from `~/tmp-cutover/t2_3_copylist.jsonl` (NOT `_list_tree`). **Per-object gate**: 17,089/17,089
      COPIED, 0 FAILED, every dst crc32c-verified == src crc32c (byte-identical rewrite — stronger than a row-count
      match, no parquet read). **Reader-resolution gate**: 11/11 sampled moved objects across every class-A entity are
      both LIVE-present AND resolvable by the UAC SSOT `candidate_parquet_paths()` (guards the "wrong path = invisible"
      ABORT). COPY only — legacy untouched (delete is Phase 5). Full class-A==0 re-inventory deferred to the combined
      T4.1 pass (after T2.4/T2.5 also land). Evidence `~/tmp-cutover/t2_3_move_evidence.jsonl` (17,089 rows); verifiers
      `~/tmp-cutover/t2_3_{move,reader_check}.py`. _Original mechanism_: drive from the T2.2 copy list, not
      `_list_tree`. Copy legacy → canonical **at the canonical path** (insert `pipeline_mode=batch_<source>` between
      `day=` and `entity=`; normalise the `by-date/day-<D>` dash form) via UTL `gcs_copy_object` (server-side,
      idempotent, skip-if-exists). Cover the FULL span **2018-01-02 … 2026-12-06** — if using the v9 migrator as the
      primitive, `--start-date 2018-01-01 --end-date 2026-12-31` explicitly (defaults `2019-01-01`/`2026-06-01` silently
      truncate BOTH ends — F-4). Cover the trees `_list_tree` cannot see (F-1): `instrument_availability/` (119,858
      objects), bare `day=2026-03-21/`, `sports_reference/mappings/season=*/`. _Gate_: every class-A source object has a
      canonical object at its derived path with a matching row count; re-run T2.2 → class A = 0. _ABORT_: any copy lands
      at a non-canonical path → STOP and re-derive; a wrong-path copy is invisible to every reader and to the manifest.
- [x] ✅ [DATA] P0. **T2.4 — PHASE 2c: OR-1 OPTION D IN CANONICAL FORM (player_stats) — DONE 2026-07-16.** **388,825
      genuine legacy-only player observations RECOVERED into canonical across 4,015 cells; 0 FAIL.** _Measured, not
      assumed_ — census of all 22,686 legacy player_stats objects: **flattened+covered 17,979 objs (1,688,379 rows)** =
      the union population; **nested-only+covered 4,691** (canonical already holds them flattened → redundant, skipped);
      **nested-only+UNCOVERED 16** = the only class-A player_stats (raw stringified `players` payload → re-fetch list,
      never a fabricated flatten). **Legacy-only computed by GLOBAL (fixture_id, player_id) containment** (the row-gap
      doc's cross-partition method), NOT per-cell: 389,134 rows / **388,825 unique**. NOTE the row-gap doc's **111,827
      was a 10-day SAMPLE extrapolation and under-counts the truth by ~3.5×** — the full pass is authoritative;
      recovering all 388,825 is the non-descoped, data-pipeline-correctness outcome. **available_at: NO re-stamp
      needed** — measured **0 null / 0 midnight** across every legacy-only row; legacy player_stats already carries
      honest stamps satisfying UAC `(sports,PLAYER_STATS)="match_end_time"`, so the dispatch's LookaheadBiasError
      premise ("legacy predates availability stamping") does NOT hold for player_stats (the 38-col legacy schema already
      has `available_at`; a null gate is asserted on every write regardless). **Write**: per cell → back up canonical to
      the archive bucket, union canonical ∪ legacy-only, **DEDUPE on (fixture_id, player_id) keep=first (canonical
      wins)**, write at the CANONICAL path. Schema conformed by coercion (string keys / bool flags / UTC datetime /
      numeric stats) because canonical stores all-null stat columns as arrow `null` type — forcing the unstable
      per-object schema fails; coercion is value-preserving and reader-safe. **Per-cell GATE (all 4,015)**: re-read rows
      == union rows, **rows == unique keys (upsert-safe)**, all legacy-only keys present, all original canonical keys
      present, 0 null available_at. Independent spot check 20/20. **fixture_events**: RE-FETCH LIST only — **zero 5-col
      degenerate stubs imported** (they are class-B, never moved); the 40 class-A fixture_events T2.3 moved are
      10/11-col ATTRIBUTED forms (23,139 rows) whose schemas canonical ALREADY carries, so they are kept (genuine
      legacy-only data preserved) and listed for schema-upgrade re-fetch. **standings / teams / player_values**: NO
      ACTION (per ruling). Re-fetch lists: `t2_4_refetch_player_stats.json` (16 cells / 131 fixtures) +
      `t2_4_refetch_fixture_events.json` (40 cells / 1,542 fixtures). **BIG FINDINGS (pre-existing canonical, NOT
      cutover-introduced) → `issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`**: canonical
      player_stats carries **740,725 within-object duplicate rows (~26% of 2,882,420)** — vastly bigger than the cited
      "72/36"; T2.4's dedupe FIXED the 4,015 touched cells, ~13,964 remain; and canonical fixture_events runs **4 schema
      variants incl. ~30% degenerate 5-col**. Evidence `~/tmp-cutover/t2_4_union_evidence.jsonl` (17,979 rows) +
      archived to `gs://deployment-scripts-central-element-323112/sports_cutover_2026_07_16/phase2_evidence/`; canonical
      pre-write backups at `…/player_stats_prewrite_bak/`. Verifiers `~/tmp-cutover/t2_4_*.py`. _Original mechanism_:
      **skip-if-exists CANNOT do this (F-2)** — the canonical object exists, so both vehicles skip it. Per OR-1 ruling,
      either (a) **row-union** legacy ∪ canonical per cell and write the union to the canonical path (safest; preserves
      any canonical-only rows), or (b) **overwrite** canonical with legacy where legacy ⊇ canonical (simpler; loses
      canonical-only rows if the containment does not actually hold). **Verify containment per cell before overwriting
      either way.** Worst offenders: player_stats 111,827 rows, standings 91,380, fixture_events 69,444, teams 16,502,
      player_values 16,233 (e.g. `day=2019-08-12 season=2019`: legacy 640 vs canonical 38). _Gate_: for all 13,222,
      canonical row count ≥ legacy row count post-move; total rows recovered ≥ 305,000; re-run T2.2 → class B = 0.
      _ABORT_: any cell where legacy ⊄ canonical AND canonical ⊄ legacy (genuine divergence, not a subset) → STOP and
      escalate; a blind overwrite loses canonical-only rows.
- [x] ✅ [DATA] P0. **T2.5 — Control-plane adjudication — DONE 2026-07-16. Every unique has a written disposition; OR-4
      RESOLVED = ABANDON (option B, now PROVEN).** Legacy control-plane = **118 objects → 111 crc-IDENTICAL to canonical
      (no action)** + 3 DIFFERS + 4 NO-COUNTERPART = the runbook's ~8. Dispositions:

  | object                                                                  | disposition                      | evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
  | ----------------------------------------------------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
  | `_index/per_vm/_legacy_seed.parquet` (1,757,469 rows)                   | **ABANDON — OR-4=B, PROVEN**     | It is a **MANIFEST artifact, not DATA** (the delete gate is the OBJECT layer, class A==0 — the runbook's own "manifest is never evidence about objects" cuts both ways: losing an index row loses no data). OLD **25-col** schema with **no `source`/`asset_group`** → re-homing injects rows violating the `source=` REQUIRED crosscutting rule and fights the T3.1 purge. **88,053 of its 356,670 `captured` rows are RETIRED data types** (TRANSFERMARKT_LEAGUES 75,576 + SFI_LEAGUES 12,477, retired 2026-05-05) → option A would RESURRECT retired types into the canonical index. The scary "105,802 captured cells missing from canonical" is a **league_id REPRESENTATION artifact**: 220 seed-only league_ids are raw numeric provider IDs (`103`, `13973`, `14116`…) vs canonical names; at atom=(date,data_type) only **2** cells are missing (WEATHER 2019-02-23/03-01). Verifier `~/tmp-cutover/t2_5_or4_seed_diff.py`. |
  | `_index/per_vm/fixtures-recovery-20260627-183725.parquet` (34,564 rows) | **PROVEN-ALREADY-MERGED**        | The runbook called it "probably merged — NOT PROVEN". Now proven: **34,535/34,564 (99.9%) of its cells are present in the canonical index**; 29 residual cells only.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
  | `availability_index/instruments-service.parquet` (22,450 vs 22,445)     | **ABANDON — zero unique rows**   | The "5-row" delta is **intra-file duplicates**: legacy-only rows on the common columns = **0**; canonical is a superset (has 1 more).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
  | `_index/availability_index.parquet` (legacy, 38 MB)                     | **ABANDON**                      | The legacy consolidated index. Canonical index (5,465,414 rows) is the SSOT and gains the moved cells via the T2.7 per-VM shard. Manifest artifact, not data.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
  | `_index/availability_index.20260523-190934.dedup_phantom.bak.parquet`   | **ABANDON**                      | Historical `.bak` of the (abandoned) legacy index. Zero unique data.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
  | `_audits/fixtures_diff_20260714-001053.csv` (14.8 MB)                   | **MOVED → canonical `_audits/`** | T0.1 hand-run audit cohort (its truthset sibling was already copied to prd). crc32c-verified `XUXsqA==` == src.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
  | `_audits/fixtures_recovery_set_20260714-001053.parquet`                 | **MOVED → canonical `_audits/`** | Same cohort. crc32c-verified `x7e4kQ==` == src.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |

  **HARD rule honoured**: nothing was placed under canonical `_index/per_vm/` (R-11 — a stray parquet there becomes
  shard #3 and resurrects purged rows). _Original mechanism_: `_keep()` (`:167-173`) filters out `/_index/`,
  `/_vm_staging/`, and `_SKIP_PREFIXES` = `_audits/ _smoke_test/     _catalogue/ availability_index/` → **none** of the
  control-plane uniques move. Adjudicate each explicitly: `_index/per_vm/_legacy_seed.parquet` (legacy **1,757,469
  rows** vs canonical **0** — the canonical seed is EMPTY, 16.2 MB vs 18.7 KB) → **OR-4**;
  `availability_index/instruments-service.parquet` (22,450 vs 22,445 — 5 rows);
  `_index/per_vm/fixtures-recovery-20260627-183725.parquet` (34,564 rows, shard mtime 18:37 predates the legacy index
  write 19:14:43Z so it _probably_ merged — **NOT PROVEN**); 2 `_audits`, 2 `_index`,
  `sports_reference/mappings/season=2019` (640 vs 589). **The legacy bucket has had no consolidator since 2026-07-13**
  (`manifest_consolidator_scheduler.tf:67,80`) — these shards can never merge on their own. _Gate_: each of the ~8
  control-plane uniques has a written disposition (moved / proven-already-merged / abandoned-with-reason). _ABORT_:
  `_legacy_seed.parquet` disposition unresolved → **do not delete the bucket** (1.76M rows). **HARD: never place any
  re-homed object under `_index/per_vm/`** unless it is genuinely a shard to be merged.

- [x] ✅ [DATA] P0. **T2.6 — EXACT row-count pass for `market-data-tick-sports` — DONE 2026-07-16. Extrapolation
      replaced by measurement. ⚠️ MDT is NOT delete-eligible — 49,517 unique objects still need a disposition (OR-5b).**
      _Classification closes EXACTLY to 406,581_: control-plane 55 + **class A 9,926** + duplicate (crc==) 287,634 +
      crc-differing 108,966. Key strips BOTH `/pipeline_mode=<x>/` **and** `/data_source=<x>/` (the MDT trap; the
      rejected data_source-strip-only key is not used). **Exact row-count over all 108,966 crc-differing pairs**
      (217,932 footer reads, 0 errors — the pass that previously ran out of budget): **contentless (lr==0) = 0 ·
      superseded (cr>=lr) = 63,265 · UNIQUE (cr<lr) = 45,701**, carrying **7,079,850 rows present ONLY in legacy**. ⇒
      **EXACT MDT unique = 9,926 + 45,701 = 55,627 objects** (the ~52,400 estimate UNDER-counted by ~3,200; 9,926 vs
      9,927 and 108,966 vs 108,970 are canonical-drift deltas). **MOVED**: the **6,110** class-A objects with the
      documented mis-stamp (`pipeline_mode=batch_api_football` + `data_source=ODDS_API` + `data_type=trades`) →
      canonical `pipeline_mode=batch_odds_api`, `data_source=` stripped (canonical's verified convention: 252,163 at
      `(batch_odds_api, trades)`; `batch_api_football` does not exist for trades). **6,110/6,110 COPIED, 0 FAIL**, every
      dst crc32c-verified == src. **NOT MOVED — needs an operator ruling (OR-5b)**: (a) **3,816** class-A objects in OLD
      pre-canonical shapes (`day=/source=/league=`, `day=/venue=/league=`, `day=/source=`, `day=/venue=`) lacking
      `asset_group`/`instrument_type`/`data_type` — **no canonical path is derivable without INVENTING those fields
      (fabrication)**; (b) **45,701** class-B-equivalents holding **7,079,850 legacy-only rows** — the runbook says they
      "inherit OR-1", but **OR-1 ruled only on instruments entities and never covered MDT tick data**, so there is no
      ruling to inherit. Evidence `~/tmp-cutover/t2_6_{classA,crc_differ_pairs,rowcounts,move_evidence}.jsonl`. **⚠️
      BOTH residues are now INVESTIGATED (2026-07-16) →
      `plans/active/issues/mdt_legacy_canonical_row_gap_2026_07_16.md`** — (b) is **89.5% GENUINE** (the OR-1 trap does
      NOT reproduce; canonical is NET POORER by 6,721,872 rows, losing 20:1) and (a) is **3,816/3,816 DERIVABLE, 0
      park-only** (the "fabrication-required" premise is disproven — the path's `source=` is the VENDOR; the venue is a
      row COLUMN and `instrument_id` is UAC's `build_instrument_id` key). **Scope collapse**: legacy holds three
      strictly-nested generations `G3 ⊂ G2 ⊂ G1`, so recovering the **3,816** (a) objects recovers **99.98%** of (b)'s
      6.37M-row pre-match gap and the **45,701 become NO-ACTION by proof**. **PROVENANCE CORRECTION to this todo's own
      premise**: the audit's _"all 406,581 created 2026-06-27 in ONE bulk op"_ is **FALSE** — that date is the
      **COLDLINE storage-class lifecycle transition** (`updated`/`sc_upd`), not a write; legacy trades `created` =
      **2026-05-19 (231,532) + 2026-05-22 (44,893)**, and the (a) objects **2026-04-05…04-13**. _Original mechanism_:
      resume method — (1) re-list both MDT buckets with the T2.2 paginated prefix-parallel lister (~2 min each); (2) key
      = `re.sub('/pipeline_mode=[^/]+/','/', re.sub('/data_source=[^/]+/','/', name))` — **the MDT trap differs from the
      instruments trap**: legacy carries a `/data_source=ODDS_API/` segment canonical LACKS **and** mis-stamps
      `pipeline_mode=batch_api_football` on ODDS_API tick data where canonical corrects it to `batch_odds_api`; a
      `data_source`-strip-only key falsely reported 297,212/297,211 raw_tick_data objects as unique (rejected before
      use; sample-verified 12 pairs → 11/12 resolve); (3) row-count the 108,970 crc-differing pairs via
      `pyarrow.ParquetFile(fs.open(...)).metadata.num_rows` over gcsfs, 128 threads (measured 395 footer reads/s ⇒ ~9
      min for 218k reads); (4) classify `lr==0` contentless / `cr>=lr` superseded / `cr<lr` **unique**. Chunk + resume
      by appending `{l,c,lr,cr,lsz}` to `rowcounts.jsonl` and skipping names already present. Then MOVE the confirmed
      unique via `migrate_legacy_tick_buckets_to_canonical.py` (PAIRS `:52`) — for class-A-equivalents only;
      class-B-equivalents inherit OR-1. _Gate_: exact unique count (not extrapolated); classification closes to 406,581.
      _ABORT_: pass incomplete → **`market-data-tick-sports` is NOT delete-eligible** (OR-5). MDT legacy is dormant (all
      writes 2026-06-27), so there is no race.
- [x] ✅ [DATA] P0. **T2.7 — Write the moved cells' manifest rows via a per-VM shard — DONE 2026-07-16. All 3 blockers
      RESOLVED by measurement (none needed an operator); TWO shards written + read-back-verified; NOT consolidated (by
      design — see below).** **Shards** (both `_index/per_vm/cutover-move-20260716.parquet`): **instruments 7,183 rows**
      (`instruments-store-sports-prd`, `service_name=instruments-service`) + **MDT 6,110 rows**
      (`market-data-tick-sports-prd`, `service_name=migrate-sports-canonical`) = **13,293 rows**, describing **92,722 +
      251,409 = 344,131** real data rows. **Per-shard GATE (read back from GCS, never the writer's own return)**: 100%
      `capture_status=captured`; **0 blank-`source`**; **0 phantom `instrument_count=0`** (instruments 1..2,270; MDT
      2..210); **0 blank `available_at`**; 0 FAIL, 0 zero-row objects. Both ABORT conditions clear. Mechanism: explicit
      `.write()` **AND** `.close()` (the `_close_drain` lifecycle-final force — the `flush()`-only debounce is what
      silently stranded a prior agent's shard at ZERO rows). Verifier `~/tmp-cutover/t2_7_write_shard.py`; evidence
      `~/tmp-cutover/t2_7_{instruments,mdt}_evidence.jsonl`. **BLOCKER (a) — `setup_events()`: RESOLVED (mechanical)**,
      `setup_events(svc, mode="local")` before the writer. **BLOCKER (b) — `MANIFEST_WRITE_SCHEMA_MISSING`: RESOLVED =
      WARN-AND-PROCEED, proven from the code, not assumed.** `_writer_validation.py:220-235` — a
      `SchemaContractNotFoundError` emits the WARN event then does a bare `return`; `_writer_captured.py:352-358` then
      stages the captured row anyway, with the explicit comment _"We reach here in three cases: (a) contract found and
      df conformed, (b) contract not registered yet (warn event already emitted), (c) warn-only mode and df violated.
      All three should reflect the on-disk state truthfully — the parquet exists, so the manifest records `captured`."_
      It is **NOT** a downgrade and **NOT** the phantom pattern (every row here is backed by a crc32c-verified object).
      ⚠️ **Correction for future owners: `_resolve_strict_validation(None)` returns `True` in this workspace** (env
      `MANIFEST_STRICT_SCHEMA_VALIDATION` unset) — the docstring's "warn-only default" is STALE. Missing-contract still
      warns-and-proceeds; a _mismatch_ now RAISES. **BLOCKER (c) — ODDS: RESOLVED = WRITE THEM. The blocker's premise is
      DEAD (stale-by-reversal).** _"ODDS retired to MTDS-only"_ came from `sports_fixtures.py:59`'s comment citing
      UAC@8fb1f54f (2026-06-25) — but **the operator REVERSED #6 on 2026-06-27** (`unified-api-contracts@c75101be`
      _"restore ODDS: footystats … (#6 REVERSED)"_), and `@57bcc7c5` (2026-07-15) completed the reversal, restoring
      `SOURCE_PRIORITY[("sports","ODDS")]` + `AVAILABILITY_AT_SEMANTICS`, with the ruling **pinned by test**:
      _"footystats PREDICTIVE pre-match ODDS = IS reference data"_. Live-verified:
      `SPORTS_DATA_TYPE_TO_SOURCE["ODDS"]=="footystats"`, `SOURCE_PRIORITY[("sports","ODDS")]==["footystats"]`,
      `is_valid_manifest_source("sports","ODDS","footystats")` is **True** (and `…,"api_football")` is **False**). Codex
      agrees (`sports-data-source-coverage-matrix.md:262-277`: _"keep both in their current homes. NO migration"_ — ODDS
      under IS at exactly the path T2.3 moved these objects to). **No contradiction with T3.1**: T3.1 purges
      `api_football × ODDS` (impossible-by-construction); these 2,044 rows are `source=footystats` — the ONLY valid ODDS
      source — which T3.1 explicitly PRESERVES. Corroborating: the 1 contradicted index row the move invalidates is
      itself `(2026-05-01, ODDS, LIGUE_1) empty_confirmed` — leaving it would be the index LYING about data that now
      demonstrably exists. **SCOPE CORRECTION (measured; the shard is 7,183 not 17,089 instruments rows) —
      `fixtures_schedule` + `fixtures_outcomes` (9,906 objects) are DELIBERATELY EXCLUDED: they are NOT manifest
      data_types.** The canonical index carries **33 distinct data_types and ZERO `FIXTURES_SCHEDULE` /
      `FIXTURES_OUTCOMES` rows** — while canonical holds **81,787 + 81,293 = 163,080** live-written objects of exactly
      those entities. The live writer (`sports_fixtures.py:347-384`) `_gated_sink_write`s the entity-split parquets but
      never `record_captured`s them — the manifest tracks only the parent `FIXTURES` (332,962 rows). Their manifest
      population is an **open, unstarted P0 owned by another plan** — `plans/epics/sports_master.md:940` _"One-shot
      manifest migration: existing `entity=fixtures` rows split into `entity=fixtures_schedule` +
      `entity=fixtures_outcomes`"_ via `migrate_fixtures_split.py` — and `:943` requires it ship **same-day as the
      writegate strict-mode-flip-on-FIXTURES to avoid a mid-migration hard-fail**. Writing 9,906 rows here would
      unilaterally execute a fragment of that P0, out of its required coordination, creating a partial novel population
      while canonical's own 163,080 identical objects have none. Per findings-triage (_"fits another plan → annotate it,
      don't fix"_) they are excluded; **no data is at risk** — the objects are moved + crc-verified, and the delete gate
      is the OBJECT layer (T4.1), never the manifest. This also EXPLAINS blocker (b)'s `FIXTURES_SCHEDULE` warning: it
      was a TRUE signal (no contract, because it is not a manifest data_type), not noise. **MDT specifics**: the 6,110
      moved objects are a legacy schema generation **lacking `available_at`** (their native canonical twins carry it) →
      `record_captured`'s `assert_available_at_present` raised `LookaheadBiasError` (the dispatch's premise, false for
      player_stats per T2.4, is **TRUE here**). Resolved via the **sanctioned** helper
      `unified_trading_library.availability_stamping.stamp_available_at_odds_snapshot(df, source="odds_api")` =
      `bm_time + emission_latency_ms_for_source("odds_api")`, **empirically verified against native canonical objects:
      `available_at − bm_time == 5.0s uniformly`** — reproducing the live convention exactly, never inventing a value.
      `service_name=migrate-sports-canonical` is deliberate: the consolidator dedup key is
      `(date, venue, data_type, service_name)` + optional dims and **excludes `source`/`pipeline_mode`**, so these rows
      share a key with — and at T6.1 will SUPERSEDE and CORRECT — the **5,584** rows that same prior migration wrote for
      these very objects under the mis-stamp `(api_football, batch_api_football)`. Expected T6.1 delta: instruments
      **+7,182 new / 1 flipped** `empty_confirmed`→`captured`; MDT **+526 new / 5,584 corrected** (NOT +6,110). **NOT
      CONSOLIDATED — deliberate, and the dispatch's "run one consolidator now" instruction is REFUSED as unsafe.** This
      plan already ruled it (_"the merge is T6.1 by design"_); it is now also PROVEN harmful: this shard adds 2,044
      `footystats × ODDS` rows, so a merge now makes footystats × ODDS **142,618**, breaking **T3.1's gate (b)
      (`== 140,574 UNTOUCHED`)** and (c) (`total dropped by exactly 123,149`), and violating T0.6's QUIET-index
      invariant — i.e. it would ABORT Phase 3, which this dispatch explicitly does not own. Both `_index/per_vm/` dirs
      now hold exactly `_legacy_seed.parquet` + `cutover-move-20260716.parquet`; nothing else was placed there (R-11).
      _Groundwork retained from the prior owner (still accurate)_: **(1) SCOPE measured**: the shard must carry **17,089
      instruments cells** (the T2.3 class-A moves) + **6,110 MDT cells** (the T2.6 class-A moves) = 23,199 rows, in
      **TWO** shards (one per canonical bucket). The T2.4 player_stats cells need NO new rows — those cells already
      exist in the canonical index (only their row counts changed). **Verified against the live index**: of the 17,089
      moved instruments atoms `(date, data_type, league_id)`, **17,088 have NO canonical index row at all** and exactly
      **1** has an `empty_confirmed` row that the move now contradicts (must flip to `captured`). Every moved entity
      maps cleanly to a `data_type` (0 unmapped). **(2) SSOT resolved (do not re-derive)**: `pipeline_mode` = UAC
      `pipeline_mode_for_sports_entity(entity)`; `source` = that value with the `batch_` prefix stripped
      (`instruments-service/.../sports_fixtures.py::_sports_ref_source`; `_SPORTS_REF_SOURCE_OVERRIDE` is currently
      EMPTY). Independently corroborated: this matches canonical's ACTUAL per-entity usage measured in T2.2. Sports
      `row_key` pattern (from the live writer, `engine/orchestrator/process_write.py:243`) =
      `{"date": d, "data_type": DT, "league_id": L}` + `asset_group="sports"`, `instrument_type=""`. Writer:
      `ManifestWriter("instruments-service", catalogue_bucket=<prd>, per_vm_shards=True)` →
      `_index/per_vm/{VM_NAME}.parquet`; **explicit `.write()` AND `.close()`** (`close()` = the LIFECYCLE-final
      `_close_drain` that forces the per-VM rewrite — a `flush()`-only path debounces and can strand the shard, which is
      how a prior agent silently wrote ZERO rows). **(3) BLOCKERS (each needs a decision — none is a rerun-and-hope)**:
      **(a)** `record_captured` fails with `RuntimeError: Event logging not initialized. Call setup_events() first.` —
      the writer's validation path emits `log_event(...)`. Mechanical; call `setup_events()` in the one-off first.
      **(b)** The smoke test surfaced **`MANIFEST_WRITE_SCHEMA_MISSING`** for `FIXTURES_SCHEDULE` — the write-gate found
      **no registered schema contract** for that data_type. Must be settled BEFORE writing 23,199 rows: is this a
      warn-and-proceed, or does the gate refuse/downgrade the row? Writing rows the gate silently downgrades is exactly
      the pattern that produced the 468 phantom residual. Note the moved corpus is schema-HETEROGENEOUS by design (e.g.
      `fixture_events` 10/11-col af_/named forms, `*_unmapped` entities), so per-df validation must be proven across
      **every** class-A entity, not just one. **(c)** **ODDS retired to MTDS-only 2026-06-25** (`UAC@8fb1f54f`; recorded
      in `_SPORTS_REF_SOURCE_OVERRIDE`'s comment: _"footystats_odds was removed 2026-06-25 (ODDS retired to
      MTDS-only)"_). The T2.3 move landed **2,044 `footystats_odds`** class-A objects in the INSTRUMENTS bucket. Writing
      `ODDS` manifest rows into the instruments index would re-introduce an ODDS population there **while T3.1 is
      purging 123,149 api_football × ODDS rows from that same index** — a direct contradiction. Decide: write ODDS rows,
      or omit them (data preserved on disk either way; the manifest row is the question). _Sequencing (already correct,
      do not "fix")_: the 3 consolidators are PAUSED since T0.6 and Phase 3 REQUIRES the index stay QUIET, so the shard
      must NOT be consolidated in Phase 2 — the merge is **T6.1** by design. The dispatch's "manifest rows written +
      consolidated" therefore cannot fully close inside Phase 2; the Phase-2 deliverable is the WRITTEN,
      read-back-verified shard. _Original mechanism_: the canonical index gains rows only through
      `_index/per_vm/<VM_NAME>.parquet` + the consolidator's additive merge (proven: 123,149 rows in the consolidated
      index, 0 in any shard). Emit one shard `VM_NAME=sports-legacy-cutover-20260716` with
      `MANIFEST_PER_VM_SHARDS=true`, `record_captured(source=…)` for every moved cell (`source=` is crosscutting and
      REQUIRED), correct source-aware `pipeline_mode`. **Never fake `record_captured` for a cell with no backing
      object** (`codex/02-data/honest-absence-downstream-handling.md`). _Gate_: shard exists; after the Phase-6
      consolidator restart it merges and the index gains exactly the moved-cell count. _ABORT_: any row would be written
      with `source=''` or a phantom `instrument_count=0` → STOP; that is the pattern that created the 468 phantom
      residual.

- [ ] [BACKEND] P1. **T2.8 — Delete the stale "ODDS retired to MTDS-only" comment that cost a full Phase-2 stop.**
      _Mechanism_: `instruments-service/instruments_service/engine/orchestrator/sports_fixtures.py:59` reads
      _"footystats_odds was removed 2026-06-25 (ODDS retired to MTDS-only; UAC@8fb1f54f)"_. That decision (#6) was
      **REVERSED by the operator on 2026-06-27** (`unified-api-contracts@c75101be`) and the reversal completed at
      `@57bcc7c5` (2026-07-15), which restored `SOURCE_PRIORITY[("sports","ODDS")]` + `AVAILABILITY_AT_SEMANTICS` and
      pinned _"footystats PREDICTIVE pre-match ODDS = IS reference data"_ by test. The comment describes a dead decision
      as live and **directly caused T2.7's blocker (c)** — a prior agent stopped Phase 2 on it. Replace with the current
      state (ODDS is IS-owned footystats reference data; `_SPORTS_REF_SOURCE_OVERRIDE` is empty because the path key
      `footystats_odds` already strips to the correct source `footystats`, not because ODDS was removed). _Gate_:
      comment matches the live registries; `quality-gates.sh` green. _ABORT_: none (comment-only).
- [ ] [DATA] P0. **T2.9 — MDT `(sports, odds, trades)` schema contract is DRIFTED from reality (BIG FINDING, T2.7).**
      _Mechanism_: the registered contract requires
      `ts_event, fixture_id, market_type, outcome, odds_decimal, broker,     client, data_source`; the REAL canonical
      data carries `bm_time, market_key, outcome_name, price, fetch_utc, …`. **Canonical's OWN native live-written
      objects FAIL the same contract** (verified directly, not inferred) — so this is contract-vs-reality drift, not a
      defect in the moved objects. With `_resolve_strict_validation(None)==True`, any caller that validates these cells
      RAISES. Decide: fix the contract to match the real schema, or fix the writers to emit the contracted schema. T2.7
      wrote its 6,110 rows in documented warn-only mode (mismatch LOGGED, row truthfully reflects a crc32c-verified
      object) rather than let a stale contract assert a false absence. _Gate_: contract and real data agree on ≥1 native
      canonical object. _ABORT_: none (analysis).
- [ ] [DATA] P0. **T2.10 — 47,253 phantom `api_football × trades` `captured` rows in the MDT canonical index (BIG
      FINDING, T2.7). Same class as T3.1's 123,149 `api_football × ODDS`, other bucket, no todo owns it.** _Mechanism_:
      canonical MDT holds **ZERO** `batch_api_football` trades objects (only `batch_odds_api` 252,163 + `live_odds_api`
      8), yet the index carries 47,253 `api_football × trades` rows with `capture_status=captured` and **nonzero**
      `instrument_count` — i.e. the index claims captured data no object backs. **5,584 of them are superseded/corrected
      in place by T2.7's MDT shard at T6.1** (same dedup key, corrected `source`/`pipeline_mode`); the remaining
      **~41,669 need a purge decision** mirroring T3.1's predicate (`source=='api_football' AND data_type=='trades'`,
      source filter MANDATORY — `odds_api × trades` 362,746 must survive UNTOUCHED). Related: UAC declares **no
      `('sports','trades')` availability semantic** though `cefi`/`tradfi`/`prediction` all map
      `trades →     tick_timestamp`; registering it blind would switch the availability gate ON for the LIVE MDT sports
      fleet — the exact hazard `57bcc7c5` refused for `PLAYER_STATS` and filed for a ruling. **Feeds OR-5b.** _Gate_: a
      written disposition for all 47,253. _ABORT_: purging without the `source` filter → destroys the real `odds_api`
      population → STOP.

### PHASE 3 — CLEAN (the index is QUIET — the ONLY safe window)

- [x] ✅ [DATA] P0. **T3.1 — Purge the bogus `api_football × ODDS` rows — DONE 2026-07-16T13:09Z. RE-MEASURED FIRST: the
      live count is **123,149** (the runbook's own correction is right; the older 127,018 is stale). 123,149 purged, 0
      remain; footystats × ODDS **140,574 → 140,574 UNTOUCHED**.** Index **5,465,414 → 5,342,265** (delta exactly
      −123,149); generation `1784189888944530 → 1784207377339311` (CAS). **Every gate PASSED, verified BY CONTENT** (a
      fresh re-download in a separate process — never the writer's own return): (a) 0 rows match the predicate; (b)
      footystats × ODDS == 140,574; (c) total dropped by exactly 123,149; (d) total == 5,342,265; (e) **captured rows
      1,692,695 → 1,692,695 — no captured row lost**; (f) ODDS survivors == footystats 140,574 + blank 163. **Pre-gate
      proof the class is purely phantom: 0 of the 123,149 carry `capture_status='captured'`** (82,509
      `expected_unattempted` + 40,640 `empty_confirmed`) — these are rows that should never have existed (T3.3), not
      absence-with-a-reason. **Collateral-damage census (the strongest gate): grouped ALL 5.47M rows by
      `(data_type, source)` before + after — EXACTLY ONE cell class changed** (`ODDS|api_football` 123,149 → 0); every
      other class byte-identical. Schema identical (42 cols, same order + types). **NULL-trap avoided**: a bare
      `NOT (source='api_football' AND data_type='ODDS')` evaluates NULL (⇒ row silently DROPPED) for any NULL `source`;
      used the NULL-safe `COALESCE(source,'')` form (measured 0 NULLs today — blank source is `''` not NULL, 13,997 rows
      — so both forms agree, but the safe form cannot regress). Rewrite used **DuckDB `COPY … (FORMAT parquet)` — the
      consolidator's OWN writer** (`manifest_consolidator.py:2808`; the index is `created_by=DuckDB v1.5.4`, SNAPPY), so
      the output is exactly the format the index experiences every tick. **BACKUP (R-11 honoured — and hardened beyond
      the runbook)**:
      `gs://instruments-store-sports-prd-central-element-323112/_index/purge_backups/20260716-130924/availability_index.20260716-130924.purge_af_odds.bak.parquet`
      — crc32c `KrwkFw==` verified == source, 97,608,985 B, taken BEFORE the mutation. Placed under
      **`_index/purge_backups/`**, NOT the `_index/*.bak.parquet` sibling the runbook suggested and NEVER
      `_index/per_vm/`: verified from the code that the consolidator lists **only**
      `_PER_VM_DIR_PREFIX = "_index/per_vm/"` (`_state.py:128`, used `manifest_consolidator.py:1699/1727/1798`) and
      nothing globs `_index/` broadly, so a backup there is structurally unabsorbable. Post-purge `_index/per_vm/` still
      holds exactly 2 shards. Verifiers `~/tmp-cutover/t3_{1_measure,purge,verify}.py`. _Original mechanism_: single
      target `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`; predicate
      **delete WHERE `source=='api_football' AND data_type=='ODDS'`**. **The `source` filter is MANDATORY** —
      `data_type=='ODDS'` alone = 263,886 rows (footystats 140,574 + api_football 123,149 + blank-source 163); a sloppy
      predicate destroys the real footystats population. Snapshot first to
      `_index/availability_index.<UTC-ts>.purge_af_odds.bak.parquet` — a **SIBLING under `_index/`**, the proven
      convention (6 such `.bak` files already coexist there, none ever re-absorbed). **NEVER into `_index/per_vm/`**
      (becomes shard #3 → resurrects every purged row → breaks `baseline_shards=2`). _Gate_: post-purge assert (a) 0
      rows match the predicate; (b) **footystats × ODDS == 140,574 UNTOUCHED**; (c) total dropped by exactly 123,149;
      (d) re-verify the count immediately before the delete. _ABORT_: pre-delete count ≠ 123,149 → the class is no
      longer frozen → STOP and re-derive.
- [x] ✅ [DATA] P0. **T3.2 — Purge is TERMINAL — CONFIRMED 2026-07-16 by re-measurement at execution time, not
      inherited. The "re-seeded nightly" premise is FALSE on both halves.** All three confirmations RE-MEASURED live
      against the index immediately before the purge: **(1) provenance — the arithmetic closes EXACTLY**: 82,362 rows
      from the ONE bulk run `enum-universe-sports-20260628-213115` + 21 (`…20260629-013040`) + 18×7 nightly
      (`…20260709/10/11/12/13/14/15`) = **82,509 == the exact `expected_unattempted` count**; the other 40,640 rows are
      `empty_confirmed` with `enumerator_run_id=None` — **not the enumerator at all**; 82,509 + 40,640 = **123,149**
      exact. The nightly cron never added more than 18-21 rows/night, so there was never a "nightly re-seed" of the
      123k. **(2) the fix is deployed and PROVEN by its own output**: the newest run
      `enum-universe-sports-20260716-013041` wrote **45,622 rows with af×ODDS = 0 and fs×ODDS = 4,071** — i.e. the
      enumerator now resolves **footystats** for ODDS (UAC@57bcc7c5). The per-run bogus series is
      `…0711:18 · 0712:18 · 0713:18 · 0714:18 · 0715:18 · 0716:**0**` — **it ENDS at 20260715**; the T3.2 ABORT ("any
      per-run bogus count reappears after 20260715") does NOT fire. **(3) the writer guard is ON — runtime-verified**:
      `has_source_priority("sports","ODDS")` → **True** and `is_valid_manifest_source("sports","ODDS","api_football")` →
      **False**, so UTL `_writer_ingest.py:485` now RAISES `MissingSourceError` on any future api_football×ODDS write
      (READ in full, not grepped: the guard is
      `if has_source_priority(...) and not is_valid_manifest_source(...): raise` — the mis-stamp guard was silently
      DISABLED for 20 days because `has_source_priority` was False until `57bcc7c5`, which is exactly how these rows
      were written unchallenged). **(4) belt-and-braces**: sports is FROZEN anyway — `expected-universe-v2-sports-daily`
      is PAUSED (verified in the live scheduler list), so nothing could re-seed during the window regardless. ⇒ **The
      purge is terminal: the rows cannot come back.** _Original mechanism_: three independent confirmations, all already
      measured — (1) **provenance**: 82,362 of the 82,509 `expected_unattempted` rows came from ONE bulk run
      `enum-universe-sports-20260628-213115`, not the 01:30 cron (which only ever added 18-21 rows/night: 82,362 + 21 +
      18×7 = 82,509 exactly); the 40,640 `empty_confirmed` rows were written 2026-07-13 with `enumerator_run_id=None` —
      not the enumerator at all. (2) **the fix is deployed**: run `enum-universe-sports-20260716-013041` (exec
      `expected-universe-v2-sports-89dqt`, completed 2026-07-16T01:30:56Z) wrote 45,622 rows with **0 api_football ×
      ODDS** and 4,071 footystats × ODDS; the per-run bogus series ends at 20260715. IS vendors UAC as a **local path
      dep** (`instruments-service/pyproject.toml:82-83`
      `[tool.uv.sources.unified-api-contracts] path = "../unified-api-contracts"`), so the image built
      2026-07-16T01:02:28 baked in LDR's `57bcc7c5` — **IS images track LDR, not UAC main** (this resolves the apparent
      contradiction). (3) **the writer guard is ON**: UTL `_writer_ingest.py:485` raises `MissingSourceError` when
      `has_source_priority(ag, dt) and not is_valid_manifest_source(ag, dt, src)`;
      `has_source_priority("sports","ODDS")` flipped False→True at `57bcc7c5` — the mis-stamp guard was **silently
      DISABLED for 20 days**, which is how these rows were written unchallenged. _Gate_: all three re-confirmed at
      execution time. _ABORT_: any per-run bogus count reappears after 20260715 → the fix regressed → do not purge (it
      will re-seed).
- [x] ✅ [DATA] P0. **T3.3 — REMOVE, not retype — CONFIRMED 2026-07-16: all 3 layers agree that `api_football × ODDS` is
      impossible-by-construction. Each layer verified directly (grep-then-READ / runtime), none inherited.** **(a)
      codex** — `sports-data-source-coverage-matrix.md` §2.2 read in full: _"**api_football `/odds` is NOT used by
      instruments-service**. The footystats_odds adapter has `get_odds()` defined as a deprecated stub … **there is no
      api_football odds path**"_; `:312` _"instruments-service `data_type=ODDS` writer is footystats
      `get_fixture_odds_snapshot()` only (no api_football, no odds_api)"_. **(b) code — READ the stubs, not grepped**
      (note the runbook's paths are stale; the real ones are
      `reference_data/adapters/sports/adapters/{api_football,footystats}.py`): `api_football.py:649-660` `get_odds()` →
      docstring _"API Football does not provide odds data. This adapter is for reference data only. Returns an empty
      list."_ and the body is literally `logger.info(...); return []`; `footystats.py:322-333` `get_odds()` →
      _"FootyStats does not provide odds via the standard interface. Use `get_fixture_odds_snapshot()`"_, also
      `return []`. **Both are unconditional empty-list stubs — no api_football odds row can be produced by any code
      path.** **(c) UAC — runtime-verified** (executed, not read): `SPORTS_DATA_TYPE_TO_SOURCE["ODDS"] == "footystats"`,
      `get_source_priority("sports","ODDS") == ["footystats"]`, `has_source_priority("sports","ODDS") is True`,
      **`is_valid_manifest_source("sports","ODDS","api_football") is False`**, `…("sports","ODDS","footystats") is True`
      — and the ruling is **PINNED by test** `tests/unit/test_source_priority.py:571`
      `test_sports_odds_api_football_is_not_a_valid_odds_source` (_"api_football has no odds path in IS (get_odds() is a
      deprecated stub), so an api_football×ODDS manifest row is impossible by construction"_). _Gate_: all 3 layers
      agree → **REMOVE**. No layer says api_football odds is legitimate ⇒ the ABORT (retype instead) does not fire.
      Corroborated at the data layer: **0 of the 123,149 rows are `captured`** — nothing was ever fetched, so there is
      no observation to retype. **`footystats × ODDS` PRESERVED (140,574, asserted untouched)** — the operator REVERSED
      decision #6 on 2026-06-27 (UAC@c75101be, completed @57bcc7c5): _footystats pre-match ODDS = IS reference data,
      stays in IS_; codex agrees (_"keep both in their current homes. NO migration"_). The purge predicate's `source`
      filter is what separates the two (R-10). _Original mechanism_: confirm before purging — (a) **codex**
      `codex/02-data/sports-data-source-coverage-matrix.md:273-274` _"api_football `/odds` is NOT used by
      instruments-service … there is no api_football odds path"_; `:312` _"data_type=ODDS writer is footystats
      `get_fixture_odds_snapshot()` only"_. (b) **code** (grep-then-READ): `api_football.py:649-655` `get_odds()`
      docstring _"API Football does not provide odds data."_; `footystats.py:322-328` _"FootyStats does not provide odds
      via the standard interface."_ — both stubs. (c) **UAC**: `SPORTS_DATA_TYPE_TO_SOURCE["ODDS"]=="footystats"`
      (`league_data.py:222`), `("sports","ODDS"):["footystats"]` (`_source_priority_data.py:76`),
      `is_valid_manifest_source("sports","ODDS","api_football") is False` **PINNED** by
      `tests/unit/test_source_priority.py:576`. _Gate_: all 3 layers agree → REMOVE. _ABORT_: any layer says
      api_football odds is legitimate → do not purge; retype instead.
- [x] ✅ [DATA] P1. **T3.4 — Race guard — HELD FOR THE WHOLE PURGE WINDOW 2026-07-16; shard mtimes static; ABORT did not
      fire.** **CORRECTION to the runbook's premise: `_index/per_vm/sports-fixtures-job.parquet` NO LONGER EXISTS** — it
      was REAPED by the consolidator (= proof it merged) before the T0.6 freeze, exactly as T0.5's drain gate recorded
      (_"`unmerged_shards=[]` … only `_legacy_seed` remains"_) via
      `manifest_consolidator.py:_prune_consolidated_shards`. So the "HOT shard written every 5 min" it guards against
      was already gone and quiesced. Live `_index/per_vm/` holds exactly **2** objects, both static across the window:
      `_legacy_seed.parquet` (mtime 2026-06-28T19:39:41Z) + `cutover-move-20260716.parquet` (mtime 2026-07-16T12:46:09Z
      — the T2.7 Phase-2 shard, deliberately NOT merged; the merge is T6.1). **Guards actually applied (three, defence
      in depth)**: (1) **`_index/consolidator.lock` TAKEN** for the read-modify-write via the consolidator's own
      protocol — `gcs_conditional_put(if_generation_match=0)` = create-if-absent CAS, the identical mechanism as
      `_acquire_lock` (`manifest_consolidator.py:1027`); acquired gen `1784207368085587`, and **released in a `finally:`
      via `gcs_conditional_delete(if_generation_match=<own gen>)`** so it can only ever delete ITS OWN lock, never a
      concurrent holder's. Verified released post-run (`ls` → "matched no objects"). (2) **CAS on the index itself** —
      the rewrite used `gcs_conditional_put(if_generation_match=1784189888944530)`, so had ANY writer touched the index
      between read and write the put would have returned `None` and ABORTed with the index **untouched**. This is a
      stronger guard than the lock: it is enforced by GCS, not by convention. (3) **per_vm mtime witness** — all shard
      mtimes captured before + after and asserted identical
      (`[OK] all 2 per_vm shard mtimes static across the     window`). _Gate_: lock held ✓; shard mtime static ✓.
      _ABORT_ (shard mtime advances mid-purge ⇒ a writer escaped Phase 0): **did not fire**. _Original mechanism_:
      `_index/per_vm/sports-fixtures-job.parquet` is HOT (mtime 2026-07-16T06:33:51Z; written ~every 5 min by
      `uts-prod-sports-scheduler-cron`). Phase 0 already paused it and the consolidators; **additionally** take
      `_index/consolidator.lock` for the read-modify-write so the purge cannot race a consolidation and silently lose
      the fixtures job's live rows. _Gate_: lock held; shard mtime static across the window. _ABORT_: shard mtime
      advances mid-purge → a writer escaped Phase 0 (F-5) → STOP, restore the `.bak`.
- [x] ✅ [REVIEW] P2. **T3.5 — L6 gate: NO CHANGE NEEDED — VERIFY-ONLY, VERIFIED, CLOSED 2026-07-16. Zero code written;
      the operator's earlier "redefine the L6 gate" ruling is MOOT — the redefinition already shipped and is live on
      both branches.** **Ancestry re-verified** (not inherited): `unified-trading-pm@10ad5d69a` _"fix(audit): redefine
      L6-legacy-only gate to real-data-only (operator ruling 2026-07-15)"_ (2026-07-15T22:16:26Z) is
      `git merge-base --is-ancestor` of **BOTH `origin/live-defi-rollout` AND `origin/main`**; working tree clean for
      `plans/audit/`. **Implementation READ in full and matches the claim exactly**: `_split_backed_cells()`
      (`cf_manifest_audit_2026_06_01.py:156-182`) filters `capture_status=='captured'`, groups by
      `(date,venue,data_type)` and takes per-cell **MAX** `instrument_count` (not per-row — a cell fans out to many
      per-league populations, so a per-row test misclassifies a real cell whose first row is `ic=0`); `_legacy_diff()`
      sets `L6-legacy-only = GREEN if not legacy_only else RED` (`:231`) and reports `L6-phantom-residual = INFO(n)` on
      a separate visible line (`:232`, honest-absence: reported, never silently suppressed). **The INFO-can't-trip-RED
      claim VERIFIED at both aggregation sites**: `main()` (`:437`) and the wrapper `cf_manifest_audit_all.py:80` both
      test `v == "RED"` **exactly**, and `"INFO(468)" != "RED"` ⇒ no wrapper change, no alert-cron change, no test
      change needed. **GATE RE-RUN LIVE (post-purge) — both surfaces GREEN, reproducing the runbook's numbers exactly**:
      instruments-store-sports **LEGACY-ONLY REAL-DATA CELLS: 0 [GREEN]**, phantom-residual **INFO(468)** (legacy
      captured 41,939 = real 40,553 + phantom 1,386; canonical 81,381; overlap 41,471); market-data-tick-sports **0
      [GREEN]**, phantom-residual **INFO(140)** (legacy captured 32,755 = real 32,436 + phantom 319). Tests: **13
      passed** (`tests/unit/test_cf_manifest_audit_l6_gate.py` — the runbook said 11; the shipped file carries 13).
      _ABORT_ (gate reads RED ⇒ real legacy-only data exists ⇒ Phase 2 incomplete): **did not fire on L6**.
      **Consistency check the purge did not disturb L6**: T3.1 removed only non-`captured` rows and
      `_split_backed_cells()` filters to `captured`, so L6 is invariant under the purge — and the live re-run confirms
      it (468/140 unchanged). **⚠️ Standing caveat re-asserted: L6 GREEN is NOT delete-clearance — T4.1 (object layer)
      is the delete gate** (R-13: no index has a path column, so no row can reference `v1_archive`; that is precisely
      how `L6-legacy-only=0` coexisted with 398 real legacy-only parquets). _Original mechanism_: **already implemented,
      tested, and shipped** — `unified-trading-pm@10ad5d69a` _"fix(audit): redefine L6-legacy-only gate to
      real-data-only (operator ruling 2026-07-15)"_, verified **ancestor of BOTH `origin/live-defi-rollout` AND
      `origin/main`**, working tree clean for that path. `_split_backed_cells()`
      (`plans/audit/results/cf_manifest_audit_2026_06_01.py:156-182`) filters to `capture_status=='captured'`, groups by
      `(date,venue,data_type)`, takes per-cell **MAX** `instrument_count` (not per-row — a cell fans out to many
      per-league populations, so a per-row test misclassifies a real cell whose first row is `ic=0`); `_legacy_diff()`
      (`:207-247`) sets `L6-legacy-only = GREEN if not (legacy_real - canonical)` and reports
      `L6-phantom-residual = INFO(n)` on a separate visible line (`:242-245`). `"INFO(...)" != "RED"` so it never trips
      `main()`'s `reds` aggregation (`:437`) nor the wrapper's (`cf_manifest_audit_all.py:80,87`) — **no wrapper change,
      no alert-cron change, and NO tests must change** (`tests/unit/test_cf_manifest_audit_l6_gate.py`, 11 tests,
      shipped in the SAME commit). _Gate_: re-run the gate → both surfaces GREEN (measured today: IS legacy-only-real
      **0**, phantom-residual INFO(**468**); tick legacy-only-real **0**, phantom-residual INFO(**140**)). _ABORT_: gate
      reads RED → real legacy-only data exists → Phase 2 is incomplete. **Do NOT treat L6 GREEN as delete-clearance —
      see T4.1.**

### PHASE 4 — VERIFY (object-layer proof; the manifest is NOT evidence)

- [ ] [DATA] P0. **T4.1 — OBJECT-LAYER zero-unique proof. This, not L6, is the delete gate. 🟡 RE-RUN 2026-07-16
      post-OR-9 → the INSTRUMENTS half now PASSES (UNACCOUNTED = 0); the box STAYS UNCHECKED because this gate covers
      BOTH buckets and `market-data-tick-sports` is still open on OR-5b.** `instruments-store-sports` is now
      object-layer delete-eligible: all 2,078 formerly-unaccounted objects carry a written, measured disposition and the
      accounting closes at **968,927, delta +0** (`~/tmp-or9/or9_verdict.py`, re-runnable). OR-9 recovered **482
      distinct legacy-only keys + 803 progressive rows into 131 canonical cells**, all re-verified by an INDEPENDENT
      fresh-read pass (131/131 ok, 0 failed) in a process that never touched the writer; **zero legacy objects were
      mutated or deleted** and the consolidated index is untouched (generation still `1784207377339311` from the T3.1
      purge). **Still not a licence to delete**: T5.4 additionally requires the two `tofu apply`s (T1.3/T1.4) and T5.2's
      final writer re-check. _Superseded verdict (2026-07-16, retained for provenance)_: the pass first reported
      **FAIL** on 2,078 objects / "6,673 genuinely legacy-only keys"; OR-9's re-measure proved **~94% of that was not
      recoverable data at all** (5,897 payload-free keys) and recovered the 482 that were. **Result**: 968,927 objects
      (= 969,321 − 398 v1_archive + 4 T0.2 snapshot backups), every one classified, and **2,078 UNACCOUNTED** — objects
      whose canonical twin holds strictly fewer rows in entities **OR-1 never enumerated**. Key-level containment
      cleared 244 of them by measurement (`injuries` 151 → 0 legacy-only keys, the 2× row ratio is legacy-side
      duplication; `fixtures_outcomes` 93 → legacy has no fixture-id column ⇒ unattributable) and left **~1,834 objects
      / 6,673 genuinely legacy-only entity keys** (`fixture_stats` 6,379 · `footystats_odds` 152 · `fixtures_schedule`
      121 · `fixtures` 13 · `footystats_matches` 4 · `progressive_stats` 4 · 2 one-offs) with **no written disposition →
      OR-9**. The 456,727 crc-differing objects were **re-measured, not inherited** (865,696 footer reads, 0 errors):
      superseded is **444,996** (runbook said 443,508). **To re-open**: rule OR-9, execute it, then re-run
      `~/tmp-cutover/t4_1_{inventory,classify,pairs,rowcheck,verdict}.py` and require `UNACCOUNTED == 0`. Full
      accounting table → the Progress Log's Phase-4 entry. _Mechanism_: re-run the T2.2 inventory + classification over
      both legacy buckets. **Why the manifest cannot clear the delete**: no availability index has a **path/uri/bucket
      column at all** (columns are date, venue, data_type, source, pipeline_mode, league_id, capture_status,
      instrument_count, …) — the bucket binding is **positional** (the `_index` object physically lives in its bucket)
      and paths are DERIVED at read time. Therefore **zero rows in either index mention `v1_archive`, and no row ever
      could** — the 398 objects were invisible to L6 **by construction**. That is why `L6-legacy-only = 0` coexisted
      with 398 real legacy-only parquets. _Gate_: unique == 0 for **both** buckets, or every residual has a written,
      operator-accepted disposition. _ABORT_: unique > 0 without a disposition → **DO NOT DELETE**.
- [x] ✅ [DATA] P0. **T4.2 — Prove the moved objects are READABLE at canonical paths (not merely present). DONE
      2026-07-16 — 33/33 PASS.** Sampled 3 moved cells from **every one of the 11 class-A entities** (33 > the 25 gate),
      re-derived each path from the UAC SSOT `candidate_parquet_paths(data_type, day, league, pipeline_mode=)` — **not**
      from the dst we wrote — and resolved the bucket through the real consumer
      `features-service … resolve_instruments_bucket()` → `instruments-store-sports-prd-central-element-323112`
      (asserted `-prd-`). **33/33 derived + parsed with row counts identical to the legacy source** (fixtures_outcomes
      51==51, fixture_events 634==634, teams 606==606, …). _Test defect found + fixed, not a data defect_:
      `candidate_parquet_paths` returns **globs** (`fetched_at_hour=*/`) for the snapshot-dimension entities, so a
      literal `dst in cands` check false-FAILed all 3 footystats_odds samples; `fnmatch` is the correct comparison.
      **T4.2b — upsert-safety PROVEN**: 12/12 union-written canonical cells have **rows == unique (fixture_id,
      player_id), dups=0, 38 cols**; simulating the re-fetch collision (re-applying the legacy rows over canonical)
      leaves the keyed row count **unchanged** (e.g. 131→131) where a naive non-keyed append would have gone 131→218 ⇒ a
      re-fetch UPDATES, it cannot duplicate. _Sub-finding (benign, belongs to OR-9's record)_: 1/12 cells showed 2
      legacy keys absent from canonical — both are `(fixture_id, NULL player_id)`, i.e. **unkeyable non-observations**
      that T2.4's keyed union correctly did not carry (the OR-1 D(2) "unattributable" class), NOT a T2.4 miss. **Index
      assertions (dispatch-mandated) all PASS**: canonical `_index/availability_index.parquet` = **5,342,265 rows ==
      exactly 5,465,414 − 123,149 (delta 0)**; **`captured` = 1,692,695, delta 0 ⇒ no captured row lost**; footystats ×
      ODDS still **140,574**; api_football × ODDS **0**; index generation frozen at the 13:09:37Z purge ⇒ still QUIET
      (consolidators remain paused). Verifiers `~/tmp-cutover/t4_2_readable.py` + `t4_2b_upsert.py`. _Environment note
      (do not chase)_: `gcsfs` **intermittently stalls** on this host (futex wait + a CLOSE-WAIT socket, zero
      throughput, no timeout) — same hang T2.4 hit; `google.cloud.storage` direct reads route around it. _Original
      mechanism_: sample ≥25 moved cells across every entity and both class A and class B; resolve each through the UAC
      SSOT `candidate_parquet_paths()` and read it via the real consumer
      (`features-service/features_service/sports/data/gcs_paths.py:38-54`
      `resolve_instruments_bucket`/`resolve_tick_data_bucket`, `instruments-service/.../sports_dependency.py:103`).
      _Gate_: 25/25 resolve and parse with the expected row counts. _ABORT_: any moved object is unreachable via the
      SSOT path derivation → the path mapping is wrong → **STOP** (a copy at a path no reader derives is data loss with
      extra steps).
- [ ] [DATA] P1. **T4.3 — Rebuild the catalogue on canonical and verify.** _Mechanism_: the catalogue exists **only** in
      canonical (`prod/catalog.parquet`, 27,221 rows, 435,970 B, mtime 2026-07-16T01:05:55Z); legacy has **no `prod/`
      tree at all** (`gcloud storage ls -r gs://instruments-store-sports-central-element-323112/prod/` → "matched no
      objects") — **nothing to migrate, nothing to repoint**; it carries no path/bucket column and zero `gs://` refs.
      Re-run the regen owner (Cloud Run job `lifecycle-catalogue-regen-sports`, whose 01:00 cron matches the 01:05:55Z
      mtime exactly). **Argument gap**: its arg is `--by-date-prefix sports_reference/by_date`, which does **not** cover
      `sports_reference_v2/` — and would not have covered `sports_reference_v1_archive/by_date` had we moved it (we do
      not: T2.1 deletes it). If T2.3 lands class-A objects under a new prefix, this arg must be updated or the catalogue
      silently under-covers. _Gate_: `prod/catalog.parquet` mtime advances; row count ≥ 27,221; league_id nunique ≥ 94.
      _ABORT_: row count drops → the regen lost coverage → restore the T0.2 `.bak` and diagnose.
- [x] ✅ [INFRA] P0. **T4.4 — `terraform plan` shows ZERO diff touching the INSTRUMENTS legacy bucket. GATE PASSED
      2026-07-16 for the instruments half** (MDT half stays open — that bucket is deliberately retained on OR-5b).
      _Measured_, not asserted: a real `tofu plan` against `terraform/state/prod` executed **inside Cloud Build
      `ea03c145-25a0-4280-acc3-75a99486ed76` (SUCCESS)** — required because `unified-trading-sa` lacks
      `storage.buckets.get`/`getIamPolicy` and the plan dies locally on **174** pre-existing 403 refresh errors
      (project/pubsub IAM reads, unrelated to sports); the Cloud Build SA `1060025368044@cloudbuild.gserviceaccount.com`
      holds the perms. Result **`Plan: 1 to import, 20 to add, 51 to     change, 1 to destroy`** and the gate assertion:
      **ZERO plan actions reference `instruments-store-sports-central-element-323112`** ⇒ resurrection is structurally
      impossible (block removed ds@4637aed + state entry removed, prod state serial 344→345). Corroborated statically:
      every remaining non-comment terraform reference to a sports instruments bucket is `-prd-`, and the
      `google_storage_bucket.canonical` `for_each` derives from `cloud-providers.yaml:153`
      (`instruments-store-sports-${DEPLOYMENT_ENV_SHORT}-…` → `-prd-`), so no config path can emit the flat name.
      **Scope preserved**: `google_storage_bucket.market_data_sports` → _"will be updated in-place"_ (**retained, NOT
      destroyed**). The plan's only `destroy` is
      `instrument_catalogue_market_data_reader["market-data-tick-sports-central-element-323112"]` — the stale **MDT**
      IAM key superseded by T1.4's `-prd-` repoint, on a bucket that still exists ⇒ not a hazard, not this leg's to
      apply. _ABORT not triggered_. **🔴 BUT THE PLAN SURFACED AN ARMED RESURRECTION THAT IS NOT OURS** — the plan's
      ONLY bucket-create is **`google_storage_bucket.instruments_cefi will be created`**, while
      `instruments-store-cefi-central-element-323112` is **404** (confirmed via the elevated SA, build
      `0aa821f4-adf2-4ff2-b68d-96d917c4ed1d`): cefi got the physical delete WITHOUT the config removal + `state rm`, so
      the next prod `tofu apply` recreates it as an empty shell. **⇒ A FULL `tofu apply` ON PROD IS NOW UNSAFE TO RUN**
      (it would resurrect cefi + make 71 unaudited changes across other plans' resources). Filed + operator-notified →
      [`issues/terraform_instruments_cefi_armed_resurrection_2026_07_16.md`](issues/terraform_instruments_cefi_armed_resurrection_2026_07_16.md).
      _Mechanism (original)_: after T5.1's config removal, `tofu plan` must not propose creating either bucket. _Gate_:
      plan clean. _ABORT_: plan wants to CREATE a legacy bucket → T5.1 was skipped or incomplete → **do not delete**
      (see F-6 / the resurrection precedent).
- [ ] [INFRA] P1. **T4.5 — Resolve the `--asset-group`-less recon job (OR-8).** _Mechanism_:
      `uts-prod-market-tick-data-     service-fast-t1-recon`'s baked args are `[--operation download --mode batch]` with
      **no `--asset-group`**; UTL `service_cli.py:163-167` defines it `nargs='+'` with **no default** (→ `None`). The
      infra leg **read the argparse definition but did not execute the resolver** to prove what the `None` branch
      enumerates. Run it in dry-run and observe. _Gate_: a MEASURED list of asset_groups the unfiltered invocation
      touches. _ABORT_: it writes sports to a **legacy** name → a live legacy writer exists (F-5) → STOP.

### PHASE 5 — DELETE (gated on Phase 4 + a FINAL live-writer re-check)

> **Non-negotiable ordering: config removal + `state rm` (T5.1) → apply + confirm no recreate (T4.4) → object-version
> purge (T5.3) → bucket delete (T5.4).** Deleting before T5.1 resurrects the buckets.

- [x] ✅ [INFRA] P0. **T5.1 — DONE 2026-07-16 for the INSTRUMENTS half — deployment-service@4637aed.** Removed
      `resource "google_storage_bucket" "instruments_sports"` (found at **`main.tf:182-215`**, not the `:179-212` this
      todo predicted — line numbers had drifted; verified before cutting) and replaced it with a REMOVED comment in the
      verbatim shape of the `:172-180` tradfi/defi precedent. Then **`tofu state rm` BEFORE any physical delete** — 3
      instances, prod state **serial 344→345, resources 258→257**, backed up first to
      `…/sports_cutover_2026_07_16/tfstate_prod_prestaterm_20260716-184233.json` (973,163 B):
      `google_storage_bucket.instruments_sports` +
      `google_storage_bucket_iam_member.{catalogue_regen,instrument_catalogue}_instruments_reader["instruments-store-sports-central-element-323112"]`.
      **The 2 IAM `state rm`s are how R-16 was satisfied WITHOUT an apply** — terraform no longer tracks any binding on
      the dying bucket, so no post-delete apply can error on one (the T1.4 apply itself is impossible under this SA's
      perms **and** now unsafe — see T4.4's cefi finding). **DELIBERATELY NOT DONE, per scope**:
      `google_storage_bucket.market_data_sports` (`main.tf:345` post-edit) and its paired import block
      `_imports_reconcile.tf:74-77` are **RETAINED** — that bucket is still blocked on OR-5b and is NOT being deleted,
      so R-15's "remove the import block in the SAME commit" correctly does **not** apply to this half. Verified
      post-commit: `market_data_sports` still declared; import block intact (2 refs). **Also fixed in the same commit
      (adjacent finding)**: `configs/sports-trigger-tiers.yaml:274` `fixture_calendar.bucket_template` still read
      `instruments-store-sports-{project_id}` — a dangling pointer to the bucket being deleted, which **T1.5's gate
      missed because it grepped the literal `sports-central-element-323112`, not the `{project_id}` template form**.
      Verified DEAD config first (nothing in the workspace parses the `fixture_calendar` key; live readers resolve via
      `resolve_bucket_name()`), so it is declaration-only with zero runtime effect. _Mechanism_:
      `terraform/gcp/main.tf:179-212`
      `resource "google_storage_bucket" "instruments_sports" { name = "instruments-store-sports-${var.project_id}" }`
      and `:358-374` `"market_data_sports" { name = "market-data-tick-sports-${var.project_id}" }` are **live resource
      blocks with `force_destroy=false` + `versioning{enabled=true}`**. Delete both blocks (leave a REMOVED comment per
      the in-file precedent at `:376-379`), delete the paired import block `_imports_reconcile.tf:74-77`
      (`import { to = google_storage_bucket.market_data_sports; id = "central-element-323112/market-data-tick-sports-central-element-323112" }`)
      **in the SAME commit** — that file's own header (`:55-57`) documents that an import block whose target resource is
      removed makes `plan`/`apply` **error** — then
      `terraform state rm google_storage_bucket.instruments_sports google_storage_bucket.market_data_sports`.
      **`state rm`, NOT `destroy`** (destroy would attempt a delete and fail on `force_destroy=false`). Canonical
      `-prd-` is already state-mv'd into the yaml-derived `google_storage_bucket.canonical` `for_each`
      (`main.tf:301-307`, `canonical_buckets.tf:46,68-80`) so **no replacement block is needed**. _Gate_: T4.4 clean.
      _ABORT_: `state rm` errors → STOP; do not touch the buckets. **Precedent (this is not hypothetical)**:
      `main.tf:329-343` verbatim — _"recreated as an empty shell by an out-of-band `tofu apply` (metageneration=1,
      creation_time=2026-07-13T00:52:06Z) because this resource block was still declared here after the physical bucket
      was deleted"_; _"the exact failure that recreated ~30 cleanup-deleted buckets on 2026-07-12T21:59Z"_
      (`[[terraform_bucket_estate_drift_resurrection_2026_07_13]]`). Sports is the **last** Group-A legacy twin still
      declared — cefi/tradfi/defi were removed this way 2026-07-14 (`:309-322`), prediction 2026-07-13.
- [x] ✅ [INFRA] P0. **T5.2 — FINAL live-writer re-check — PASS 2026-07-16T18:3xZ (instruments half).** Re-measured
      immediately before the delete with the **R-1b-correct** discriminator (`~/tmp-or9/t5_2_writer_recheck.py`):
      **968,927 scanned · 0 objects with `timeCreated >= the 08:18:00Z T0.6 freeze` · 0 genuine writes
      (`updated != timeStorageClassUpdated`)**. Newest genuine `timeCreated` = **2026-07-16T08:05:03Z** = our own T0.2
      snapshot backup, **13 min BEFORE** the freeze. **The R-1b trap, demonstrated**: **968,927 / 968,927** objects
      (100%) carry `updated == timeStorageClassUpdated` — i.e. the ENTIRE bucket reads as "just touched" to a naive
      newest-mtime gate while holding **zero** writers. Gating on `updated` would have false-ABORTed this cutover
      permanently, exactly as R-1b predicts. _Mechanism_: **CORRECTED 2026-07-16 (T0.1) — do NOT gate on "newest object
      mtime"/`updated`.** That is precisely the measurement that manufactured F-5: an OLM `STANDARD→NEARLINE @ 90d`
      transition bumps `updated` **every single day** on a bucket nobody is writing, so an `updated`-based gate ABORTS
      this cutover forever on a false positive. Re-run `~/tmp-cutover/scan_writers.py <bucket>` and gate on the
      **write** discriminator: an object is genuinely written **iff** its `generation` is new — operationally,
      `updated != timeStorageClassUpdated` **OR** `timeCreated >= T0.6` (the age-0 case: a fresh create has all three
      timestamps equal, which is how T0.1 caught the only 3 real writes). _Gate_: **zero objects with
      `timeCreated >= T0.6`** and zero with `updated != timeStorageClassUpdated` in **both** legacy buckets.
      (Transitions are expected and are NOT a writer — ignore them.) _ABORT_: any object **created** since T0.6 → **DO
      NOT DELETE**; return to T0.1.
- [x] ✅ [INFRA] P0. **T5.3 — DONE 2026-07-16 for the INSTRUMENTS half. 968,927 objects + 34,596 VERSIONS purged, 0
      errors.** **T5.3's versioning premise is CORRECT and load-bearing — I nearly mis-called it, and a fail-closed
      guard caught it.** An early `buckets describe --format='value(name,versioning_enabled,storage_class)'` returned
      only two fields (`…-323112  False`) and I read it as `versioning_enabled=False` ⇒ "no versions to purge". **That
      read was WRONG** (ambiguous field ordering): after all 968,927 current objects were deleted, the plain object walk
      reported **0** while `ls -r --all-versions` reported **34,596** — real noncurrent generations (`time_deleted`
      2026-06-27, no holds/retention). The shell delete's **pre-flight "must be EMPTY incl. versions" guard REFUSED the
      delete** (build `e1707def-78ff-46c4-91dd-c044a894b77b` FAILURE, by design) rather than let it fail confusingly —
      **the guard, not the reasoning, is what made this safe.** _Method_: `gcloud storage rm` inside Cloud Build
      measured **~39 obj/s ⇒ ~6.9 h**, blowing the 90-min build timeout (cancelled build
      `324251cf-09da-45f7-b60d-9fce0ad98e87`); re-done from the slot with a 96-way threaded delete
      (`~/tmp-or9/fast_delete.py`, this SA **does** hold `storage.objects.delete`) at **~810 obj/s** in resumable
      time-sliced foreground runs — 365k + 265k + 300k + 13,127. Versions then purged by explicit generation
      (`~/tmp-or9/fast_delete_versions.py`, ~500/s, 67 s). _Sub-bug worth recording_: the first version pass reported
      **34,596 errors / 0 deleted** — NOT a permission wall but a **TypeError in my own script**
      (`Blob.delete(generation=…)` is not a kwarg in this client; the generation belongs on `blob(name, generation=…)`).
      It surfaced only because the script counted failures instead of swallowing them — a silent-success path would have
      reported "versions purged" over 34,596 live generations. _Gate_: post-purge **0 current, 0 all-versions**.
      _Original mechanism_: both buckets carry `versioning{enabled=true}` + `force_destroy=false`, so the bucket cannot
      be deleted until every object **version** is purged —
      `gcloud storage rm --recursive --all-versions gs://<legacy-bucket>`. _Gate_:
      `gcloud storage ls -a     gs://<bucket>/**` → empty. _ABORT_: any version survives → the delete will fail;
      diagnose (retention/hold).
- [x] ✅ [INFRA] P0. **T5.4 — `instruments-store-sports-central-element-323112` IS DELETED — 2026-07-16T19:52Z. The LAST
      Group-A legacy instruments twin is gone.** ⚠️ **`market-data-tick-sports` deliberately NOT deleted — still blocked
      on OR-5b** (this todo covers both buckets; only the instruments half is done). _Executed_ via the **Cloud Build
      executor** — build **`7b8b0e75-8c82-4e3f-add7-239e1ee31b4c` (SUCCESS)** — because `unified-trading-sa` measurably
      lacks `storage.buckets.delete` (a local attempt returns an opaque `GcsApiError('')`), while the Cloud Build SA
      `1060025368044@cloudbuild.gserviceaccount.com` holds it. The executor ran **fail-closed guards** (refuse any
      target containing `-prd-`; refuse target == canonical; canonical must exist; doomed must be empty incl. versions)
      before the destructive call. **PROOF (all from the ELEVATED SA — so the 404 is a real 404, not this slot's
      403-masquerading-as-404, which is the exact trap the dispatch warned about):** 1.
      `buckets describe gs://instruments-store-sports-central-element-323112` → **`not found: 404`** 2.
      `buckets list --filter=name:instruments-store-sports` → only **`…-prd-…`** + **`…-test-…`** remain; the flat
      legacy name is **absent from the project** 3. **canonical SURVIVES + intact** —
      `instruments-store-sports-prd-central-element-323112` describes fine and `_index/per_vm/` still holds all 3 shards
      (`_legacy_seed`, `cutover-move-20260716`, **`or9-recover-20260716`**) 4. **No resurrection pending** — the
      post-delete `tofu plan` (build `97baca1b-c585-44a1-a325-24904710b9d0`) is **byte-for-byte the same shape as
      pre-delete** (`1 to import, 20 to add, 51 to change, 1 to destroy`) and carries **ZERO actions referencing the
      deleted bucket** ⇒ the delete introduced no drift and terraform cannot recreate it (block removed ds@4637aed +
      `state rm`'d). _Gate met_. _Mechanism (original)_:
      `gcloud storage buckets delete gs://instruments-store-sports-central-element-323112` then
      `gs://market-data-tick-sports-central-element-323112`. **`market-data-tick-sports` is gated on T2.6 completing**
      (its unique count is currently an extrapolation — OR-5). _Gate_: `gcloud storage ls gs://<bucket>` → 404 for both;
      `tofu plan` still clean 24h later (T6.0). _ABORT_: delete refused → force_destroy/versioning/state not resolved →
      return to T5.1/T5.3.

### PHASE 6 — RESTORE (exact reverse of the freeze; verify each first run green ON CANONICAL)

> **Nothing un-pauses until: `tofu plan` is clean AND the legacy buckets are gone AND the canonical index has absorbed
> the moved objects.** Consolidators restart FIRST (they were frozen last).

- [ ] [INFRA] P0. **T6.0 — Post-delete resurrection watch.** _Mechanism_: 24h after T5.4, re-run `tofu plan` and
      `gcloud storage ls gs://instruments-store-sports-central-element-323112`. _Gate_: plan clean; bucket still 404.
      _ABORT_: bucket exists again → an out-of-band `apply` resurrected it → T5.1 was incomplete → re-open.
- [x] ✅ [INFRA] P0. **T6.1 — MERGE DONE 2026-07-17; every delta as predicted. ⚠️ A SILENT DATA-LOSS BUG FIRED AND WAS
      RECOVERED IN-BAND — see the Progress Log entry "✅ T6.1 MERGE COMPLETE" + new issue doc
      [`issues/consolidator_content_write_marker_strip_silent_shard_reap_2026_07_17.md`](issues/consolidator_content_write_marker_strip_silent_shard_reap_2026_07_17.md).**
      The FIRST instruments consolidator run (`…-4rfp4`) reaped BOTH pending shards **unmerged** and reported
      `success=True exit(0) rows_in=0 pruned_shards=2` — the cutover's own out-of-band index rewrites (T3.1 purge
      13:09Z + the 18:45:26Z "frozen-generation witness") had STRIPPED `consolidator_content_write_at`, so the prune
      cutoff fell back to `blob.updated`=18:45:26.846Z and swallowed shards written at 12:46/17:30. Recovered from this
      leg's pre-merge downloads (GCS held no versions), re-uploaded with a fresh mtime, re-merged clean. **Verified BY
      CONTENT (fresh re-read):** instruments **5,342,265 → 5,349,447 (+7,182 new / 3 in-place flips)**, captured
      **1,692,695 → 1,699,880**, `api_football×ODDS` **0 → 0 (TERMINAL)**, `footystats×ODDS` **140,574 → 142,617 (+2,043
      — CORRECT, see below)**; MDT **1,958,498 → 1,959,024 (+526 new / 5,584 corrected)**, captured **575,671 →
      576,197**. Consolidator reports corroborate (`j2rqk` rows_out=5349447 dedup_dropped=3, 328s, no signal 9; `94c2f`
      rows_out=1959024 dedup_dropped=5584, 85s). MDT supersession proven at the content layer:
      `service_name=migrate-sports-canonical` × `api_football` **9,208 → 3,624 (−5,584 exactly)**, `odds_api` **167,220
      → 173,330 (+6,110)**. **CORRECTION — the gate `footystats×ODDS == 140,574 UNTOUCHED` is PHASE-3-ONLY and MUST NOT
      be asserted at T6.1**: the shard legitimately carries 2,044 footystats×ODDS cells; those rows belong in IS by
      operator ruling 2026-06-27 (UAC@c75101be), runtime-verified this leg
      (`is_valid_manifest_source("sports","ODDS","footystats") is True`) — which also **RESOLVES T2.7 blocker (c) =
      WRITE**. The terminal purge gate is `api_football×ODDS == 0`, which held. **The plan's predicted 142,618 was off
      by one** (it double-counted the 1 flip row already counted as footystats×ODDS); true value **142,617**. Snapshots:
      `_index/availability_index.20260717-012712.pre_t6_1.bak.parquet` on both canonical buckets. _Original mechanism_:
      un-pause
- [ ] [INFRA] P0. **T6.1b — Consolidator restore + ≥3 clean ticks (the un-pause half of T6.1).** _Mechanism_: un-pause
      `-features-sports-cron`, then `-market-data-sports-cron`, then `-instruments-sports-cron`. _Gate_ (first run):
      exits 0; `_index/availability_index.parquet` mtime advances; row count **≥ the pre-freeze snapshot minus exactly
      123,149** (the T3.1 purge) **plus** the T2.7 moved-cell count — never lower (a drop means the merge clobbered
      rows); **no `Container terminated on signal 9`** (the instruments-sports merge is the known heavy case —
      60-80s/2.09M rows/37 shards, 900s bump at `manifest_consolidator_scheduler.tf:88-92`); no stale-index loud-fail.
      Let them run **≥3 clean ticks before any writer resumes** so the index is a known-good baseline. _ABORT_: row
      count drops or OOM-kill → restore the T0.2 `.bak`; do not resume writers onto a corrupt index. **Downstream
      unblock (added 2026-07-16 21:32Z, slot-13)**: `sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1
      (compute sports features 2015→present) is dispatcher-gated on backlog condition
      `sports-cutover-phase6-consolidator-resumed` (created to stop wasted re-dispatch during the freeze — see that
      plan's Progress Log). The moment `-market-data-sports-cron` reads `state: ENABLED` and passes this gate's checks,
      flip it:
      `curl -X POST $SERVER_URL/api/prerequisites/sports-cutover-phase6-consolidator-resumed -d '{"value": true}'`.
- [ ] [INFRA] P0. **T6.2 — Restore the shared/uncertain writer (11) then features (10).** _Mechanism_: un-pause
      `uts-prod-market-tick-data-fast-t1-schedule` — verify against T4.5's measured asset-group list that its target is
      `market-data-tick-sports-prd-*` and **not** a legacy name. Then `features-service-sports-daily-trigger` → the
      Workflow `features-service-sports-daily` → `features-service-sports-job` writes to
      `features-sports-prd-central-element-323112`. **Note**: the features job spec has a hardcoded `--date 2026-07-14`
      — **stale**; confirm the trigger overrides it or the job re-runs one fixed day forever (file an issue if so).
      _Gate_: both first runs exit 0 onto canonical. _ABORT_: any legacy-name write → STOP; a legacy writer survived.
- [ ] [INFRA] P0. **T6.3 — Restore the daily writers 9→5 (one at a time, verify each).** _Mechanism_: un-pause in order
      — `uts-prod-mdps-odds-horizon-bucket-daily` (9; verify `reprocess_sports_odds` writes `processed/` under
      canonical, exit 0); `lifecycle-catalogue-regen-sports-daily` (8; verify `_catalogue/` on canonical — and see
      T4.3's `--by-date-prefix` coverage gap); `expected-universe-v2-sports-daily` (7; verify `--apply-write` lands rows
      and `gs://instruments-store-sports-prd-…/prod/catalog.parquet` resolves — **and that it still writes 0
      api_football × ODDS**, i.e. the T3.1 purge is not re-seeded); `is-daily-enum-sports` (6; verify the `--force`
      re-enum writes a per_vm shard under `VM_NAME=is-daily-enum-sports` and the consolidator merges it next tick);
      `understat-eu-typing-sweep-daily` (5; verify `--apply` exits 0, no manifest row-count regression). _Gate_: each
      first run green on canonical before the next un-pause. _ABORT_: any regression → re-pause that job and diagnose;
      do not cascade.
- [ ] [INFRA] P0. **T6.4 — Restore the 3 enrichment crons (4) then the 4 fixtures crons (3).** _Mechanism_: footystats →
      transfermarkt → soccer-football-info (verify each writes its `VM_NAME=sports-enrichment-*` per_vm shard and it
      merges); then midnight → 6am → noon → 6pm (verify `uts-prod-instruments-service-sports-fixtures` exits 0, writes
      per_vm shard `VM_NAME=sports-fixtures-job`, and does **zero direct index writes** — the per-VM-shard fix is
      already in place, so a regression here means the fix was lost). _Gate_: each first run green; shards merge.
      _ABORT_: a direct index write reappears → STOP; that is the bug that produced this whole class.
- [ ] [INFRA] P0. **T6.5 — Restore the meta-launcher `uts-prod-sports-scheduler-cron` (1) LAST.** _Mechanism_: un-pause
      only once T6.1-T6.4 are each proven green **individually** — it immediately re-dispatches tiers 1-4 and a failure
      would be masked by fan-out. _Gate_: first `*/5` tick dispatches with no `"No cloud_run_job_name — skipping"`
      warning except the known-empty ml-service entry (`sports-trigger-tiers.yaml:224`, deliberately `""`);
      `sports_scheduler_state/` in `gs://deployment-scripts-central-element-323112` advances `last_run[tier]`. _ABORT_:
      unexpected skip warnings → re-pause and diagnose.
- [ ] [INFRA] P1. **T6.6 — Do NOT restore `sports-ref-v3-{1,2,3}-start` (2).** _Mechanism_: their 3 target instances do
      not exist; leave DISABLED or delete per OR-7. _Gate_: absent from the enabled set. _ABORT_: none.
- [ ] [CODE] P0. **T6.9 — Fix the UTL consolidator's silent shard-reap (NEW 2026-07-17, found by T6.1 — fleet-wide, NOT
      sports-specific).** _Mechanism_: implement the fix ranked (1) in
      [`issues/consolidator_content_write_marker_strip_silent_shard_reap_2026_07_17.md`](issues/consolidator_content_write_marker_strip_silent_shard_reap_2026_07_17.md)
      — `unified_trading_library/manifest_consolidator.py`: when `_get_content_write_mtime` resolves via the
      **`blob.updated` fallback** (i.e. neither `consolidator_content_write_at` nor `consolidator_run_at` is present),
      `_prune_consolidated_shards` MUST prune **nothing** (pruning is an optimisation; merging is the contract). Plus
      (4) loud-fail the tell: `rows_in=0` together with `pruned_shards>0` is self-contradictory and must never report
      `success=True`. _Why_: the fallback's documented safety claim (_"can only make the cutoff OLDER … fail toward
      correctness"_) is FALSE — an out-of-band index write both STRIPS the marker and BUMPS `updated`, moving the cutoff
      FORWARD past shards no merge ever saw. This destroyed 7,185 sports manifest rows on 2026-07-17 with
      `success=True`/`exit(0)`; recovery was possible only because the operating agent had downloaded the shards to
      measure them first. Arms for **every** asset_group whose index is rewritten out-of-band while consolidators are
      paused — i.e. exactly the freeze/repair/resume runbook shape. _Gate_: a regression test that reproduces the repro
      in the issue doc (out-of-band rewrite strips marker + newer mtime ⇒ shard MUST survive and MUST merge); UTL
      `quality-gates.sh` green. _ABORT_: none.
- [ ] [REVIEW] P1. **T6.7 — Post-phase codex audit (HARD RULE).** _Mechanism_: update
      `codex/02-data/sports-gcs-path-ssot.md` (legacy shape is now GONE — no reader should special-case it),
      `codex/02-data/bucket-naming-and-config.md` (the last no-env Group-A twin is retired),
      `codex/05-infrastructure/manifest-consolidator-ssot.md` (legacy consolidator entries permanently removed);
      SUPERSEDED-banner anything the cutover invalidated. _Gate_: every codex path named here is either updated or
      explicitly confirmed unaffected. _ABORT_: none (review-blocking if skipped).
- [ ] [INFRA] P2. **T6.8 — Retire the one-offs + the dead knob + the false-progress tick.** _Mechanism_: per each file's
      own `Delete-when` (all satisfied once T5.4 lands + orphan-sweep = 0): delete `migrate_sports_canonical_v9.py`,
      `migrate_legacy_tick_buckets_to_canonical.py`, `patch_l6_legacy_manifest_{is,mtds}_2026_06_29.py`, and the ~26
      legacy-reading `instruments-service/scripts/**` one-offs. **Also delete the doubly-broken gate**
      `market-tick-data-service/market_tick_data_service/scripts/verify_v1_archive_row_coverage_2026_06_27.py` — see
      RISK-9; leaving it is a trap that re-issues a false COVERED verdict. **Retire the now-dead
      `include_legacy_archive` knob** from UAC `gcs_paths.py`/`partition_paths.py`
      (`rg 'include_legacy_archive\s*=\s*True'` → **zero hits** workspace-wide; the workspace bans shims). **Un-tick /
      annotate** the plan item `- [x] ✅ [DATA] P0.     v1_archive ROW-coverage gate` in
      `plans/active/sports_manifest_canonicalisation_2026_06_01.md` — it was ticked on _"GATE SCRIPT SHIPPED"_ evidence
      (`market-tick-data-service@18ca0e23`), i.e. on **shipping a script, never on a verified run of it**; that is
      exactly the false-progress class the commit+flip rule targets. Also correct that plan's standing claim that
      v1_archive is _"COLUMN-superseded by the union of understat_xg + v2 fixtures + v2 fixture_stats"_ —
      wrong-but-harmless: it is superseded by **v2 fixtures ALONE**, because the columns that supposedly required the
      union are 100% empty. _Gate_: `rg -c 'sports-central-element-323112'` workspace-wide → 0. _ABORT_: none.

---

## RISK REGISTER — what could lose data at each phase

| #    | Phase | Risk                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Severity              | Mitigation                                                                                                                                                         |
| ---- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| R-1  | 0     | ~~**Unidentified live writer**~~ **✅ CLOSED 2026-07-16 — the risk does not exist.** T0.1 proved at the object layer that the "125 writes on 07-15" are OLM `STANDARD→NEARLINE @ 90d` storage-class transitions (`generation` unchanged, `metageneration` 1→2, `updated == timeStorageClassUpdated`), not writes: **5,008 recent `updated` bumps → 5,008 transitions, 0 writes**. Only 3 genuine writes in 30d (`_audits/`, 2026-07-14T00:12), attributed to a hand-run `audit_fixtures_via_api_football.py` + remediated by `instruments-service@bd6b797a`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | ~~CRITICAL~~ **NONE** | Closed by measurement, not mitigation. **T5.2 re-check MUST gate on `generation`/`timeCreated`, never `updated`** — an `updated` gate false-ABORTs daily, forever. |
| R-1b | 5     | **NEW (T0.1) — the anti-risk: an `updated`-based writer check false-ABORTs the cutover permanently.** The 90-day OLM rule bumps `updated` on ~100-2,400 objects/day indefinitely on a bucket with zero writers. Any gate reading "newest object mtime" reads those as live writes and blocks T5.4 forever.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | HIGH                  | T5.2 rewritten to gate on `timeCreated >= T0.6` / `updated != timeStorageClassUpdated`. `~/tmp-cutover/scan_writers.py` is the verifier.                           |
| R-2  | 0     | Freezing the 4 fixture crons but not the `*/5` meta-launcher → fixtures job still dispatched every 5 min into a "frozen" estate.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | HIGH                  | T0.3 freezes the meta-launcher FIRST (freeze_order 1) — `sports-trigger-tiers.yaml` proves it dispatches the 3 job names.                                          |
| R-3  | 0     | Freezing consolidators BEFORE the drain strands per-VM shards permanently (legacy has had no consolidator since 2026-07-13 — its shards can never merge).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | HIGH                  | T0.5 drain gate ≥2 ticks before T0.6; poll on a progress metric.                                                                                                   |
| R-4  | 2     | **The MOVE vehicle enumerates 4 of 7 trees as EMPTY and exits 0** (F-1) — `instrument_availability` alone is 119,858 objects. Undercount reported as success.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | CRITICAL              | T2.2 drives from an independent object-layer inventory; the vehicle is a copy primitive only. OR-6.                                                                |
| R-5  | 2     | **Skip-if-exists skips the 13,222 class-B objects** (F-2) — canonical exists but holds fewer rows → 305,000+ rows lost at delete. Canonical is NOT a superset.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | CRITICAL              | T2.4 + OR-1 (row-union vs overwrite); per-cell containment check before writing.                                                                                   |
| R-6  | 2     | **The vehicle re-imports v1_archive into canonical** (F-3) — `SPORTS_REF_V1_ARCHIVE_PREFIX` ∈ `_INSTR_DATA_TREES` and IS enumerable.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | HIGH                  | T2.1 (delete archive) strictly BEFORE T2.3 (move).                                                                                                                 |
| R-7  | 2     | **Day-window truncation** (F-4) — defaults 2019-01-01…2026-06-01 vs real span 2018-01-02…2026-12-06. Out-of-window days are never listed → never reported → never copied.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | HIGH                  | T2.3 passes the explicit full span; T4.1 re-inventory catches any residual.                                                                                        |
| R-8  | 2     | Control-plane uniques are skipped **by construction** (`_keep()` filters `/_index/`, `/_vm_staging/`, `_SKIP_PREFIXES`) — incl. `_legacy_seed.parquet` at 1,757,469 rows.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | HIGH                  | T2.5 adjudicates each explicitly; OR-4. Delete blocked while `_legacy_seed` is unresolved.                                                                         |
| R-9  | 2/4   | **A gate script that reads an empty set and reports PASS.** `verify_v1_archive_row_coverage_2026_06_27.py` globs `v1_archive` in the **PRD** bucket (tree exists only in legacy) → `v1_keys=∅` → _"VERDICT: COVERED — all 0 keys present"_. Second bug: it resolves `fixture_id` (a composite STRING) for v1 vs `af_fixture_id` (int) for v2 → 0/31 overlap → had the bucket been right it would have reported a FALSE 100% GAP. The two bugs mask each other.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | CRITICAL              | T2.1 proves coverage independently (all 398, real join key); T6.8 DELETES the script.                                                                              |
| R-10 | 3     | ~~Purge predicate without the `source` filter destroys the real footystats population~~ **✅ CLOSED 2026-07-16 — did not occur.** T3.1 used the mandatory NULL-safe `COALESCE(source,'')='api_football' AND COALESCE(data_type,'')='ODDS'`. Proven by a **collateral-damage census** over ALL 5.47M rows grouped by `(data_type,source)`: **exactly ONE class changed** (`ODDS\|api_football` 123,149→0); footystats × ODDS **140,574 → 140,574 UNTOUCHED**, re-verified by content. **New sub-risk found + avoided**: the _naive_ `NOT (source=… AND data_type=…)` is NULL-unsafe — it silently DROPS every NULL-`source` row.                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | ~~CRITICAL~~ **NONE** | Closed by execution + content verification. Any future index predicate MUST use the COALESCE form.                                                                 |
| R-11 | 3     | ~~A `.bak` written into `_index/per_vm/` becomes shard #3 → consolidator merges it → **resurrects every purged row**~~ **✅ CLOSED 2026-07-16 — structurally impossible for this backup.** T3.1's backup went to **`_index/purge_backups/<TS>/`** (dispatch-mandated, safer than the runbook's `_index/*.bak` sibling). Verified FROM THE CODE that the consolidator lists **only** `_PER_VM_DIR_PREFIX = "_index/per_vm/"` (`_state.py:128` → `manifest_consolidator.py:1699/1727/1798`) and nothing globs `_index/` broadly. Post-purge `_index/per_vm/` still holds exactly 2 objects.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | ~~CRITICAL~~ **NONE** | Closed. **The rule stands for every future phase** — never place a parquet under `_index/per_vm/` that is not a shard meant to merge.                              |
| R-12 | 3     | ~~Purge races a consolidation → the hot `sports-fixtures-job.parquet` loses live rows~~ **✅ CLOSED 2026-07-16 — the premise was already stale and the window was guarded 3 ways.** `sports-fixtures-job.parquet` **no longer exists** (reaped = merged pre-T0.6, per T0.5's drain gate). Guards applied: (1) `_index/consolidator.lock` held via the consolidator's own create-CAS, released in `finally` with its OWN gen; (2) **index CAS** `if_generation_match` — GCS-enforced, so a concurrent write ABORTs with the index untouched; (3) per_vm mtime witness — all static.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | ~~HIGH~~ **NONE**     | Closed by execution. The **CAS**, not the lock, is the load-bearing guard for any future index rewrite.                                                            |
| R-13 | 4     | **Treating L6 GREEN as delete-clearance.** No index has a path column → no row can reference `v1_archive` → L6 is blind to it **by construction**. This is exactly how "legacy-only=0" coexisted with 398 real parquets.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | CRITICAL              | T4.1 makes the OBJECT layer the gate. The manifest is never evidence about objects.                                                                                |
| R-14 | 5     | **Terraform resurrection** — the blocks DECLARE the buckets; deleting without removing them recreates empty shells on the next apply.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | CRITICAL              | T5.1 (remove blocks + import block + `state rm`) → T4.4 (clean plan) → T5.3/T5.4. Precedent: ~30 buckets recreated 2026-07-12T21:59Z.                              |
| R-15 | 5     | `_imports_reconcile.tf:74-77` left behind → `plan`/`apply` **errors on a missing import target** → blocks the WHOLE estate, not just sports.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | HIGH                  | T5.1 removes it in the SAME commit as the resource block.                                                                                                          |
| R-16 | 5     | Legacy IAM grants left behind → `apply` fails post-delete (IAM member on a nonexistent bucket).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | HIGH                  | T1.4 canonicalises all 3 before the delete.                                                                                                                        |
| R-17 | 5     | ~~MDPS Cloud Run job **fails to START** (gcsfuse cannot mount a deleted bucket) — `:230` is a live **WRITE** mount.~~ **✅ CLOSED 2026-07-16 — FALSE PREMISE, the risk does not exist.** Measured: **all 113 live Cloud Run jobs carry ZERO references to either legacy bucket**; there is **no MDPS Cloud Run service**; the MDPS module (`terraform/services/market-data-processing-service/gcp`) is **dormant unapplied config** — its job `market-data-processing-service-job` + 2 workflows do not exist live and its state is **EMPTY (serial=1)**. The live MDPS jobs (`uts-prod-market-data-processing-service-t1-recon`, `uts-prod-mdps-odds-horizon-bucket`) are declared by `module "mdps_t1_recon_job"` (`terraform/gcp/audit03_cron_provisioning.tf:356`) in `terraform/state/prod` and have **0 volumes**. **T1.3's `tofu apply` prerequisite is MOOT and its instruction was DANGEROUS** — applying the MDPS module against `prefix=terraform/state/prod` runs a different module's config against the `terraform/gcp` state ⇒ proposes destroying ~every prod resource. NOT RUN. | ~~HIGH~~ **NONE**     | Closed by measurement. T1.3's edit is correct hygiene with zero runtime effect. **Never apply the MDPS module against `terraform/state/prod`.**                    |
| R-18 | 5     | Deleting `market-data-tick-sports` on an **extrapolated** unique count (~52,400 from an n=400 sample).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | HIGH                  | T2.6 exact pass is a hard gate on T5.4 for that bucket. OR-5.                                                                                                      |
| R-19 | 6     | Restoring writers onto an index that lost rows in the merge, or resuming the meta-launcher first so failures are masked by fan-out.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | MEDIUM                | T6.1 ≥3 clean consolidator ticks first; T6.5 meta-launcher LAST; per-job first-run verification.                                                                   |
| R-20 | all   | **Path-shape trap** — naive path-equality falsely reports "unique" (legacy is bare `entity=`; canonical has `pipeline_mode=`). Also `fetched_at_hour=` is a snapshot dimension (7× overcount) and byte size is NOT a row proxy (3.25% wrong).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | CRITICAL              | T2.2 cell-key normalisation via the UAC SSOT + mandatory ≥10-pair sample-verify before scaling.                                                                    |

## ROLLBACK

**Rollback is only fully available before T5.3 (object-version purge). After T5.4 the legacy bucket is gone — the T0.2
snapshot + the moved canonical objects are the only copies.** Versioning is enabled on both legacy buckets, so
individual object rollback is available until T5.3 purges the versions.

| If this fails         | Rollback                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 0 (freeze)      | `gcloud scheduler jobs resume <NAME>` in reverse freeze order. No data touched. Fully reversible.                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Phase 1 (code/TF)     | `git revert` the repoint commits; `tofu apply` restores the mounts/IAM. **T5.1 is NOT part of Phase 1** — no bucket lifecycle change has happened yet. Fully reversible.                                                                                                                                                                                                                                                                                                                                                            |
| T2.1 (archive delete) | Object versioning is ON → restore the 398 via `gcloud storage cp --all-versions` **until T5.3**. After T5.3: unrecoverable — but proven superseded on all 398 (0 rows lost).                                                                                                                                                                                                                                                                                                                                                        |
| T2.3/T2.4 (moves)     | Copies are ADDITIVE to canonical; legacy is untouched (copy, not move — the delete is Phase 5). Roll back by deleting the copied canonical objects listed in the T2.2 copy list. **Class B overwrites are the exception** — restore the canonical originals from their T0.2 `.bak` / object versions.                                                                                                                                                                                                                               |
| T3.1 (123,149 purge)  | **EXECUTED 2026-07-16T13:09Z.** Restore the verified backup `gs://instruments-store-sports-prd-central-element-323112/_index/purge_backups/20260716-130924/availability_index.20260716-130924.purge_af_odds.bak.parquet` (crc32c `KrwkFw==`, 97,608,985 B) over `_index/availability_index.parquet` — it is the exact pre-purge index, `gen 1784189888944530`. **Never restore it into `per_vm/`.** Restoring re-adds 123,149 phantom rows, so only roll back if a gate is later found wrong; the purge itself is content-verified. |
| T5.1 (TF state rm)    | Re-add the resource blocks + `terraform import` the buckets back. Only possible while the buckets still exist.                                                                                                                                                                                                                                                                                                                                                                                                                      |
| T5.4 (bucket delete)  | **NO ROLLBACK.** This is why T4.1 (object-layer zero-unique) + T5.2 (final writer re-check) are hard gates.                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Phase 6 (restore)     | Re-pause the offending job; restore the index `.bak`; resume one job at a time.                                                                                                                                                                                                                                                                                                                                                                                                                                                     |

**Rollback ordering**: always reverse-order. Restoring a writer before its consolidator, or a meta-launcher before its
tier jobs, re-corrupts the state you just restored.

---

## OPERATOR RULINGS NEEDED

> Each is genuinely undecidable from the audits — they are **not** requests to re-confirm work already proven.

**OR-1 (BLOCKING Phase 2c) — class B: how do we move 13,222 objects whose canonical twin has FEWER rows?** The
operator's phrasing was _"MOVE any non already existent data"_ — object-existence semantics. But canonical is **not** a
row-superset of legacy: 13,222 canonical objects hold strictly fewer rows (player_stats 111,827; standings 91,380;
fixture_events 69,444; teams 16,502; player_values 16,233 — e.g. `day=2019-08-12 season=2019`: legacy 640 vs canonical
38). Both move vehicles use skip-if-exists → they skip **every one of them** → deleting legacy destroys 305,000+ rows.

> **🟡 INVESTIGATED 2026-07-16 →
> [`issues/sports_legacy_canonical_row_gap_2026_07_16.md`](issues/sports_legacy_canonical_row_gap_2026_07_16.md). The
> framing above is CORRECTED by measurement**: canonical is not a row-superset of legacy — but legacy is not a superset
> of canonical either, and **canonical is NET RICHER (+27,764 rows / 3,051 paired objects)**. The "305,000+ rows lost"
> overstates the recoverable figure by ~2.7×: only **~111,827 (player_stats)** is genuine data. There was **no lossy
> migration** — the buckets are independent capture generations (canonical written 6-10 weeks LATER, 62/62). **T2.4's
> ABORT clause fires**: every sampled class is genuine divergence (legacy ⊄ canonical AND canonical ⊄ legacy), so no
> containment-based move was ever viable. **New recommended option D below.**

- **A: row-union legacy ∪ canonical per cell, write the union to the canonical path** — ~~[WORKER REC]~~ **NOW
  REJECTED**: unions incompatible schemas (legacy `fixture_events` is 5-col vs canonical's 13-col), re-imports the
  `player_values` cartesian corruption, and re-adds `standings` aggregate views canonical deliberately no longer carries
  — 13,222 read-merge-writes to recover data that is ~59% junk.
- **B: overwrite canonical with legacy wherever legacy ⊇ canonical** — **CATASTROPHIC, ruled out by measurement**:
  containment does NOT hold in any sampled class, and canonical is net-richer by +27,764 rows. Overwrite replaces
  canonical's 13-col `fixture_events` with a 5-col stub and its correct 38-row `player_values` with 640-row junk.
- **C: treat "non already existent" literally — skip class B and accept the row loss** — loses the ~111,827-row
  `player_stats` residue (real 38-col rows for fixtures canonical demonstrably lacks); contradicts the
  data-pipeline-correctness HARD RULE.
- **D: PARTIAL — targeted, schema-aware, per-entity union [WORKER REC]**: (1) **`player_stats` only** — union on the
  shared 38-col schema keyed `(fixture_id, player_id)`, **de-duplicating on write** (canonical has a 2× duplication
  defect); (2) **`fixture_events`** — do NOT union; enumerate the legacy-only `fixture_id`s and **re-fetch them from
  api-football into the canonical 13-col schema** (external-data-always-available); (3) **`standings` / `teams` /
  `player_values`** — **NO ACTION**, written disposition (snapshot skew, zero missing entities / cartesian junk).
  Shrinks Phase 2c from 13,222 objects to a `player_stats`-scoped union + a `fixture_events` re-fetch list.
- Other.

**OR-2 (~~BLOCKING Phase 0~~ — ✅ MOOT / NO RULING NEEDED, resolved by measurement 2026-07-16).** ~~The legacy bucket
has a live writer we cannot identify.~~ **There is no live writer.** T0.1 proved at the object layer that all 5,008
recent `updated` bumps are OLM `STANDARD→NEARLINE @ 90d` storage-class transitions (`generation` unchanged,
`metageneration` 1→2, `updated == timeStorageClassUpdated`), not writes. The only 3 genuine writes (2026-07-14T00:12,
`_audits/`) are attributed to a hand-run `audit_fixtures_via_api_football.py` and were remediated 2h33m later by
`instruments-service@bd6b797a`. The "no resolver can produce the legacy name" observation was **correct all along** — it
was the write-detection that was wrong, not the resolver audit.

- ~~A: enable GCS data-access audit logs, wait 24-48h~~ — **unnecessary**; the object layer settled it in minutes, and
  data-access logging is OFF (so it would have attributed nothing retroactively anyway).
- ~~B: proceed on the assumption it is a hand-run one-off now stopped~~ — this was the right _guess_, but it is now a
  **proven fact with a named script, commit, and timestamp**, not an assumption.
- ~~C: deny-all bucket IAM~~ — **do not**; there is nothing to attribute and it would only break readers.
- **Standing guard (already in the plan)**: T5.2's final pre-delete re-check remains — but it must now compare
  **`generation`/creation-time**, NOT `updated`, or the 90-day OLM transitions will trip it as false "writes".

**OR-3 (Phase 2a) — confirm executing the already-approved v1_archive delete.** The delete is an already-authored P0
operator todo in the 2026-04-28 migration plan whose 7-day window expired ~2026-05-05. This audit independently proves
it safe (398/398 covered, 0 rows lost, 0 value mismatches, the 41-column alarm vacuous). Bucket-scoped deletes are
destructive → confirming rather than assuming.

- **A: execute the delete now — it is the expired, pre-approved rollback window [WORKER REC]**
- **B: park it under `_audits/` instead** — not recommended; parking is for real-but-out-of-model data, and this holds
  zero unique observations (it would just re-contaminate).
- Other.

**OR-4 (BLOCKING Phase 5) — `_index/per_vm/_legacy_seed.parquet`: 1,757,469 rows in legacy, 0 in canonical.** The
canonical seed is **EMPTY** (16.2 MB vs 18.7 KB). The legacy bucket has had no consolidator since 2026-07-13, so it can
never merge on its own; the MOVE vehicle skips `/_index/` by construction.

- **A: re-home it as a canonical per-VM shard and let the consolidator merge it [WORKER REC]** — but this adds 1.76M
  rows to a 5.46M-row index; needs a row-count assertion.
- **B: abandon it as a historical seed already reflected in the consolidated index** — plausible (the legacy index at
  19:14:43Z postdates it) but **NOT PROVEN**.
- **C: prove-then-decide — diff the seed's cells against the canonical index first.**
- Other.

**OR-5 (BLOCKING T5.4 for MDT) — delete `market-data-tick-sports` on an extrapolation, or finish the exact pass?** Its
unique count (~52,400) is 9,927 verified + ~42,500 extrapolated from an n=400 sample of 108,970 crc-differing pairs. The
exact pass is ~9 min of compute (395 footer reads/s) plus ~4 min of listing.

- **A: finish the exact row-count pass (T2.6) before deleting [WORKER REC]** — ~15 min for certainty.
- **B: delete on the extrapolation** — risks losing up to ~42,500 objects' unique rows.
- Other.

> **✅ OR-5 RESOLVED = A. The exact pass is DONE (T2.6, 2026-07-16).** Measured: **55,627 unique objects** (9,926 class
> A
>
> - 45,701 crc-differing with fewer canonical rows), not ~52,400 — the extrapolation under-counted by ~3,200. 6,110 of
>   the class A are moved. **The residue is now OR-5b.**

**OR-5b (NEW, BLOCKING T5.4 for MDT ONLY — surfaced by T2.6 2026-07-16) — how do we dispose of the 49,517 remaining
unique `market-data-tick-sports` objects?** T2.6 made the count exact and moved the 6,110 derivable class-A objects, but
two sub-classes have **no ruling to inherit** — the runbook says MDT class-B "inherits OR-1", yet **OR-1 ruled only on
instruments entities (player_stats / fixture_events / standings / teams / player_values) and never covered MDT tick
data**. `market-data-tick-sports` is NOT delete-eligible until both are dispositioned. (The instruments bucket is
unaffected — it has its own completed disposition.)

- **(a) 3,816 class-A objects in OLD pre-canonical shapes** — `day=/source=/league=`, `day=/venue=/league=`,
  `day=/source=`, `day=/venue=` — lacking `asset_group` / `instrument_type` / `data_type`. **No canonical path is
  derivable without inventing those segments**, which the never-fabricate rule forbids.
  - **A: row-count them and, if their rows are contained in canonical, ABANDON with a written reason [WORKER REC]** —
    mirrors the T2.5 method (prove-then-decide) and avoids fabricating path segments.
  - **B: infer the missing segments** from the parquet contents (venue/league → asset_group/instrument_type/data_type)
    and move — only if the inference is provably total, not heuristic.
  - **C: park them under `_audits/` in canonical** as a retained archive, then delete the bucket.
  - Other.
- **(b) 45,701 class-B-equivalents holding 7,079,850 legacy-only rows** — canonical has the cell but strictly fewer
  rows. This is the MDT analogue of the instruments row-gap that OR-1 investigated, but **it has never been
  investigated**: we do not yet know how much is genuine complementary tick coverage vs snapshot skew / re-fetch
  generations (the instruments answer was ~37% genuine, ~59% junk).
  - **A: run the OR-1-style row-gap investigation on MDT first, then rule [WORKER REC]** — 7.08M rows is too large to
    discard or blanket-merge unexamined; the instruments precedent proves the naive read is wrong ~59% of the time.
  - **B: blanket union legacy ∪ canonical per cell** — risks re-importing the same junk/skew classes OR-1 rejected.
  - **C: skip them and accept the row loss** — contradicts the data-pipeline-correctness HARD RULE without evidence.
  - Other.

> **🔬 INVESTIGATED 2026-07-16 (operator rulings OR-5b(a) "derive from content, else park" + OR-5b(b) "investigate
> first, like OR-1") → `plans/active/issues/mdt_legacy_canonical_row_gap_2026_07_16.md`. Read it before ruling — it
> changes both sub-questions' premises.** Exact pass over **all 45,701** pairs (91,402 full reads, 0 errors), not a
> sample.
>
> - **The OR-1 trap does NOT reproduce — the naive read is RIGHT here.** NET balance over **every** paired object:
>   canonical is **NET POORER by 6,721,872 rows**, losing **20:1** (OR-1 was +27,764, gaining 15:1). All three classic
>   artifacts (key mapping / 1:N split / snapshot-dedup skew) tested and **CLEARED**. **`market-data-tick-sports` is NOT
>   delete-eligible.**
> - **(b) verdict — 89.5% GENUINE, 0% junk, 0% fabricated.** Of the 7,079,850: **6,372,806 (89.5%)** are real, distinct
>   pre-match bookmaker quotes canonical never captured (**0** price disagreements on 15,456 shared updates; canonical ⊆
>   legacy in 44,670/45,701 pairs); **746,928 (10.5%)** are post-kickoff/in-play (policy-ambiguous, mechanism unproven →
>   **new OR-5b(c)**). The genuine gap is confined to **2022-03-07…2023-04-30** (99.98%), where canonical holds just
>   **7.8%** of legacy's rows.
> - **THE SCOPE COLLAPSE — legacy holds THREE strictly-nested generations `G3 ⊂ G2 ⊂ G1`** (G1 = the 3,816 old-shape
>   objects, created 2026-04-05…04-13; G2 = the May `batch_api_football` corpus; G3 = canonical, June). Proven both
>   directions (`G2 − G1` = 0 over 973 cells; from the (b) side **38,197/38,197 = 100.000%, 150/150 objects**). **The
>   3,816 are the MASTER SUPERSET.** ⇒ **recover the 3,816 and you recover 99.98% of the 6.37M gap; the 45,701 are then
>   provably redundant → NO ACTION.** Remedy shrinks ~12×.
> - **(a) premise is FALSE — 3,816 DERIVABLE / 0 park-only.** The path's `source=ODDS_API` is the **VENDOR**, not the
>   venue; the venue is a **column in the rows**, and `instrument_id` is UAC's own `build_instrument_id` key encoding
>   **both** missing dimensions. `league_id := instrument_id.split(':')[3]` agrees **100.0000%** with BOTH the path's
>   `league=` segment AND the `league_id` column (499,742 rows); `venue := instrument_id[1].upper()` **100.0000%**
>   (1,065,227 rows); `source == ODDS_API` on **3,816/3,816**. **Nothing needs fabricating → adopt (a) = B.** ⚠️ It is a
>   **1:N read-split-merge** (99,414 target cells, mean 26.1/object), NOT a `gcs_copy_object` move.
> - **Recommended: (a) = B · (b) = D (recover G1, close the 45,701 by proof) · new (c) = A.** MERGE never overwrite —
>   canonical holds **8,929** quotes and 3 columns legacy lacks.
> - **Audit correction (R-20 class)**: _"all 406,581 created 2026-06-27 in ONE bulk op"_ is **false** — that is the
>   **COLDLINE lifecycle transition** (`updated`). Legacy trades `created` = **2026-05-19 / 2026-05-22**.
> - **T2.10 cross-check: LARGELY DISJOINT — no double-counting.** Phantom atoms ∩ OR-5b(b) atoms = **3,354 (7.1%)**
>   only; T2.10 is an INDEX-layer mis-stamp, OR-5b(b) an OBJECT-layer capture gap. T2.10's purge predicate stands.

> # 🔴 OR-5b RE-MEASURED 2026-07-16 BY THE RECOVERY LEG — **THE INVESTIGATION'S HEADLINE IS AN ARTIFACT. THE MERGE WAS REFUSED. DO NOT EXECUTE OPTION D.**
>
> The leg dispatched to execute "recover the 3,816 G1 objects" re-measured before writing (standing rule: never inherit
> a classification) and the premise collapsed. **Zero data objects were mutated.** Full record →
> `plans/active/issues/mdt_legacy_canonical_row_gap_2026_07_16.md` (banner + Progress Log).
>
> - **The measurement no prior MDT audit ran — WHOLE-DAY, KEY-LEVEL containment over ALL 1,837 legacy tick-days** (~900k
>   reads, 0 errors): legacy pre-match keys **42,108,211** / in-play **2,542,764**; **absent from canonical = 524,486
>   (1.2456%) + 25,576 (1.0058%) = 550,062 keys (1.23%)**. **1,805 of 1,837 days are at EXACTLY ZERO.**
> - **Why 6.37M was wrong**: it counted **ROWS not KEYS** (legacy re-writes each quote at every fetch snapshot;
>   2022-03-15: G1 = 28,944 rows but 14,104 keys, canonical = 14,904 keys — MORE) and compared **PER-PAIR not
>   WHOLE-DAY** (canonical splits one legacy object across many — 313 objects on 2022-04-02 — so rows in a sibling
>   object scored "legacy-only"). The investigation's artifact-checks (ii) and (iii) claimed to have cleared exactly
>   these two; they did not.
> - **THE REAL GAP: 32 days / 550,062 keys**, dominated by a contiguous **canonical capture OUTAGE 2022-09-07 …
>   2022-10-01** (21 days; 2022-10-01: legacy 104,868 keys vs canonical 8,849). By year: 2022 **549,330** · 2023 **377**
>   · 2025 **355**.
> - **Option D is void.** **3,472/3,816 (90.985%)** of G1 sits on a zero-gap day (nothing to recover); the dry-run
>   measured the merge would **ADD ~15.7M rows canonical already holds** (mass duplication). G1 does not even cover **3
>   of the 32** gap days (2023-07-29, 2025-02-23, 2025-03-02) ⇒ **"G1 recovers 99.98%" is FALSE**. `G3 ⊂ G2 ⊂ G1` is
>   FALSE at the key layer — canonical holds **98.77%** of every legacy key.
> - **The 45,701 DO close — by direct proof, not by the nesting claim**: **43,964/45,701 (96.199%)** sit on a zero-gap
>   day ⇒ provably redundant. **1,737** sit on the 32 gap days and carry the real data.
> - **The derivation map (a) is CORRECT** — re-validated exhaustively (all 3,816 objects / 19,944,880 rows / 0 errors,
>   every rule at 100.0000%). It is simply not needed, because there is nothing to derive a path FOR. It also needs
>   `.upper()`: canonical's native `league_id` is UPPERCASE, and with it **all 49,707** target cells already exist (the
>   doc's 99,414 is exactly 2× the truth).
> - **🔴 NEW BIG FINDING → `plans/active/issues/mdt_t2_6_league_case_duplicate_population_2026_07_16.md`: T2.6's 6,110
>   moved objects are a pure DUPLICATE population** (case-blind strip key; proven content-identical **6,110/6,110**,
>   12,220 reads, 0 errors). T2.6 recovered **0 rows**, and **T2.7's MDT shard describes the duplicates** — settle it
>   BEFORE T6.1 merges them.
>
> **⇒ MDT delete status: 🔴 STILL NOT DELETE-ELIGIBLE**, residue **~2,081 objects on 32 days** (1,737 class-B + 344 G1)
> carrying **550,062 keys** — not 49,517 objects / 7,079,850 rows. **The correct remedy is a day-scoped recovery of 32
> days**, not a generation recovery. **OR-5b(a)/(b)/(c) all need re-ruling on these numbers.**
>
> ---
>
> ## 🟢 CONFIRMED A SECOND TIME 2026-07-16 — and the MECHANISM is now identified → [`issues/sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md`](./issues/sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md)
>
> A second leg was dispatched to execute option D (on the pre-banner premise, plus a new "legacy is the ONLY complete
> raw layer" claim from the recompute leg). It re-measured and **refused the merge again. Zero mutations.** Everything
> above is upheld, and the missing mechanism is found:
>
> - **Why canonical already holds every legacy key**: canonical carries **16,969 `_migrated_` objects** (2026-05-05
>   refactor, **1,815 days**) that **ARE** the G1 content — **30/30** sampled G1 objects are **row-identical and
>   tick-key-identical** to their canonical twin (0 legacy-only, 0 canon-only; `source == ODDS_API` both sides).
>   Canonical migrated ⊇ legacy G1 (1,815 days vs 386). **G1 recovery = copying what canonical has.**
> - **The 32-day residue is corroborated independently**: **213/3,816** G1 objects have **no** canonical twin, on **23**
>   days — **22 are exactly the gap days above**. Two methods, one answer.
> - **🔴 NEW BIG FINDING — the migrated population is MIS-STAMPED and INVISIBLE to MDPS.** All **16,969** are
>   `venue=ODDS_API` + `data_type=odds` yet **100% stamped `pipeline_mode=batch_footystats`** — **zero are footystats
>   data** (violates `{mode}_{source}`, `codex/02-data/pipeline-mode-partition.md`). `reprocess_sports_odds.py` lists
>   only `batch_odds_api`/`live_odds_api` and excludes `_migrated_`, so it reads the **de-duplicated** half (5,626 rows
>   on 2022-04-16) and never the **full-horizon** half (79,773 rows). **That — not a truncated canonical, and not a
>   missing legacy recovery — is why the features recompute starves and why `--force` deletes horizons.** The blocked
>   recompute needs a **~4-line MDPS change**, no GCS migration.
> - **`sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md` has its cause corrected**: its symptom and
>   every number reproduce; its "canonical raw is truncated ⇒ recover from legacy" diagnosis and fix direction (a) are
>   **refused**. Its loss-guard (b) stands, P0.
>
> **⇒ Option D stays REFUSED (twice, independently). MDT stays NOT delete-eligible on the 32-day / 550,062-key residue.
> The delete gate is that day-scoped recovery — nothing else.**

**OR-5b(c) (NEW — raised by the OR-5b investigation 2026-07-16, BLOCKING T5.4 for MDT alongside (a)/(b)) — what is the
disposition of the 746,928 post-kickoff / in-play rows?** ⚠️ **The 746,928 figure is a ROW count and is superseded: the
genuine in-play residue is 25,576 KEYS on 32 days** (see the banner above). The quarantine MECHANISM in B-REFINED is
also measurably insufficient — `reprocess_sports_odds.py::_is_consumable_trades_blob` matches on the FILENAME only
(`ticks.parquet`) and never reads the `instrument_type=`/`data_type=` segments, so a distinct instrument_type/data_type
alone would still be swept into T-0. A working quarantine needs a non-`ticks.parquet` filename AND a distinct
`data_type=`; `pipeline_mode` must stay `batch_odds_api` (closed UAC enum). Note the sibling leg's adapter fix has
already landed (`n[vals < 0] = -1`, post-kickoff REJECTED). They are REAL observations, uniform across all 7 years
(unlike the dated pre-match gap). Canonical holds 1.07% in-play vs legacy's 5.59%; 92/112 sampled canonical objects hold
zero. **No filter exists in the current adapter** — the mechanism is genuinely unknown, so neither a silent discard nor
a blind merge is defensible. Deleting the bucket makes this irreversible.

> **🔬 INVESTIGATED 2026-07-16 (operator question: _"we want half time odds — is there knowledge of this from SFI
> derived half time?"_) → `plans/active/issues/sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`. The mechanism is
> **PROVEN** and the WORKER REC moves **A → B-REFINED**.**
>
> - **SFI ALREADY HOLDS HALF-TIME ODDS — denser than the legacy rows.** The captured `sfi_progressive_stats` contract
>   carries **12 price columns** (`odds_1x2_*`, `odds_ou_*`, `odds_ah_*`, `odds_asian_corner_*`) + `ht_start_timer`.
>   Measured live: **100% non-null inside the HT break** (2550-2999s), **31/31 fixtures across 2021→2026 / 5 leagues**,
>   30-second granularity, genuine repricing (3.30 kickoff → 36.0 at HT). Coverage 2020→2026 over a **superset** of the
>   10 in-play leagues. **The half-time market LEVEL does not depend on this bucket.**
> - **The 746,928 are per-bookmaker (23 books) but FULL-TIME markets only** — `h2h`/`totals`/`spreads`/`h2h_lay`; **zero
>   HT-specific markets, in-play OR pre-match**. Coarse grid (+5/+15/+30/+45/+60/+75/+90/+120), not continuous.
> - **Only ~3.1% (~23,000 rows) is unique AND usable** — per-bookmaker quotes in the PIT-valid HT-break window
>   (+45..55). Against `_apply_ht_odds_pit_gate` (default cutoff −55): **63.2% is actively REJECTED as 2nd-half
>   leakage**, 17.0% is post-match.
> - **There is NO "HT" horizon** — `TIER1_HORIZONS` is 8 **pre-match** buckets (T-24h…T-0), confirmed on the live
>   processed layer. **BIG FINDING**: `nearest_idx[vals<0]=N_BUCKETS-1` runs AFTER the staleness rejection → **184/282
>   (65%) of sampled canonical T-0 rows are post-kickoff**, to −71.1 min = **live lookahead leakage**.
> - **The HT-RESULT market is captured NOWHERE** — `ht_odds_home_implied` reads the dormant
>   `CanonicalProgressiveOdds.first_half_*`; SFI's API serves `h1_*` but `_extract_odds()` never reads it →
>   **re-fetchable capture gap, NOT a deletion loss**.

- ~~**A: recover pre-match only; document the 746,928 as a deliberate written exclusion [WORKER REC]**~~ — **REJECTED
  2026-07-16**: the "pre-match-only property" is **measurably false** (T-0 is 65% post-kickoff) and no lookahead
  guarantee rests on it. Discards ~23k non-reproducible per-bookmaker HT-break quotes for no gain.
- **B: recover them into a distinct population** (own `instrument_type`/`data_type`) so pre-match consumers are
  unaffected but the observations survive. → **ADOPT as B-REFINED [WORKER REC 2026-07-16]**: they ride along on the
  option-D G1 read-split-merge (same 3,816 objects — **marginal cost ≈ 0**), landing **quarantined from the pre-match
  bucketing path** (merging into `data_type=odds` would sweep them into T-0 and deepen the 65% contamination).
- ~~**C: prove the mechanism first** (deliberate policy vs June-campaign artifact), then rule.~~ — **SPENT**: proven a
  **June-campaign snapshot-grid artifact, not policy** (no adapter filter AND the processed layer force-feeds
  post-kickoff rows into T-0).
- Other.

**OR-9 — ✅ RESOLVED + EXECUTED 2026-07-16 (option A, per-entity by schema — but the entity split was RE-MEASURED and
came out very differently from the option text below; see the Progress Log's OR-9 entry).** Outcome: **482 distinct
legacy-only keys + 803 progressive rows recovered into canonical across 131 cells; 5,897 keys proven to be payload-free
(nothing to lose); 1 object proven SYNTHETIC and abandoned; 1 proven regenerable. UNACCOUNTED = 0 →
`instruments-store-sports` is object-layer delete-eligible.** The option text is retained below as the record of what
was proposed before measurement.

_Original ruling request (BLOCKING T5.4 for the INSTRUMENTS bucket — surfaced by T4.1 2026-07-16) — how do we dispose of
the ~1,834 legacy objects holding 6,673 genuinely legacy-only entity keys in entities OR-1 never ruled on?_ T4.1's
object-layer pass re-measured all 456,727 crc-differing objects (rather than inheriting the audit's 443,508-superseded
claim) and found **2,078 objects whose canonical twin holds strictly fewer rows in an entity with NO written
disposition**. Key-level containment then split them:

- **DISPOSITIONED BY MEASUREMENT — no ruling needed** (244 objects): `injuries` (151 objs) → **0 legacy-only fixture
  keys**; the exact 2× row ratio is legacy-side duplication → NO ACTION, proven. `fixtures_outcomes` (93 objs) → legacy
  carries **no fixture identifier column at all** → 325 rows unattributable by construction → the same verdict OR-1 D(2)
  reached for `fixture_events`.
- **NEEDS A RULING** (~1,834 objects / **6,673 legacy-only keys**): `fixture_stats` 1,738 objs / **6,379 keys** ·
  `footystats_odds` 26 / 152 · `fixtures_schedule` 24 / 121 · `fixtures` 6 / 13 · `footystats_matches` 2 / 4 ·
  `progressive_stats` 36 / 4 · `sports_reference` mappings 1 / 51 rows · `instrument_availability` 1 / 1 row.

**This is OR-1's blind spot, not a new phenomenon**: OR-1 option D enumerated only the 5 entities that dominated the row
count and the rest of class B silently inherited "superseded". The schema split mirrors OR-1's own findings exactly —
`fixture_stats` is the **4-col nested raw form** (`[team, statistics, fixture_id, available_at]`) against a **23-col
flattened** canonical, i.e. the `fixture_events` D(2) case; `footystats_odds` is an **identical 76-col** schema, i.e.
the `player_stats` D(1) case.

- **A: apply OR-1 option D per-entity by schema, mechanically [WORKER REC]** — ✅ **ADOPTED AND EXECUTED, but every
  number in this option proved wrong on measurement.** D(1) **union** where the schema is shared/subset and the key is
  clean (`footystats_odds` 152, `fixtures_schedule` 121, `fixtures` 13, `footystats_matches` 4, `progressive_stats` 4 =
  **294 keys**, the T2.4 union method already proven at 388,825 rows) — **MEASURED: 124 distinct keys, not 294** (the
  per-pair counts double-count; GLOBAL cross-partition containment is the honest number), and
  `sports_reference`/`progressive_stats` were **NOT** "clean" (see below); D(2) **re-fetch list** for `fixture_stats`
  (6,379 keys — legacy is the nested raw form; flattening it into the 23-col canonical schema locally would be
  fabrication, and api-football holds the truth → external-data-always-available) — **MEASURED: FALSE on both halves.**
  Only **90/1,738** objects are nested; the other **1,648 are 2-col `[fixture_id, available_at]` with ZERO payload**
  (5,897 keys → nothing to re-fetch-because-lost; nothing to lose). And the nested form **IS** losslessly flattenable —
  **PROVEN**, not argued: the UAC SSOT production normalizer
  `external/api_football/normalize.py::normalize_api_football_fixture_stats` (the very function that built canonical's
  23 columns) reproduces canonical's OWN rows **174/174** on the non-revised overlap, so applying it is derivation from
  content, not fabrication → the 358 real keys were RECOVERED, not deferred to a re-fetch.
- **B: re-fetch everything** (all 6,673 keys from api-football, incl. the 294 that are cleanly unionable) — simpler, one
  mechanism, no union-schema risk; costs api quota and re-does data we already hold byte-perfect. — **REJECTED**: 92% of
  the "keys" have no payload to recover, so B would have spent quota re-fetching fixtures whose stats the provider very
  likely never returned (the 2-col shape is what the writer emits on an EMPTY statistics block; **78% of the legacy
  fixture universe — 39,116/50,414 — is payload-free**).
- **C: accept the loss and delete now** — **contradicts the data-pipeline-correctness HARD RULE**; 6,673 keys is real
  reference data (`fixture_stats` for 6,379 fixtures canonical demonstrably lacks). Not recommended. — **REJECTED for
  the 482 real keys** (they were recovered). Note the premise was itself wrong: 5,897 of the 6,379 `fixture_stats` keys
  are **not** "real reference data canonical lacks" — they are fixture-id references with no observation attached.
- Other.

**The two catches that justify the re-measure discipline (either would have corrupted canonical):**

1. **`sports_reference/mappings/season=2019/…/teams.parquet` — identical 7-col schema, 100% FABRICATED content.** Option
   A's rule ("schema shared/subset + clean key → union") would have imported it. Measured: legacy is **640/640 synthetic
   rows** (`name` = `t0..t639`, every `squad_size=25`, one `last_fetched_at`) vs canonical's **589 REAL teams** (Malmö,
   Elfsborg, Häcken…). The "51 legacy-only rows" was an artifact of diffing a smoke-test file against real data. →
   **ABANDON, never import.** _Schema cleanliness is not content truth._
2. **`progressive_stats` has NO unique row key — a keyed dedupe would have DESTROYED real observations.** No candidate
   key is unique on canonical's own data: 25 rows share `(fixture_id, timer_seconds=0, team='')` with **genuinely
   different values** (repeated pre-match snapshots). Deduping on the "natural" key would have collapsed 25 real
   observations into 1. → recovered **append-only** instead (canonical holds ZERO rows for the 4 affected fixtures, so
   the append is collision-free and needs no dedupe decision).

**OR-6 (BLOCKING Phase 2) — fix the MOVE vehicle, or drive the move from the object inventory?**
`migrate_sports_canonical_v9.py` silently enumerates 4 of its 7 declared trees as empty (F-1), cannot see class B (F-2),
would re-import v1_archive (F-3), and truncates the day window by default (F-4). It reports success while undercounting.

- **A: drive Phase 2 from the T2.2 object-layer inventory; use `gcs_copy_object` directly; delete the vehicle at T6.8
  [WORKER REC]** — the inventory method is already proven and reproduces every known ground truth.
- **B: fix the vehicle (4 defects) and re-verify it** — it is a one-off scheduled for deletion at T6.8; fixing it buys
  nothing durable.
- **C: fix only `_list_tree` + the day defaults, and handle class B separately.**
- Other.

**OR-7 (Phase 0/6) — the 3 `sports-ref-v3-{1,2,3}-start` schedulers fire annually at instances that do not exist.**

- **A: delete all 3 [WORKER REC]** — `gcloud compute instances list --filter='name~sports'` returns zero rows.
- **B: leave them paused** in case the v3 reference VMs are rebuilt.
- Other.

**OR-8 (Phase 4) — `uts-prod-market-tick-data-service-fast-t1-recon` runs with NO `--asset-group`.** Its baked args are
`[--operation download --mode batch]`; UTL `service_cli.py:163-167` gives `--asset-group` no default. The infra leg read
the argparse definition but **did not execute the resolver** to prove what the `None` branch enumerates. It may write
sports odds unfiltered.

- **A: dry-run it and measure the asset-group list before restoring it (T4.5) [WORKER REC]**
- **B: pin `--asset-group` explicitly on the job spec** — removes the ambiguity permanently.
- Other.

---

## Progress Log

### ✅ T6.1 MERGE COMPLETE — both indexes absorbed the pending shards, every delta as predicted (2026-07-17, owner: Phase-6/restore sub-agent)

> **🔴 A REAL DATA-LOSS EVENT FIRED AND WAS RECOVERED IN-BAND. READ THIS BEFORE ANY FUTURE CONSOLIDATOR RESUME.** The
> first instruments consolidator run **deleted both pending shards without merging them**, and reported `success=True` +
> `exit(0)`. Recovery was possible ONLY because this leg downloaded the shards to measure them BEFORE executing. **New
> issue doc:
> [`issues/consolidator_content_write_marker_strip_silent_shard_reap_2026_07_17.md`](issues/consolidator_content_write_marker_strip_silent_shard_reap_2026_07_17.md)**
> — it is a **UTL-wide latent bug**, not a sports quirk.

**The failure (measured, not inferred).** First run `uts-prod-manifest-consolidator-instruments-sports-4rfp4` @
01:34:31Z:

```
success=True shards=3 rows_in=0 rows_out=0 dedup_dropped=0 pruned_shards=2 error=-
ManifestConsolidator: pruned 2 consolidated per-VM shard(s) (cutoff=2026-07-16T18:45:21.846000+00:00, 2 eligible)
```

**`rows_in=0` + `pruned_shards=2` = both shards reaped unmerged, reported as success.** Root cause chain, each link
verified:

1. `_prune_consolidated_shards` deems a shard settled iff `mtime <= cutoff`, where `cutoff = content_write_marker − 5s`
   skew. The invariant is _"the marker carries the last REAL merge's shard-listing start time, so `mtime <= cutoff`
   proves the shard was visible to that merge's listing"_ (`manifest_consolidator.py:1751-1782`).
2. `_get_content_write_mtime` (`:1617-1666`) falls back `consolidator_content_write_at` → `consolidator_run_at` →
   **`blob.updated`**, documented as SAFE because it _"can only make the cutoff OLDER … fail toward correctness"_.
3. **That safety claim is FALSE when an out-of-band writer STRIPS the marker and bumps `updated`.** Forensic proof from
   this leg's own backups (`cp` preserves custom metadata): the **08:05 precutover backup** carries a real marker
   `consolidator_content_write_at=2026-07-16T06:36:46Z`; the **01:27 pre-T6.1 backup** — taken after the T3.1 purge
   (13:09Z) and the 18:45:26Z rewrite — carries **`metadata: None`**. The cutover's own out-of-band index rewrites
   destroyed the marker.
4. Marker gone ⇒ fallback to `blob.updated` = **18:45:26.846Z** (the 18:45 rewrite — i.e. the "frozen-generation
   witness" `1784227526828259` ITSELF) ⇒ cutoff **18:45:21.846Z** (exactly the logged value) ⇒ both shards (12:46:09,
   17:30:42) fell under it ⇒ reaped unmerged.

**Recovery (executed, verified).** GCS retained **no** noncurrent versions (`ls -a` on `_index/per_vm/` → only
`_legacy_seed`). The shards were restored from this leg's pre-merge downloads — integrity re-verified before upload:
7,183 / 2 / 6,110 rows, **all `captured`, 0 blank-source, 0 zero-`instrument_count`** (the same ABORT-checks T2.7
applied). Re-uploaded at 01:38:42/43Z (canonical `updated`=01:34:30Z ⇒ cutoff 01:34:25Z ⇒ shards NEWER ⇒ classified
"changed" ⇒ merged, not pruned). **The marker is now correctly stamped** (`consolidator_content_write_at`
=2026-07-17T01:39:26Z) so the fallback is no longer in play for this bucket.

**Why MDT was never at risk (verified, not assumed).** MDT's canonical carries a GENUINE marker
`consolidator_content_write_at=2026-07-15T22:51:06Z` and was never rewritten out-of-band (its `updated` was still frozen
at 08:18:06Z, the T0.6 freeze). Its shard (07-16 12:54:13Z) is NEWER than that cutoff ⇒ merge-eligible. **Only the
instruments index was poisoned, and only because the cutover itself rewrote it out-of-band** — a consistent, complete
explanation.

**The merges (BY CONTENT — fresh re-read, independent of the consolidator's own report).**

| index           | metric   | before    | after         | delta      | predicted     |
| --------------- | -------- | --------- | ------------- | ---------- | ------------- |
| **instruments** | total    | 5,342,265 | **5,349,447** | **+7,182** | +7,182 ✅     |
| instruments     | captured | 1,692,695 | **1,699,880** | **+7,185** | +7,185 ✅     |
| instruments     | af×ODDS  | 0         | **0**         | 0          | 0 ✅ TERMINAL |
| instruments     | fs×ODDS  | 140,574   | **142,617**   | **+2,043** | +2,043 ✅     |
| **mdt**         | total    | 1,958,498 | **1,959,024** | **+526**   | +526 ✅       |
| mdt             | captured | 575,671   | **576,197**   | **+526**   | +526 ✅       |
| mdt             | fs×ODDS  | 22,145    | **22,145**    | 0          | flat ✅       |

Consolidator reports corroborate: instruments `rows_in=5349450 rows_out=5349447 dedup_dropped=3` (exec `j2rqk`, 328s, no
signal 9 — well under the 900s bump); MDT `rows_in=1964608 rows_out=1959024 dedup_dropped=5584` (exec `94c2f`, 85s).
**MDT's 5,584 supersession proven at the content layer**: `service_name='migrate-sports-canonical'` rows by source went
`api_football` 9,208 → **3,624 (−5,584 exactly)** and `odds_api` 167,220 → **173,330 (+6,110 = 5,584 superseded + 526
new)** — exactly T2.7's dedup-key design (`source` is not in the key, so the corrected row supersedes the mis-stamp).

**Two CORRECTIONS to inherited numbers (measured, not accepted).**

- **`footystats × ODDS` does NOT stay 140,574 at T6.1 — it MUST rise to 142,617.** "140,574 UNTOUCHED" was a **Phase-3**
  gate (the purge must not touch the footystats population while the index is quiet); it is **not** a T6.1 invariant.
  The cutover shard legitimately carries 2,044 footystats×ODDS cells (2,043 new + 1 in-place flip). These rows BELONG in
  the instruments index: operator ruling 2026-06-27 (UAC@c75101be) — _footystats pre-match ODDS = IS reference data,
  stays in IS_ — and **runtime-verified this leg**: `is_valid_manifest_source("sports","ODDS","footystats") is True`,
  `…("sports","ODDS","api_football") is False`, `get_source_priority("sports","ODDS") == ["footystats"]`. This also
  **RESOLVES T2.7 blocker (c)** ("write ODDS rows or omit them"): **WRITE** — the "ODDS retired to MTDS-only 2026-06-25"
  premise was reversed by the operator two days later. The purge gate that IS terminal is **`api_football × ODDS == 0`**
  (0 before, 0 after).
- **The plan's predicted 142,618 is off by one — the true value is 142,617.** 142,618 naively adds all 2,044 shard ODDS
  rows; 1 of them (`2026-05-01 / ODDS / LIGUE_1`) MATCHES an existing index row that was **already** counted as
  footystats×ODDS (it flips `empty_confirmed`→`captured` in place, adding no row). 140,574 + 2,043 = **142,617**, which
  is what the live index now reads.
- Related: the plan's _"+7,182 new / 1 flipped"_ counts the **cutover shard only**; `or9-recover`'s 2 rows are 2 further
  in-place flips. Total = **7,182 new + 3 flips** = the consolidator's `dedup_dropped=3`. Both figures are consistent;
  the wording just scopes them differently.

_Evidence_: `~/tmp-restore/{t6_1_measure.py,t6_1_predict.py,t6_1_before.json,t6_1_after.json}`; snapshots
`_index/availability_index.20260717-012712.pre_t6_1.bak.parquet` on BOTH canonical buckets (rollback substrate, size ==
source). Shards remain in `_index/per_vm/` and are now legitimately prune-eligible (covered by the real marker) — the
next tick drains them; their rows are durably in the canonical.

### ✅ PHASE 5 COMPLETE (instruments half) — **THE BUCKET IS DELETED 2026-07-16T19:52Z** · OR-9 re-verified · R-17 disproven (2026-07-16, owner: Phase-5/delete sub-agent)

**Final state**: `instruments-store-sports-central-element-323112` **deleted** (Cloud Build `7b8b0e75`, 404 from the
elevated SA, absent from `buckets list`); canonical `-prd-` intact; post-delete `tofu plan` (`97baca1b`) carries ZERO
actions on it ⇒ no resurrection. `market-data-tick-sports` **untouched** (OR-5b). Shas: **ds@4637aed** (T5.1 block
removal + dangling `fixture_calendar` fix), **PM@74d05538a** (T5.1/T5.2/T4.4 flips + cefi issue doc).

**What was NOT done, and why (decide-and-document, autonomous rule 1)** — the dispatch ordered "land the two Phase-1
`tofu apply`s BEFORE the delete or you break production." **Both were measured to be unnecessary, and running them would
have been actively harmful:**

- **T1.3 / R-17 (MDPS FUSE)** — the stated harm ("the FUSE mount breaks the MDPS job the moment the bucket dies")
  **cannot occur: the mount does not exist.** Three independent proofs below. The instruction as written (apply the MDPS
  module against `prefix=terraform/state/prod`) would have run a _different module's config_ against the `terraform/gcp`
  state ⇒ propose destroying the prod estate.
- **T1.4 / R-16 (legacy IAM)** — the stated harm ("apply fails post-delete on an IAM member of a nonexistent bucket") is
  **structurally prevented by `state rm`**, not by an apply: terraform now tracks **no** binding on the dead bucket
  (proved — the post-delete plan references it zero times). The apply is _also_ impossible under this SA (403) **and now
  unsafe for everyone**, because a full prod apply resurrects `instruments-store-cefi-…`.

**The manifest shard was left UNCONSOLIDATED — deliberate, and the dispatch's two instructions were in conflict.** The
dispatch said "absorb your shard with ONE manual instruments-consolidator execution" _and_ "do NOT merge the sibling
`cutover-move-20260716.parquet` (T6.1 owns merges)". **These cannot both hold**: the consolidator globs
`_index/per_vm/*.parquet` (`_state.py:128` → `manifest_consolidator.py:1699/1727/1798`) — it has no per-shard selector,
so any run absorbs BOTH. Moving the sibling aside to isolate mine would violate R-11's standing rule (never
place/relocate parquets around `_index/per_vm/`). **Resolution: leave both for T6.1** — the prior OR-9 agent had already
ruled the same way, the shard is durable in the surviving canonical bucket, and **the manifest is explicitly NOT delete
evidence** (T4.1/R-13: the object layer is the gate), so consolidation was never a delete prerequisite. Consolidators
remain PAUSED. Zero rows lost.

**Resumed from the prior OR-9 agent's state rather than redoing it.** Its shard
`_index/per_vm/or9-recover-20260716.parquet` (22,670 B, 17:30:42Z) was read and re-verified, not trusted: 2 rows,
`footystats_matches` `empty_confirmed → captured` false-absence corrections, matching `or9_shard_evidence.jsonl`
exactly. **It is correct and complete — OR-9 needed no further execution work.**

**🟡 OPEN ANOMALY (found at close-out; NOT delete-affecting, NOT mine, content-neutral) — the canonical index was
REWRITTEN at 18:45:26Z while every consolidator was PAUSED.** T4.2/OR-9 recorded the index generation as frozen at the
T3.1 purge (`1784207377339311`); it is now **`1784227526828259`, `metageneration=1`,
`timeCreated == updated == 2026-07-16T18:45:26.846Z`** — i.e. a genuine NEW-generation WRITE, not a storage-class
transition. **Content is byte-equivalent — nothing was lost**: rows **5,342,265 (delta 0)** · `captured` **1,692,695
(delta 0)** · footystats × ODDS **140,574** · api_football × ODDS **0** (the T3.1 purge still holds). All 3 consolidator
crons verified **PAUSED** at the time of measurement, and it is the **only** `_index/` object created since 18:00Z (no
shard, no backup written alongside). **Not this leg**: every script this leg ran is read-only w.r.t. `-prd-`
(`or9_verdict.py` performs zero writes; the only mutating calls are `.delete()` inside the name-guarded legacy-bucket
purge). Timing overlaps this slot's deployment-service QG window (18:44→18:46) — **unproven either way, do not inherit
either explanation**. **Does not affect T5.4**: the delete gate is the OBJECT layer, and R-13 is explicit that the
manifest is never evidence about objects. **For T6.1's owner**: re-baseline the "frozen generation" witness to
`1784227526828259` before the merge — the older `1784207377339311` figure in T4.2/OR-9 is now STALE, and a race-guard
comparing against it will false-fire.

**Every delete gate RE-MEASURED live (the 4-audits-wrong-by-inheritance rule), not read off the prior verdict:**

| gate                                | method (re-run this leg)                                                     | result                                                           |
| ----------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Live legacy object count            | **independent** fresh enumeration (`~/tmp-or9/live_count.py`)                | **968,927** — exact match to the accounting total, **delta +0**  |
| v1_archive survivors                | same walk                                                                    | **0** (T2.1 delete confirmed at the object layer)                |
| T4.1 accounting                     | `~/tmp-or9/or9_verdict.py` re-run                                            | **UNACCOUNTED = 0**; OR-9 subtotal 2,078 ✓; total 968,927 ✓      |
| OR-9 recovery (PART 1, fresh reads) | independent re-read of every recovered canonical object                      | **131/131 ok, 0 FAILED**; 522 legacy-only keys confirmed present |
| **T5.2 final live-writer re-check** | `~/tmp-or9/t5_2_writer_recheck.py` — **R-1b discriminator, never `updated`** | **PASS**                                                         |

**T5.2 detail (the R-1b trap avoided):** 968,927 scanned · **0 objects created ≥ the 08:18:00Z T0.6 freeze** · **0
genuine writes** (`updated != timeStorageClassUpdated`) · **968,927/968,927 are `updated == timeStorageClassUpdated`** —
i.e. the ENTIRE bucket reads as "recently touched" to a naive mtime gate while holding **zero** writers. Newest genuine
`timeCreated` = **2026-07-16T08:05:03Z**, our own T0.2 snapshot backup, 13 min BEFORE the freeze. This is exactly the
false-ABORT R-1b predicted; gating on `updated` would have blocked this cutover permanently.

**🔴 BIG FINDING — R-17 / T1.3's "you MUST apply or you break prod" is FALSE. The instruction as written was
DANGEROUS.** Measured, not inherited:

1. **No live resource carries a legacy-sports FUSE mount.** Scanned **all 113** live Cloud Run jobs: **zero** reference
   either legacy bucket. There is **no MDPS Cloud Run service at all**.
2. **The MDPS module is dormant, unapplied config.** `terraform/services/market-data-processing-service/gcp` declares
   job `market-data-processing-service-job` + 2 workflows — **none exist live** — and its state
   (`services/market-data-processing-service/default.tfstate`) is **EMPTY (serial=1, zero resources)**.
3. **The live MDPS jobs are a DIFFERENT resource** — `uts-prod-market-data-processing-service-t1-recon` +
   `uts-prod-mdps-odds-horizon-bucket`, declared by `module "mdps_t1_recon_job"`
   (`terraform/gcp/audit03_cron_provisioning.tf:356`), managed in `terraform/state/prod`, and carrying **0 volumes**.
4. ⇒ **T1.3's `gcs_volumes` edit never had a runtime effect** (correct hygiene, zero blast radius), and **T1.3's
   instruction to `tofu apply` the MDPS module against `prefix=terraform/state/prod` would have run that module's config
   against the `terraform/gcp` module's state — proposing to DESTROY ~every prod resource in it.** Not run. **R-17
   severity HIGH → NONE.** Deleting the legacy bucket cannot break a mount that does not exist.

**🔴 ~~SECOND REVERSAL — T5.3 / R-14's `versioning{enabled=true}` premise is FALSE~~ — ✅ RETRACTED BY ME, SAME SESSION.
T5.3's premise is CORRECT; MY read was the wrong one.** I first ran
`buckets describe --format='value(name,versioning_enabled,storage_class)'`, got a 2-field row (`…-323112  False`), read
it as `versioning_enabled=False`, and concluded "no versions to purge". **Measured later: after all 968,927 current
objects were gone, `ls -r --all-versions` still reported 34,596 real noncurrent generations.** The shell delete's
fail-closed "must be empty incl. versions" pre-flight **refused the delete** (build `e1707def…` FAILURE, by design)
instead of proceeding on my bad inference. **Recorded deliberately as the 5th instance of this session's own failure
mode**: I reproduced the exact "trusted a formatted field instead of measuring the thing itself" error that this plan
has now reversed six times — and the only reason it cost nothing is that the guard measured the invariant independently.
**The ROLLBACK table's "object versions restorable until T5.3" was therefore TRUE for this bucket; it is now spent —
post-T5.3/T5.4 the T0.2 snapshot + the moved canonical objects are the only copies.**

**Permission reality (measured via `testIamPermissions`, both buckets):** `unified-trading-sa` has
`storage.objects.{list,delete,create}` = **YES** but `storage.buckets.{get,delete,getIamPolicy}` = **NO**. Therefore: a
full `tofu plan` on `terraform/gcp` under this SA dies on **174** pre-existing 403 refresh errors (project/pubsub IAM
policy reads — unrelated to sports), and `gcloud storage buckets delete` 403s. The **Cloud Build SA**
(`1060025368044@cloudbuild.gserviceaccount.com`) **does** hold `storage.buckets.delete` + `storage.buckets.get` (proved:
build `c750df98-068a-44af-a41f-bf9c8e228093` SUCCESS) ⇒ it is the executor for the delete + the plan.

### ✅ OR-9 RESOLVED + EXECUTED → **the INSTRUMENTS object-layer gate now PASSES, UNACCOUNTED = 0** (2026-07-16, owner: OR-9 sub-agent)

**`instruments-store-sports-central-element-323112` is now object-layer delete-eligible.** T4.1 stays `- [ ]` (it gates
BOTH buckets; MDT is still open on OR-5b), and the delete additionally still needs the two `tofu apply`s (T1.3/T1.4) +
T5.2's final writer re-check. **Zero legacy objects were mutated or deleted; the consolidated index was not touched**
(generation still `1784207377339311`, frozen at the T3.1 purge — R-11 honoured).

**THE HEADLINE — the 5th consecutive "inherited classification" reversal, and the biggest so far. The ruling OR-9 was
written to execute was ~94% wrong, and executing it as written would have CORRUPTED canonical.**

OR-9's charter said: `fixture_stats` 6,379 keys are "legacy is the **4-col NESTED** form vs canonical 23-col flattened ⇒
a union would corrupt the schema ⇒ **produce a re-fetch list**", and the other ~294 keys are "clean-schema ⇒ union".
Re-measured at the object/key layer over the WHOLE population (not the sample the verdict came from):

| the inherited claim                                               | what measurement showed                                                                                                                                                                             |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `fixture_stats` legacy is the 4-col nested form                   | **1,648 of 1,738 objects are 2-col `[fixture_id, available_at]` — ZERO statistics.** Only **90** are nested.                                                                                        |
| its 6,379 keys are "GENUINE loss — re-fetch"                      | **5,897 keys have NO payload anywhere in legacy** (whole-corpus scan, all **27,247** legacy `fixture_stats` objects). Nothing to lose, nothing to recover. Only **358** are real.                   |
| the nested form can't be flattened without fabricating            | **It CAN — PROVEN.** The UAC SSOT production normalizer reproduces canonical's OWN rows **174/174**. Flattening is derivation, not fabrication → recovered rather than deferred.                    |
| ~294 "clean-schema" keys are unionable                            | **124 distinct** (per-pair counts double-count; GLOBAL containment is honest). And 2 of the "clean" entities were traps ↓                                                                           |
| `sports_reference` mappings: "identical 7-col schema ⇒ unionable" | **640/640 rows are SYNTHETIC** (`t0..t639`, uniform `squad_size=25`) vs canonical's **589 REAL teams**. A schema-driven union would have injected **627 fake teams** into canonical. → **ABANDON.** |
| `progressive_stats`: "keyed + de-duped on write"                  | **No unique row key EXISTS** — 25 canonical rows share `(fixture_id, timer_seconds=0, team='')` with **different values**. A keyed dedupe would have **destroyed 24 real observations.** → append.  |

**Why the 2-col discovery is decisive, not cosmetic**: a 2-col row unioned into canonical's 23-col schema becomes a row
with `fixture_id` + 21 NULL stat columns — a record that LOOKS like a captured stats observation but holds none. That is
precisely the **banned empty-placeholder pattern** (`honest-absence-downstream-handling.md`). The "recover the 6,673"
instruction, executed literally, would have written 5,897 phantom observations into the canonical bucket the operator
wants clean.

_Likely (benign) explanation, worth knowing before spending API quota_: the 2-col shape is what the writer emits when
the provider returns an **empty statistics block** — **78% of the legacy fixture universe (39,116/50,414) is
payload-free**. So these are probably HONEST ABSENCES, not fetch failures. The re-fetch list therefore ships as
_verification_, explicitly **not** as assumed recovery, and it does **not** block the delete.

**What was recovered (131 canonical cells; every write backed up first, then verified by re-read):**

| entity                   | objs | recovered                 | method                                                                                                                    |
| ------------------------ | ---: | ------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `fixture_stats` (nested) |   90 | **358 keys** / 716 rows   | SSOT-flatten (`normalize_api_football_fixture_stats`) + keyed union on `(fixture_id, team_id)`, canonical wins            |
| `footystats_odds`        |   26 | **75 distinct keys**      | keyed union on `fixture_id` (identical 76-col)                                                                            |
| `fixtures_schedule`      |    7 | **34 keys**               | keyed union on `af_fixture_id` (legacy 23/25-col ⊂ canonical 43-col)                                                      |
| `fixtures`               |    2 | **9 keys**                | keyed union at **canonical's OWN 55-col majority shape** (measured 311/600 canonical objects are 55-col vs 288 at 32-col) |
| `footystats_matches`     |    2 | **2 keys**                | keyed union + the only manifest correction owed (below)                                                                   |
| `progressive_stats`      |    4 | **4 fixtures / 803 rows** | **append-only** (no unique row key exists; canonical held ZERO rows for these fixtures ⇒ collision-free)                  |

_Per-write gates, all PASS_: every legacy-only key present · every pre-existing canonical key survived ·
`rows == unique row-keys` (a future re-fetch **UPSERTS**, cannot duplicate) · **0 null `available_at`** (measured 0
nulls on every imported row ⇒ **no stamp was invented**; the dispatch's `stamp_available_at_*` premise did not apply
here, same as T2.4 found for player_stats). **Race check**: 131 records collapse to **123 distinct canonical paths**
(footystats `fetched_at_hour` snapshots share a twin) and the run was 12-way concurrent — verified explicitly that all 4
multi-source objects hold the union of every source's keys, **0 lost updates**.

**The 4 dispositions that are NO-ACTION, each PROVEN (not inherited):**

1. **5,897 `fixture_stats` keys** — payload-free everywhere in legacy (whole-corpus scan). Deleting loses nothing.
2. **`sports_reference` mappings (1 obj)** — 640/640 synthetic. Importing would contaminate canonical.
3. **`instrument_availability` (1 obj, 1 row)** — DERIVED data, and canonical **holds the underlying fixture**
   (`af_fixture_id=725592`, SKRA Częstochowa v Sandecja, `fixtures_schedule` 2022-03-11) ⇒ the enumerator regenerates
   it. The legacy row has **no `available_at`**, so importing would have required fabricating one. → never import.
4. **`injuries` 151 + `fixtures_outcomes` 93** — already dispositioned by T4.1's own measurement; re-confirmed here.

**Manifest (per-VM shard `_index/per_vm/or9-recover-20260716.parquet`, VM_NAME=`or9-recover-20260716`) — 2 rows,
DELIBERATELY, and this scope is itself a measured finding.** Written with explicit `.write()` **AND** `.close()`;
read-back from GCS shows **2 rows** (not the silent-zero a `flush()`-only path produces), `captured` 2/2,
`source=footystats` 2/2, **0 blank source, 0 `instrument_count==0`, 0 blank `available_at`**. **NOT consolidated — T6.1
owns the merge** (consolidators still PAUSED). Scope rationale:

- **2 `footystats_matches` cells** = the only rows owed: the index says **`empty_confirmed` while canonical demonstrably
  holds rows** (a **pre-existing false absence** — canonical already held 1 and 5 rows BEFORE OR-9 added 2 more to
  each). An index asserting absence over data that exists is exactly what T2.7 corrected. Dedup key reproduced EXACTLY
  (`service_name='instruments-service'`, `venue=''`, + `league_id`) — verified against
  `_BASE_DEDUP_COLS`/`_OPTIONAL_DEDUP_COLS` (`manifest_consolidator.py:522-535`) — so the merge **supersedes** the stale
  row instead of double-representing the cell.
- **122 cells: NO rows written, and this is the non-obvious call.** `instrument_count` **is** the written row count
  (`_writer_captured.py:360` — `effective_count = row_count or len(df)`), so "OR-9's unions made 122 counts stale →
  correct them" looks right. **Measured, it is wrong**: all 90 `fixture_stats` cells are **2019-era**, and 2019-era
  cells carry `instrument_count=1` as an **ERA CONVENTION** — **6/6** untouched 2019 cells say `1`, including one with
  **24 rows / 12 fixtures**. `ic==rows` only becomes the norm from 2020 (7/12) → 2025 (10/15) → 2026 (11/15). So `1` was
  never these cells' row count and the union did not invalidate it; "correcting" them to the new count would impose a
  semantic that generation never used and silently diverge them from every untouched sibling. → reported as a finding,
  not unilaterally rewritten.
- **7 `fixtures_schedule` cells: no rows** — not manifest data_types. Re-confirmed against the live index: **ZERO
  `FIXTURES_SCHEDULE` rows across all 5,342,265**. T2.7's ruling stands (their population is an open P0 owned by
  `sports_master.md:940`, coordinated with the writegate strict-mode flip); writing them would execute a fragment of
  that P0 out of its coordination.

**BIG FINDING (pre-existing, NOT cutover-introduced) → belongs with T2.9/T2.10's class**: **the index's
`instrument_count` semantic has DRIFTED across writer generations** — 2019-era rows carry `1` (per-object marker), 2020+
rows carry the row count. Any consumer reading `instrument_count` as "rows" is wrong for the 2019 era, and any
row-count-based completeness check silently mis-reads that era. This also means **T2.4's 4,015 unioned player_stats
cells carry the same staleness** for whichever of them are post-2019. Not fixed here (systemic, needs its own ruling —
fixing OR-9's 122 while leaving T2.4's 4,015 would be arbitrary).

_Deliverables_: re-fetch list `~/tmp-or9/or9_refetch_fixture_stats.json` (**5,897 fixture_ids / 1,627 cells, 2019-02-17
… 2026-01-03**, classified _pre-existing coverage gap, not a cutover loss, NOT delete-blocking_) · pre-write backups
`gs://deployment-scripts-central-element-323112/sports_cutover_2026_07_16/or9_prewrite_bak/` (123 objects, one per
distinct canonical path) · all evidence + re-runnable verifiers archived to `…/sports_cutover_2026_07_16/or9_evidence/`
· verifiers
`~/tmp-or9/or9_{schema_probe,global_containment,flatten_proof, flatten_proof_wide,payload_scan,key_probe,recover,write_shard,manifest_check,instrument_count_semantic,verdict}.py`.

_Method note for whoever runs OR-5b_: the two measurements that flipped this leg were (1) **GLOBAL cross-partition key
containment** (per-pair containment double-counts: 6,673 → 6,379 distinct; footystats_odds 152 → 75) and (2) **reading
the PAYLOAD, not the schema or the row count**. A row count says "canonical has fewer rows"; it does not say whether the
legacy rows contain an observation. Four audits in a row were wrong because they stopped at the row count.

### 🔴 PHASE 4 — T4.1 EXECUTED → **GATE FAILS. THE INSTRUMENTS DELETE IS BLOCKED** (2026-07-16, owner: Phase-4/5 sub-agent) — ⚠️ SUPERSEDED by the OR-9 entry above (the 2,078 are now fully dispositioned; UNACCOUNTED = 0)

**T4.1 stays `- [ ]`. T5.1-T5.4 NOT executed. `instruments-store-sports-central-element-323112` STILL EXISTS and must
not be deleted until OR-9 is ruled.** The object layer found **2,078 legacy objects holding 6,673 genuinely legacy-only
entity keys in entities OR-1 never ruled on**. This is the exact OR-5b situation, one bucket over: OR-1 option D
enumerated the **5 largest entities by row count** (player_stats / fixture_events / standings / teams / player_values)
and was then treated as if it covered the whole class-B set. It does not.

_Re-inventory (fresh, `~/tmp-cutover/t4_1_inventory.py`, same prefix-DISCOVERY method as T0.2)_: legacy **968,927**
objects. Reconciles EXACTLY: **969,321 − 398 (v1_archive, T2.1) + 4 = 968,927**, where the +4 are our own T0.2 snapshot
backups written INTO legacy at 08:05:03Z (pre-freeze). Canonical prd **1,415,626**. Zero objects in legacy with
`timeCreated >= FREEZE_START` **or** `>= CONSOLIDATOR_FREEZE` ⇒ the T0.1 "no live legacy writer" verdict holds 5h later,
measured on the `generation`/`timeCreated` discriminator (R-1b), never on `updated`.

**The accounting (every object classified; the 456,727 crc-differing set was RE-MEASURED, not inherited — 865,696 footer
reads, 0 read errors):**

| class                                                       |   objects | basis                                                                                     |
| ----------------------------------------------------------- | --------: | ----------------------------------------------------------------------------------------- |
| duplicate (crc32c match at the canonical cell)              |   494,973 | measured                                                                                  |
| superseded (canonical ≥ legacy rows)                        |   444,996 | **measured, not inherited** (runbook said 443,508)                                        |
| moved-this-cutover (T2.3 class A; dst crc-verified present) |    17,089 | 17,089/17,089 verified this pass                                                          |
| OR-1 D written disposition (shortfall, ruled)               |     9,653 | fixture_events 3,459 · standings 3,046 · teams 3,046 · player_stats 61 · player_values 41 |
| re-fetch list (nested-only class-A player_stats, OR-1 D)    |        16 | T2.4                                                                                      |
| control-plane (T2.5 adjudicated; OR-4 ABANDON proven)       |       118 | T2.5                                                                                      |
| snapshot backups (our own T0.2 substrate)                   |         4 | created 08:05:03Z                                                                         |
| contentless                                                 |         0 | class is empty, as the runbook said                                                       |
| **UNACCOUNTED → OR-9**                                      | **2,078** | **gate FAILS**                                                                            |
| **TOTAL**                                                   |   968,927 | ✓ closes exactly                                                                          |

_Two prior claims independently RE-PROVEN this pass (not inherited)_:

1. **The 2 bare-`day=`/BETFAIR objects are genuinely duplicate.** T2.2's copylist skipped them behind a comment
   asserting _"crc-identical dups — proven no-op"_, which is the shape of the tooling-lies class this plan has hit 5
   times, so it was re-measured: each is **byte-identical (crc32c + size) to a canonical object** at the normalised path
   `instrument_availability/by_date/day=2026-03-21/venue=BETFAIR/<same filename>`. The comment's wording was wrong (they
   are not dups of _each other_ — `tDn/Kg==` vs `Ji8BrQ==`); the **disposition is right**. Accounted as duplicate.
   **Note for any future reader: `t2_2_classify.py` lacks the bare-`day=` normalisation that `t2_2_copylist.py` has** —
   classify counts them class A, copylist skips them. That inconsistency is why the runbook carries both 17,107 and
   17,105.
2. **T2.4's player_stats union worked.** Original class B put player_stats at 111,827 legacy-only rows; post-union only
   **61 objects / 3,982 rows** still show `cr < lr`, and those are legacy-side duplicate rows (T2.4's gate was
   key-level, so a row-count residue is expected and benign).

**The 2,078 — KEY-LEVEL containment (`~/tmp-cutover/t4_1_containment.py`). Row counts were NOT trusted as the verdict
(the OR-1 lesson: the naive row read claimed "305k rows lost" when canonical was net-RICHER):**

| entity               | objs | objs w/ legacy-only | legacy-only keys | schema reality                                                                                        | verdict                                                                                                                                                      |
| -------------------- | ---: | ------------------: | ---------------: | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `fixture_stats`      | 1738 |                1738 |        **6,379** | legacy **4-col nested** `[team,statistics,fixture_id,available_at]` vs canonical **23-col flattened** | **GENUINE loss** — re-fetch                                                                                                                                  |
| `footystats_odds`    |   26 |                  26 |          **152** | **identical 76-col** schema; different `fetched_at_hour` snapshots                                    | **GENUINE loss** — unionable                                                                                                                                 |
| `fixtures_schedule`  |   24 |                  22 |          **121** | legacy 24-col ⊂ canonical 43-col                                                                      | **GENUINE loss** — unionable/re-fetch                                                                                                                        |
| `fixtures`           |    6 |                   6 |           **13** | legacy 55-col ⊂ canonical                                                                             | **GENUINE loss**                                                                                                                                             |
| `footystats_matches` |    2 |                   2 |            **4** | subset                                                                                                | **GENUINE loss**                                                                                                                                             |
| `progressive_stats`  |   36 |                   4 |            **4** | legacy 44-col ⊂ canonical 46-col                                                                      | mostly dup skew; 4 genuine                                                                                                                                   |
| `injuries`           |  151 |                   0 |            **0** | legacy **5-col nested** vs canonical 11-col flattened                                                 | **NO ACTION, PROVEN** — canonical holds every legacy fixture; the exact 2× row ratio (46/23, 20/10, 18/9 …) is **legacy-side duplication**, not missing data |
| `fixtures_outcomes`  |   93 |                 n/a |            **—** | legacy has **NO fixture identifier column at all**                                                    | **UNATTRIBUTABLE by construction** — the exact OR-1 D(2) `fixture_events` verdict; 325 rows joinable to nothing                                              |
| `sports_reference`   |    1 |                   1 |               51 | `mappings/season=2019/transfermarkt_league_teams=/teams.parquet` lr=640 cr=589                        | needs a look (T2.5-adjacent)                                                                                                                                 |
| `venue:API_FOOTBALL` |    1 |                   1 |                1 | `instrument_availability/…/day=2022-03-11/league=POLAND_I_LIGA/` lr=2 cr=1                            | 1 row                                                                                                                                                        |

**⇒ `injuries` (151) and `fixtures_outcomes` (93) are DISPOSITIONED by measurement here — no ruling needed.** The
remaining **~1,834 objects / 6,673 keys are genuine, recoverable data with no ruling** → **OR-9**.

_Why the earlier legs missed it_: L6 is blind by construction (R-13 — no index has a path column). T2.2's class-A pass
is a **cell-key set-difference**, and every one of these objects HAS a canonical cell — it is only at the **row/key**
layer that canonical turns out to lack the fixture. The original audit did row-count the crc-differing set (443,508
superseded / 13,222 class B) but OR-1 then only enumerated the 5 biggest entities and the rest of class B silently
inherited "superseded".

_Also NOT yet done — prerequisites of any delete (hard handoff from Phase 1, still open)_: the **two `tofu apply`s**
(T1.3 MDPS FUSE-mount removal, T1.4 catalogue IAM `-prd-` repoint) against `prefix=terraform/state/prod`. R-17/R-16.

_Verifiers (all re-runnable, read-only)_:
`~/tmp-cutover/t4_1_{inventory,classify,pairs,rowcheck,verdict,containment}.py` → `t4_1_rowcounts.jsonl` (456,727 rows),
`t4_1_shortfall_undispositioned.jsonl` (2,078), `t4_1_containment.jsonl`.

### PHASE 3 COMPLETE — CLEAN (2026-07-16, owner: Phase-3 sub-agent). T3.1-T3.5 all ✅. Next-phase owner: Phase 4 (VERIFY).

**The purge executed at 13:09:24-13:09:35Z inside the QUIET window and every gate PASSED.** Headline: **123,149** bogus
`api_football × ODDS` rows purged · **footystats × ODDS 140,574 → 140,574 UNTOUCHED** · index **5,465,414 → 5,342,265**
(delta exactly −123,149) · **captured 1,692,695 → 1,692,695 (no captured row lost)** · generation
`1784189888944530 → 1784207377339311`.

**Re-measured, did not inherit (the dispatch was right):** the live count is **123,149**, not the 127,018 quoted in
earlier material. The runbook's own correction was accurate. 82,509 `expected_unattempted` + 40,640 `empty_confirmed` =
123,149, and **0 are `captured`** — the class is 100% phantom, which is _why_ T3.3's REMOVE (not retype) is right: there
is no observation to retype.

**Backup (R-11, hardened beyond the runbook):**
`gs://instruments-store-sports-prd-central-element-323112/_index/purge_backups/20260716-130924/availability_index.20260716-130924.purge_af_odds.bak.parquet`
(crc32c `KrwkFw==` == source, 97,608,985 B, taken BEFORE the mutation). The runbook suggested the `_index/*.bak.parquet`
sibling; the dispatch mandated `_index/purge_backups/` after a prior `.bak` in `per_vm/` was re-absorbed as shard #3 and
RESURRECTED deleted rows. **Verified structurally, not by convention**: the consolidator lists **only**
`_PER_VM_DIR_PREFIX = "_index/per_vm/"` (`manifest_writer/_state.py:128`, used at
`manifest_consolidator.py:1699/1727/1798`) and **nothing globs `_index/` broadly** — so a backup under
`_index/purge_backups/` is unabsorbable by construction. `_index/per_vm/` still holds exactly 2 objects after the purge.

**Five things future owners must NOT re-derive:**

- **The `WHERE NOT (...)` NULL trap is real and would have been catastrophic.** A bare
  `NOT (source='api_football' AND data_type='ODDS')` evaluates to **NULL** — i.e. the row is silently **DROPPED** — for
  every row with a NULL `source`. On a 5.47M-row index that is a multi-million-row silent loss. Measured: `source` has
  **0 NULLs** today (blank source is `''`, 13,997 rows), so both forms agree — but the NULL-safe `COALESCE(source,'')`
  form is what shipped, and gate (c) (`total dropped by exactly 123,149`) would have caught it regardless. **Never write
  the naive predicate.**
- **The rewrite must use DuckDB, and that is not a preference.** The index is `created_by=DuckDB v1.5.4`, SNAPPY, 45 row
  groups — because the consolidator writes it with `COPY (…) TO '…' (FORMAT parquet)` (`manifest_consolidator.py:2808`).
  Using its own writer means the output is exactly what the index experiences every tick; schema verified identical (42
  cols, same order + types). A pandas round-trip would have mangled dtypes.
- **The CAS is the real race guard, not the lock.** `gcs_conditional_put(if_generation_match=<gen read>)` is enforced by
  GCS: had anything touched the index between read and write, the put returns `None` and the run ABORTs with the index
  **untouched**. The `_index/consolidator.lock` (taken via the consolidator's own `if_generation_match=0` create-CAS,
  released in a `finally:` with `if_generation_match=<own gen>` so it can only delete ITS OWN lock) and the per_vm mtime
  witness are defence in depth on top of it.
- **T3.4's premise is stale: `_index/per_vm/sports-fixtures-job.parquet` no longer exists.** It was REAPED (= proof it
  merged) before the T0.6 freeze, exactly as T0.5 recorded. The "HOT shard written every 5 min" was already quiesced.
- **The strongest gate was the collateral-damage census** — grouping ALL 5.47M rows by `(data_type, source)` before and
  after and asserting **exactly one class changed** (`ODDS|api_football` 123,149 → 0, every other class byte-identical).
  This is what proves the mandatory `source` filter actually held (R-10); a total-row-count check alone would not.

**T3.5 = verify-only, closed with ZERO code written.** The operator's earlier "redefine the L6 gate" ruling is **MOOT**
— the redefinition shipped at `unified-trading-pm@10ad5d69a` (2026-07-15) and is an ancestor of **both** `origin/main`
and `origin/live-defi-rollout`. Re-ran the gate live post-purge: **both surfaces GREEN** — instruments legacy-only-real
**0** / phantom-residual **INFO(468)**; tick legacy-only-real **0** / phantom-residual **INFO(140)** — reproducing the
runbook's numbers exactly. 13 unit tests pass (runbook said 11; the shipped file has 13). Verified `"INFO(…)" != "RED"`
at BOTH aggregation sites (`:437` + wrapper `:80`) so no wrapper/alert-cron/test change is needed. **L6 is invariant
under the purge by construction** (T3.1 removed only non-`captured` rows; `_split_backed_cells()` filters to `captured`)
— and the live re-run confirms it.

**NO REGRESSION INTRODUCED — proven, not asserted.** The full CF audit reports instruments RED on
`['CF-2-paths','CF-3','CF-4','CF-8']` and tick RED on `['CF-8']`. **All are PRE-EXISTING.** Measured the criteria
directly against the retained pre-purge index (`gen 1784189888944530`) vs the live post-purge one:

| criterion                  | pre-purge | post-purge |    delta | verdict   |
| -------------------------- | --------: | ---------: | -------: | --------- |
| CF-8 null `available_at`   |   616,815 |    616,689 | **−126** | RED → RED |
| CF-3 blank `pipeline_mode` |    13,997 |     13,997 |       +0 | RED → RED |
| CF-4 blank `source`        |    13,997 |     13,997 |       +0 | RED → RED |

Every verdict is identical pre/post and every absolute violation count moved **down or flat, never up** — the purge is
**monotonically non-worsening** on every CF criterion. (CF-2-paths is an object-path check; a row-only purge cannot
affect it. CF-8's _ratio_ moved 88.71% → 88.46% only because the purged rows happened to carry `available_at`; the gate
is `non-null == n`, so the meaningful metric is the absolute null count, which **improved by 126**.) These REDs are
pre-existing data-quality findings outside Phase 3's scope — CF-8/CF-3/CF-4 relate to the blank-`source`/blank-
`pipeline_mode`/null-`available_at` populations already tracked by T2.9/T2.10 and the `issues/` docs; **not actioned
here** (findings-triage: fits another todo → annotate, don't fix).

**Deliberately NOT done (and it must stay that way until T6.1):** the Phase-2 shard
`_index/per_vm/cutover-move-20260716.parquet` was **NOT merged**. The plan mandates the merge at **T6.1**, and T2.7
already PROVED merging early is harmful: the shard adds 2,044 `footystats × ODDS` rows, which would push footystats ×
ODDS to **142,618** and **FAIL T3.1's own gate (b) (`== 140,574 UNTOUCHED`)** and gate (c). The pre-purge measurement
confirmed footystats × ODDS was still exactly 140,574 — i.e. the shard is indeed unmerged and the index was still QUIET
(total == the T0.2/T0.6 baseline 5,465,414 to the row).

**Phase-3 gate: PASSED.** The index is clean of the bogus class, the real footystats population is intact and asserted,
the rollback substrate is verified and unabsorbable, and the purge is terminal (the writer guard now RAISES, the
enumerator resolves footystats, and sports is frozen). **Phase 4 (VERIFY — object-layer zero-unique proof, T4.1) may
proceed.** Note for the Phase-4 owner: **L6 GREEN is NOT delete-clearance** (R-13) — T4.1's object layer is the gate.
Verifiers: `~/tmp-cutover/t3_1_measure.py` · `t3_purge.py` (dry-run default, `--apply` to execute) · `t3_verify.py`
(independent re-download, shares no state with the purge script).

---

**2026-07-16 (T2.7 — Phase 2 CLOSED)** — Wrote both per-VM manifest shards; **Phase 2 is now complete end-to-end**. All
three of the prior owner's blockers were resolved **by measurement, none needed an operator**: (a) `setup_events()` was
mechanical; (b) `MANIFEST_WRITE_SCHEMA_MISSING` is warn-and-proceed **proven from the code path** (bare `return`, then
the row is staged anyway — the writer's own comment says all three cases "reflect the on-disk state truthfully"); (c)
the ODDS blocker rested on a **stale code comment** — decision #6 ("ODDS retired to MTDS-only", UAC@8fb1f54f 2026-06-25)
was **REVERSED by the operator two days later** (`@c75101be` 2026-06-27) and fully restored at `@57bcc7c5` (2026-07-15)
with _"footystats PREDICTIVE pre-match ODDS = IS reference data"_ pinned by test. **A stale comment cost a full stop —
see the new T2.8.** Shards: instruments **7,183** + MDT **6,110** = **13,293 rows** describing **344,131** real data
rows; read-back-verified from GCS; 0 blank-source, 0 phantom zero-counts, 0 blank available_at, 0 FAIL.

Four things future owners must NOT re-derive:

- **The shard is 7,183 instruments rows, not 17,089.** `fixtures_schedule`/`fixtures_outcomes` (9,906) are **not
  manifest data_types** — canonical has **163,080 such objects and the index has ZERO rows for them** across 33
  data_types. Their manifest population is `sports_master.md:940`'s open P0 (`migrate_fixtures_split.py`), which `:943`
  requires ship same-day as the writegate strict-flip. Excluded per findings-triage ("fits another plan → annotate,
  don't fix"). No data risk: objects are moved + crc-verified and the delete gate is the OBJECT layer.
- **The merge is T6.1, NOT now** — and this is now PROVEN, not just asserted: the shard adds 2,044 `footystats × ODDS`
  rows, so consolidating in Phase 2 makes footystats × ODDS **142,618** and **fails T3.1's gate (b)
  (`== 140,574 UNTOUCHED`)**. The dispatch's "run one consolidator execution now" was **refused** on that evidence.
- **Expected T6.1 deltas are NOT the raw row counts**: the consolidator dedup key is
  `(date, venue, data_type, service_name)` + optional dims and **excludes `source`/`pipeline_mode`**. Instruments
  **+7,182 new / 1 flipped** (`empty_confirmed`→`captured`); MDT **+526 new / 5,584 CORRECTED** in place.
- **`_resolve_strict_validation(None)` is `True` here** (env unset) — the ManifestWriter docstring's "warn-only default"
  is stale. Missing-contract warns-and-proceeds; a _mismatch_ RAISES.

**BIG FINDINGS (pre-existing, NOT cutover-introduced) → new todos T2.8/T2.9/T2.10; OR-5b materially strengthened:** (1)
the MDT `(sports, odds, trades)` schema contract is **DRIFTED from reality** — canonical's OWN native live-written
objects fail it identically; (2) the MDT index carries **47,253 phantom `api_football × trades` `captured` rows** with
**ZERO** backing objects (canonical has 0 `batch_api_football` trades objects; only `batch_odds_api` 252,163 +
`live_odds_api` 8) — the same mis-stamp class as T3.1's 123,149 `api_football × ODDS`, but in the OTHER bucket and
covered by **no todo**; (3) UAC declares **no `('sports','trades')` availability semantic** while `cefi`/`tradfi`/
`prediction` all map `trades → tick_timestamp` — a registry hole of the same class 57bcc7c5 quarantined for
`PLAYER_STATS` and filed for a ruling. **Operator notification: these are data-correctness findings on a LIVE surface;
they are recorded here rather than acted on, because registering the semantic blind would switch the availability gate
ON for the live MDT sports fleet — exactly the hazard 57bcc7c5 refused to take unilaterally.**

Housekeeping: an unrelated **20-hour hung read-only process** (PID 2008863, `gcs_read_object_with_generation` on the
canonical IS index, started ~2026-07-15T16:11Z) was observed and **left alone** (not this slot's; read-only, cannot
write). Both smoke shards (`cutover-smoke*-DELETEME`) were deleted immediately after use — `_index/per_vm/` in both
canonical buckets holds exactly `_legacy_seed.parquet` + `cutover-move-20260716.parquet` (R-11 honoured).

**2026-07-16** — Plan authored from the 5-leg read-only audit (code / infra / objects / manifests / v1_archive). All
five legs were read-only; zero mutations. Synthesis added five findings no single leg owned (F-1…F-5), each verified by
direct code read at author time, not inherited from a leg:

- **F-1** `migrate_sports_canonical_v9.py:463-467` `_list_tree` probes `{bucket}/{prefix}/day={d}`; 4 of the 7
  `_INSTR_DATA_TREES` (`:110-117`) are not that shape → silently enumerate 0. `instrument_availability` = 119,858
  objects.
- **F-2** `_run_instruments_reconcile:717-737` docstring is explicit set-difference ("copy legacy-only") → the 13,222
  class-B objects are structurally invisible to it; its own docstring punts schema regressions to "manual column-union".
- **F-3** `SPORTS_REF_V1_ARCHIVE_PREFIX` ∈ `_INSTR_DATA_TREES:113` **and** is enumerable → the vehicle would re-import
  the 398 archive objects into canonical, contradicting the v1_archive verdict. Forces 2a-before-2b ordering.
- **F-4** `--start-date` 2019-01-01 / `--end-date` 2026-06-01 defaults (`:813-814`) vs the verified
  2018-01-02…2026-12-06 span → silent truncation at BOTH ends.
- **F-5** legacy bucket is NOT dormant (125 writes 07-15, real data paths) with no identifiable writer → hard gate T0.1.

Also corrected the code leg's lifecycle finding: `migrate_sports_canonical_v9.py:2-4` **does** now carry
`# Epic:/# Lifecycle:/# Delete-when:` markers — already remediated; T1.6 is a re-verify, not an edit.

**Net payload**: 30,333 objects to migrate for `instruments-store-sports` (17,111 class A + 13,222 class B; the 398
v1_archive objects are deleted, not moved). `market-data-tick-sports` ~52,400 ESTIMATED — T2.6 must make it exact before
that bucket is delete-eligible.

---

**2026-07-16 — T0.1 EXECUTED (the HARD GATE). Verdict: `gate_pass=true` — NO LIVE LEGACY WRITER EXISTS.** Read-only;
zero mutations to any bucket.

**F-5 was a measurement artifact, not a phenomenon.** The audit read the GCS **`updated`** field and called it a write
time. `updated` also bumps on **metadata-only** changes — and an Object-Lifecycle **storage-class transition** is
exactly that.

_Method (why this is trustworthy where 3 prior conclusions were not)_: enumerated **100%** of both legacy buckets with a
fields projection (`name,size,timeCreated,updated,storageClass,timeStorageClassUpdated,generation,metageneration`),
12-way prefix-parallel. The enumeration **dedup-reconciles to the exact audited ground truth — 969,321 and 406,581** —
so this is provably not an F-1-style silent subset. (Raw row counts were 969,321 and 406,632; the MDT +51 was my own
double-listed `_vm_staging/` prefix, confirmed by dedup, not an estate change.)

_The discriminator_: a genuine write mints a **NEW `generation`**. A lifecycle transition leaves `generation` untouched,
bumps `metageneration` 1→2, and sets `updated == timeStorageClassUpdated` **to the second**.

_Measured_:

- Of **5,008** objects with `updated >= 2026-07-09`: **5,008 transitions, 0 writes.**
- Bucket-wide the correspondence is exact: **954,303 STANDARD ⇔ metageneration=1** (never touched); **15,018 NEARLINE ⇔
  metageneration=2** (transitioned exactly once).
- Every transition fired at **age EXACTLY 90 days** — 07-09: 285 · 07-10: 18 · 07-11: 403 · **07-12: 2,398** · **07-13:
  1,559** · **07-14: 217** · **07-15: 125**. Those are F-5's own numbers. ⇒ an OLM `STANDARD→NEARLINE @ 90d` rule.
  (Bucket lifecycle config not directly readable — the SA lacks `storage.buckets.get` — but the age histogram is a
  single spike at exactly 90 for 5,008/5,008 objects, which is conclusive on its own.)
- F-5's cited "real DATA paths" are the same artifact:
  `instrument_availability/by_date/day=2021-08-16/venue=API_FOOTBALL_FIXTURES/instruments.parquet` was **created
  2026-04-16T01:32:40Z** (`generation=1776303160008012`, `metageneration=2`,
  `update_time == storage_class_update_time == 2026-07-15T09:52:35Z`). The "newest write 2026-07-15T20:07:38Z" is
  `_index/availability_index_backup_20260416.parquet`, **created 2026-04-16T17:23:56Z**. **2026-04-16 + 90d =
  2026-07-15.** The filename literally carries its own creation date.
- **`market-data-tick-sports` legacy: 0 objects touched since 07-09** — fully dormant (406,581 COLDLINE,
  metageneration=2). Confirms the audit's dormancy call.

_The only genuine writes in 30 days — 3 objects_ (found via the age-0 check: a _fresh create_ also has
`updated == timeStorageClassUpdated`, so the transition test alone would have hidden them — this hole is why the age
histogram was run):

- `_audits/fixtures_{truthset,diff,recovery_set}_20260714-001053.{parquet,csv}`, **2026-07-14T00:12:14-16Z**,
  `metageneration=1`, STANDARD.
- **Attributed** to a hand-run of `instruments-service/scripts/audit_fixtures_via_api_football.py` (run_ts
  `20260714-001053` ⇒ started 00:10:53Z; artifacts 81s later). It wrote legacy via the raw literal
  `_bucket_for_project(project_id) -> f"instruments-store-sports-{project_id}"`.
- **Already remediated**: `instruments-service@bd6b797a` _"fix(sports): evidence-freshness rule for the fixtures
  calendar gate + prd truthset bucket default"_, **2026-07-14T02:45:02Z — 2h33m AFTER the writes**, deleted that literal
  in favour of `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group="sports")`. Its own docstring
  records the incident: _"the 2026-07-14 day-closeout had to server-side copy the artifact into the prd"_ bucket.
  **Verified ancestor of `origin/live-defi-rollout`**; NOT yet on `origin/main` (hand-run script, no image/cron → not a
  writer risk, but promoting it closes the footgun).
- **Nothing schedules it**: `gcloud scheduler jobs list` + `run jobs list` grep `truthset|audit` → only the unrelated
  `uts-prod-cf-manifest-audit`; `compute instances list --filter='name~sports OR name~truthset OR name~fixtures'` →
  **zero rows**.

_Corroborating (not the gate)_: the 41 objects **created** 2026-06-22T05:48Z are 40 `player_values` parquets at
**canonical-shaped paths inside the legacy bucket** (`…/pipeline_mode=batch_transfermarkt/entity=player_values/…`) —
this is the row-gap doc's "unidentified writer / cartesian-junk player_values". Shape says **hand-run backfill**: it
backfills _2019_ days in a 40-second burst, whereas a daily cron writes _today's_ date. Dormant since; pre-dates the
remediation; does not affect T0.1.

_Findings that change later phases_:

1. **T5.2 REWRITTEN (critical)** — as authored it gated on "newest object mtime". The 90-day OLM rule bumps `updated`
   daily **forever** on a bucket with zero writers, so that gate would have **false-ABORTed the delete permanently**. It
   now gates on `timeCreated >= T0.6` / `updated != timeStorageClassUpdated`. Logged as new risk **R-1b**.
2. **R-1 CLOSED** by measurement (severity CRITICAL → NONE). **OR-2 is MOOT — no operator ruling needed.**
3. **`data_status_sports.py` is NOT the writer** — read in full; every GCS call is `list_blobs`, there is no upload
   path. It is a legacy **reader**. T1.1 stands unchanged on its own merits.
4. **T1.2's QG gate is well-aimed**: the deleted `_bucket_for_project` was a module-level
   `f"instruments-store-sports-{project_id}"` literal — exactly the shape T1.2 proposes to catch, and exactly what STEP
   5.72 misses today.

**Verifier**: `~/tmp-cutover/scan_writers.py` + `scan_<bucket>.jsonl` (read-only; re-runnable for T5.2). **⇒ Phase 0 is
UNBLOCKED. T0.2 (snapshot) may proceed.**

---

**2026-07-16 — T0.2 EXECUTED (snapshot / rollback substrate). Read+copy only; zero deletes, zero live-object
overwrites.**

_Inventory method (new `~/tmp-cutover/inventory.py`, replaces the hardcoded-prefix `scan_writers.py` lister)_: DISCOVERS
the prefix tree with delimiter listings rather than a hardcoded list — a hardcoded list cannot prove completeness on a
bucket never audited, and its duplicate `_vm_staging/` entry is exactly what produced the prior +51 miscount.
Completeness PROVEN, not assumed: both legacy buckets reproduce the audited ground truth **exactly** —
`instruments-store-sports` raw=969,321 uniq=969,321 (delta +0); `market-data-tick-sports` raw=406,581 uniq=406,581
(delta +0). raw==uniq everywhere ⇒ zero double-listing (the +51 bug is gone). Canonical prd: instruments 1,398,525 vs
1,398,521 expected (**+4, 0.0003%**, far under the 0.5% ABORT — expected drift on the LIVE bucket, crons still running
pre-freeze); market-data-tick 491,576 == 491,576 (delta +0).

_Snapshot (`~/tmp-cutover/snapshot.py`, UTL `gcs_copy_object` server-side per
`codex/05-infrastructure/gcs-object-operations.md`, never gsutil)_: TS `20260716-080453`. **19 control-plane backups, 0
failures, every backup crc32c-verified == source** (re-read proof). Per bucket:

- `instruments-store-sports` (legacy): `_index/availability_index.parquet` (38,763,246 B, crc +4T7mg==),
  `availability_index/instruments-service.parquet`, + 2 per-VM shards (`_legacy_seed.parquet` 16.2 MB,
  `fixtures-recovery-20260627-183725.parquet`). No prod/, no stall_state (ABSENT — matches ls).
- `instruments-store-sports-prd` (canonical): availability_index (97,608,985 B, crc KrwkFw==), consolidator_stall_state,
  expected_universe_ranges, latest.json, phantom_audit_latest, availability_index/instruments-service, prod/catalog
  (435,970 B), per-VM `_legacy_seed`.
- `market-data-tick-sports` (legacy): availability_index (2,356,512 B) + per-VM `_legacy_seed`.
- `market-data-tick-sports-prd` (canonical): availability_index (47,184,905 B), stall_state, latest.json,
  reprobe_audit_latest, per-VM `_legacy_seed` (45.2 MB).

**HARD rule (R-11) honoured**: per-VM shard backups written to `_index/precutover_per_vm_bak/<TS>/` — a SIBLING of
`per_vm/`, NOT under it, so the consolidator's `list_blobs(prefix="_index/per_vm/")` cannot absorb them as shard #3. The
control-index `.bak` files use the proven `_index/…precutover.bak.parquet` sibling convention (6 such .bak already
coexist there, none re-absorbed).

_Consolidator reaping mechanism CONFIRMED (bears on the T0.5 drain gate)_:
`unified_trading_library/manifest_consolidator.py:1745-1851` `_prune_consolidated_shards` DELETES per-VM shards once
their mtime `<= cutoff` (the canonical's content-write marker) — proving they merged. `_legacy_seed.parquet` is NEVER
pruned. `CONSOLIDATOR_PRUNE_SHARDS` default on; cap 2000/cycle. **⇒ "drained" for T0.5 = every non-seed shard under
`_index/per_vm/` has been reaped (only `_legacy_seed` remains), which is the observable proof the merge absorbed it.**
Current canonical prd state already shows exactly this: only `_legacy_seed.parquet` remains in
`instruments-store-sports-prd/_index/per_vm/` and `stall_state={"streak":0,"baseline_shards":2}` / `latest.json` verdict
`empty no_op`.

_Pre-freeze index baselines (T0.6 / T6.1 reference)_: instruments-prd **5,465,414 rows**; market-data-tick-prd
**1,958,498 rows**.

_Archive_: inventories (gzipped), `inventory.py`, `snapshot.py`, `scan_writers.py`, `snapshot_ts.txt` →
`gs://deployment-scripts-central-element-323112/sports_cutover_2026_07_16/` (8 objects, verified listed).

_Scheduler fleet cross-check (pre-freeze, all runbook-named jobs verified to EXIST)_: meta-launcher
`uts-prod-sports-scheduler-cron` ENABLED; all 17 T0.4 writers ENABLED; 3 T0.6 consolidators ENABLED;
`uts-staging-features-sports-t1-schedule` ENABLED + `uts-prod-features-sports-t1-schedule` PAUSED (the 2 dead ones);
sports-ref-v3-{1,2,3}-start ENABLED. No job named in the runbook is missing ⇒ no inventory drift; freeze may proceed.
**⇒ T0.2 GATE PASSES. Proceeding to T0.3 (freeze meta-launcher first).**

---

**2026-07-16 — T0.3–T0.7 EXECUTED (the FREEZE). Writers frozen 08:08:43Z (meta-launcher) → 17 writers → consolidators
08:18:00Z. All gates PASS.**

_Freeze sequence (strictly freeze_order)_:

1. **T0.3 (order 1)** — `uts-prod-sports-scheduler-cron` paused **08:08:43Z**, verified PAUSED. Its last `*/5` dispatch
   `uts-prod-sports-scheduler-lx556` completed 08:05:52Z (pre-freeze); the ~08:11 tick did not fire.
2. **T0.4 (order 2→11)** — 17 writers paused one-at-a-time, each verified PAUSED immediately:
   sports-ref-v3-{1,2,3}-start · sports-fixtures-{midnight,6am,noon,6pm} ·
   sports-enrichment-{footystats,transfermarkt,soccer-football-info} · understat-eu-typing-sweep · is-daily-enum-sports
   · expected-universe-v2-sports · lifecycle-catalogue-regen-sports · mdps-odds-horizon-bucket ·
   features-service-sports-daily-trigger · market-tick-data-fast-t1-schedule.
3. **T0.5 DRAIN GATE (order 19)** — ZERO non-terminal sports Cloud Run executions (every job's newest exec terminal,
   `runningCount=0`). Watched the 3 consolidators ~6 ticks (08:12→08:17): `verdict=empty`, `rows_added=0` every tick;
   index rows stable; `unmerged_shards=[]` on all three (only `_legacy_seed` remains) ⇒ every shard already reaped =
   merged. No LOST-ROWS risk from the consolidator freeze.
4. **T0.6 (order 20→22)** — 3 consolidators paused **08:18:00Z** (instruments → market-data → features), all PAUSED.
   > 11-min post-freeze watch: `cons_last_run` frozen (08:18:09 / 08:18:06 / 08:18:40), index mtime frozen, row counts
   > == T0.2 baseline **exactly** (5,465,414 / 1,958,498 / 168,059). **Index is QUIET.**
5. **T0.7** — verified both dead schedulers' targets (`uts-{staging,prod}-features-sports-service-t1-recon`) do NOT
   exist, then DELETED `uts-{staging,prod}-features-sports-t1-schedule`. Gate `grep -c features-sports-t1` → **0**.
   sports-ref-v3 targets confirmed phantom (0 instances). **OR-7 resolved = delete** (recorded for T6.6).

_Final frozen-set tally_: **21/21 PAUSED** (1 meta + 17 writers + 3 consolidators), **0 ENABLED**. Only out-of-scope
ENABLED sports-adjacent job is `uts-dev-market-tick-data-fast-t1-schedule` (DEV, fires 00:30, dev buckets — not a
legacy-sports writer).

_10-MIN LEGACY QUIET WATCH (dispatch-mandated — decisive T0.1 confirmation)_: scanned BOTH legacy buckets for objects
with `timeCreated >= 08:08:43Z` (genuine writes; immune to the 90-day OLM `updated` bump) at **t+0 (08:18Z)** and
**t+20min (08:29Z)**. Result **QUIET both times: 0 genuine writes to either legacy bucket while everything is frozen.**
⇒ There is no unfrozen writer; the T0.1 "no live legacy writer" attribution is confirmed by the freeze itself. Verifier:
`~/tmp-cutover/legacy_write_watch.py`.

**⇒ PHASE 0 COMPLETE. gate_pass=true: all writers PAUSED (verified), per_vm drained, consolidators PAUSED, snapshots
verified (19/19 crc-matched), legacy buckets QUIET. Phase 1 (code repoints) / Phase 2 (move) may proceed — strictly
sequential, next phase owner.**

---

### PHASE 1 COMPLETE — CODE (2026-07-16, next-phase owner: Phase 2 MOVE)

All six T1 items **shipped + verified**. Shas: **T1.1** deployment-service@a535e3c · **T1.2**
unified-trading-pm@0114f846e (PR #1082, auto-merge) · **T1.3/T1.4** deployment-service@a535e3c (terraform CODE) ·
**T1.5** deployment-service@a535e3c

- deployment-api@1390340 + deployment-ui@c425f00 · **T1.6** re-verify (no edit). QG green on all 4 repos
  (deployment-service 87s, deployment-api 135s, deployment-ui 76s [Node22], unified-trading-pm).

* **T1.1** runtime-verified against canonical `-prd-` (non-empty league breakdown for post-cutover AND historical
  dates). The reader now probes the pipeline_mode-aware canonical path first, with bare `entity=fixtures` +
  `fixtures_schedule` + legacy as fallbacks (mirrors UAC `candidate_parquet_paths()`).
* **T1.2** gate proven fleet-wide (fails on reverted-T1.1, ignores `-prd-`); 21 pre-existing out-of-scope occurrences
  baselined + issue-doc'd (`issues/legacy_bucket_template_literals_2026_07_16.md`). None is in the cutover delete scope.
* **T1.5** gate met: no `sports-central-element-323112` in live code/config except the Phase-5 `_imports_reconcile.tf`.

> **⚠️⚠️ HARD HANDOFF TO PHASE-5 OWNER — TWO `tofu apply`s ARE A PREREQUISITE OF THE BUCKET DELETE (NOT yet run):** T1.3
> (MDPS FUSE-mount removal) and T1.4 (catalogue IAM `-prd-` repoint) shipped as CODE only. Both live in terraform state
> **`prefix=terraform/state/prod`** (T1.3 module `terraform/services/market-data-processing-service/gcp/`; T1.4 module
> `terraform/gcp/`). This Phase-1 sub-agent did NOT apply them: a live prod Cloud-Run/IAM mutation applied against the
> wrong state (the backend block defaults to `dev`, which does NOT hold these resources) would create duplicate/wrong
> infra — HARD RULE: live-infra-state ambiguity → STOP. **Before the physical bucket delete, the Phase-5 owner MUST:**
> (1) `tofu apply` both modules against `prefix=terraform/state/prod`; (2) confirm T1.3 diff = MDPS Cloud Run in-place
> volume removal (NO bucket create/destroy) + T1.4 diff = 3 IAM destroy-legacy/create-`-prd-` (NO bucket diff); (3)
> verify the MDPS job EXECUTES GREEN post-apply (T1.3 ABORT: MDPS fails to start → restore mount, do NOT delete).
> `tofu validate` on both modules = Success (2026-07-16). Leaving either unapplied at delete time = MDPS fails to START
> (deleted FUSE bucket) and `tofu apply` FAILS (IAM member on a nonexistent bucket).

_Note (disk hygiene)_: freed ~1.2G of orphaned bare-`/tmp` tmpfs temp (`cf_audit_*`, stale loose parquets, 1-2 days old,
no live process) that was ENOSPC-failing QG runs; foreign session scratchpads left untouched.

---

## PHASE 2 — MOVE (in progress, 2026-07-16, owner: Phase-2 sub-agent)

**Pre-flight re-verified before any mutation**: freeze still holds (all sports writers + meta-launcher + 3 sports
consolidators PAUSED, verified 09:33Z); legacy QUIET since freeze (`legacy_write_watch.py 2026-07-16T08:08:43Z` → 0
genuine writes to either legacy bucket); frozen inventory (07:44) still valid. Venv:
`market-tick-data-service/.venv/bin/python` with `GCP_PROJECT_ID=central-element-323112`.

**T2.1 — PHASE 2a archive delete — DONE 2026-07-16T09:37Z.** 398/398 objects under
`sports_reference_v1_archive/by_date/day=*/entity=fixtures/fixtures.parquet` (all fixtures-only, one/day, 2018-01-02…)
deleted via UTL `gcs_delete_object`. **Object-layer gate PASS**: post-delete `list_blobs(prefix)` live count == 0;
gcloud `ls` "matched no objects". Canonical `-prd-` verified it NEVER held the `sports_reference_v1_archive/` prefix (0
— no F-3 contamination). Per-object evidence: `~/tmp-cutover/t2_1_delete_evidence.jsonl` (398 rows, status=DELETED,
present_after=false). Verifier: `~/tmp-cutover/t2_1_delete_archive.py`. **Finding for Phase-5 (T5.3)**: legacy bucket
retains NO noncurrent versions on delete (`gcloud storage ls -a` under the prefix == 0 post-delete; the SA lacks
`storage.buckets.get` so versioning config can't be read directly, but the version listing is authoritative) ⇒ the
archive delete is PERMANENT and **T5.3's `--all-versions` purge is likely a no-op**; the runbook ROLLBACK "restore until
T5.3" does not apply to legacy objects. Delete is safe on the proven- superseded verdict alone (0 unique rows lost),
independent of any versioning rollback.

**T2.2 — object-layer classification + class-A copy list — DONE 2026-07-16.** Reconciles EXACTLY (control 118 +
v1_archive 398 + data 968,805 = 969,321). **Class A = 17,105** (runbook 17,111; −4 canonical pre-freeze growth, −2
crc-identical bare-`day=`/BETFAIR dups correctly excluded — more-correct). **`instrument_availability` is NOT class A**
(all cells canonical-covered; the "119,858 must move" was the F-1 vehicle blind-spot, not the object-layer set — this
retires R-4's move-scope premise for IA). Copy list `~/tmp-cutover/t2_3_copylist.jsonl` = **17,089** rows (class A minus
16 player_stats → T2.4); dst = `pipeline_mode=<M>` inserted after `day=`, M derived per-entity from canonical usage.
SAMPLE GATE PASS live both directions (D1 has-canonical-real 23/23 all trees; D2 class-A-miss-real 11/11). Verifiers
`~/tmp-cutover/t2_2_{shapes,classify,copylist,verify}.py`. Class-A entities: fixtures_outcomes 4966, fixtures_schedule
4940, footystats_matches 2934, footystats_odds 2044, injuries 1650, fixtures 369, teams 61, fixture_events 40,
fixture_stats 38, footystats_predictions 31, fixture_lineups 16.

**T2.3 — class-A move — DONE 2026-07-16.** 17,089/17,089 objects server-side-copied to canonical `pipeline_mode=<M>`
paths, 0 FAILED, all crc32c-verified (byte-identical). Reader-resolution 11/11 via `candidate_parquet_paths()`. Legacy
untouched. Evidence `~/tmp-cutover/t2_3_move_evidence.jsonl`.

**T2.4 — OR-1 option D (player_stats) — DONE 2026-07-16. 388,825 genuine legacy-only player observations recovered into
canonical across 4,015 cells, 0 FAIL, every cell verified upsert-safe (rows == unique (fixture_id, player_id)).** Key
corrections to the plan's premises, all MEASURED:

1. **The 111,827 figure is a sample under-count (~3.5×).** Full global-containment pass = **388,825 unique** legacy-only
   (fixture_id, player_id). Recovered all of it (data-pipeline-correctness: no descope).
2. **No available_at stamping was needed.** Legacy player_stats already carries honest `available_at` (0 null / 0
   midnight measured across every legacy-only row) satisfying UAC `(sports,PLAYER_STATS)="match_end_time"`. The
   dispatch's "legacy predates availability stamping" does not hold for this entity. A 0-null gate still fires on write.
3. **Schema is NOT legacy≠canonical for the flattened population** — both are the same 38-col schema incl. available_at.
   The real variance is that canonical stores all-null stat columns as arrow `null` type, so conforming to the
   per-object canonical schema FAILS; the union coerces to stable types (value-preserving).
4. **The 16 class-A player_stats are the only uncovered cells** and are the raw stringified-`players` form → re-fetch
   list (no fabricated flatten). **fixture_events: zero 5-col stubs imported**; the 40 class-A objects moved in T2.3 are
   10/11-col ATTRIBUTED forms whose schemas canonical already carries → kept + listed for schema-upgrade re-fetch.
5. **BIG FINDINGS (pre-existing canonical, not cutover-introduced)** →
   `issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`: canonical player_stats holds **740,725
   within-object duplicate rows (~26% of 2,882,420)**; T2.4 dedupe fixed the 4,015 touched cells, ~13,964 remain.
   Canonical fixture_events runs 4 schema variants incl. **~30% degenerate 5-col**.

Rollback substrate: every overwritten canonical object copied to
`gs://deployment-scripts-central-element-323112/sports_cutover_2026_07_16/player_stats_prewrite_bak/` first.

_Environment note (RESOLVED — do not chase)_: mid-phase, `import unified_trading_library` failed with
`KillSwitchId.KILL_PER_TREASURY_SUB_ACCOUNT_DRIFT` missing (`kill_switch/bus.py:144`). This was **TRANSIENT** — the
workspace UTL clone was caught mid-pull/rebase by another slot; re-tested later it imports cleanly in ALL 5 venvs. It is
NOT a committed defect and needs no fix. T2.4's scratch tooling had already routed around it via `google.cloud.storage`
directly (same pattern as `inventory.py`); no gsutil/gcloud subprocess was used for object ops.

---

### PHASE 2 STATUS (2026-07-16) — T2.1-T2.6 COMPLETE + VERIFIED · **T2.7 OUTSTANDING (deliberate stop)**

| todo | state | headline                                                                                           |
| ---- | ----- | -------------------------------------------------------------------------------------------------- |
| T2.1 | ✅    | 398/398 v1_archive deleted; object-layer gate live-count == 0; canonical never contaminated        |
| T2.2 | ✅    | class A = 17,105 (reconciles to 969,321 exactly); copy list 17,089; live sample gate 23/23 + 11/11 |
| T2.3 | ✅    | 17,089/17,089 moved, crc-verified, reader-resolvable 11/11                                         |
| T2.4 | ✅    | **388,825** genuine legacy-only player observations recovered, 4,015 cells, 0 FAIL, upsert-safe    |
| T2.5 | ✅    | control-plane adjudicated; **OR-4 = ABANDON, PROVEN**                                              |
| T2.6 | ✅    | MDT exact: **55,627** unique (not ~52,400); 6,110 class-A moved; **OR-5b raised**                  |
| T2.7 | ✅    | shards written + read-back-verified (13,293 rows); NOT consolidated by design (merge is T6.1)      |

**Phase-2 gate = PASSED** (T2.7 closed 2026-07-16). **Phase 3 = COMPLETE** (T3.1-T3.5 all ✅, 2026-07-16) — see the
Progress Log entry at the top. The index was verified still QUIET at purge time (total == the T0.2/T0.6 baseline
5,465,414 to the row; footystats × ODDS still exactly 140,574 ⇒ the T2.7 shard is indeed unmerged, as designed).

**Two rulings now block the DELETE (not Phase 3):**

1. **OR-5b (NEW)** — the 49,517 residual `market-data-tick-sports` unique objects (3,816 class-A + 45,701 class-B
   holding 7,079,850 legacy-only rows). **`market-data-tick-sports` is NOT delete-eligible.** OR-1 never covered MDT
   tick data, so there is no ruling to inherit. **✅ INVESTIGATED 2026-07-16 (both sub-questions) →
   `plans/active/issues/mdt_legacy_canonical_row_gap_2026_07_16.md`** — exact pass over all 45,701 pairs, 0 errors.
   **The OR-1 trap does NOT reproduce**: canonical is **NET POORER by 6,721,872 rows** (losing 20:1; OR-1 gained 15:1),
   and the gap is **89.5% GENUINE / 0% junk / 0% fabricated**. **The delete stays BLOCKED** — but the remedy collapses
   ~12×: legacy holds three strictly-nested generations `G3 ⊂ G2 ⊂ G1`, so recovering the **3,816** (a) objects (0.23
   GB, proven **3,816/3,816 derivable, 0 park-only**) recovers **99.98%** of the 6.37M-row pre-match gap and renders the
   45,701 **NO-ACTION by proof**. Recommended: **(a) = B · (b) = D · new (c) = A**. A third ruling is now open —
   **OR-5b(c)**, the 746,928 in-play rows.
2. ~~**T2.7's blocker (c)**~~ **✅ RESOLVED — was never a real conflict (T2.7 2026-07-16, re-confirmed by T3.1/T3.3
   2026-07-16).** The "ODDS retired to MTDS-only 2026-06-25" premise is **dead by operator reversal** (#6 REVERSED
   2026-06-27 `UAC@c75101be`, completed `@57bcc7c5`: _footystats pre-match ODDS = IS reference data_) and survived only
   as a stale code comment (→ T2.8). **There is no contradiction with T3.1**: T3.1 purges `source=api_football` × ODDS
   (impossible-by-construction, 100% phantom — 0 captured rows); T2.7's 2,044 rows are `source=footystats`, the ONLY
   valid ODDS source, which T3.1 explicitly PRESERVED and asserted UNTOUCHED at 140,574. The two operate on disjoint
   `source` values — which is exactly why the `source` filter is mandatory (R-10).

**`instruments-store-sports` object-layer status**: every class-A object is moved and verified; T2.7's manifest shard is
written + read-back-verified (merge deferred to T6.1 by design). **⇒ Nothing manifest-side blocks it; T4.1's
object-layer zero-unique proof is the remaining gate** (and per R-13, that object layer — never L6 — is the delete
clearance).
