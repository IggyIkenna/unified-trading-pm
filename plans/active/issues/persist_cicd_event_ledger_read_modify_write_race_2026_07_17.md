---
doc_type: issue
title:
  The CI/CD event ledger is written with an unlocked read-modify-write (gsutil cp down -> append -> cp up) on one shared
  events.jsonl per repo per day, so concurrent writers silently overwrite each other's rows — structurally lossy, and
  the loss is invisible because every writer reports success
summary: >
  `persist-cicd-event` (now also `.github/actions/persist-event`) appends a CI/CD event to
  `gs://${CICD_EVENTS_BUCKET}/cicd/events/{repo}/{date}/events.jsonl` by downloading the whole object, appending one
  line locally, and re-uploading it. There is no locking, no CAS/generation precondition, and no append primitive — so
  two writers whose windows overlap both start from the same base object and the second upload DISCARDS the first's row.
  Every writer still logs "Persisted event to gs://…" and exits 0, so the loss is completely silent. The write is
  best-effort by design (`continue-on-error`), which is correct for the CALLER but means nothing ever surfaces the drop.
  Volume: ~22 caller workflows; `ci-status-update` alone measured **14,320 runs/30d**, and all PM-scoped callers share
  ONE object (`cicd/events/unified-trading-pm/{date}/events.jsonl`), so PM's own file takes roughly 150-200 writes/day.
  **The loss RATE is NOT measured** — this is a code-read finding plus an argument, not a measurement, and it is
  recorded as such deliberately (this epic has been burned by presenting deduction as measurement). CI completions
  cluster in bursts, so a uniform-arrival estimate understates it. Found 2026-07-17 while converting the reusable
  workflow to a composite action for CI-cost STEP 2c; the conversion REPRODUCES the existing behaviour faithfully (it
  does not add or worsen the race) because changing it alters the reader contract and is a design call, not a cleanup.
