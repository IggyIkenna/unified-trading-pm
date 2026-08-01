---
doc_type: issue
title: >-
  data-pipeline-check-features's --env staging fix (for the IAM issue) makes SPORTS reference-data reads target the
  empty staging tier instead of real prod data — no source-bucket override exists for sports, unlike delta_one
summary: >-
  Fixing `pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md` (features-service@524b71ef, `--env staging`
  so the VM runs as `uts-test-sa` instead of `uts-prd-sa`) correctly unblocked the IAM/write-path problem, but exposed a
  SECOND, independent gap for the `sports` feature family specifically:
  `features_service/sports/data/gcs_paths.py::resolve_instruments_bucket()` / `resolve_tick_data_bucket()` route
  reference-data READS through the yaml-SSOT `resolve_bucket()` helper, which is env-tiered by design
  (`instruments-store-sports-{env}-{pid}`) — with NO source-bucket-style override to decouple reads from the VM's own
  `DEPLOYMENT_ENV`. Every reference entity (fixtures, standings, odds, etc.) legitimately reads from
  `instruments-store-sports-stg-...` under `--env staging`, and that tier has never been seeded with real sports
  reference data — so the compute always finds "17/17 entities missing" and correctly (per the honest-absence model)
  records `empty_confirmed`, even for `SPORTS_SMOKE_DATES`' explicitly-"busy" days that have real fixtures in the
  `-prd-` tier.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [features-service]
scope: [engineer]
tags: [pipeline-e2e-check, sports, honest-absence, bucket-routing, iam]
related:
  [
    plans/active/issues/pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: "2026-08-01"
parent_epic: infrastructure_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [sports_consolidated_native_ao_extract-032]
resolved_by:
locked_by:
context_scope: [/codex/02-data/honest-absence-downstream-handling.md]
depends_on: []
---

# sports feature e2e-check reads empty staging-tier reference data, not real prod data

## What I found

After shipping the `--env staging` fix (`features-service@524b71ef`) and a supporting IAM grant (see
`pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md`), re-ran the Track K (features) baseline checkpoint
for `SPORTS:sports` day `2025-12-20` (a `SPORTS_SMOKE_DATES` "busy" day, chosen specifically because it has known real
fixtures). The force leg completed cleanly (`exit_status=0`, `run.log` fully populated — both prior blockers genuinely
fixed) but reported:

```
WARNING Reference data for 2025-12-19: 17/17 entities missing — ['leagues', 'teams', 'standings', ...]
WARNING No GCS reference data found for 2025-12-19
INFO sports batch startup gate: instruments-store consolidator healthy for sports
     (bucket=instruments-store-sports-stg-central-element-323112)
```

Compare to the SAME day's read under the pre-fix (`uts-prd-sa`, implicit `DEPLOYMENT_ENV=prod`) run, which read real
data fine before crashing on the WRITE side:
`GCS read standings: 574 rows from gs://instruments-store-sports-prd-central-element-323112/...`,
`GCS read fixtures: 324 rows`, etc.

**Root cause**: `features_service/sports/data/gcs_paths.py::resolve_instruments_bucket()` (used by
`gcs_reader.py::read_reference_entity`, the actual reference-data fetch) and the parallel `resolve_tick_data_bucket()`
both route through `features_service.common.resolve_bucket(kind=..., asset_group="sports")` — explicitly documented as
always returning the **env-tiered** form (`instruments-store-sports-{env}-{pid}` /
`market-data-tick-sports-{env}-{pid}`), by design, "never the legacy no-env form." There is no
`--source-bucket`-equivalent override for sports the way `pipeline_e2e_check.py`'s `_build_launch_argv` provides for
`delta_one`'s downstream families (`multi_timeframe`/`cross_instrument` read delta_one's freshly-written `-test-` output
via an explicit `source_bucket` param) — `source_bucket` is ONLY ever populated from `FeatureFamily.DELTA_ONE`'s own
test sink (`pipeline_e2e_check.py:1977`), never wired to sports at all. So under `--env staging`, sports reference reads
have no way to target `-prd-` while writing to `-test-` — the two are coupled via one env-derived bucket name.

**`instruments-store-sports-stg-central-element-323112` has never been seeded** with real reference data (it's a
genuinely empty tier, not a stale/lagging one) — confirmed by "17/17 entities missing" across every entity type, not a
partial gap.

This is NOT a bug in the honest-absence machinery itself — `empty_confirmed` IS the correct, honest verdict for what the
compute actually saw (a genuinely empty staging bucket). The problem is one layer up: the e2e-check's own premise
("prove the compute pipeline works against real data") is silently defeated for sports specifically, because the input
it reads isn't real data at all.

## Why it matters

- **Every sports feature e2e-check checkpoint (past and future, until this is fixed) will report `empty_confirmed`
  regardless of which day is targeted** — including deliberately-chosen "busy" SPORTS_SMOKE_DATES days with abundant
  real fixtures. The checkpoint mechanically PASSES (force leg exits 0, writes an honest `empty_confirmed` manifest row)
  but does NOT prove the sports feature-computation LOGIC actually works against real inputs — only that the VM boots,
  has the right IAM, and the honest-absence path itself functions correctly.
- **This is a real correctness gap someone could easily miss**: a report reading "PASSED, empty_confirmed: source
  legitimately had no data for this window" reads as a clean, complete proof unless you cross-check against the actual
  `run.log` and notice the bucket resolved is `-stg-`, not `-prd-`. Future users of the `data-pipeline-check-features`
  skill for `sports` should NOT treat a clean `empty_confirmed` result as proof the compute logic works — only that the
  plumbing/IAM does.
- **Does not affect other families/asset_groups** the same way — `delta_one`'s own read-source override mechanism
  already exists (and is exercised); this is sports-specific because its reference-data reader has no equivalent.

