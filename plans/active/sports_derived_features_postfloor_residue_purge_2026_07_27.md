---
doc_type: plan
title: Sports POST-FLOOR derived_features fabricated-residue census + operator-gated purge
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
tags: [sports, derived-features, gcs-delete, delete-safety, tier2-census, operator-gated]
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

# Sports POST-FLOOR derived_features fabricated-residue: census + operator-gated purge

> **`sequential: true`** — todo 2 (the purge) is genuinely gated on todo 1's census manifest existing; this is a real
> dependency chain, not reflexive serialization. Both todos touch different scopes (a VM-launch read-only script vs an
> `[OPERATOR]`-only delete), so `sequential` here means "wait for the census artifact to exist", not a same-file
> conflict.

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
      action. No `[OPERATOR]` tag needed for this todo per `task_template.md` finding O's safe-idempotent carve-out; the
      actual delete (Todo 2) is the one that carries the hard stop.
- [ ] [OPERATOR] P1. **Purge the objects named in Todo 1's census manifest — human-executed only.** Per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3.1 (prod-bucket hard stop) this step is NEVER
      autonomous. Before executing: snapshot the delete list (already IS the census manifest from Todo 1), run the
      delete-safety five-part proof against a SAMPLE of the flagged objects (twin/content/writer/reader/legacy-copy
      checks — most parts trivially pass here since these are fabricated duplicates being replaced by their own
      already-regenerated same-cell successor, but do not skip the proof), then execute the delete and re-run a
      confirmation census (0 remaining pre-`2026-07-19` objects in scope). Repo: features-service (GCS delete only, no
      code change). **Done when**: the confirmation census returns 0 remaining post-floor `derived_features` objects
      with a pre-`2026-07-19` creation timestamp, closing `sports_consolidated_native_ao_extract_2026_07_25.md`'s Todo 1
      for real.

## Progress Log

- 2026-07-27 (slot-12, `data_engineering`): Plan authored per main-agent ruling on BLK-600e6b68 (2026-07-26) — the
  actual creation of this follow-up plan was deferred past that session's compact boundary; caught and filed during this
  session's `/pre-compact` audit rather than lost. No todos executed yet.
