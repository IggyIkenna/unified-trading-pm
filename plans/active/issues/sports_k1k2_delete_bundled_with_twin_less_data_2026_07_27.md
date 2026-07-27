---
doc_type: issue
title:
  K1/K2 "old non-canonical" GCS-object delete was unsafe as scoped — ~27.5% of the population is twin-less, sole-copy
  data
summary: >-
  sports_satellite_ao_dispatch_batch7_2026_07_27.md todo 1 asked an AO worker to execute a bulk DELETE of "old
  non-canonical K1/K2 GCS objects" in market-data-tick-sports-prd, citing the §3a soft-delete-retention carve-out as
  sufficient authorization. Investigation before executing (BLK-2cf85627, operator-confirmed) found the population is
  NOT uniformly redundant: a live-writer window (2026-07-22 K1 ship through 2026-07-27 revert, ~5 days) produced
  UPPERCASE-only objects with no lowercase twin at all — the same population the plan's own Deferred section already
  flagged as "~27.5% of sampled uppercase-keyed rows have no lowercase GCS twin yet". A blind delete would have
  permanently destroyed that slice. HELD per operator decision; the K1/K2 casing-revert migration (copy twin-less rows
  to lowercase) must land first.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [delete-safety, k1-k2, casing-migration, sports, gcs, data-correctness, blocked-question]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch7_2026_07_27.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-07-27
parent_epic: sports_master
priority: P1
source: "BLK-2cf85627 (slot 4, 2026-07-27) — operator answered Option B, confirming the finding and directing this doc."
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: research
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.8
last_updated: 2026-07-27
supersedes:
superseded_by:
depends_on: []
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

## What I found

`sports_satellite_ao_dispatch_batch7_2026_07_27.md` todo 1 (P0) asked me to "Execute the 5-part-proof-gated DELETE of
old non-canonical K1/K2 GCS objects + the ~7,251 `api_football` captured-cell objects" in
`market-data-tick-sports-prd-central-element-323112`, citing a fresh §3a `gcs_bucket_soft_delete_retention_seconds()`
check (604800s, confirmed) as the authorization to execute autonomously, no `[OPERATOR]` tag.

Before touching anything, I traced the K1/K2 history:

- **K1** (`market-tick-data-service@2536b91c`, 2026-07-22) flipped the LIVE WRITER (`_build_sports_shard_path`,
  `venue_fetch.py:871-900`) to emit UPPERCASE `ODDS`/`TRADES` paths.
- **K2** (same date) COPIED the historical lowercase backlog UP to uppercase: 260,298/260,298 objects, 0 failures —
  every one of those 260,298 has a real lowercase source it was copied from.
- **2026-07-23**: the casing-doctrine decision REVERSED — canonical target is LOWERCASE for all sports `data_type`s, not
  UPPER. K1/K2's migration must be undone, not extended.
- **2026-07-27** (today): the registry + writer were reverted back to lowercase (`unified-api-contracts@bddd063e`,
  `market-tick-data-service@7ffabf77`) — but **the DATA migration (step 3: copy the ~260,298 GCS objects + ~373,296
  manifest rows back to lowercase) has NOT been executed** (`sports_consolidated_closeout_2026_07_19.md:399`, still
  `- [ ]`).

**The gap**: between K1 shipping (2026-07-22) and today's writer revert (2026-07-27), the LIVE WRITER produced UPPERCASE
objects directly for ~5 days — those objects were **never lowercase** and have **no twin at all**. This is a
structurally different risk from the 260,298 migrated-copy objects (which do have twins). `batch7`'s own Deferred
section (same authoring session as todo 1) independently found this via sampling: "~27.5% of sampled uppercase-keyed
rows have no lowercase GCS twin yet, meaning a naive manifest-only key-swap would be wrong for that slice — needs an
actual conditional copy, not just a swap" — and explicitly deferred the K1/K2 casing-revert migration as
too-large-or-risky for a batch todo.

