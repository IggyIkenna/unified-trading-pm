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

- [ ] [DATA] P0. **T2.1 — PHASE 2a: delete `sports_reference_v1_archive/` (398 objects) — do NOT move it.** _Mechanism_:
      this executes the already-authored, already-approved P0 operator todo in
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
- [ ] [DATA] P0. **T2.2 — Regenerate the object-layer inventory and emit an EXPLICIT copy list (do not trust the
      vehicle's enumeration — F-1).** _Mechanism_: paginated `list_blobs` with a fields projection
      (`name,size,crc32c,updated`), 12-way prefix-parallel over top-level prefixes (~2 min/bucket; the naive recursive
      `ls` times out). Key = **cell-key normalisation**, NOT path equality: (1) delete the canonical-only
      `/pipeline_mode=<x>/` segment, (2) normalise legacy `instrument_availability/by-date/day-<D>/` → hive
      `by_date/day=<D>`. Derive from the UAC SSOT
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
- [ ] [DATA] P0. **T2.3 — PHASE 2b: MOVE class A (17,111 objects = 17,509 − 398 archive) to canonical paths.**
      _Mechanism_: drive from the T2.2 copy list, not `_list_tree`. Copy legacy → canonical **at the canonical path**
      (insert `pipeline_mode=batch_<source>` between `day=` and `entity=`; normalise the `by-date/day-<D>` dash form)
      via UTL `gcs_copy_object` (server-side, idempotent, skip-if-exists). Cover the FULL span **2018-01-02 …
      2026-12-06** — if using the v9 migrator as the primitive, `--start-date 2018-01-01 --end-date 2026-12-31`
      explicitly (defaults `2019-01-01`/`2026-06-01` silently truncate BOTH ends — F-4). Cover the trees `_list_tree`
      cannot see (F-1): `instrument_availability/` (119,858 objects), bare `day=2026-03-21/`,
      `sports_reference/mappings/season=*/`. _Gate_: every class-A source object has a canonical object at its derived
      path with a matching row count; re-run T2.2 → class A = 0. _ABORT_: any copy lands at a non-canonical path → STOP
      and re-derive; a wrong-path copy is invisible to every reader and to the manifest.
- [ ] [DATA] P0. **T2.4 — PHASE 2c: MOVE class B (13,222 objects where canonical has FEWER rows) — BLOCKED on OR-1.**
      _Mechanism_: **skip-if-exists CANNOT do this (F-2)** — the canonical object exists, so both vehicles skip it. Per
      OR-1 ruling, either (a) **row-union** legacy ∪ canonical per cell and write the union to the canonical path
      (safest; preserves any canonical-only rows), or (b) **overwrite** canonical with legacy where legacy ⊇ canonical
      (simpler; loses canonical-only rows if the containment does not actually hold). **Verify containment per cell
      before overwriting either way.** Worst offenders: player_stats 111,827 rows, standings 91,380, fixture_events
      69,444, teams 16,502, player_values 16,233 (e.g. `day=2019-08-12 season=2019`: legacy 640 vs canonical 38).
      _Gate_: for all 13,222, canonical row count ≥ legacy row count post-move; total rows recovered ≥ 305,000; re-run
      T2.2 → class B = 0. _ABORT_: any cell where legacy ⊄ canonical AND canonical ⊄ legacy (genuine divergence, not a
      subset) → STOP and escalate; a blind overwrite loses canonical-only rows.
- [ ] [DATA] P0. **T2.5 — Re-home the control-plane objects the vehicle skips by construction.** _Mechanism_: `_keep()`
      (`:167-173`) filters out `/_index/`, `/_vm_staging/`, and `_SKIP_PREFIXES` =
      `_audits/ _smoke_test/     _catalogue/ availability_index/` → **none** of the control-plane uniques move.
      Adjudicate each explicitly: `_index/per_vm/_legacy_seed.parquet` (legacy **1,757,469 rows** vs canonical **0** —
      the canonical seed is EMPTY, 16.2 MB vs 18.7 KB) → **OR-4**; `availability_index/instruments-service.parquet`
      (22,450 vs 22,445 — 5 rows); `_index/per_vm/fixtures-recovery-20260627-183725.parquet` (34,564 rows, shard mtime
      18:37 predates the legacy index write 19:14:43Z so it _probably_ merged — **NOT PROVEN**); 2 `_audits`, 2
      `_index`, `sports_reference/mappings/season=2019` (640 vs 589). **The legacy bucket has had no consolidator since
      2026-07-13** (`manifest_consolidator_scheduler.tf:67,80`) — these shards can never merge on their own. _Gate_:
      each of the ~8 control-plane uniques has a written disposition (moved / proven-already-merged /
      abandoned-with-reason). _ABORT_: `_legacy_seed.parquet` disposition unresolved → **do not delete the bucket**
      (1.76M rows). **HARD: never place any re-homed object under `_index/per_vm/`** unless it is genuinely a shard to
      be merged.
- [ ] [DATA] P0. **T2.6 — Finish the exact row-count pass for `market-data-tick-sports` (the ~52,400 is an
      EXTRAPOLATION, not a gate).** _Mechanism_: resume method — (1) re-list both MDT buckets with the T2.2 paginated
      prefix-parallel lister (~2 min each); (2) key =
      `re.sub('/pipeline_mode=[^/]+/','/', re.sub('/data_source=[^/]+/','/', name))` — **the MDT trap differs from the
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
- [ ] [DATA] P0. **T2.7 — Write the moved cells' manifest rows via a per-VM shard (never a direct index write).**
      _Mechanism_: the canonical index gains rows only through `_index/per_vm/<VM_NAME>.parquet` + the consolidator's
      additive merge (proven: 123,149 rows in the consolidated index, 0 in any shard). Emit one shard
      `VM_NAME=sports-legacy-cutover-20260716` with `MANIFEST_PER_VM_SHARDS=true`, `record_captured(source=…)` for every
      moved cell (`source=` is crosscutting and REQUIRED), correct source-aware `pipeline_mode`. **Never fake
      `record_captured` for a cell with no backing object** (`codex/02-data/honest-absence-downstream-handling.md`).
      _Gate_: shard exists; after the Phase-6 consolidator restart it merges and the index gains exactly the moved-cell
      count. _ABORT_: any row would be written with `source=''` or a phantom `instrument_count=0` → STOP; that is the
      pattern that created the 468 phantom residual.

### PHASE 3 — CLEAN (the index is QUIET — the ONLY safe window)

- [ ] [DATA] P0. **T3.1 — Purge the bogus `api_football × ODDS` rows — RE-MEASURE FIRST; the count is 123,149, not
      127,018.** _Mechanism_: single target
      `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`; predicate **delete
      WHERE `source=='api_football' AND data_type=='ODDS'`**. **The `source` filter is MANDATORY** — `data_type=='ODDS'`
      alone = 263,886 rows (footystats 140,574 + api_football 123,149 + blank-source 163); a sloppy predicate destroys
      the real footystats population. Snapshot first to `_index/availability_index.<UTC-ts>.purge_af_odds.bak.parquet` —
      a **SIBLING under `_index/`**, the proven convention (6 such `.bak` files already coexist there, none ever
      re-absorbed). **NEVER into `_index/per_vm/`** (becomes shard #3 → resurrects every purged row → breaks
      `baseline_shards=2`). _Gate_: post-purge assert (a) 0 rows match the predicate; (b) **footystats × ODDS == 140,574
      UNTOUCHED**; (c) total dropped by exactly 123,149; (d) re-verify the count immediately before the delete. _ABORT_:
      pre-delete count ≠ 123,149 → the class is no longer frozen → STOP and re-derive.
- [ ] [DATA] P0. **T3.2 — Confirm the purge is TERMINAL before executing it (the "re-seeded nightly" premise is FALSE on
      both halves).** _Mechanism_: three independent confirmations, all already measured — (1) **provenance**: 82,362 of
      the 82,509 `expected_unattempted` rows came from ONE bulk run `enum-universe-sports-20260628-213115`, not the
      01:30 cron (which only ever added 18-21 rows/night: 82,362 + 21 + 18×7 = 82,509 exactly); the 40,640
      `empty_confirmed` rows were written 2026-07-13 with `enumerator_run_id=None` — not the enumerator at all. (2)
      **the fix is deployed**: run `enum-universe-sports-20260716-013041` (exec `expected-universe-v2-sports-89dqt`,
      completed 2026-07-16T01:30:56Z) wrote 45,622 rows with **0 api_football × ODDS** and 4,071 footystats × ODDS; the
      per-run bogus series ends at 20260715. IS vendors UAC as a **local path dep**
      (`instruments-service/pyproject.toml:82-83`
      `[tool.uv.sources.unified-api-contracts] path = "../unified-api-contracts"`), so the image built
      2026-07-16T01:02:28 baked in LDR's `57bcc7c5` — **IS images track LDR, not UAC main** (this resolves the apparent
      contradiction). (3) **the writer guard is ON**: UTL `_writer_ingest.py:485` raises `MissingSourceError` when
      `has_source_priority(ag, dt) and not is_valid_manifest_source(ag, dt, src)`;
      `has_source_priority("sports","ODDS")` flipped False→True at `57bcc7c5` — the mis-stamp guard was **silently
      DISABLED for 20 days**, which is how these rows were written unchallenged. _Gate_: all three re-confirmed at
      execution time. _ABORT_: any per-run bogus count reappears after 20260715 → the fix regressed → do not purge (it
      will re-seed).
