---
doc_type: issue
title: >-
  pipeline_e2e_check's per-shard VM name is date-independent — two concurrent different-day runs of the same (family,
  asset_group) cell launched in the same wall-clock second collide on an identical VM name
summary: >-
  `features-service/scripts/pipeline_e2e_check.py::_vm_name()` builds
  `features-e2e-{asset_group}-{run_ts}-{hash(family:asset_group)}` where `run_ts` is second-granularity and the hash
  input is ONLY `(family, asset_group)` — no date/window component. Two independent driver processes checking the SAME
  cell (e.g. `sports`/`SPORTS`) for DIFFERENT target days, if their VM-launch calls land in the same UTC second, compute
  the identical name. The second `gcloud compute instances create` then fails ("already exists"), and the shared
  `unified_trading_library/pipeline_e2e_check/launcher.py::_run_launcher_script` retry/fallback treats this as
  "launched" and polls the FIRST run's VM instead of its own — reproduced live 2026-08-01 running 3 concurrent
  same-second checkpoint dates for Track K (features)/sports.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos:
  [
    features-service,
    unified-trading-library,
    market-tick-data-service,
    market-data-processing-service,
    instruments-service,
  ]
scope: [engineer]
tags: [pipeline-e2e-check, vm-launcher, race-condition, tooling]
related:
  [
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/issues/features_sports_env_staging_reads_empty_staging_reference_data_2026_08_01.md,
  ]
created: "2026-08-01"
parent_epic: infrastructure_master
priority: P2
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [sports_consolidated_native_ao_extract-032]
resolved_by:
  '2026-08-01 — both todos done. Todo 1: VM-name hash widened to include the target day across all 4 sibling drivers
  (features-service@4d7fc825, market-tick-data-service@ad169495, market-data-processing-service@c9caf54a,
  instruments-service@82cc429a). Todo 2: re-audited `_find_inflight_duplicate_vm()` — confirmed it cannot itself cause a
  cross-window misattribution (a dedup-skip is honestly reported as `status="skipped"`, excluded from the pass/proven
  tally, and the all-skipped exit-code guard fails loudly), but its coverage claim was false for non-overlapping
  windows, so narrowed the dedup filter to the same day via the day-aware VM-name hash slug in both features-service and
  its MDPS sibling (features-service@4455210, market-data-processing-service@2405b16). Zero open todos, unlocked,
  archived same-session per the archive-immediately rule.'
locked_by:
context_scope: []
depends_on: []
---

# pipeline_e2e_check VM-name collision on same-second, different-day, same-cell concurrent runs

## What I found

While running the Track K (features) sports checkpoints (baseline `2025-12-20`, mid `2025-12-24`, final `2025-12-18`) as
3 concurrent background invocations of
`features-service/scripts/pipeline_e2e_check.py --asset-group SPORTS --family sports`, the skip-leg launches for the
baseline and final runs fired within 6ms of each other (`13:56:20.164` and `13:56:20.170`) and BOTH computed the
identical VM name `features-e2e-sports-20260801-135620-281e78`. The final run's `gcloud compute instances create` failed
(exit 1, name already taken by the baseline run's VM); the shared launcher's retry logic
(`unified_trading_library/pipeline_e2e_check/launcher.py::_run_launcher_script`, ~line 186) detected the name was
already present via `_vm_is_present` and logged `"launcher exited 1 but the VM already exists — treating as launched"`,
then polled that (wrong, baseline-owned) VM for the final run's EXIT_STATUS.

**Root cause** — `features-service/scripts/pipeline_e2e_check.py::_vm_name()` (~line 1196):

```python
def _vm_name(shard: FeatureShardSpec, run_ts: str) -> str:
    # ... "A 6-char (family, asset_group) hash makes same-second same-cell collisions
    # require a real hash collision (MTDS vm-name-collision lesson)."
    slug = hashlib.sha256(f"{shard.family}:{shard.asset_group}".encode()).hexdigest()[:6]
    return f"features-e2e-{shard.asset_group.lower()}-{run_ts}-{slug}"
```

`run_ts` (`_run_ts()`) is `datetime.now(UTC).strftime("%Y%m%d-%H%M%S")` — second granularity. The hash's own comment
claims it "makes same-second same-cell collisions require a real hash collision," but the hash input is
`(family, asset_group)` ONLY — it does not include the target day/window. Two runs of the identical cell
(`sports`/`SPORTS`) targeting DIFFERENT days therefore produce the SAME hash, so the comment's stated guarantee is false
whenever two different-day runs of the same cell race within the same second — which is exactly the "independent
parallelizable work" pattern this very workspace's plan-authoring rules encourage (concurrent same-plan todos touching
different files/dates).

**Why this instance didn't corrupt the result** (lucky, not by design): the final run's target day (`2025-12-18`) and
the baseline run's target day (`2025-12-20`) write to non-overlapping GCS path prefixes (`by_date/day=2025-12-18/...` vs
`by_date/day=2025-12-20/...`), so once the baseline VM exited, the final run's fingerprint-based skip-check correctly
found ITS day's object unchanged and reported a genuine skip. Independently re-verified: the final run's reported
numbers (`total=2 passed=2`, force `parquet=6/captured`, skip `genuine`) are byte-identical to an earlier, uncorrupted
sequential run of the same day from earlier in this same session. This coincidence should not be relied on — a different
timing (e.g. the colliding VM failing, or overlapping paths for a different shard shape) could produce a silently WRONG
verdict attributed to the wrong day.

