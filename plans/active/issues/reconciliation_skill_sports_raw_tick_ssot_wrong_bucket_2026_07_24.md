---
doc_type: issue
title:
  "four-surface-reconciliation-procedure.md SS4.2/SS6 (and the /data-pipeline-reconciliation skill's own SS3d hazard
  table) misdescribe the bucket they resolve for sports raw-tick — conflates market-data-tick-sports-prd with a
  different bucket's reference-data layout"
summary: >-
  Discovered while running /data-pipeline-reconciliation --asset-group sports --layer raw-tick (2026-07-24 dispatch).
  four-surface-reconciliation-procedure.md SS4.2 states "every sports object lives under sports_reference/" and "the
  oracle does NOT cover sports"; SS6 and the skill's own SS3d hazard table repeat "sports — No asset_group= key at
  all... entity= is never a data_type." Directly verified against the ACTUAL bucket the skill's own Phase-0 step
  resolves for sports raw-tick (market-data-tick-sports-prd-central-element-323112, kind='market-data'):
  sports_reference/ has ZERO objects and ZERO child prefixes there. Every real raw-tick object instead lives under the
  STANDARD
  raw_tick_data/by_date/day={D}/pipeline_mode={m}/asset_group=sports/venue={V}/league_id={L}/instrument_type={IT}/data_type={DT}/ticks.parquet
  grammar, which DOES carry an asset_group=sports key and IS covered by the standard oracle (canonical_path_violations()
  returns 0 violations on a 20-object sample, both require_pipeline_mode settings). The sports_reference/ layout is
  real, but lives in a DIFFERENT bucket (instruments-store-sports-{env}-{project_id}, per SPORTS_BUCKET_TEMPLATE in
  unified_api_contracts/canonical/domain/sports/gcs_paths.py:149) that this raw-tick dispatch never resolves. Any future
  agent trusting SS4.2/SS6 literally for a market-data-tick-sports-prd reconciliation will skip running the oracle when
  it should run, and will dispatch to candidate_parquet_paths() (the sports_reference resolver), which returns paths
  that do not exist in this bucket at all.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm, unified-api-contracts]
scope: [engineer, admin]
tags: [sports, codex-accuracy, reconciliation-skill, ssot-drift, oracle-coverage, raw-tick, documentation]
related:
  [
    /codex/02-data/four-surface-reconciliation-procedure.md,
    /codex/02-data/sports-gcs-path-ssot.md,
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    plans/active/issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md,
    plans/audit/results/data_pipeline_reconciliation_sports_2026_07_24.md,
  ]
created: 2026-07-24
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.15
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "/data-pipeline-reconciliation sports raw-tick dispatch, 2026-07-24 — direct GCS listing of
  market-data-tick-sports-prd-central-element-323112 plus a code read of gcs_paths.py's SPORTS_BUCKET_TEMPLATE and
  canonical_path_violations() run on a live sample"
resolved_by:
---

# The reconciliation skill's own codex is wrong about which bucket its sports raw-tick description applies to

## Why this is not a duplicate of the 2026-07-14 phantom-audit issue

`sports_phantom_audits_reference_not_marketdata_2026_07_14.md` documents that the **phantom auditor**
(`reconcile_phantom_manifest_rows_all.py`) maps sports to `("instruments-store", "sports")` while reprobe maps it to
`("market-data", "sports")` — a bucket-routing split in ONE specific tool's `_BUCKET_KIND_MAP`. That issue is scoped to
that tool and its cockpit-card symptom.