- [ ] [DATA] P0. **T3.3 — REMOVE, do not retype: `api_football × ODDS` is impossible-by-construction at 3 layers.**
      _Mechanism_: confirm before purging — (a) **codex** `codex/02-data/sports-data-source-coverage-matrix.md:273-274`
      _"api_football `/odds` is NOT used by instruments-service … there is no api_football odds path"_; `:312`
      _"data_type=ODDS writer is footystats `get_fixture_odds_snapshot()` only"_. (b) **code** (grep-then-READ):
      `api_football.py:649-655` `get_odds()` docstring _"API Football does not provide odds data."_;
      `footystats.py:322-328` _"FootyStats does not provide odds via the standard interface."_ — both stubs. (c)
      **UAC**: `SPORTS_DATA_TYPE_TO_SOURCE["ODDS"]=="footystats"` (`league_data.py:222`),
      `("sports","ODDS"):["footystats"]` (`_source_priority_data.py:76`),
      `is_valid_manifest_source("sports","ODDS","api_football") is False` **PINNED** by
      `tests/unit/test_source_priority.py:576`. _Gate_: all 3 layers agree → REMOVE. _ABORT_: any layer says
      api_football odds is legitimate → do not purge; retype instead.
- [ ] [DATA] P1. **T3.4 — Race guard for the purge window.** _Mechanism_: `_index/per_vm/sports-fixtures-job.parquet` is
      HOT (mtime 2026-07-16T06:33:51Z; written ~every 5 min by `uts-prod-sports-scheduler-cron`). Phase 0 already paused
      it and the consolidators; **additionally** take `_index/consolidator.lock` for the read-modify-write so the purge
      cannot race a consolidation and silently lose the fixtures job's live rows. _Gate_: lock held; shard mtime static
      across the window. _ABORT_: shard mtime advances mid-purge → a writer escaped Phase 0 (F-5) → STOP, restore the
      `.bak`.
