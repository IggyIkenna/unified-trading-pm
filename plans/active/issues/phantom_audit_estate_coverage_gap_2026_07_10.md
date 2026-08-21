---
doc_type: issue
title:
  "Phantom audit covers only 5 hardcoded buckets (one per AG) — the rest of the consolidated-manifest estate
  (instruments-cefi/defi/tradfi, market-data-sports, gas-fees, lending-indices, oracle-prices, features/execution/…) is
  never phantom-checked"
summary:
  "Verified 2026-07-10. The recurring phantom audit (dp-manifest-hygiene-full, weekly) resolves exactly ONE bucket per
  asset_group via a hardcoded 5-entry map (`_BUCKET_KIND_MAP`, reconcile_phantom_manifest_rows_all.py:84-90) —
  market-data-{cefi,defi,tradfi} + instruments-store-sports + market-data-tick-prediction — and the cron never passes
  the `--manifest-bucket` override. Every OTHER consolidated availability_index.parquet in the estate is therefore never
  checked for phantom rows (`capture_status=captured` with no parquet on disk). Confirmed un-audited manifests that DO
  hold captured rows: instruments-store-cefi (86,977 rows / 64,227 captured — the flagship case), gas-fees,
  lending-indices, oracle-prices; and by the same map instruments-{cefi,defi,tradfi} + market-data-sports are skipped
  while their sibling bucket is audited. A phantom (the index lying about coverage — the scariest data-lie because
  everything downstream trusts the index) in any of these is silently undetected. Detection logic itself is sound; this
  is a COVERAGE gap. NOT a bug: the tradfi/prediction reprobe no-auto-heal + the weekly cadence were both checked and
  are deliberate design (see § Checked-and-not-a-gap)."
status: open
nature: notes
asset_group: [cefi, defi, tradfi, sports]
stage: [data]
repos: [instruments-service, e2e-testing, deployment-service]
scope: [engineer]
tags: [phantom, manifest, hygiene, coverage, data-correctness, audit, consolidator]
related: [/plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md]
created: 2026-07-10
author: unknown
parent_epic: security_and_cross_cutting_master
priority: P2
source:
  "Consolidator-cockpit UI design follow-up, 2026-07-10 — operator asked to verify (not delegate) the phantom/reprobe
  gap-findings before filing. Verified by reading the source + live gcloud bucket checks."
assigned_vm: NA
resolved_by:
locked_by:
context_scope:
  [
    instruments-service/scripts/reconcile_phantom_manifest_rows_all.py,
    e2e-testing/scripts/audit/manifest_hygiene_daily.py,
    /plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md,
    deployment-service/terraform/gcp/data_pipeline_audit_scheduler.tf,
  ]
execution_scope: local-only
estimate_class: design
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
last_updated: 2026-08-09
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

# Phantom audit's bucket coverage is a hardcoded 5-of-estate — most consolidated manifests are never phantom-checked

> **Filed for the data-pipeline owner (Ikenna).** Surfaced while designing the consolidator-cockpit UI
> (`consolidator_throughput_backlog_monitor_2026_07_09.md`). Operator directive 2026-07-10: verify the gap directly
> before filing — done (source read + live `gcloud storage` checks). This is a **coverage** gap in an otherwise-sound
> detector, not a detection bug.

## The gap

The phantom audit — Cloud Run job `dp-manifest-hygiene-full` (weekly `0 8 * * 0`) →
[`manifest_hygiene_daily.py`](../../../e2e-testing/scripts/audit/manifest_hygiene_daily.py)` --mode full` →
[`reconcile_phantom_manifest_rows_all.py`](../../../instruments-service/scripts/reconcile_phantom_manifest_rows_all.py)` --dry-run`
— resolves the bucket to scan from a **hardcoded 5-entry map**, one bucket per asset_group:

