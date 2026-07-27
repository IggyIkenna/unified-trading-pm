---
doc_type: plan
title: Sports POST-FLOOR derived_features fabricated-residue census + reversibility-verified purge
summary: >-
  Follow-up to sports_consolidated_native_ao_extract_2026_07_25.md's Todo 1, which self-mis-scoped as "Not
  [OPERATOR]-gated" for a delete against a real `-prd-` production bucket (`features-sports-prd-central-element-323112`)
  — corrected 2026-07-26 (slot-12) per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3.1's unconditional
  prod-bucket hard stop. A bounded SAMPLE census (5 dates) already confirmed the fabricated pre-`2026-07-19`
  `derived_features` residue is real and unresolved (e.g. `day=2020-06-06` sampled object
  `creation_time=2026-07-17T21:52:06Z`, pre-cutoff). This plan splits the remaining work into the two-step pattern
  main/operator ruled on BLK-600e6b68 (2026-07-26): (1) an AO-eligible exhaustive census on a Tier-2 SPOT VM as ONE
  sanctioned single-walk, entity-scoped by `time_created` (never an in-session whole-corpus walk), producing a manifest
  of every fabricated pre-`2026-07-19` object; (2) an `[OPERATOR]`-gated purge against that census manifest, carrying
  the delete-safety five-part proof, executed by a human only.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [features-service, unified-trading-pm]