**Separately, and NOT the confirmed trigger here but a related design smell worth checking together**:
`_find_inflight_duplicate_vm()` (~line 1206, same file) is DELIBERATELY coarser than day-window by design ("the observed
waste was always same-cell/different-window, and a same-cell VM already in flight will itself produce this cell's
result, so skipping here never loses coverage") — but that assumption only holds if the in-flight VM's launch window
actually covers the requesting run's target day. For two genuinely non-overlapping windows (as in this reproduction), a
label-based dedup-skip on this criterion would ALSO be wrong, for the same underlying reason. Worth re-auditing once the
name-collision fix lands, since fixing the name uniqueness doesn't itself fix this related assumption if it were ever
the trigger for a different scenario.

## Why it matters

- **Silent cross-day/cross-shard result attribution**: a checkpoint report for day X can end up polling a VM that is
  actually computing day Y, with no error surfaced — the only signal is a WARNING log line easy to miss in a
  multi-minute VM-launch flow.
- **Not sports-specific**: `_vm_name()`'s pattern (date-independent hash + second-granularity timestamp) is generic to
  `pipeline_e2e_check.py` across services; any concurrent same-cell/different-window dispatch (which this workspace's
  own plan-authoring rules actively encourage — "independent parallelizable work → split, run concurrently") can hit it.
  The comment's own framing ("MTDS vm-name-collision lesson") suggests this general problem shape has been partially
  addressed before without fully closing it for the date dimension.
- **Correctness, not just cosmetic**: `data-pipeline-check-*` skills exist specifically to prove real infra behavior on
  real data — a silently-misattributed VM result undermines exactly the guarantee these smoke checks are meant to
  provide.

## Recommended decision

1. **Fix**: include the target day/window in `_vm_name()`'s hash input (e.g.
   `hashlib.sha256(f"{shard.family}:{shard.asset_group}:{day}".encode())`), or otherwise widen `run_ts` / append a short
   random/uuid component, so two concurrent different-window launches of the same cell cannot collide. Apply the same
   fix to any sibling `_vm_name()`-style helper in the other `pipeline_e2e_check.py` drivers (IS/MTDS/MDPS) if they
   share this pattern — grep for `hashlib.sha256(f"{.*family.*asset_group.*}"` across `scripts/pipeline_e2e_check.py` in
   each service repo.
2. Re-check `_find_inflight_duplicate_vm()`'s "any window" coarseness against the same failure mode once (1) lands — not
   blocking (1), since (1) alone closes the confirmed mechanism.

## Todos

- [x] ✅ [CODE] P2. Add the target day/window to `_vm_name()`'s hash input in
      `features-service/scripts/pipeline_e2e_check.py` (and any sibling driver with the same pattern in
      instruments-service/market-tick-data-service/market-data-processing-service), so concurrent different-window
      launches of the same `(family, asset_group)` cell cannot collide on VM name. Add a regression test asserting two
      `_vm_name()` calls for the same cell but different days produce different names even with a stubbed/frozen
      `run_ts`. (repo: features-service, + sibling repos if the pattern is shared) — confirmed all 3 sibling drivers
      shared the same date-independent-hash pattern and fixed all four: features-service@4d7fc825,
      market-tick-data-service@ad169495, market-data-processing-service@c9caf54a, instruments-service@82cc429a.
      Regression tests added/extended in each repo asserting two VM-name calls for the same cell/shard but different
      days (frozen run_ts) produce different names.
- [x] ✅ [CODE] P3. Re-audit `_find_inflight_duplicate_vm()`'s day-window-agnostic dedup assumption
      (`features-service/scripts/pipeline_e2e_check.py` ~line 1206) once the above lands — confirm it cannot itself
      cause a cross-window misattribution for non-overlapping launch windows of the same cell, or narrow its filter to
      include the window. (repo: features-service) — **confirmed no misattribution risk**: a dedup-skip hit is honestly
      reported as `status="skipped"` (never a spurious `passed`), excluded from `report.proven`/the pass tally, and the
      "PROVED NOTHING" exit-code guard fails loudly if every cell in a run skips — so unlike the confirmed
      name-collision mechanism, a coarse dedup hit can never itself misattribute a wrong verdict to the wrong day.
      HOWEVER the docstring's coverage claim ("a same-cell VM already in flight will itself produce this cell's result")
      was FALSE for non-overlapping windows, so a genuine same-cell/different-day in-flight VM would silently cause a
      real coverage gap (the day gets skipped, not verified, though never mis-reported as passed). Fixed by narrowing
      the filter to the window: `_vm_name()`'s day-aware hash slug (from todo 1) is reused as a name-suffix filter on
      the label-filtered RUNNING-instance candidates, so only a genuine SAME-day duplicate now triggers a skip. Found +
      fixed the identical pattern in MDPS's `_find_inflight_duplicate_vm()` sibling too (IS/MTDS don't have this
      function). Regression tests added asserting a different-day in-flight VM is ignored and a same-day one still
      matches: features-service@4455210, market-data-processing-service@2405b16.

## Codex SSOTs

None specific — this is a `pipeline_e2e_check.py` driver-internals defect, not a data/manifest contract issue.
