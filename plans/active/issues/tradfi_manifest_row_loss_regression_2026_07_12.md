---
doc_type: issue
title: TradFi manifest — 1.02M distinct rows disappeared from _index between 2026-07-10 and 2026-07-12 (unexplained)
summary:
  The tradfi-prd `_index/availability_index.parquet` lost 1,017,024 distinct manifest rows (by natural key) between the
  2026-07-10T11:33Z snapshot (6,107,337 rows) and a fresh read on 2026-07-12T03:34Z (5,088,405 rows). Root cause NOT yet
  identified — ruled out `cleanup_legacy_twins.py` (reads manifest, never writes it) and ruled out a benign natural-key
  dedup (distinct-key count also dropped by ~1.02M, not just raw row count). This blocks `tradfi_v9_stage1_finish` task
  4 (manifest rebuild) and calls into question every downstream gate that reads this manifest (task 2 orphan-sweep E=0,
  task 7 EU-seed, task 8 IS catalogue) since all were certified against a manifest that has since silently lost
  coverage.
status: open
resolved_by:
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [tradfi, manifest, data-correctness, regression, row-loss, big-finding]
related:
  [
    tradfi_v9_stage1_finish_2026_07_06.md,
    tradfi_manifest_canonicalisation_2026_06_01.md,
    migration_verification_orphan_safety_2026_06_10.md,
  ]
created: 2026-07-12
source:
  - tradfi_v9_stage1_finish_2026_07_06.md task 4 dispatch (slot-8 sonnet/high)
assigned_vm: planning
assigned_role: data_engineering
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.5
drift_direction: advance-code
parent_epic: instruments_master
execution_scope: orchestrator-agent
depends_on: []
last_updated: 2026-07-12
locked_by:
locked_since:
---

# TradFi manifest — 1.02M-row disappearance between 2026-07-10 and 2026-07-12

> **🔴 BIG FINDING — data-correctness regression, NOT fixed this session.** Filed by slot-8 (sonnet/high) while
> dispatched to `tradfi_v9_stage1_finish` task 4 (E5 manifest rebuild). Re-verifying task 4's gate surfaced this instead
> of the expected "same 13,971-row v4 tail, still waiting on fleet-drain" state from the prior 3 sessions. **This
> FREEZES confident progress on task 4/task 11/task 2-dependent work for tradfi** until root-caused — every downstream
> gate this plan certified GREEN (orphan-sweep E=0, EU-seed 0-unseeded, IS catalogue freshness) was certified against a
> manifest state that has since silently shrunk by ~1M rows, so those certifications can no longer be trusted without a
> re-check.

## What I found

Dispatched to `tradfi_v9_stage1_finish_2026_07_06.md` task 4 ("Rebuild the tradfi manifest"). Per the plan's own
history, the E5 rebuild tool already ran to completion 2026-07-07 and the only known-remaining gap was a static
13,971-row `schema_version=4` tail gated on task 10 (fleet-drain). Re-verified fleet-drain state first (still FALSE —
see below), then re-read the manifest to confirm the tail count was unchanged, as the last 3 sessions had done. It was
NOT unchanged — the corpus itself had shrunk.

**Fleet-drain state (re-confirmed, 2026-07-12T03:3x UTC, via direct Compute API — `gcloud` is broken in this slot per
the documented snap-confine issue, same as every prior session)**: 8 `tradfi-bf-*` VMs still `RUNNING` in
`asia-northeast1-c` (`tradfi-bf-cboe-ohlcv-1m-vx-2026-*`, `tradfi-bf-cme-ohlcv-1m-{cl,es,gc,hg,ng,nq,si}-2025-*`, launch
timestamps 2026-07-11/07-12 — i.e. the fleet has been cycling, not draining). Task 10 remains correctly
BLOCKED-PREREQUISITES; unchanged from the 2026-07-10 finding.

**Manifest row-count comparison** (`market-data-tick-tradfi-prd-central-element-323112`, read via UTL
`StorageClient.download_bytes` — `gcloud`/`gsutil` both broken in-slot):