```python
# instruments-service/scripts/reconcile_phantom_manifest_rows_all.py:84-90
_BUCKET_KIND_MAP = {
    "cefi":       ("market-data", "cefi"),
    "defi":       ("market-data", "defi"),
    "tradfi":     ("market-data", "tradfi"),
    "sports":     ("instruments-store", "sports"),
    "prediction": ("market-data-tick-prediction", None),
}
```

A `--manifest-bucket` override exists (`reconcile_phantom_manifest_rows_all.py:954-955`, applied at `:1049-1053`) to
point the audit at any other bucket — **but the cron never passes it.** The orchestrator loops the 5 AGs and calls the
CLI with only `--asset-group <ag> --dry-run`
([`manifest_hygiene_daily.py:384`](../../../e2e-testing/scripts/audit/manifest_hygiene_daily.py)), so exactly 5 buckets
are ever walked:

- `market-data-{cefi,defi,tradfi}`, `instruments-store-sports`, `market-data-tick-prediction`.

Everything else with a consolidated `_index/availability_index.parquet` is **never phantom-checked**, including — note
the asymmetry — the **instruments** manifests for cefi/defi/tradfi (only _sports_ instruments are audited) and
**market-data** for sports (only sports _instruments_ are audited).

## Why it matters

A phantom = a manifest row with `capture_status=captured` but **no parquet on disk** → the index is _lying about
coverage_. It's the highest-severity data-lie because every downstream reader (data-status %, strategy, features) trusts
the index. Leaving most of the estate un-audited means such a lie in those buckets is silent until someone reads a
missing file at runtime.

## The numbers (full estate enumeration, verified 2026-07-10 live)

A `gcloud storage` sweep of all 332 project buckets found **47 that carry a consolidated
`_index/availability_index.parquet`**. The phantom audit walks **exactly 5** (the prd env-resolved targets of
`_BUCKET_KIND_MAP`, confirmed via `resolve_bucket_name`):

- ✅ AUDITED (5): `market-data-tick-cefi-prd`, `market-data-tick-defi-prd`, `market-data-tick-tradfi-prd`,
  `instruments-store-sports-prd`, `market-data-tick-pred-prd`.

→ **The other 42 consolidated manifests are NEVER phantom-checked.** Grouped (all `…-central-element-323112`):

| Category                                     | Un-audited buckets                                                                                                                                                                   | why it's real data                                                                                       |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| **DeFi onchain per-data-type**               | `dex-pools`(+`-prd`), `dex-swaps`(+`-prd`), `evm-defi`(+`-prd`), `solana-defi`(+`-prd`), `gas-fees`, `lending-indices`, `lst-rates`, `oracle-prices`, `perp-funding`, `liquidations` | raw DeFi market data; `gas-fees` re-consolidated 2026-07-10                                              |
| **Instruments (non-sports AGs)**             | `instruments-store-cefi`(+`-prd`), `-defi`(+`-prd`), `-tradfi`(+`-prd`), `-prediction`, `-pred-prd`                                                                                  | reference-data catalogues; **`instruments-store-cefi-prd` = 86,977 rows / 64,227 `captured`** (flagship) |
| **Sports MARKET-DATA**                       | `market-data-tick-sports`(+`-prd`)                                                                                                                                                   | only sports _instruments_ are audited, never sports _market-data_                                        |
| **Features**                                 | `features-delta-one-cefi`(+`-test`), `-defi`, `-tradfi`, `features-mtf-cefi`, `features-onchain-defi`(+`-prd`), `features-sports-prd`                                                | computed feature manifests                                                                               |
| **Strategy / ML**                            | `strategy-store-cefi`, `ml-models-store`                                                                                                                                             | (phantom semantics differ — lower priority, confirm applicability)                                       |
| **Legacy/non-prd variants of AUDITED kinds** | `market-data-tick-cefi`, `-cefi-test`, `-defi`, `-tradfi`, `market-data-tick-prediction`                                                                                             | the audit only hits the `-prd` variant; these siblings hold manifests too                                |
| **Unexpected (worth a look)**                | `alerting-service`, `commodity-signals-batch`                                                                                                                                        | not obvious manifest owners — flag why they carry an `_index`                                            |