## Recommended decision (not unilaterally fixed here — real design work)

1. **Add a source-bucket-style override** to `resolve_instruments_bucket()`/`resolve_tick_data_bucket()` (e.g. an
   optional explicit-env param, or a `PROTOCOL_DATA_SOURCE_BUCKET_SPORTS`-style env var mirroring the existing
   `PROTOCOL_DATA_SINK_BUCKET_SPORTS` sink override), threaded from `pipeline_e2e_check.py`'s sports shard build so
   e2e-checks can read real `-prd-` reference data while still writing to `-test-` output — matching the architecture
   principle every other family already follows ("input stays the PROD source bucket").
2. **Alternative**: seed real reference data into the `-stg-` tier for sports (a one-time backfill/ copy job) — simpler
   but duplicates real data into a tier meant to stay isolated/ephemeral, and would need re-seeding as new dates are
   added; probably the WORSE option long-term.
3. This needs an operator/main call on which approach — not a unilateral pick, since it touches the sports
   bucket-routing SSOT (`gcs_paths.py`'s own docstring explicitly protects the env-tiered behavior as intentional).

## CORRECTION (2026-08-01, slot 12) — override was implemented; live evidence is MIXED (looks intermittent, not consistently broken)

Since this doc was written, `features-service` shipped exactly the recommended fix: `247ecdaa` (feat: add
source-bucket override for reference-data reads) + `8ea48a33` (fix: source-bucket override silently no-oped via
`get_data_source()`) + `72393fbf` (fix: drop hardcoded prod project ID from the new source-bucket test) — see
`features_service/sports/config.py::FeaturesSportsServiceConfig.get_instruments_bucket()`, which now reads
`PROTOCOL_DATA_SOURCE_BUCKET_SPORTS`/`PROTOCOL_DATA_SOURCE_BUCKET` directly via a pydantic field (bypassing the
`get_data_source()` factory's `PROTOCOL_DATA_SOURCE_BACKEND` gate that caused the original no-op).

**Two back-to-back live runs, same day/flags, opposite outcomes** (Track K features final checkpoint, day=2024-03-09,
`sports_consolidated_native_ao_extract-032`, ~15 min apart, identical `pipeline_e2e_check.py` invocation):

- **12:39-12:45 run** (`features-e2e-sports-20260801-123939-281e78`): launch argv + VM command-line both correctly
  carried `PROTOCOL_DATA_SOURCE_BUCKET=instruments-store-sports-prd-central-element-323112` (verified via
  `gcloud compute instances describe --format='value(metadata.items[].value)'` while it was still running), yet
  `run.log` shows EVERY reference entity read hitting `instruments-store-sports-stg-...` (`17/17 entities missing`) —
  the pre-fix symptom, reproduced.
- **12:57-13:01 run** (`features-e2e-sports-20260801-125420-281e78`), same shard/day/flags, launched ~15 min later:
  `run.log` shows real reads succeeding against `instruments-store-sports-prd-...` (`GCS read leagues: 1228 rows`,
  `GCS read teams: 606 rows`, `GCS read standings: 732 rows`, etc.) — the override worked correctly, producing a
  genuine non-`empty_confirmed` force-leg pass (7 parquet files, `manifest=captured`) and a genuine skip-leg proof
  (byte-unchanged fingerprint).

So the override is NOT categorically broken (todo 1's original framing) — it is **intermittent**, which is arguably
worse to leave untriaged since a future checkpoint could silently land on either outcome depending on timing. Not
investigated further this session (out of `data_engineering` craft scope for a Track K checkpoint-running todo).
Candidates worth checking for the race: (1) a cold-start pydantic-settings read racing against env-var visibility at
process spawn, (2) `bash -c`'s env-var prefix occasionally getting lost across
`setup-data-pipeline-vm.sh`'s `python ` → `$VENV/bin/python ` substitution, (3) GCS/IAM eventual-consistency on a
freshly-impersonated read token. Re-run a few more times to establish a failure rate before assuming any single fix
resolves it.

Evidence: `gs://deployment-scripts-central-element-323112/vm-logs/features-e2e-sports-20260801-123939-281e78/run.log`
(failed run), `gs://deployment-scripts-central-element-323112/vm-logs/features-e2e-sports-20260801-125420-281e78/run.log`
(succeeded run).

## Todos

- [ ] [CODE] P1. **STILL OPEN — see CORRECTION above.** The source-bucket override
      (`features_service/sports/data/gcs_paths.py` / `features_service/sports/config.py`) is implemented and wired
      through `pipeline_e2e_check.py`'s sports shard build + the launcher's env-prefix, and DOES work (real `-prd-`
      reads confirmed live 2026-08-01) — but is INTERMITTENT: a back-to-back run with identical flags 15 min earlier
      still read the empty `-stg-` tier. Establish a failure rate (re-run the same shard/day several times) and trace
      the race — candidates in the CORRECTION section above (env-var visibility at process spawn, the `bash -c`
      substitution, GCS/IAM token eventual-consistency). Not safe to treat a single clean run as proof the gap is
      closed. (repo: features-service)
- [x] ✅ [DOC] P2. Noted this limitation in the `data-pipeline-check-features` skill doc
      (`cursor-configs/skills/data-pipeline-check-features/SKILL.md`), as a ⚠️ callout right after the existing
      "Required INPUT per family" table's Reality-check callout (same pattern/style) — so a future run doesn't mistake a
      clean `empty_confirmed` sports result for genuine proof the compute logic works. (repo: unified-trading-pm, same
      commit as this checkbox flip)

## Codex SSOTs

`/codex/02-data/honest-absence-downstream-handling.md`.