| Snapshot                                                                                                                                  | Read at           | Total rows     | `schema_version=9` | `schema_version=4` (v4 tail) |
| ----------------------------------------------------------------------------------------------------------------------------------------- | ----------------- | -------------- | ------------------ | ---------------------------- |
| `_index/snapshots/pre_tradfi_source_restamp_20260710T113305Z.parquet` (last verified-fresh snapshot, used for the 2026-07-10 E7 re-audit) | 2026-07-10T11:33Z | 6,107,337      | 6,093,366          | 13,971                       |
| `_index/availability_index.parquet` (live, fresh — `get_blob_metadata` confirms `last_modified=2026-07-12T03:34:03Z`, not stale/cached)   | 2026-07-12T03:34Z | 5,088,405      | 5,074,434          | 13,971                       |
| **Delta**                                                                                                                                 |                   | **-1,018,932** | **-1,018,932**     | **0 (unchanged)**            |

The v4 tail is byte-identical in count to the 2026-07-08/07-10 readings — that specific population is untouched. The
loss is entirely within rows that WERE `schema_version=9` (`captured`/`empty_confirmed` rows), i.e. rows the plan had
already certified as canonical and correctly captured.

**`capture_status` breakdown of the loss** (old → new):

| `capture_status`       | 2026-07-10 | 2026-07-12 | delta    |
| ---------------------- | ---------- | ---------- | -------- |
| `empty_confirmed`      | 3,352,487  | 3,037,867  | -314,620 |
| `captured`             | 2,326,685  | 1,620,804  | -705,881 |
| `attempted_failed`     | 343,079    | 342,211    | -868     |
| `expected_unattempted` | 85,086     | 87,523     | +2,437   |

Real `captured` rows (actual object-backed manifest entries) account for the majority of the loss (705,881 of 1,018,932)
— this is not a cosmetic honest-absence-bookkeeping change.

**Ruled out — natural-key duplicate collapse (benign explanation)**: computed a natural key
(`date, venue, asset_group, data_type, instrument_type, underlying, instrument_id, pipeline_mode`) on both snapshots.
Distinct-key count ALSO dropped by the same order of magnitude (5,723,660 → 4,711,672, a drop of 1,011,988) — if this
were merely deduplication of previously-duplicated rows, the distinct-key count would be unchanged or would have
INCREASED as a share of total rows, not dropped by nearly the same amount as the raw row count. **Direct key-set diff
confirms it definitively**: 1,017,024 keys present in the 2026-07-10 snapshot are absent from the 2026-07-12 read (only
5,036 new keys were added in the same window — consistent with the ~97K rows whose `written_at` falls after 2026-07-10,
the expected live-writer trickle, not a rebuild). Sample of missing keys spans multiple venues (CME, NYSE confirmed in a
random sample), multiple `data_type`s (`ohlcv_1s`, `ohlcv_1m`), and a wide date range (2021-01 through 2026-03) — this
is a broad, corpus-wide loss, not an isolated shard or a single bad write.

**Ruled out — `cleanup_legacy_twins.py --apply` (the operator-gated bucket-delete this plan explicitly HARD-STOPs on)**:
found a NEW, previously-undocumented artifact `_index/audit/legacy_dup_delete_list_tradfi.parquet` (1,706,332 rows,
`SAFE-TO-DELETE` classification) — this is `cleanup_legacy_twins.py --dry-run`'s own report output (task 11's sanctioned
prep step, never `--apply`). Read the script source directly (`instruments-service/scripts/cleanup_legacy_twins.py`): it
only calls `client.delete_blob()` on GCS objects and `client.download_bytes()` to READ the manifest for twin
verification — **it has no code path that writes to `_index/availability_index.parquet`**, so even an (unauthorized)
`--apply` run of this specific tool cannot explain manifest rows disappearing. Confirmed via `grep` for
`upload_bytes`/`ManifestWriter`/`to_parquet` in the file — zero hits.

**`written_at` distribution of the surviving 5,088,405 rows**: the bulk (3.37M rows) still carries `written_at` from
2026-07-07 (the original E5 rebuild day); only ~96,924 rows carry a `written_at` after 2026-07-10. This rules out "a
fresh full rebuild overwrote the index with a smaller correct result" — a full rebuild would stamp a fresh `written_at`
on every row it (re-)emits. Instead, the OLD rows (with their original `written_at` preserved) are simply gone from the
new file — consistent with some process reading the main index, dropping ~1M rows via an incorrect
filter/anti-join/merge, and writing the result back over the same object path, rather than a legitimate full-corpus
rebuild.