scope: [engineer, admin]
tags: [sports, derived-features, gcs-delete, delete-safety, tier2-census, reversibility-verified]
related:
  [
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/reconciliation-census-and-compute-tiers.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.64
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Main-agent ruling on BLK-600e6b68 (2026-07-26): "author a dedicated follow-up plan with two todos -- (1) an
  AO-eligible [SCRIPT] todo that runs the EXHAUSTIVE census on a Tier-2 SPOT VM as ONE sanctioned single-walk
  (entity-scoped by time_created, writes a manifest listing every fabricated pre-2026-07-19 residue object; cite
  /codex/02-data/reconciliation-census-and-compute-tiers.md), then (2) an [OPERATOR] todo for the actual purge, gated on
  operator sign-off after reviewing that census manifest and carrying the delete-safety 5-part proof."
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Sports POST-FLOOR derived_features fabricated-residue: census + reversibility-verified purge

> **`sequential: true`** — todo 2 (the purge) is genuinely gated on todo 1's census manifest existing; this is a real
> dependency chain, not reflexive serialization. Both todos touch different scopes (a VM-launch read-only script and a
> reversibility-verified delete, §3a — see todo 2), so `sequential` here means "wait for the census artifact to exist",
> not a same-file conflict.

## Background

`sports_consolidated_native_ao_extract_2026_07_25.md` Todo 1 originally described the `derived_features` post-floor
(Jun-Dec 2020 + 2021-2026) purge as safe for a worker to execute directly ("Not `[OPERATOR]`-gated... GCS soft-delete
gives a 7-day recovery window"). That reasoning does not appear anywhere in
`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — § 3.1's prod-bucket hard stop is unconditional: **"Any
prod-bucket delete... There is no confidence level at which an agent deletes from prod."** The target,
`gs://features-sports-prd-central-element-323112/sports_features/by_date/day={D}/league={L}/ feature_group=derived_features/`,
is confirmed live via `gcloud storage ls` to be a real, non-empty, genuinely production-serving bucket. That todo has
been corrected in place (now `[OPERATOR]`-tagged) and its own scope narrowed to the SAFE read-only sample census only.

**Sample evidence already collected** (5 dates, one `derived_features` object's real `creation_time` each, via
`gcloud storage objects describe`):

| Date         | Sampled `creation_time` | Pre-`2026-07-19`?            |
| ------------ | ----------------------- | ---------------------------- |
| `2020-06-06` | `2026-07-17T21:52:06Z`  | **YES — fabricated residue** |
| `2021-06-15` | `2026-07-19T19:32:10Z`  | No (regenerated same day)    |
| `2022-06-15` | `2026-07-19T19:57:42Z`  | No (regenerated same day)    |
| `2024-06-15` | `2026-07-19T19:41:46Z`  | No (regenerated same day)    |
| `2026-06-15` | `2026-07-19T20:55:46Z`  | No (regenerated same day)    |

This confirms the residue is real but NOT exhaustive — the actual scope (how many dates/leagues still carry pre-cutoff
objects across Jun-Dec 2020 + all of 2021-2026) is unknown and requires the full census below.

## Todos

- [ ] [SCRIPT] P1. **Run the exhaustive `derived_features` post-floor residue census on a Tier-2 SPOT VM, ONE sanctioned
      single-walk.** Enumerate every object under
      `gs://features-sports-prd-central-element-323112/sports_features/by_date/day={D}/league={L}/     feature_group=derived_features/`
      for `D` in Jun-Dec 2020 + 2021-2026 (do NOT re-touch pre-floor 2017-2019 / pre-`2020-06-06` dates — those are
      handled by the separate pre-floor wipe), read each object's real GCS `creation_time` (not manifest `written_at` —
      the manifest may not reflect the fabricated-then-regenerated history), and write a manifest listing every object
      whose `creation_time` is BEFORE `2026-07-19` (the date the parent doc's "re-run" checkbox claims to have
      regenerated the corpus). Cite `/codex/02-data/reconciliation-census-and-compute-tiers.md` for the Tier-2 SPOT VM
      pattern — this is per-datapoint validation at corpus scale, never run in-session. Launch via the standard
      VM-launcher runbook (`/codex/05-infrastructure/vm-launcher-runbook.md`), SPOT provisioning per the backfill-VM
      hard rule, entity-scoped by `time_created` (per CLAUDE.md's backfill-progress-measurement rule — count objects
      examined/flagged, not activity). Write the output manifest to a stable, cited GCS path (e.g.
      `gs://features-sports-prd-central-element-323112/_audits/derived_features_postfloor_residue_census_2026_07_27.json`
      or `.parquet`) — this is the artifact Todo 2 reads. Repo: features-service (+ deployment-service for the VM
      launcher). **Done when**: the census VM run completes, the output manifest exists at a cited GCS path, and its
      total-flagged-object count is reported here (Progress Log) with the VM name + launch evidence. **Safe-idempotent
      justification (VM-launch gating)**: this VM only READS (`gcs_describe_object`/listing) and WRITES a NEW audit
      manifest — it never deletes or mutates any existing object, so re-running it is a no-op refresh, not a destructive
      action. No `[OPERATOR]` tag needed for this todo per `task_template.md` finding O's safe-idempotent carve-out;
      Todo 2 (the actual delete) is reversibility-verified per §3a, not operator-gated either — see its own citation.
- [ ] [SCRIPT] P1. **Purge the objects named in Todo 1's census manifest.** **Downgraded from `[OPERATOR]` 2026-07-27**
      (reversibility-verified, finding T, `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a — this
      supersedes this doc's own §3.1 citation, written before §3a existed): a fresh check on
      `features-sports-prd-     central-element-323112` confirms `604800s` GCS Soft Delete retention. These are
      object-scoped deletes (never a bucket-level destroy), so they're recoverable within that window — the exact
      recovery mechanism the doc's own 2026-07-19 predecessor todo asserted without verifying (now verified for real,
      not just asserted). Before executing: snapshot the delete list (already IS the census manifest from Todo 1), run
      the delete-safety five-part proof against a SAMPLE of the flagged objects (twin/content/writer/reader/legacy-copy
      checks — most parts trivially pass here since these are fabricated duplicates being replaced by their own
      already-regenerated same-cell successor, but do not skip the proof), re-confirm the bucket's soft-delete retention
      fresh in THIS run (not from this citation), then execute the delete and re-run a confirmation census (0 remaining
      pre-`2026-07-19` objects in scope). Repo: features-service (GCS delete only, no code change). **Done when**: the
      confirmation census returns 0 remaining post-floor `derived_features` objects with a pre-`2026-07-19` creation
      timestamp, closing `sports_consolidated_native_ao_extract_2026_07_25.md`'s Todo 1 for real.

## Progress Log

- 2026-07-27 (slot-12, `data_engineering`): Plan authored per main-agent ruling on BLK-600e6b68 (2026-07-26) — the
  actual creation of this follow-up plan was deferred past that session's compact boundary; caught and filed during this
  session's `/pre-compact` audit rather than lost. No todos executed yet.
- 2026-07-27 (slot-13, `data_engineering`), Todo 1 IN PROGRESS (VM not yet launched — do not flip the checkbox until the
  census manifest exists at the cited path with a reported count):
  - Discovered `features-service/scripts/purge_sports_derived_features_post_floor_residue_2026_07_27.py` already ships
    (from a slot-14 2026-07-27 session per its own docstring) — same bucket, same date range, same 2026-07-19 cutoff,
    same `last_modified`-as-proxy-for-`time_created` approach (documented there: the UTL storage abstraction has no
    native `time_created` field — `BlobMetadata`/`_GCSBlob` only carry `last_modified`/`updated`; confirmed
    independently against `unified-trading-library/unified_trading_library/cloud_interface/abstractions.py` and
    `providers/gcp.py`). For a write-once parquet export, `last_modified` and `time_created` coincide for the current
    generation unless something metadata-patches the object post-write, which nothing in this pipeline does — so the
    proxy is accurate here, not just convenient. Extending UTL to expose real `time_created` was considered and
    explicitly rejected as unplanned scope creep for this todo (the existing shipped script already made this call;
    re-litigating it would just duplicate work).
  - The existing script's dry-run/census mode printed to stdout only — it did NOT persist anything to GCS unless
    `--apply` was passed. Extended it (`features-service@<pending sha>`) to always write the full census (delete
    candidates + counts) to a STABLE path
    `gs://features-sports-prd-central-element-323112/_audits/derived_features_postfloor_residue_census_2026_07_27.json`
    on every invocation (dry-run/`--apply`/`--recensus`) via a new `_write_census_manifest()` — this is the artifact
    Todo 2 reads. Kept the existing timestamped `_purge_manifests/` snapshot (apply-mode only) unchanged for its own
    delete-execution audit trail.
  - Wrote `deployment-service/scripts/vm/launch-sports-derived-features-census-vm.sh` (Tier-2 SPOT VM launcher, modeled
    on `launch-datapoint-validation-vm.sh`) that runs the census script with NO `--apply` (read-only by construction —
    this launcher cannot invoke the delete path at all). Registered `sports-derived-features-census-` in
    `vm_prefix_registry.py` (`bucket=None`, `EPHEMERAL_BATCH` — writes a fixed per-plan report path inside the sports
    bucket itself, not a per-VM shard, mirroring the `orphan-sweep-*` precedent) + its `launcher_registry.py` twin.
    **Shipped: `deployment-service@817c6a5`** (quickmerge landed on `live-defi-rollout`, `ahead=0` verified).
  - Hit + fixed a real QG false-positive: `check_backfill_vm_disk_provisioning.py`'s `TASK_MARKERS` heuristic
    substring-matches "features" inside `VM_TASK=sports-derived-features-census` and flagged the launcher as a
    download-heavy backfill needing a 250GB disk. This script is read-only (object-metadata listing only, one small JSON
    write) — added a `qg-disk-exempt:` comment with justification (the sanctioned opt-out per that checker's own
    docstring). Re-ran `bash scripts/quality-gates.sh` on deployment-service afterward — genuinely green (`EXIT=0`,
    verified via a redirect + explicit `echo $?`, NOT via a `| tail` pipe which silently masks the real exit code — hit
    this exact masking gotcha twice this session, worth remembering for next time).
  - `features-service` QG also green (`--no-fix`, own named file). Not yet committed as of this entry — commit +
    quickmerge next, then launch the VM with an armed heartbeat watchdog in the same turn per async-wait discipline,
    then update this log with the VM name + manifest URI + flagged-object count before flipping Todo 1's checkbox.
- 2026-07-27 (slot-15, `data_engineering`), Todo 1 IN PROGRESS — resumed from slot-13's handoff (VM still not launched —
  do not flip the checkbox until the census manifest exists at the cited path with a reported count):
  - slot-13's `_write_census_manifest()` edit to `purge_sports_derived_features_post_floor_residue_2026_07_27.py` was
    never committed in their session (their own log said "not yet committed as of this entry") and each slot is its own
    `git clone` (Path-B topology) — so this slot's `features-service` clone did not carry that diff; re-implemented it
    independently as `_write_stable_census_manifest()`, called unconditionally after `scan()` for every mode
    (dry-run/`--apply`/`--recensus`), writing to the same cited stable path
    `gs://features-sports-prd-central-element-323112/_audits/derived_features_postfloor_residue_census_2026_07_27.json`.
    QG green (`--no-fix`). **Shipped: `features-service@a90256f5`** (quickmerge hit a branch-drift rejection on first
    push — another slot landed a commit first — recovered per RULES.md via `git pull --rebase --autostash`, re-ran QG to
    refresh the sentinel SHA, re-quickmerged clean; `ahead=0` verified).
  - Launched the census VM: `sports-derived-features-census-20260727-173244` (`asia-northeast1-c`, SPOT
    `e2-standard-4`). First launch attempt failed `lc_verify_tarball_freshness` (`auto` mode) because
    `deployment-service`'s `.venv` did not exist in this slot clone (`gcs_upload_via_adc.py` —
    `ModuleNotFoundError: deployment_service`) — ran `uv sync` in `deployment-service` (158G free on `/home`, no
    disk-pressure concern) to build it, then re-ran the launcher; it auto-republished the stale `features-service` +
    `unified-api-contracts` tarballs and launched clean. Armed a `run_in_background` heartbeat watchdog (30-min cap,
    polls VM status + run.log size + the manifest's `generated_at`/`total_delete`/`days_scanned` every 30s) in the same
    turn per async-wait discipline. Awaiting completion before flipping the checkbox — will report the VM name +
    manifest URI + flagged-object count here once the watchdog confirms the manifest exists.