- [ ] [REVIEW] P2. **T3.5 — L6 gate redefinition: NO CHANGE NEEDED — verify-only, then close the item.** _Mechanism_:
      **already implemented, tested, and shipped** — `unified-trading-pm@10ad5d69a` _"fix(audit): redefine
      L6-legacy-only gate to real-data-only (operator ruling 2026-07-15)"_, verified **ancestor of BOTH
      `origin/live-defi-rollout` AND `origin/main`**, working tree clean for that path. `_split_backed_cells()`
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

- [ ] [DATA] P0. **T4.1 — OBJECT-LAYER zero-unique proof. This, not L6, is the delete gate.** _Mechanism_: re-run the
      T2.2 inventory + classification over both legacy buckets. **Why the manifest cannot clear the delete**: no
      availability index has a **path/uri/bucket column at all** (columns are date, venue, data_type, source,
      pipeline_mode, league_id, capture_status, instrument_count, …) — the bucket binding is **positional** (the
      `_index` object physically lives in its bucket) and paths are DERIVED at read time. Therefore **zero rows in
      either index mention `v1_archive`, and no row ever could** — the 398 objects were invisible to L6 **by
      construction**. That is why `L6-legacy-only = 0` coexisted with 398 real legacy-only parquets. _Gate_: unique == 0
      for **both** buckets, or every residual has a written, operator-accepted disposition. _ABORT_: unique > 0 without
      a disposition → **DO NOT DELETE**.