**Venue/data_type/date breakdown of a 200K-row sample of the missing keys** (confirms broad corpus-wide scope, not one
bad shard): venues
`CME=114,023 · NYSE=56,788 · NASDAQ=26,990 · CBOE=1,419 · KRX=316 · YAHOO_FINANCE=237 · ICE=136 · FX=91`; `data_type`
`ohlcv_1s=114,625 · ohlcv_1m=84,777 · ohlcv_24h=354 · ohlcv_15m=237 · trades=7`; date range `2019-01-05` through
`2026-07-02`. Sample `capture_status`: `captured=138,099 · empty_confirmed=61,737 · attempted_failed=164` (proportions
consistent with the full-corpus delta table above). Every major venue and a 6-year date span is represented — this rules
out a single misconfigured shard or a narrow-range bad write.

**Not yet identified**: which script/job actually performed the write. This slot has no `gcloud`/`gsutil` access
(snap-confine) and therefore no Cloud Logging / Cloud Run job history visibility to identify the writer process or
another slot's in-flight session. This needs either (a) an operator/main-agent check of Cloud Logging for writes to
`gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` around
2026-07-10T11:33Z–2026-07-12T03:34Z, or (b) checking other active slots' sessions/commits for any manifest-editing
script run against tradfi in that window.

## Writer identified (2026-07-12, slot-7)

**Cloud Logging was a dead end** — confirmed GCS Data Access audit logs are NOT enabled for `central-element-323112`
(`gcloud logging read` against `cloudaudit.googleapis.com%2Fdata_access` filtered to any `storage.googleapis.com`
resource, unrestricted by time, returns zero rows; the only `data_access` entries present are BigQuery
`jobservice`/`InsertJob` calls from the billing-export pipeline). This is a project-level gap, not a slot-access gap —
even an operator with full Cloud Logging access would find nothing here without first enabling Data Access audit logs
for the storage service (a separate, forward-looking fix — see new P2 todo below).

**Identified instead via Cloud Scheduler + Cloud Run Jobs configuration + GCS object custom metadata**:

- The canonical object carries consolidator-stamped custom metadata on every write — `consolidator_run_at` /
  `consolidator_content_write_at` (both `2026-07-12T03:57:00.156735+00:00` on the freshest read at investigation time) —
  which is the consolidator's own provenance marker (`unified_trading_library/manifest_consolidator.py`, keys
  `_CONSOLIDATOR_RUN_AT_KEY` / `_CONSOLIDATOR_CONTENT_WRITE_AT_KEY`).
- **Writer = Cloud Run Job `uts-prod-manifest-consolidator-market-data-tradfi`** (project `central-element-323112`,
  region `asia-northeast1`), triggered every 1 minute continuously (`*/1 * * * *`, state `ENABLED`) by Cloud Scheduler
  job `uts-prod-manifest-consolidator-market-data-tradfi-cron` via
  `uts-prod-batch-sa@central-element-323112.iam.gserviceaccount.com`. Command:
  `python -m unified_trading_library.manifest_consolidator --bucket market-data-tick-tradfi-prd-central-element-323112`,
  image `asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/market-tick-data-service:latest`.
  Confirmed this is the ONLY configured writer of this bucket's `_index/availability_index.parquet` — no other Cloud
  Scheduler/Cloud Run job in the project targets this bucket/path (checked the full `gcloud scheduler jobs list`
  - `gcloud run jobs list` output for anything else tradfi/market-data-adjacent).
- Cloud Run execution history for this job (`gcloud run jobs executions list`) shows **zero failed executions inside the
  loss window** (2026-07-10T11:33Z–2026-07-12T03:34Z, sampled) — every execution in the fetched range reports
  `Execution completed successfully` (32–67s typical duration). So if the loss happened via this job, it happened inside
  a "successful" merge cycle, not a crash/partial-write — rules out "job died mid-write" as the mechanism. (Note:
  execution-history retention doesn't cover the full window contiguously — earliest execution reliably fetched
  inside-window starts 2026-07-11T11:10Z, so the first ~23.5h of the window, 2026-07-10T11:33Z–2026-07-11T11:10Z, is not
  independently confirmed failure-free from this source alone.)
