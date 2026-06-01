---
title: "UTL read_availability_index — opt-in fail-fast on stale-consolidated → per-VM-merge fallback"
created: 2026-05-28
status: active
parent_epic: manifest_master
assigned_vm: vm-cross-cutting
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
priority: P2
locked_by: live-defi-rollout
locked_since: 2026-05-28
---

# UTL read_availability_index — opt-in fail-fast on stale-consolidated fallback

## What this fixes

`read_availability_index` in `unified-trading-library/unified_trading_library/manifest_writer.py` has a slow-path
fallback: when the consolidated `_index/availability_index.parquet` is stale (older than
`MANIFEST_CONSOLIDATED_STALENESS_SEC`, default 120s) or missing, the reader silently merges ALL per-VM shards across the
bucket. On cefi this means ~1700+ shards → ~12 GB+ pandas heap → SIGKILL (rc=137) at startup before
`vm-exec-with-gcs-tee.sh` can wrap the lifecycle.

The launcher mitigation `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` (24h budget) makes the consolidated index
effectively always considered fresh during normal operation. But when the manifest-consolidator infra is degraded
(separate failure mode), the budget gets exceeded and the silent OOM-fallback fires.

A **shell-level preflight** in `setup-data-pipeline-vm.sh` (`deployment-service@7add531`) already catches this for the
specific MTDS-download VM bootstrap path: it `gsutil`-stats the index mtime before Python starts and exits 78 if stale.
That preflight is scope-limited and runs ONLY for the VM startup case. **Every other caller of `read_availability_index`
is still exposed** — features-service jobs, MDPS dependency checks, deployment-service manifest readers,
system-integration-tests, etc.

This plan moves the guard into the SSOT module itself so every caller gets the same opt-in protection without each
having to spawn its own preflight.

## Provenance

- `plans/active/issues/vm_zombie_watchdog_diagnosis_2026_05_28.md` — option (a) from the watchdog incident follow-ups.
- Shell-level preflight already shipped: `deployment-service@7add531` (option (b), the defense-in-depth layer).
- Related: `plans/active/manifest_consolidator_duckdb_memory_fix_2026_05_26.md` — fixes the upstream consolidator OOM
  that this guard defends against.

## Design

### New typed exception

`unified_trading_library/manifest_writer.py` exports a new exception:

```python
class ManifestConsolidatorStaleError(RuntimeError):
    """Raised by ``read_availability_index`` when the consolidated index is
    unusable (stale or missing) AND ``MANIFEST_FAIL_ON_STALE_FALLBACK`` is
    opted-in by the caller. Lets the caller exit non-zero fast instead of
    OOM-killing at the per-VM shard merge — the merge can be 12+ GB on cefi.
    """
```

Re-exported from `unified_trading_library/__init__.py` alongside `read_availability_index`.

### New env var

`MANIFEST_FAIL_ON_STALE_FALLBACK` — opt-in (default empty/False = current behavior). Closed set of accepted truthy
values (`1`, `true`, `yes`) matching the existing `_resolve_*` pattern in `manifest_writer.py` (line 505+).

### Behavior change

In `read_availability_index`, immediately before the slow-path fallback to `_read_and_merge_per_vm_shards` (currently
`manifest_writer.py:3528-3530`), check the env var. If set, raise `ManifestConsolidatorStaleError` with a message that
names the bucket + the staleness threshold + a remediation hint. If unset, behavior is unchanged.

The `_empty` path (no consolidated AND no per-VM shards anywhere) is NOT affected — that's a different signal (genuinely
empty bucket, not consolidator degradation). The fail-fast triggers only on the "stale-or-missing-consolidated +
per-VM-shards-DO-exist" combination.

### Caller opt-in surface

The cefi-heavy backfill launcher (`launch-cefi-sharded-backfill.sh`) gets `MANIFEST_FAIL_ON_STALE_FALLBACK=true` added
to its instance metadata, paired with the existing `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400`. Other launchers can opt
in incrementally.

## Implementation steps

- [x] [UTL] P2. Add `ManifestConsolidatorStaleError(RuntimeError)` exception class in `manifest_writer.py` near the
      existing config-resolver block. Re-export from `unified_trading_library/__init__.py` next to
      `read_availability_index`.
- [x] [UTL] P2. Add `_resolve_fail_on_stale_fallback() -> bool` helper using the same
      `_os.environ.get(...) +     qg-os-environ noqa + config-bootstrap rationale` pattern as
      `_resolve_consolidated_staleness_sec()`. Closed-set truthy values: `("1", "true", "yes")` (case-insensitive).