status: open
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [ci-cd, github-actions, event-ledger, gcs, race-condition, data-loss, silent-failure, read-modify-write, telemetry]
related:
  [
    plans/active/github_actions_ci_cost_reduction_2026_07_15.md,
    plans/active/issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md,
    codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-17
parent_epic: deployment_and_user_management_master
priority: P2
source:
  github_actions_ci_cost_reduction_2026_07_15, slot 1, 2026-07-17 — found while reading persist-cicd-event.yml line by
  line in order to convert it to a composite action (STEP 2c). Raised with the operator twice in-session; the
  fix-vs-defer call is theirs and is still open.
assigned_vm: NA
execution_scope: local-only
assigned_role: devops
drift_direction: advance-code
last_updated: 2026-07-17
locked_by:
resolved_by:
depends_on: []
---

# The event ledger loses rows, and every writer says it succeeded

## The mechanism

`.github/workflows/persist-cicd-event.yml` (and the composite action that now mirrors it,
`.github/actions/persist-event/action.yml`):

```bash
OBJECT_PATH="cicd/events/${REPO_NAME}/${DATE_PARTITION}/events.jsonl"
GCS_URI="gs://${CICD_EVENTS_BUCKET}/${OBJECT_PATH}"

gsutil cp "$GCS_URI" "$LOCAL_FILE" 2>/dev/null || touch "$LOCAL_FILE"   # 1. read whole object
echo "$EVENT_JSON" >> "$LOCAL_FILE"                                     # 2. append one line
gsutil cp "$LOCAL_FILE" "$GCS_URI" || true                              # 3. write whole object back
```

Two writers, A and B, overlapping:

| t   | Writer A                       | Writer B                       | Object on GCS                |
| --- | ------------------------------ | ------------------------------ | ---------------------------- |
| 0   | `cp` down → \[rows 1..N]       |                                | rows 1..N                    |
| 1   |                                | `cp` down → \[rows 1..N]       | rows 1..N                    |
| 2   | append A → \[rows 1..N, **A**] |                                | rows 1..N                    |
| 3   |                                | append B → \[rows 1..N, **B**] | rows 1..N                    |
| 4   | `cp` up                        |                                | rows 1..N, **A**             |
| 5   |                                | `cp` up                        | rows 1..N, **B** ← A is GONE |

There is no lock, no `x-goog-if-generation-match` precondition, and GCS objects are immutable-on-overwrite (no append
primitive). **Both writers logged `Persisted event to gs://…` and exited 0.** A is unrecoverable and unlogged.

## Why nobody has noticed

Three independent reasons, and they compound:

1. **The write is best-effort by design.** `continue-on-error: true` exists so a telemetry hiccup can never redden a
   caller's run (the right call — plan #220). But it means no failure path is loud, and this failure is not even a
   failure: the upload genuinely succeeds.
2. **The healthy output and the lossy output are the same string.** `Persisted event to gs://…` prints either way.
   Exactly the shape this epic has now found four times (`digest-drift-sweep`'s `Dispatched: 0`,
   `reconcile-release-tags`' `created 0 tag(s)`, `cassette-drift-check`'s green no-op). See
   `codex/02-data/honest-absence-downstream-handling.md` — the same principle, applied to automation rather than data.
3. **Nothing reconciles the ledger against a known count.** A dropped row leaves no hole anyone looks for.

## Scale (measured where stated, estimated where stated)

- **Measured:** 22 caller workflows; `ci-status-update` = **14,320 runs/30d**.
- **Measured:** the path is keyed `{repo}/{date}`. `ci-status-update` passes `repo_name: client_payload.repo` (fans over
  ~24 repos), but **every other PM caller passes `repo_name: unified-trading-pm`**, so ~20 workflows contend for ONE
  object per day.
- **Estimated, NOT measured:** PM's own file takes roughly 150-200 writes/day; with a ~2-4s read-modify-write window and
  uniform arrivals that is ~1-2 lost rows/day. **CI completions cluster in bursts** (the whole fleet's CI finishes
  together — the same burst behaviour that sizes the glue runner pool), so the real number is higher and the uniform
  estimate is a floor, not an answer.
- **MEASURED 2026-07-17 (post-STEP-2c cutover — the first real datapoint, and it is WORSE than the estimate):** at
  12:40Z, PM's `events.jsonl` for 2026-07-17 held **1 row from the entire pre-cutover day** (00:00→12:11Z), despite the
  OLD reusable-path persist job firing ~145 times in that window for `repo_name: unified-trading-pm`
  (`sit-debounce-trigger` alone persists every 5 min). Yesterday looked the same: the pilot's write left a 339 B object
  ≈ the file was near-empty then too. In the first **26 min** after the composite-action path went live on `main`, the
  same file gained **14 rows**, including 3 writers landing within 9 s of each other, all surviving. So under the old
  path the shared PM object was retaining ~nothing — either near-total loss to this race under burst arrival, or the old
  persist step was failing silently (its `|| true` upload made both indistinguishable, which is this issue's point).
  Either reading strengthens the case: the ledger's history to date is NOT trustworthy as a record, and the new path's
  healthier accumulation does NOT close this issue — the read-modify-write is unchanged, only the write reliability
  improved.

**Do not quote the estimate as a finding.** How to actually measure it going forward, cheaply: count `events.jsonl` rows
for a day and compare against `gh api` run counts for the same workflows/day; the delta is the floor of the loss.
Alternatively, emit a per-writer sequence number and look for gaps.

## Options

| #   | Option                                                            | Cost                                                | Notes                                                                                                                                                                              |
| --- | ----------------------------------------------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **One object per event** — `…/{date}/{run_id}-{job}.jsonl`        | Small write change; **changes the reader contract** | Kills the race outright: no read, no merge, no lock. Readers must glob a prefix instead of reading one file. Standard event-sink shape. **Recommended if a reader can absorb it.** |
| 2   | **CAS retry loop** — `gsutil -h x-goog-if-generation-match:<gen>` | Moderate; a retry loop inside a best-effort step    | Preserves the one-file contract. But it turns a 3s write into an unbounded retry under burst — the exact condition where it is needed. Ugly on a shared runner.                    |
| 3   | **Write to Firestore instead**                                    | Larger                                              | `ci_status` already does per-doc CAS + `is_stale_write` ordering (CLAUDE.md § CI verification). Consistent with where CI state already lives. Biggest change.                      |
| 4   | **Accept + document**                                             | Zero                                                | Defensible IF the ledger is genuinely advisory. **Then say so in the workflow**, so the next reader does not build something load-bearing on a lossy source.                       |

**The blocking question is not which option — it is WHO READS THIS LEDGER.** That determines whether option 1's contract
change is free or expensive, and whether option 4 is honest or negligent. That has not been established:
`CICD_EVENTS_BUCKET` defaults to `unified-trading-cicd-events`; the event schema is declared to match
`GitHubWorkflowEvent` from `unified_api_contracts.internal`, which implies a real consumer exists. **Find the consumer
first.**

## What was deliberately NOT done

The STEP 2c composite-action conversion (`d0e25fcb6`) **reproduces this behaviour exactly**, adding only a `timeout` on
each `gsutil` call (composite steps cannot take `timeout-minutes`, so an unbounded transfer would otherwise hang the
CALLER's job). Fixing the race inside that conversion would have bundled a silent behaviour change into a cost refactor
— two unrelated risks in one diff, in a file that 22 workflows depend on. It is filed instead.