- **This is a continuously-running incremental writer** (1-cycle-per-minute, merge/anti-join/prune every time), not a
  one-shot job — so there is no single "the commit that wrote it" the way there would be for a one-off script. Instead,
  the exact _code_ running during the loss window changed multiple times, because
  `unified_trading_library/manifest_consolidator.py` (the shared script every asset group's consolidator job runs) was
  under active, rapid bug-fixing this exact week:
  - `unified-trading-library@0de04b6e` — fixed the incremental merge's `survivors` CTE streaming pre-existing canonical
    rows through with **zero self-dedup** (any duplicate that ever entered the canonical, by any mechanism, persisted
    forever). Real, confirmed data-correctness bug in this exact script. Landed/deployed 2026-07-10 per
    `defi_manifest_consolidator_duplicate_race_2026_07_10.md`. Its own P2 cleanup pass found tradfi's genuine-duplicate
    count was only 346 rows / 173 groups (cleaned 2026-07-10) — far too small to explain a 1,018,932-row loss, so this
    specific bug is not the cause, but it establishes this script had at least one other real correctness gap fixed
    inside the loss window.
  - `unified-trading-library@800af156` — follow-on fix for a scaling regression in the `0de04b6e` fix itself (the
    survivors-side self-dedup window function ran over the ENTIRE untouched canonical every cycle, OOM-killing the defi
    job once its canonical passed ~14M rows). Also landed 2026-07-10. Tradfi's canonical (~5-6M rows) is well under that
    threshold, and no failed tradfi executions were observed in-window (see above), so this is a weaker lead for tradfi
    specifically, but it's the same script, same window.
  - `unified-trading-library@d3c36842` ("fix(consolidator): widen lock TTL 90s->300s") — landed 2026-07-12T02:37:49Z
    UTC, pulled into `market-tick-data-service@a1361fc9` (02:52:57Z), built+pushed as image tag `20e854c`/`0.92.0`/
    `latest` at **2026-07-12T03:01:48Z** (Artifact Registry `createTime`) — i.e. deployed ~33 min BEFORE the issue doc's
    03:34Z read that showed the loss already present, so this specific fix's deploy cannot be the ORIGINATING cause (the
    loss predates it), though the bug it fixes — the old 90s TTL being shorter than real cycle durations — was actively
    occurring in production throughout 2026-07-11 per the commit's own cited evidence (93-121s observed cycles for the
    sibling defi cron that day). **However**, per the fix author's own conclusion (same day,
    `defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md` summary): "no data corruption risk; the canonical
    write's CAS already protects against that" — i.e. this lock race is documented as causing wasted concurrent merges /
    SIGKILLs, not row loss. Tradfi's own observed cycle durations (32-67s, sampled post-fix) are comfortably under even
    the old 90s TTL, which weakens (but doesn't rule out — no pre-fix tradfi cycle-duration samples were captured) this
    as tradfi's mechanism specifically.
  - Sample of a 200K-row missing-key set (from the original evidence table above): `written_at` values are original
    (mostly 2026-07-07), consistent with an INCREMENTAL merge cycle dropping pre-existing `survivors` rows rather than a
    full rebuild — i.e. whatever dropped the rows did so via this same incremental survivors/contested/prune code path,
    not a competing tool.

**Bottom line for this todo**: the script is `unified_trading_library/manifest_consolidator.py`; the job is Cloud Run
Job `uts-prod-manifest-consolidator-market-data-tradfi` (Cloud Scheduler-triggered, `*/1 * * * *`); there is no single
smoking-gun commit — the loss occurred across some subset of this job's continuous 1-minute cycles during the window,
running whichever consolidator revision was live at each moment, several of which had real, confirmed correctness or
scaling bugs in the SAME merge/prune code path this week. Pinning the exact cycle(s)/commit(s) actually responsible (vs.
merely being deployed during the window) is the next todo below — it needs either finer-grained row-count snapshots than
exist, or a direct code read of `_duckdb_merge_payload`'s survivors/contested/prune SQL to find a bug that can drop
`survivors` rows outright (as opposed to the already-fixed no-dedup / OOM bugs above).

## Why it matters

- This is the SAME manifest every other checkbox in `tradfi_v9_stage1_finish_2026_07_06.md` certified against: task 2's
  orphan-sweep `E=0` (certified 2026-07-10T17:17Z, i.e. BEFORE this loss — may no longer hold if the missing rows
  correspond to canonical objects that now have no manifest row, which is exactly the orphan-sweep's Class-E
  definition), task 7's EU-seed "0 unseeded candidates" (certified against a manifest that has since lost ~1M rows), and
  task 8's IS catalogue freshness (built from `by_date/` snapshots, likely also affected).
- Per workspace HARD RULE ("Data pipeline correctness is the heartbeat" — a RED data audit FREEZES layer-N+1 work): this
  is exactly that class of finding. Task 4 cannot be meaningfully progressed (rebuilding on top of a manifest that is
  actively losing rows for an unknown reason risks compounding the problem or masking it).
- Task 11 (legacy-twin bucket deletes) is especially sensitive here — its own `--dry-run` safety check (`is_deletable`
  requiring "canonical twin captured in manifest") depends on manifest completeness; if the MANIFEST itself is silently
  losing captured rows, a future dry-run could misclassify a legacy object as safe-to-delete when its canonical twin's
  manifest row has been (incorrectly) dropped — even though task 11 stays operator-gated for the actual delete, its prep
  evidence quality depends on this being fixed first.

## Recommended decision

1. ~~Operator/main-agent: identify the writer.~~ **DONE 2026-07-12 (slot-7)** — see "Writer identified" above. Writer =
   Cloud Run Job `uts-prod-manifest-consolidator-market-data-tradfi` running
   `unified_trading_library.manifest_consolidator`; no single commit pinned as the exact cause yet (next todo).
2. **Do NOT run task 4 (E5 rebuild) again until root-caused** — re-running the rebuild on top of an already-lossy index
   could either mask the bug (re-adding the missing rows and hiding the regression) or compound it if the same bug is
   triggered by the rebuild itself.
3. **Do NOT proceed with task 11's `--dry-run` prep** using the current manifest state until this is resolved — its
   evidence quality depends on manifest completeness.
4. Once root-caused: if recoverable from a snapshot (the 2026-07-10T11:33Z snapshot pre-dates the loss and is still in
   `_index/snapshots/`), consider restoring the missing 1,017,024 rows via a targeted re-add rather than a full re-scan,
   to avoid another multi-hour full-corpus operation.

## Todos

- [x] ✅ [DATA] P0. Identify the exact script/job/commit that wrote `_index/availability_index.parquet` for
      `market-data-tick-tradfi-prd-central-element-323112` between 2026-07-10T11:33Z and 2026-07-12T03:34Z. **Done
      2026-07-12 by slot-7.** See "Writer identified" below — Cloud Logging turned out unnecessary; identified via Cloud
      Scheduler/Cloud Run Jobs config + GCS object custom metadata instead. `gcloud` IS usable in-slot via the non-snap
      SDK at `/home/ubuntu/google-cloud-sdk/bin/gcloud` (the snap `gcloud`/`gsutil` are broken by snap-confine as prior
      sessions found, but this alternate install has working ADC and was not tried before).
- [ ] [DATA] P0. Root-cause why the identified writer (`unified_trading_library/manifest_consolidator.py`'s
      `_duckdb_merge_payload` incremental merge, run by Cloud Run Job
      `uts-prod-manifest-consolidator-market-data-tradfi`) dropped 1,017,024 distinct manifest rows
      (`captured`=-705,881, `empty_confirmed`=-314,620) while leaving the 13,971-row v4 tail untouched, and fix the bug
      (repo: unified-trading-library, the shared consolidator — NOT market-tick-data-service, which only vendors it).
      Start from the `survivors`/`contested`/prune SQL in `_duckdb_merge_payload` — 3 real bugs in this exact code path
      were found+fixed this same week (`0de04b6e` no-dedup-on-survivors, `800af156` OOM-scaling regression in that fix,
      `d3c36842` lock-TTL race) but none is yet CONFIRMED to explain outright row loss (as opposed to duplication or
      wasted-compute); the mechanism suggested by the "Writer identified" evidence (old `written_at` preserved on
      survivors, so a full rebuild is ruled out) is a bug in the survivors ANTI JOIN or the post-merge prune step
      incorrectly excluding/deleting rows it shouldn't. See "Writer identified" section above for the full lead list.
- [ ] [DATA] P0. Restore the 1,017,024 missing rows — either replay them from
      `_index/snapshots/pre_tradfi_source_restamp_20260710T113305Z.parquet` (targeted re-add of exactly the missing
      keys, verified via the same key-set diff this issue doc used) or via a fresh full E5 rebuild once the root cause
      is fixed and confirmed non-recurring (repo: market-tick-data-service).
- [ ] [DATA] P1. Re-run task 2's orphan-sweep (`migration_orphan_sweep.py --asset-group tradfi`) after the restoration
      to re-confirm `orphan_class_E=0` still holds — the 2026-07-10T17:17Z GREEN certification may not survive against
      the current (or restored) manifest state (repo: instruments-service).
- [ ] [DATA] P2. Add a row-count sanity check (delta vs. the last known-good snapshot, alert on any drop >0.1%) to
      whichever job writes `_index/availability_index.parquet`, so a future regression of this class is caught
      immediately rather than 2 days later by an unrelated task's re-verification (repo: market-tick-data-service or
      unified-trading-library, wherever the writer/consolidator lives).