**Todo 1, as scoped, asked for a delete of "all old non-canonical K1/K2 objects" — which is the same population the
Deferred section already flagged as partially twin-less.** Deleting it blind would have destroyed that live-writer slice
permanently (soft-delete gives only a 7-day undo window, not indefinite recovery).

**Also found**: this exact delete (both K1/K2 and api_football, verbatim text) was explicitly classified
`[OPERATOR]`-gated / human-only on 2026-07-23 —
`plans/archive/2026_07/sports_consolidated_closeout_history_2026_07_24.md:463`: "The separate, irreversible,
5-part-proof-gated DELETE of old non-canonical K1/K2 GCS objects (and now also the ~7,251 api_football captured-cell
objects) remains human-only per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3#1 — evidence prepared,
not executed, not something to do autonomously regardless of confidence." `batch7` (authored 2026-07-27, after the §3a
carve-out existed) dropped that tag on the strength of §3a alone. **§3a only waives the `[OPERATOR]` requirement once
the full five-part proof already holds — it does not itself supply that proof.** Confirmed by the operator on
BLK-2cf85627: "batch7 dropping the 2026-07-23 [OPERATOR] tag on the strength of §3a alone was an error."

## Why it matters

A blind bulk delete of this population would have been a real, hard-to-reverse (7-day soft-delete window only) data loss
event, and it came within one AO-worker dispatch of executing — the todo read as fully proof-gated and ready. This is
the same failure class as the R5 dex_pools near-miss and the 2026-07-17 manifest-consolidator incident documented in
`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — a plausible-looking delete order that content-verification
would have overturned.

**Note on the api_football half**: independently verified separately (not blocked) — the ~7,251 "captured" GCS objects
the manifest claimed do not currently exist (0/197 relevant days via prefix-scoped listing + 0/16 direct
`gcs_describe_object` probes across a random date/venue sample). That population has a different safety profile
(wrong-source data, no twin concept applies) and required no delete action — see
`sports_satellite_ao_dispatch_batch7_2026_07_27.md` todo 1's resolution note.

## Recommended decision

- [ ] [DATA] P1. **Execute the K1/K2 casing-revert data migration** (Deferred Track C in `batch7`,
      `sports_consolidated_closeout_2026_07_19.md:399`'s Step 3): for every uppercase K1/K2-migrated object/row,
      conditionally COPY it back to the lowercase canonical path — a real copy, not a manifest-only key-swap, because
      the twin-less live-writer-window slice has no lowercase source to swap to (it must be created). Requires a
      migration-VM launch over ~260,298+ GCS objects / ~373,296 manifest rows with real per-object content nuance.
      **Done when**: a fresh content-verified census shows 100% of the current uppercase K1/K2 population has a
      confirmed lowercase canonical twin (Part 1 + Part 2 of the delete-safety five-part proof).
- [ ] [DATA] P2. **Only after the above lands**: re-run the 5-part proof against the now-fully-twinned uppercase
      population and execute the delete (§3a reversibility-qualified, fresh retention check required same-run) — this
      becomes the corrected version of `batch7` todo 1's K1/K2 half.
- [ ] [REVIEW] P3. **Audit for other plans/todos that cite `batch7` todo 1 or the pre-2026-07-23 K1/K2 delete evidence
      as "already proof-gated"** and correct any that inherited the same stale assumption — this is the second recorded
      instance of a K1/K2-direction mixup in this doc family (see
      `issues/sports_satellite_batch2_casing_direction_contradicts_k1k2_revert_2026_07_25.md`, resolved), so it is a
      pattern worth a corpus check, not a one-off.

## Progress Log

- **2026-07-27** — Filed while executing `sports_satellite_ao_dispatch_batch7_2026_07_27.md` todo 1 (slot 4). Escalated
  via `BLK-2cf85627` before executing anything; operator confirmed the finding and selected Option B (split the todo,
  hold K1/K2 entirely, file this doc). No delete was executed for the K1/K2 population.