- [ ] [DATA] P0. **T4.2 — Prove the moved objects are READABLE at canonical paths (not merely present).** _Mechanism_:
      sample ≥25 moved cells across every entity and both class A and class B; resolve each through the UAC SSOT
      `candidate_parquet_paths()` and read it via the real consumer
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
- [ ] [INFRA] P0. **T4.4 — `terraform plan` shows ZERO diff touching either legacy bucket. THIS IS THE GATE.**
      _Mechanism_: after T5.1's config removal, `tofu plan` must not propose creating either bucket. _Gate_: plan clean.
      _ABORT_: plan wants to CREATE a legacy bucket → T5.1 was skipped or incomplete → **do not delete** (see F-6 / the
      resurrection precedent).
- [ ] [INFRA] P1. **T4.5 — Resolve the `--asset-group`-less recon job (OR-8).** _Mechanism_:
      `uts-prod-market-tick-data-     service-fast-t1-recon`'s baked args are `[--operation download --mode batch]` with
      **no `--asset-group`**; UTL `service_cli.py:163-167` defines it `nargs='+'` with **no default** (→ `None`). The
      infra leg **read the argparse definition but did not execute the resolver** to prove what the `None` branch
      enumerates. Run it in dry-run and observe. _Gate_: a MEASURED list of asset_groups the unfiltered invocation
      touches. _ABORT_: it writes sports to a **legacy** name → a live legacy writer exists (F-5) → STOP.

### PHASE 5 — DELETE (gated on Phase 4 + a FINAL live-writer re-check)

> **Non-negotiable ordering: config removal + `state rm` (T5.1) → apply + confirm no recreate (T4.4) → object-version
> purge (T5.3) → bucket delete (T5.4).** Deleting before T5.1 resurrects the buckets.

- [ ] [INFRA] P0. **T5.1 — Remove the Terraform DECLARATIONS + the import block, then `state rm`. Terraform does not
      _reference_ these buckets — it OWNS them.** _Mechanism_: `terraform/gcp/main.tf:179-212`
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
- [ ] [INFRA] P0. **T5.2 — FINAL live-writer re-check immediately before the delete.** _Mechanism_: **CORRECTED
      2026-07-16 (T0.1) — do NOT gate on "newest object mtime"/`updated`.** That is precisely the measurement that
      manufactured F-5: an OLM `STANDARD→NEARLINE @ 90d` transition bumps `updated` **every single day** on a bucket
      nobody is writing, so an `updated`-based gate ABORTS this cutover forever on a false positive. Re-run
      `~/tmp-cutover/scan_writers.py <bucket>` and gate on the **write** discriminator: an object is genuinely written
      **iff** its `generation` is new — operationally, `updated != timeStorageClassUpdated` **OR** `timeCreated >= T0.6`
      (the age-0 case: a fresh create has all three timestamps equal, which is how T0.1 caught the only 3 real writes).
      _Gate_: **zero objects with `timeCreated >= T0.6`** and zero with `updated != timeStorageClassUpdated` in **both**
      legacy buckets. (Transitions are expected and are NOT a writer — ignore them.) _ABORT_: any object **created**
      since T0.6 → **DO NOT DELETE**; return to T0.1.
- [ ] [INFRA] P0. **T5.3 — Purge object VERSIONS before the shell delete.** _Mechanism_: both buckets carry
      `versioning{enabled=true}` + `force_destroy=false`, so the bucket cannot be deleted until every object **version**
      is purged — `gcloud storage rm --recursive --all-versions gs://<legacy-bucket>`. _Gate_:
      `gcloud storage ls -a     gs://<bucket>/**` → empty. _ABORT_: any version survives → the delete will fail;
      diagnose (retention/hold).