**This issue is scoped to a different target: `/codex/02-data/four-surface-reconciliation-procedure.md` itself** — the
SSOT the `/data-pipeline-reconciliation` skill cites for how to interpret sports raw-tick. §4.2 and §6 assert facts ("no
`asset_group=` key", "the oracle does NOT cover sports", "every sports object lives under `sports_reference/`") that are
TRUE of the `instruments-store-sports-{env}` bucket's reference-data layout, but presented as a blanket statement about
"sports raw-tick" without naming which bucket they apply to — and the skill's own Phase-0 dispatch
(`--asset-group sports`, default `--layer raw-tick`) resolves `market-data-tick-sports-prd` via `kind='market-data'`, a
DIFFERENT bucket where none of those three claims hold.

## What was verified (2026-07-24, direct read)

```
Bucket: market-data-tick-sports-prd-central-element-323112 (resolve_bucket_name(kind='market-data', asset_group='sports', deployment_env='prd'))

list_blobs(delimiter='/', prefix='sports_reference/') -> 0 objects, 0 prefixes  (claim "every sports object lives under sports_reference/" is FALSE for this bucket)

Real raw-tick objects found at:
  raw_tick_data/by_date/day=2026-07-24/pipeline_mode=batch_odds_api/asset_group=sports/venue=DRAFTKINGS/
    league_id=ALLSVENSKAN/instrument_type=ODDS/data_type=TRADES/ticks.parquet

canonical_path_violations(<above path, bucket-relative>, require_pipeline_mode=False) -> []
canonical_path_violations(<above path, bucket-relative>, require_pipeline_mode=True)  -> []
  (0 violations on a 20-object sample spanning 2021-05-16..2026-07-20; claim "the oracle does NOT cover sports" is
   FALSE for this bucket's raw-tick estate — the path DOES carry asset_group=sports and IS oracle-covered)

SPORTS_BUCKET_TEMPLATE (unified_api_contracts/canonical/domain/sports/gcs_paths.py:149) =
  "instruments-store-sports-{env}-{project_id}"
  -> candidate_parquet_paths() / the sports_reference/ layout targets THIS bucket, not market-data-tick-sports-prd.
```

## Why it matters

`four-surface-reconciliation-procedure.md` §4.2's instruction is unambiguous: _"Running the oracle on a sports path
returns a 100% false-positive violation... Dispatch to
`unified_api_contracts.canonical.domain.sports.gcs_paths.candidate_parquet_paths()` instead."_ A future agent following
this literally for a `market-data-tick-sports-prd` raw-tick reconciliation would (a) skip the oracle entirely — even
though it is the correct, working canonicality check for this bucket, verified above — and (b) probe
`candidate_parquet_paths()`'s `sports_reference/`-shaped candidate paths, which return zero hits in this bucket by
construction, producing either a false "100% phantom" verdict (mirroring the exact false-positive class the 2026-07-14
issue documents for the phantom auditor) or a silent no-op that never actually checks anything. Given
`plans/audit/results/data_pipeline_reconciliation_sports_2026_07_24.md`'s F1 finding — a real, 20,443+-object,
currently-growing S3 gap in this exact bucket that generic tooling appears to have missed for years — a codex that tells
auditors "there's nothing here to check with the oracle" for the one bucket that most needed checking is a contributing
factor worth fixing on its own merits, independent of F1's root cause.

## Suggested fix (not attempted here — doc-only issue, no code change needed)

Add a bucket-scoping clause to `four-surface-reconciliation-procedure.md` §4.2 and §6, and to the
`/data-pipeline-reconciliation` skill's own §3d hazard-table row for sports, along these lines:

- The "`no asset_group=` key / oracle-exempt / dispatch to `candidate_parquet_paths()`" description applies to the
  **`instruments-store-sports-{env}`** bucket's `sports_reference/` reference-data tree (fixtures, lineups, injuries,
  player stats, weather, standings, etc.) — the domain instruments-service owns.
- The **`market-data-tick-sports-{env}`** bucket (raw-tick MTDS odds-tick estate: `TRADES`/`trades`, resolved via
  `kind='market-data'`) uses the **standard** `raw_tick_data/by_date/.../asset_group=sports/...` grammar, carries a real
  `asset_group=sports` key, and **IS** covered by the standard oracle — treat it like every other asset_group for
  Surface-1 purposes.

## Todos

- [x] ✅ 1. [DOC] P2. Add the bucket-scoping clause above to `/codex/02-data/four-surface-reconciliation-procedure.md`
      §4.2 and §6 (repo: unified-trading-pm) — `pm@34de8774e`.
- [x] ✅ 2. [DOC] P2. Mirror the same clause into the `/data-pipeline-reconciliation` skill's own §3d sports
      hazard-table row (`.claude/skills/data-pipeline-reconciliation/SKILL.md`) so a future dispatch does not repeat the
      same wrong-playbook risk (repo: unified-trading-pm) — `pm@34de8774e`.
- [x] ✅ 3. [DOC] P3. Cross-link this issue and `sports_phantom_audits_reference_not_marketdata_2026_07_14.md` from
      `/codex/02-data/sports-gcs-path-ssot.md`'s existing bucket-naming section, since both stem from the same
      underlying dual-bucket architecture for sports — `pm@34de8774e`.