- [ ] [INFRA] P2. Enable GCS Data Access audit logging (`storage.googleapis.com` data-write, at minimum, project-wide or
      on the `*-prd-central-element-323112` market-data buckets) — this investigation found it is currently OFF
      project-wide (confirmed: `cloudaudit.googleapis.com/data_access` has zero `storage.googleapis.com` entries, only
      BigQuery). Its absence is why this todo had to be solved via Cloud Scheduler/Cloud Run config + object custom
      metadata instead of a direct "who wrote this object and when" log query — much slower and less precise than Cloud
      Logging would have been, and won't work for any writer that doesn't self-stamp custom metadata like the
      consolidator does (repo: unified-trading-pm or deployment-service, wherever project audit-log config is IaC'd;
      needs an operator/main-agent decision on log-volume cost tradeoff before enabling broadly).

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-12** — slot-7 (sonnet/high, data_engineering). Closed todo 1 (writer identification). Cloud Logging was a
  dead end (GCS Data Access audit logs off project-wide, confirmed via direct query) but `gcloud` DOES work in-slot via
  the non-snap SDK at `/home/ubuntu/google-cloud-sdk/bin/gcloud` (contrary to slot-8's finding that `gcloud` is broken
  here — that's true only of the snap install; ADC + this alternate binary work fine). Identified the writer via Cloud
  Scheduler (`uts-prod-manifest-consolidator-market-data-tradfi-cron`, `*/1 * * * *`) → Cloud Run Job
  `uts-prod-manifest-consolidator-market-data-tradfi` → `unified_trading_library.manifest_consolidator` (running from
  `market-tick-data-service:latest`), corroborated by the canonical object's own `consolidator_run_at`/
  `consolidator_content_write_at` custom metadata. Confirmed via `gcloud run jobs executions list` that no executions
  failed inside the (partially-sampled) loss window — the loss happened inside "successful" merge cycles, not a crash.
  Traced 3 real bug-fix commits landing in this exact script this same week (`unified-trading-library@0de04b6e`,
  `@800af156`, `@d3c36842`) as leads for the next todo, cross-referencing 2 sibling issue docs
  (`defi_manifest_consolidator_duplicate_race_2026_07_10.md`,
  `defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md`) filed by slot-3 on the same script. None of the 3 is
  yet CONFIRMED as the row-loss mechanism (details + full reasoning in "Writer identified" above) — root-causing which
  one (or a 4th, undiscovered bug) is the next todo, not done here. Added a new P2 todo (enable GCS Data Access audit
  logging — found it's off project-wide, which is why this had to be solved indirectly). No code change — this is a
  data-state finding; issue doc itself ships via the PM `docs(plans):` carve-out.
- **2026-07-12** — Filed by slot-8 (sonnet/high), dispatched to `tradfi_v9_stage1_finish` task 4. Full characterization
  above; root cause NOT yet identified (needs Cloud Logging access this slot lacks). No code change — this is a
  data-state finding, no repo commit for this entry (issue doc itself ships via the PM `docs(plans):` carve-out).