- [ ] [INFRA] P0. **T5.4 — Delete the two legacy buckets.** _Mechanism_:
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
- [ ] [INFRA] P0. **T6.1 — Restore the 3 consolidators FIRST (reverse order 22→20).** _Mechanism_: un-pause
      `-features-sports-cron`, then `-market-data-sports-cron`, then `-instruments-sports-cron`. _Gate_ (first run):
      exits 0; `_index/availability_index.parquet` mtime advances; row count **≥ the pre-freeze snapshot minus exactly
      123,149** (the T3.1 purge) **plus** the T2.7 moved-cell count — never lower (a drop means the merge clobbered
      rows); **no `Container terminated on signal 9`** (the instruments-sports merge is the known heavy case —
      60-80s/2.09M rows/37 shards, 900s bump at `manifest_consolidator_scheduler.tf:88-92`); no stale-index loud-fail.
      Let them run **≥3 clean ticks before any writer resumes** so the index is a known-good baseline. _ABORT_: row
      count drops or OOM-kill → restore the T0.2 `.bak`; do not resume writers onto a corrupt index.
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

| #    | Phase | Risk                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Severity              | Mitigation                                                                                                                                                         |
| ---- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| R-1  | 0     | ~~**Unidentified live writer**~~ **✅ CLOSED 2026-07-16 — the risk does not exist.** T0.1 proved at the object layer that the "125 writes on 07-15" are OLM `STANDARD→NEARLINE @ 90d` storage-class transitions (`generation` unchanged, `metageneration` 1→2, `updated == timeStorageClassUpdated`), not writes: **5,008 recent `updated` bumps → 5,008 transitions, 0 writes**. Only 3 genuine writes in 30d (`_audits/`, 2026-07-14T00:12), attributed to a hand-run `audit_fixtures_via_api_football.py` + remediated by `instruments-service@bd6b797a`. | ~~CRITICAL~~ **NONE** | Closed by measurement, not mitigation. **T5.2 re-check MUST gate on `generation`/`timeCreated`, never `updated`** — an `updated` gate false-ABORTs daily, forever. |
| R-1b | 5     | **NEW (T0.1) — the anti-risk: an `updated`-based writer check false-ABORTs the cutover permanently.** The 90-day OLM rule bumps `updated` on ~100-2,400 objects/day indefinitely on a bucket with zero writers. Any gate reading "newest object mtime" reads those as live writes and blocks T5.4 forever.                                                                                                                                                                                                                                                   | HIGH                  | T5.2 rewritten to gate on `timeCreated >= T0.6` / `updated != timeStorageClassUpdated`. `~/tmp-cutover/scan_writers.py` is the verifier.                           |
| R-2  | 0     | Freezing the 4 fixture crons but not the `*/5` meta-launcher → fixtures job still dispatched every 5 min into a "frozen" estate.                                                                                                                                                                                                                                                                                                                                                                                                                             | HIGH                  | T0.3 freezes the meta-launcher FIRST (freeze_order 1) — `sports-trigger-tiers.yaml` proves it dispatches the 3 job names.                                          |
| R-3  | 0     | Freezing consolidators BEFORE the drain strands per-VM shards permanently (legacy has had no consolidator since 2026-07-13 — its shards can never merge).                                                                                                                                                                                                                                                                                                                                                                                                    | HIGH                  | T0.5 drain gate ≥2 ticks before T0.6; poll on a progress metric.                                                                                                   |
| R-4  | 2     | **The MOVE vehicle enumerates 4 of 7 trees as EMPTY and exits 0** (F-1) — `instrument_availability` alone is 119,858 objects. Undercount reported as success.                                                                                                                                                                                                                                                                                                                                                                                                | CRITICAL              | T2.2 drives from an independent object-layer inventory; the vehicle is a copy primitive only. OR-6.                                                                |
| R-5  | 2     | **Skip-if-exists skips the 13,222 class-B objects** (F-2) — canonical exists but holds fewer rows → 305,000+ rows lost at delete. Canonical is NOT a superset.                                                                                                                                                                                                                                                                                                                                                                                               | CRITICAL              | T2.4 + OR-1 (row-union vs overwrite); per-cell containment check before writing.                                                                                   |
| R-6  | 2     | **The vehicle re-imports v1_archive into canonical** (F-3) — `SPORTS_REF_V1_ARCHIVE_PREFIX` ∈ `_INSTR_DATA_TREES` and IS enumerable.                                                                                                                                                                                                                                                                                                                                                                                                                         | HIGH                  | T2.1 (delete archive) strictly BEFORE T2.3 (move).                                                                                                                 |
| R-7  | 2     | **Day-window truncation** (F-4) — defaults 2019-01-01…2026-06-01 vs real span 2018-01-02…2026-12-06. Out-of-window days are never listed → never reported → never copied.                                                                                                                                                                                                                                                                                                                                                                                    | HIGH                  | T2.3 passes the explicit full span; T4.1 re-inventory catches any residual.                                                                                        |
| R-8  | 2     | Control-plane uniques are skipped **by construction** (`_keep()` filters `/_index/`, `/_vm_staging/`, `_SKIP_PREFIXES`) — incl. `_legacy_seed.parquet` at 1,757,469 rows.                                                                                                                                                                                                                                                                                                                                                                                    | HIGH                  | T2.5 adjudicates each explicitly; OR-4. Delete blocked while `_legacy_seed` is unresolved.                                                                         |
| R-9  | 2/4   | **A gate script that reads an empty set and reports PASS.** `verify_v1_archive_row_coverage_2026_06_27.py` globs `v1_archive` in the **PRD** bucket (tree exists only in legacy) → `v1_keys=∅` → _"VERDICT: COVERED — all 0 keys present"_. Second bug: it resolves `fixture_id` (a composite STRING) for v1 vs `af_fixture_id` (int) for v2 → 0/31 overlap → had the bucket been right it would have reported a FALSE 100% GAP. The two bugs mask each other.                                                                                               | CRITICAL              | T2.1 proves coverage independently (all 398, real join key); T6.8 DELETES the script.                                                                              |
| R-10 | 3     | Purge predicate without the `source` filter destroys the real footystats population (`data_type=='ODDS'` alone = 263,886 rows vs the 123,149 target).                                                                                                                                                                                                                                                                                                                                                                                                        | CRITICAL              | T3.1 mandates `source=='api_football' AND data_type=='ODDS'`; post-assert footystats × ODDS == 140,574 untouched.                                                  |
| R-11 | 3     | A `.bak` written into `_index/per_vm/` becomes shard #3 → consolidator merges it → **resurrects every purged row** + breaks `baseline_shards=2`.                                                                                                                                                                                                                                                                                                                                                                                                             | CRITICAL              | T0.2 + T3.1 mandate the SIBLING `_index/*.bak.parquet` convention (6 such files already coexist, none re-absorbed).                                                |
| R-12 | 3     | Purge races a consolidation → the hot `sports-fixtures-job.parquet` (mtime T-seconds) loses live rows.                                                                                                                                                                                                                                                                                                                                                                                                                                                       | HIGH                  | T3.4 `_index/consolidator.lock` + Phase-0 pauses; ABORT if shard mtime advances.                                                                                   |
| R-13 | 4     | **Treating L6 GREEN as delete-clearance.** No index has a path column → no row can reference `v1_archive` → L6 is blind to it **by construction**. This is exactly how "legacy-only=0" coexisted with 398 real parquets.                                                                                                                                                                                                                                                                                                                                     | CRITICAL              | T4.1 makes the OBJECT layer the gate. The manifest is never evidence about objects.                                                                                |
| R-14 | 5     | **Terraform resurrection** — the blocks DECLARE the buckets; deleting without removing them recreates empty shells on the next apply.                                                                                                                                                                                                                                                                                                                                                                                                                        | CRITICAL              | T5.1 (remove blocks + import block + `state rm`) → T4.4 (clean plan) → T5.3/T5.4. Precedent: ~30 buckets recreated 2026-07-12T21:59Z.                              |
| R-15 | 5     | `_imports_reconcile.tf:74-77` left behind → `plan`/`apply` **errors on a missing import target** → blocks the WHOLE estate, not just sports.                                                                                                                                                                                                                                                                                                                                                                                                                 | HIGH                  | T5.1 removes it in the SAME commit as the resource block.                                                                                                          |
| R-16 | 5     | Legacy IAM grants left behind → `apply` fails post-delete (IAM member on a nonexistent bucket).                                                                                                                                                                                                                                                                                                                                                                                                                                                              | HIGH                  | T1.4 canonicalises all 3 before the delete.                                                                                                                        |
| R-17 | 5     | MDPS Cloud Run job **fails to START** (gcsfuse cannot mount a deleted bucket) — `:230` is a live **WRITE** mount.                                                                                                                                                                                                                                                                                                                                                                                                                                            | HIGH                  | T1.3 removes both mounts + applies BEFORE the delete.                                                                                                              |
| R-18 | 5     | Deleting `market-data-tick-sports` on an **extrapolated** unique count (~52,400 from an n=400 sample).                                                                                                                                                                                                                                                                                                                                                                                                                                                       | HIGH                  | T2.6 exact pass is a hard gate on T5.4 for that bucket. OR-5.                                                                                                      |
| R-19 | 6     | Restoring writers onto an index that lost rows in the merge, or resuming the meta-launcher first so failures are masked by fan-out.                                                                                                                                                                                                                                                                                                                                                                                                                          | MEDIUM                | T6.1 ≥3 clean consolidator ticks first; T6.5 meta-launcher LAST; per-job first-run verification.                                                                   |
| R-20 | all   | **Path-shape trap** — naive path-equality falsely reports "unique" (legacy is bare `entity=`; canonical has `pipeline_mode=`). Also `fetched_at_hour=` is a snapshot dimension (7× overcount) and byte size is NOT a row proxy (3.25% wrong).                                                                                                                                                                                                                                                                                                                | CRITICAL              | T2.2 cell-key normalisation via the UAC SSOT + mandatory ≥10-pair sample-verify before scaling.                                                                    |