Flagship proof: `instruments-store-cefi-prd` capture_status = captured 64,227 / empty_confirmed 22,630 /
attempted_failed 81 / expected_unattempted 39 (inspected directly). A phantom among those 64,227 captured cells is never
caught by the current cron. Note the asymmetry the map bakes in: for cefi/defi/tradfi it audits _market-data_ but not
_instruments_; for sports it audits _instruments_ but not _market-data_.

## Suggested fix (data-pipeline owner to scope)

Make the phantom audit's bucket list **dynamic**, mirroring what the manifest consolidator estate already is: enumerate
every consolidated-manifest bucket (or every `(kind, asset_group)` the consolidator covers) and walk each — either by
looping `--manifest-bucket` per bucket in `manifest_hygiene_daily.py`, or by widening `_BUCKET_KIND_MAP` to the full
kind×AG matrix. Same detector, wider input. (Ties to the cockpit-side plan's "dynamic enumeration of all ~25
consolidators" requirement — a shared bucket-census source would serve both.) Watch cost: these are full-corpus GCS
walks; the weekly `--mode full` cadence + single-walk discipline should be preserved, so a fan-out over ~20 buckets
needs a runtime/parallelism check.

## Checked-and-NOT-a-gap (so this isn't re-litigated)

Two sibling claims were verified and found to be **deliberate design**, not defects — do not file as bugs:

1. **tradfi + prediction reprobe hooks never auto-heal.** True mechanically — `reprobe_tradfi.py:75` /
   `reprobe_prediction.py:71` always return `reached_source=False`, and the auto-flip requires
   `reached_source and rows_returned > 0` (`reprobe_new_empty_confirmed.py:243`). **But** those cells are still
   _detected_ via the oracle cross-check (`ORACLE_EXPECTS_DATA` verdict, `:247-250` → Slack alert), and the docstrings
   state the design explicitly (DATABENTO/MASSIVE and Polymarket are batch/archive sources where a per-cell live
   re-fetch isn't the model; the oracle is the control). So detection works; only the _automated_ correction is
   intentionally absent. Residual (unverified) question if ever revisited: does the coverage oracle itself have good
   tradfi/prediction coverage? — out of scope here.
2. **Phantom + 4-pillar run weekly only** (`--mode full`; daily `changed` mode scopes them out,
   `manifest_hygiene_daily.py:465-471`). Deliberate — full GCS-existence walks are expensive and the daily index-only
   checks (v9 / path-canonicality / divergence / missing-expected) still run every day. Cadence is a cost tradeoff, not
   a correctness bug — though it _compounds_ the coverage gap above (narrow AND infrequent), which the cockpit UI must
   show honestly (loud staleness, never a false "all clear").

## Separately (owned elsewhere, not this issue)

The **visibility** gap — phantom + reprobe results are Slack-terminal, not queryable (phantom writes an unwired
timestamped triage JSONL to `gs://central-element-323112-phantom-triage/`, no latest-pointer, zero consumers; reprobe
persists nothing) — is a UI-surfacing item tracked in `consolidator_throughput_backlog_monitor_2026_07_09.md` (WS-3
dark-actors: persist a per-AG `latest.json` + a read endpoint). That's cockpit scope, not a data-pipeline detection gap;
noted here only so the two aren't conflated.

## Verification method

- Source read: `_BUCKET_KIND_MAP` + `--manifest-bucket` handling in `reconcile_phantom_manifest_rows_all.py`; the cron
  invocation + `--mode full`-gating in `manifest_hygiene_daily.py`; the reprobe verdict/reclassify logic in
  `reprobe_new_empty_confirmed.py`; the cron args + schedules in
  `deployment-service/terraform/gcp/data_pipeline_audit_scheduler.tf` (`args = ["--mode","full"]`, `0 8 * * 0`; reprobe
  `["--reclassify-apply"]`, `0 9 * * *`).
- Live checks: `gcloud storage ls --long gs://<bucket>/_index/availability_index.parquet` across instruments-store-\*,
  gas-fees, lending-indices, oracle-prices (project `central-element-323112`); capture_status distribution of the
  downloaded instruments-cefi index.

## Todos

- [x] ✅ [DECISION] P2. **RULED (operator, 2026-08-08)**: "Widen it, but batch/optimize the walks rather than doing 42
      separate full-corpus GCS walks." Approves widening `_BUCKET_KIND_MAP` to the full ~47-bucket kind×AG matrix, on
      the explicit condition that it ships as ONE batched pass, not 42 independent sequential walks — filed as the
      concrete `[SCRIPT]` implementation todo below.
- [ ] [SCRIPT] P2. **Widen the phantom audit to the full ~47-bucket kind×AG matrix as ONE combined batched walk** (per
      the 2026-08-08 ruling above), not N separate full-corpus GCS walks. Concrete batching approach:
  > 1. **Replace the hardcoded 5-entry `_BUCKET_KIND_MAP`** (`reconcile_phantom_manifest_rows_all.py:106`) with the full
  >    kind×AG matrix — mirror the manifest consolidator's own bucket census rather than re-deriving a parallel list (a
  >    second hand-maintained bucket enumeration is its own drift risk).
  > 2. **Cheap phase first, in-memory (not a walk)**: for every bucket in the matrix, read ONLY its small
  >    `_index/availability_index.parquet` (one file per bucket — not a corpus walk) to pull the `captured` rows +
  >    derive each row's candidate `(date, venue[, chain])` prefixes via the existing `_venue_level_prefixes()` /
  >    `prefix_tpls` machinery (`reconcile_phantom_manifest_rows_all.py:231-306`), unchanged. Aggregate every bucket's
  >    prefix-list into ONE combined in-memory work queue — `list[tuple[bucket_name, prefix]]` across all 47 buckets —
  >    instead of building 47 separate per-bucket prefix lists that each spawn their own listing pass.
  > 3. **Expensive phase once, shared pool**: submit that ENTIRE combined queue to a SINGLE shared `concurrent.futures`
  >    worker pool (the same `list_blobs()`-per-prefix pattern `_audit_generic`/`_audit_sports` already use per-bucket
  >    today, at `reconcile_phantom_manifest_rows_all.py:517-524` — reuse the pattern, widen the pool's input) — one
  >    shared client, one shared concurrency cap, one shared progress/log stream — rather than 47 sequential invocations
  >    each paying its own process-startup + client-init + logging overhead and running back-to-back. This is the actual
  >    "batch/optimize" the operator asked for: same total GCS `list_blobs` call count (unavoidable — 47 real buckets
  >    need real listings), but ONE orchestrated pass instead of 47 independent full walks.
  > 4. **Classify + emit phantoms in-memory, per bucket**, from the aggregated listing results (substring-match each
  >    captured row's key against its bucket's listing set, same logic as today, just fed from the shared pool's output
  >    keyed by bucket).
  > 5. **Concurrency/QPS safety check** (per the doc's own "Suggested fix" note): the existing per-bucket concurrency
  >    cap was tuned for 5 buckets' worth of prefixes; widening the SAME pool to ~47 buckets' combined prefix count
  >    needs a fresh cap/backoff check against GCS QPS limits before shipping — measure real prefix-count totals across
  >    the full matrix first (cheap, phase 2 above already computes this) rather than guessing a safe pool size.
  > 6. **Orchestrator side**: `manifest_hygiene_daily.py`'s cron loop (`:384`, currently 5 sequential per-AG CLI
  >    invocations) changes to ONE invocation carrying the full bucket list (or an `--all-buckets` flag), preserving the
  >    weekly `--mode full` cadence (schedule-level single-walk-discipline unchanged — still once/week, just wider per
  >    run).
  >
  > Covers the other 42 un-audited manifests (incl. the 64,227-row `instruments-store-cefi-prd` flagship case). Repo:
  > instruments-service (script) + e2e-testing (cron orchestrator).

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - the doc explicitly files it "for the
  data-pipeline owner to scope", and the fix fans a weekly full-corpus GCS walk over ~20 more buckets (cost/runtime
  design call).
- **na-eligibility-audit 2026-07-30** (tranche=defi, autonomous): KEEP-NA, valid - widening the audit from 5 to 47
  buckets adds ~42 new whole-corpus GCS walks — review-blocking under single-walk discipline; doc defers the scoping to
  the data-pipeline owner. Reached independently of the cefi tranche above; both agree.

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — the sole todo's own section header is
  'Suggested fix (data-pipeline owner to scope)' and the fix carries an unresolved cost/parallelism question (a fan-out
  over ~20 buckets of full-corpus GCS walks against the deliberate weekly cadence) — a scoping call, not a determinable
  outcome. 4-tranche doc, cefi-flagship evidence
- **context-scout 2026-08-03**: refreshed context_scope (4 entries, unchanged from prior scout — still accurate: the 2
  source scripts the hardcoded bucket-map lives in, the cockpit-side sibling plan, and the cron's terraform schedule).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=cefi, autonomous): KEEP-NA, valid — sole open todo (dynamic bucket-list
  enumeration for the phantom audit) sits under a section explicitly titled "Suggested fix (data-pipeline owner to
  scope)" with an unresolved runtime/parallelism cost-tradeoff against the single-walk-discipline hard rule.
