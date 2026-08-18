---
doc_type: audit-result
title: "B22 bidirectional reconciliation — manifest⇄path, all asset groups (2026-08-18)"
summary: >-
  Synthesizes the B22 gate ("path ↔ manifest reconciled BOTH ways") per asset group from already-published
  manifest-side artifacts only — no new whole-corpus GCS walk. Direction 1 (manifest→path, phantom) is read from each
  AG's most recent `_index/phantom_audit_latest.json`. Direction 2 (path→manifest, orphan) is read from the most
  recent published whole-corpus orphan-sweep result where one exists, and reported as NOT ASSESSED — never a false
  "0 orphans" — where none does, per `orphan-object-detection.md` §3's honest-reporting corollary. Headline finding:
  path→manifest has never been assessed for cefi/tradfi/prediction, and the 2 AGs that have been measured (defi
  63.74% orphan_real, sports 27,348 objects) are ~26 days stale.
status: fail
nature: record
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [reconciliation, orphan, phantom, manifest, b22, single-walk, cross-cutting]
related:
  [
    /plans/active/data_pipeline_completion_2026_08_21.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md,
    /codex/02-data/orphan-object-detection.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
  ]
created: 2026-08-18
resulting_plan:
lib_version:
doc_versions_checked:
audited_scope:
  "B22 gate (data_pipeline_completion_2026_08_21.md) across all 5 asset groups (cefi, tradfi, defi, sports,
  prediction), raw-tick layer, manifest-side artifacts only — a synthesis read of already-published reports, zero
  new GCS reads, per B13 single-walk discipline."
date: 2026-08-18
auditor: "backend_engineer (slot 7, task cross_cutting_satellite_ao_dispatch_batch15-1d0c8d58f6ff)"
parent_epic: infrastructure_master
severity: P1
skill: data-pipeline-reconciliation
---

# B22 bidirectional reconciliation — manifest ⇄ path

