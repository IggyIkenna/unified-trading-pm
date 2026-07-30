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
related: [../consolidator_throughput_backlog_monitor_2026_07_09.md]
created: 2026-07-10
parent_epic: infrastructure_master
priority: P2
source:
  "Consolidator-cockpit UI design follow-up, 2026-07-10 — operator asked to verify (not delegate) the phantom/reprobe
  gap-findings before filing. Verified by reading the source + live gcloud bucket checks."
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
estimate_class: design
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
last_updated: 2026-07-10
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

- [ ] [DATA] P2. **Make the phantom audit's bucket list dynamic** — enumerate every consolidated-manifest bucket (or
      widen `_BUCKET_KIND_MAP` to the full kind×AG matrix) instead of the hardcoded 5-entry map, so the other 42
      un-audited manifests (incl. the 64,227-row `instruments-store-cefi-prd` flagship case) get phantom-checked too
      (see "Suggested fix" above).

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - the doc explicitly files it "for the
  data-pipeline owner to scope", and the fix fans a weekly full-corpus GCS walk over ~20 more buckets (cost/runtime
  design call).
- **na-eligibility-audit 2026-07-30** (tranche=defi, autonomous): KEEP-NA, valid - widening the audit from 5 to 47
  buckets adds ~42 new whole-corpus GCS walks — review-blocking under single-walk discipline; doc defers the scoping to
  the data-pipeline owner. Reached independently of the cefi tranche above; both agree.