- **na-corpus-digest-closeout 2026-08-08**: operator ruled "widen it, but batch/optimize the walks rather than doing 42
  separate full-corpus GCS walks." Filed the concrete `[SCRIPT]` implementation todo above: replace the hardcoded
  5-entry map with the full kind×AG matrix, read every bucket's small index parquet first (cheap, in-memory), aggregate
  every bucket's candidate prefixes into ONE combined work queue, submit that queue to a SINGLE shared worker pool
  (instead of 47 separate per-bucket sequential passes), classify phantoms in-memory per bucket from the shared pool's
  output, and re-check the concurrency/QPS cap against the widened combined prefix count before shipping. Doc stays
  `assigned_vm: NA` — this is real, non-trivial engineering (touches the audit script's core listing strategy + the cron
  orchestrator), not a bounded single-worker AO-dispatch task as scoped.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — independently re-assessed rather than
  deferring to the same-day verdict above. The 6-step batching plan is unusually well-specified (exact file/function
  references, no open "how should this work" question), which is a genuine RECLASSIFY signal — but step 5's
  concurrency/QPS safety check ("measure real prefix-count totals... rather than guessing a safe pool size") still asks
  the worker to PICK a safe concurrency cap/backoff strategy against GCS QPS limits from first principles, not apply a
  stated formula — a residual judgment component. Combined with the multi-file, 2-repo scope (audit script's core
  listing strategy + the cron orchestrator) touching a single-walk-discipline-sensitive path, this stays just shy of
  whole-doc worker-determinable. No cheat-sheet ruling matches directly. Reaffirms the concurrent verdict on independent
  grounds.
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — sole open item is a well-specified
  6-step batching plan (2026-08-08 operator ruling: widen to full ~47-bucket matrix, batch the walks) with one residual
  judgment step (GCS QPS concurrency-cap selection) on a single-walk-discipline-sensitive path. 2 independent same-day
  (2026-08-08) passes already scrutinized this exact tension and landed KEEP-NA; concurring.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reaffirms prior verdicts; sole open item is a
  well-specified 6-step batching plan (2026-08-08 operator ruling) with one residual judgment step (GCS QPS
  concurrency-cap selection) on a single-walk-discipline-sensitive path.