> **Gate under test**: B22 (`data_pipeline_completion_2026_08_21.md`) — *"Every path entry is recorded in the
> manifest in canonical format, bidirectional: manifest→path (does every entry have an object?) AND path→manifest
> (does every object have an entry?). Manifest-driven, no new whole-corpus walk (B13)."*
>
> **Method — manifest as the sole read surface.** This report opens **zero new GCS listings and zero new
> whole-corpus walks**. Every number below is a **read-back** of an artifact some prior pass already wrote:
> - **Direction 1 (manifest→path, "does every entry have an object?")** is exactly what the phantom auditor computes
>   (a manifest row with no matching object = phantom) via prefix-scoped, single-walk-exempt listing — read from
>   each AG's `_index/phantom_audit_latest.json`, never re-run.
> - **Direction 2 (path→manifest, "does every object have an entry?")** is the **orphan** question
>   (`/codex/02-data/orphan-object-detection.md`). It is **structurally impossible to enumerate off the manifest
>   alone** — an orphan has no manifest row by definition, so the manifest cannot supply the work list for it. The
>   only sanctioned way to answer it without a new walk is to **read back a prior full-corpus orphan-sweep result**
>   (route #3, single-walk-exempt). Where none is published or none is fresh enough to trust, the honest verdict is
>   **`NOT ASSESSED`** — orphan-object-detection.md §3 is explicit that an unmeasured "0 orphans" must never be
>   reported, and that is followed here rather than worked around.

## Per-AG bidirectional verdict

| AG             | Direction 1 — manifest→path (phantom)                                                                                        | Direction 2 — path→manifest (orphan)                                                                                                                                          |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **cefi**       | **0 phantom** — `phantom_count=0` @2026-07-27T17:38:18Z (**21 days stale** as of the 08-17 report; `instruments-store-cefi` has no phantom/reprobe audit at all — declared coverage gap) | **NOT ASSESSED this cycle** — the 08-17 four-surface report explicitly ran no orphan-object sweep. An orphan-sweep execution plan is `active` (`cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md`, last touched 2026-08-03) but has not published a terminal per-AG orphan count into a reconciliation report. |
| **tradfi**     | **16,997 phantom** @2026-07-30 (**18 days stale**; **10× jump** from 1,635 @2026-07-14 — flagged as its own finding, not re-derived here) | **NOT ASSESSED** — 08-17 report states explicitly: *"Orphans: NOT ASSESSED (no whole-corpus walk this run — per orphan-object-detection.md §3)."* AWS-side bucket also not probed this run. |
| **defi**       | **1,558 phantom** @2026-07-19T12:31:33Z (07-24 report; not re-run since)                                                       | **MEASURED — 63.74% orphan_real** (15,865,384 of 24,890,959 objects), read back from the 2026-07-23 terminal orphan sweep (`orphan-sweep-defi-20260723-043605`, published in `plans/active/issues/defi_orphan_sweep_test_artifact_prod_leak_2026_07_24.md`), reused per single-walk discipline, not re-walked. **Never delete-eligible** (orphan = only-copy, not a duplicate). |
| **sports**     | `market-data-tick-sports` (raw-tick, in-scope for B22): **phantom_audit_latest.json ABSENT** — declared coverage gap across multiple runs (07-24, 08-01); S3-phantom verdict not independently checked. `instruments-store-sports` (reference bucket, separate scope): `phantom_count=0` @2026-07-25T02:23:45Z. | **MEASURED (stale) — 27,348 `E_orphan_real` objects**, read back from `_index/audit/orphan_sweep_sports.parquet` (single-walk-exempt route #3) in the 2026-07-24 report — HIGH severity, reported "active and growing" at that time; not re-measured since. |
| **prediction** | **2,028 phantom** @2026-07-13T15:14:37Z (down from a 2026-06-28 baseline of 19,675 after the bundle-atom-exemption fix; **11-12 days stale** relative to the 07-24 report that cited it) | **NOT ASSESSED** — 07-24 report states explicitly: *"NOT ASSESSED (no whole-corpus walk this run)."* Note the phantom reconciler itself must never be run against prediction (CQG bundle grain, §2.2 of the four-surface procedure) — a structural exclusion, not a gap. |

## Headline finding — direction 2 is the one that gets skipped, exactly as the gate text warns

B22's own text calls this out: *"The path→manifest direction is the one that gets skipped, and it is the one that
matters: an object in GCS with no manifest row is invisible to every coverage number we quote."* This synthesis
confirms it empirically:

- **3 of 5 asset groups (cefi, tradfi, prediction) have NEVER had a path→manifest (orphan) verdict published** in
  their most recent four-surface reconciliation report. Their honest orphan status today is `NOT ASSESSED`, not
  "clean."
- **The 2 asset groups that HAVE been measured are both materially non-trivial**: defi at 63.74% orphan_real (a
  supermajority of the raw-tick corpus by object count is present on disk with zero manifest coverage — this is a
  pre-existing, already-tracked finding, not new here) and sports at 27,348 objects, both last measured over three
  weeks ago (2026-07-23/24) and not re-verified since.
- **This is not a new discovery** — defi's number is already load-bearing in `defi_orphan_sweep_test_artifact_prod_leak_2026_07_24.md`
  and sports's in its own 07-24 report — but B22's own acceptance bar ("reconciled BOTH ways, per AG") is **not met**
  for cefi, tradfi, or prediction, and the defi/sports numbers that DO exist are stale enough (~26 days) that neither
  should be quoted as current without a fresh Tier-2/route-3 read-back.

## Direction 1 — a secondary finding

tradfi's phantom count jumped 10× (1,635 → 16,997) between 2026-07-14 and 2026-07-30 and has not been re-measured in
the 18 days since — already flagged as its own todo in the tradfi 08-17 report (`Run a fresh phantom audit for
tradfi`), not duplicated as a new todo here. cefi's raw-tick phantom count is clean (0) but 21 days stale, and its
`instruments-store-cefi` bucket has never had a phantom audit at all. sports's raw-tick bucket has never had a
phantom audit published — the S3-phantom direction is unmeasured there for the SAME reason the S1-orphan direction
is: no audit has ever targeted that bucket.

## What this report is and is not

- **Is**: a synthesis of already-published, manifest-side (or manifest-adjacent single-walk-exempt) artifacts,
  answering the bidirectional question honestly per AG, including where the honest answer is "we don't know."
- **Is not**: a new measurement. No GCS bucket was listed and no corpus was walked to produce this report — every
  number cited above already existed in a prior report or plan doc before this one was written, consistent with
  B13's single-walk discipline and the B22 done-when ("citing the manifest as the sole read surface").
- **Does not** change any AG's canonicalisation verdict (B21) or schema-locking verdict (B23) — those are separate
  gates, tracked by batch15 items 1 and 3.

## Follow-up (tracked, not prose)

- [ ] [DATA] P1. Run a fresh path→manifest (orphan) pass for **cefi** — the only surface with an active-but-unpublished
      sweep plan (`cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md`) and no terminal count in any
      reconciliation report; read back its results into the next `/data-pipeline-reconciliation --asset-group cefi`
      run rather than re-walking.
- [ ] [DATA] P2. Run a fresh path→manifest (orphan) pass for **tradfi** and **prediction** — both have never had one;
      tradfi via a Tier-2 route-3 single-walk (bundle onto the next scheduled corpus walk, do not open a new one
      standalone), prediction via the sports-style `_index/audit/orphan_sweep_prediction.parquet` read-back if/when
      one is produced (none exists today).
- [ ] [DATA] P2. Re-run (bundle, do not open standalone) the defi and sports orphan sweeps — both last measured
      2026-07-23/24, now ~26 days stale; the defi 63.74% and sports 27,348 figures should not be quoted as current
      coverage without a fresher read-back.
- [ ] [DATA] P3. Publish `phantom_audit_latest.json` for `instruments-store-cefi` and `market-data-tick-sports` —
      both buckets have never had a phantom (manifest→path) audit target them at all, a distinct gap from the
      orphan-side gap above.

## Progress Log

- **2026-08-18 (slot 7, backend_engineer, task `cross_cutting_satellite_ao_dispatch_batch15-1d0c8d58f6ff`)**: authored
  from a synthesis read of the 5 most recent per-AG `/data-pipeline-reconciliation` reports
  (`data_pipeline_reconciliation_{cefi_2026_08_17, tradfi_2026_08_17, sports_2026_08_16 + sports_2026_07_24 for the
  only-published orphan figure, defi_2026_07_24, prediction_2026_07_24}.md`) plus the cefi orphan-sweep execution
  plan. No new GCS read of any kind was performed.