## ROLLBACK

**Rollback is only fully available before T5.3 (object-version purge). After T5.4 the legacy bucket is gone — the T0.2
snapshot + the moved canonical objects are the only copies.** Versioning is enabled on both legacy buckets, so
individual object rollback is available until T5.3 purges the versions.

| If this fails         | Rollback                                                                                                                                                                                                                                                                                              |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 0 (freeze)      | `gcloud scheduler jobs resume <NAME>` in reverse freeze order. No data touched. Fully reversible.                                                                                                                                                                                                     |
| Phase 1 (code/TF)     | `git revert` the repoint commits; `tofu apply` restores the mounts/IAM. **T5.1 is NOT part of Phase 1** — no bucket lifecycle change has happened yet. Fully reversible.                                                                                                                              |
| T2.1 (archive delete) | Object versioning is ON → restore the 398 via `gcloud storage cp --all-versions` **until T5.3**. After T5.3: unrecoverable — but proven superseded on all 398 (0 rows lost).                                                                                                                          |
| T2.3/T2.4 (moves)     | Copies are ADDITIVE to canonical; legacy is untouched (copy, not move — the delete is Phase 5). Roll back by deleting the copied canonical objects listed in the T2.2 copy list. **Class B overwrites are the exception** — restore the canonical originals from their T0.2 `.bak` / object versions. |
| T3.1 (127k purge)     | Restore `_index/availability_index.<ts>.purge_af_odds.bak.parquet` over `_index/availability_index.parquet`. **Never restore it into `per_vm/`.**                                                                                                                                                     |
| T5.1 (TF state rm)    | Re-add the resource blocks + `terraform import` the buckets back. Only possible while the buckets still exist.                                                                                                                                                                                        |
| T5.4 (bucket delete)  | **NO ROLLBACK.** This is why T4.1 (object-layer zero-unique) + T5.2 (final writer re-check) are hard gates.                                                                                                                                                                                           |
| Phase 6 (restore)     | Re-pause the offending job; restore the index `.bak`; resume one job at a time.                                                                                                                                                                                                                       |

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