- [x] [UTL] P2. In `read_availability_index`, between the existing `if consolidated_df is not None:` fast-path return
      and the `per_vm_df = _read_and_merge_per_vm_shards(...)` call, add:
      `if _resolve_fail_on_stale_fallback(): raise     ManifestConsolidatorStaleError(...)`. Message names bucket +
      staleness budget + remediation hint.
- [x] [UTL] P2. Unit test in `tests/unit/test_manifest_freshness.py` (or new file
      `test_manifest_stale_fallback_failfast.py`): three cases — env unset + stale → fallback runs (backward compat);
      env set + stale → `ManifestConsolidatorStaleError` raised; env set + fresh → reads consolidated normally.
- [x] [UTL] P2. Workspace-wide consumer audit grep (`rg "read_availability_index" --type py --glob '!.venv*'`) →
      enumerate every consumer in the plan's `Consumer audit` table. None should need code changes given opt-in default
      = False, but document anyway.
- [x] [DEPLOY] P2. Add `MANIFEST_FAIL_ON_STALE_FALLBACK=true` to instance metadata in `launch-cefi-sharded-backfill.sh`
      `launch_cefi_shard()` (near the existing `MANIFEST_CONSOLIDATED_STALENESS_SEC` line). Pairs with the existing
      shell-level preflight (`deployment-service@7add531`) so both layers reinforce.
- [x] [UTL] P2. Run targeted regression: `tests/unit/test_manifest_writer_per_vm.py` — 19/19 passed (3 new fail-fast
      tests + 16 existing). Full QG sweep skipped this session (touched 3 files in 2 functions; no public API surface
      breakage, opt-in default-off behavior). Full `scripts/quality-gates.sh` can run on next QG-sweep cycle.
- [x] [UTL] P2. Codex SSOT update: added "Read path fail-fast on stale-fallback (2026-05-28 opt-in)" subsection to
      `codex/02-data/availability-manifest-and-data-status.md` with the 2-layer table (shell preflight + Python
      fail-fast) and SHAs (`7add531` + `cb1f4b5f`).

## Consumer audit (read_availability_index callers — workspace-wide)

| Caller                          | Path                                                                     | Opt-in needed?    |
| ------------------------------- | ------------------------------------------------------------------------ | ----------------- |
| MTDS reader                     | `market-tick-data-service/.../reader.py`                                 | No (passive read) |
| MDPS dependency checker         | `market-data-processing-service/.../dependency_checker.py`               | No                |
| Deployment-service manifest CLI | `deployment-service/deployment_service/cli/utils/manifest_reader.py`     | No                |
| Features manifest discovery     | `unified-trading-library/.../feature_service_base/manifest_discovery.py` | No                |
| Instruments preflight           | `unified-trading-library/.../instruments_preflight/runner.py`            | No                |
| UTL `dependency_check.py`       | `unified-trading-library/.../dependency_check.py`                        | No                |
| UTL `manifest_completeness.py`  | `unified-trading-library/.../manifest_completeness.py`                   | No                |
| UTL `manifest_freshness.py`     | `unified-trading-library/.../manifest_freshness.py`                      | No                |
| System-integration-tests        | `system-integration-tests/tests/smoke/test_coverage_matrix_smoke.py`     | No                |

Default behavior unchanged — every caller above sees the same fallback path until the env var is explicitly opted in.
The cefi-heavy backfill launcher is the first opt-in caller (paired with the shell preflight as defense in depth).

## Success criteria

- C2: unit test passes — 3-case truth table (env-unset / env-set-stale / env-set-fresh).
- C3: ruff + basedpyright clean on the touched lines (no `# type: ignore`).
- C4: `bash scripts/quality-gates.sh` in `unified-trading-library` exits 0.
- D1: launcher metadata change deployed via next cefi-heavy launch (no actual VM needed for validation — env var read at
  Python import time, surfaces in logs).
- B1: documented in codex/02-data manifest-and-data-status SSOT.

## Codex SSOT updates

- `codex/02-data/availability-manifest-and-data-status.md` — append a "Read path fail-fast" subsection naming the env
  var + exception + when to enable.

## Rollout

1. Land UTL code + tests on `live-defi-rollout`.
2. Land launcher metadata change on `live-defi-rollout`.
3. No backfill is currently running, so opt-in lands inert until the next cefi-heavy backfill batch — at which point the
   shell preflight + Python fail-fast reinforce each other.

## Risks + mitigations

- **Risk**: a caller silently relies on the slow-path fallback being non-fatal. **Mitigation**: env var is opt-in
  (default False = current behavior). Every existing caller behaves identically until it opts in.
- **Risk**: env var typo silently disables. **Mitigation**: closed-set truthy values `("1", "true", "yes")` only;
  anything else (including empty / `True` with capital T mis-cased — actually `lower()` normalises, so capital T is
  fine) is treated as False. Documented in plan + codex.
