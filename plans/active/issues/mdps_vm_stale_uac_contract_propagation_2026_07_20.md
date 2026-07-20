---
doc_type: issue
title:
  P0 — MDPS service VMs validate against a STALE unified-api-contracts schema despite the current UAC tarball being
  correct; contract/schema changes do not reliably reach service VMs (wheel-cache shadow + launcher does not pin
  UAC_TARBALL_SHA)
summary: >-
  The loop-closing real-VM re-verify of the derivative_ticker candle fix proved the MDPS code fix is CORRECT (the VM ran
  the new adapter, emitted the required *_mean columns and left empty-window OHLC as NaN exactly as intended) - but the
  write still failed StreamingParquetWriter validation with "Column 'open' has NaN but is NOT NULLABLE for
  data_type=derivative_ticker" because the VM validated against a STALE deriv_ohlcv contract (non-nullable OHLC) even
  though the current UAC on LDR AND in the current unified-api-contracts-code.tar.gz both carry nullable_ohlcv=True
  (verified by extracting the tarball). Root cause: (1) launch-mdps-backfill-vm.sh pins UTL_TARBALL_SHA and
  MDPS_TARBALL_SHA into VM metadata but NOT UAC_TARBALL_SHA, so UAC is not version-pinned at launch; and (2) the setup
  installs a GCS-cached compiled wheel for UAC, and because the workspace's internal packages keep a static 0.x.y
  version across commits, a cached stale UAC wheel shadows the "editable, always fresh" install. Net: a UAC schema
  change can be fully shipped + tarballed and STILL not reach a service VM - a silent, correctness-critical deployment
  gap that affects every schema/contract change, not just this one.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [deployment-service, unified-api-contracts, market-data-processing-service]
scope: [engineer, admin]
tags: [data-correctness, p0, deployment, tarball, wheel-cache, schema, contract-propagation, silent-failure, mdps]
related:
  [../data_pipeline_check_mdps_features_2026_07_20.md, mdps_derivative_ticker_candle_schema_violation_2026_07_20.md]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  loop-closing real-VM re-verify 2026-07-20 of the derivative_ticker fix; every claim below verified (tarball extracted,
  git SHAs checked, launcher + setup script read).
---

# P0 — service VMs run a stale UAC schema; contract changes do not reach VMs

> **The GOOD news first:** the derivative_ticker candle fix (`mdps@beea161`) is CORRECT. On the re-verify VM the error
> changed from the pre-fix `column 'funding_rate_mean' missing` (old adapter) to
> `Column 'open' has NaN but is NOT NULLABLE` — i.e. the new adapter ran, emitted
> `funding_rate_mean`/`mark_price_mean`/`index_price_mean`, and left empty-window OHLC as NaN exactly as the operator
> specified. The ONLY thing wrong is the VM's UAC contract copy.

## Evidence (all verified 2026-07-20)

- **Fix is correct + shipped:** `mdps@beea161` (adapter) + `uac@8e58b009` (`nullable_ohlcv=True` on the
  `deriv_ohlcv_{tf}` registration, `_candle_contracts.py:318`). MDPS QG 2058 passed; UAC QG 124 passed; runtime-proven
  locally vs the real `StreamingParquetWriter` for all 7 timeframes.
- **LDR UAC is correct:** `git show origin/live-defi-rollout:…/_candle_contracts.py` → line 318 `nullable_ohlcv=True` on
  the deriv registration; `test_cefi_perpetual_deriv_ohlcv_is_nullable` guards it.
- **The current UAC TARBALL is correct:** extracted `gs://…/code/unified-api-contracts-code.tar.gz` (manifest SHA
  `ad317c32`, a descendant of the fix; built 20:00Z) → its `_candle_contracts.py:318` has `nullable_ohlcv=True`.
- **The MDPS tarball is correct** (`09da08c`, 20:43Z) and does NOT bundle UAC source (verified — 898 KB, no
  `unified_api_contracts/` inside), so the VM installs UAC separately.
- **Yet the VM (booted 20:53Z) validated against a NON-nullable deriv contract** →
  `mdps-backfill-cefi-pipelinecheck-20260720-205051-a63425/run.log`:
  `SCHEMA_VALIDATION_FAILED … Column 'open' has 2737 NaN/null values but is NOT NULLABLE for data_type=derivative_ticker, category=cefi`
  (open/high/low/close), 0 objects written, EXIT_STATUS 0 (the "reports success while writes failed" class — separate P0
  in the sibling issue).

## Root cause (two compounding gaps)

1. **The launcher does not pin `UAC_TARBALL_SHA`.** `launch-mdps-backfill-vm.sh:276-277,284-285` stamps
   `UTL_TARBALL_SHA` and `MDPS_TARBALL_SHA` into VM metadata (the "prevents race with concurrent tarball rebuilds" pin
   the setup honors at `setup-data-pipeline-vm.sh:667`) but **omits `UAC_TARBALL_SHA`** — so UAC falls to the unpinned
   default path.
2. **The GCS wheel cache shadows the fresh editable UAC.** `setup-data-pipeline-vm.sh:738-760` downloads compiled wheels
   from `gs://…/wheels/py313-linux-x86_64` before the "editable, always fresh" install. Because the workspace's internal
   packages hold a **static `0.x.y` version across commits** (semver only bumps on a major graduation), a previously
   cached `unified_api_contracts-0.x.y-…whl` built at an OLD SHA satisfies the version constraint, so a same-version
   contract change is NOT reinstalled — the editable source is effectively shadowed by the stale cached wheel.

Either gap alone can serve a stale UAC; together they make it the default outcome for a same-version contract change.

## Why this is P0 (blast radius beyond derivative_ticker)

Every UAC schema/contract change (nullable flips, new columns, new capture-status semantics, canonical-path rules) can
be fully shipped to LDR, tarballed, and **still silently not reach a running service VM** — the VM validates/behaves
against a stale contract. That is a silent, correctness-critical propagation gap for the ENTIRE fleet, and it directly
blocks the derivative_ticker candle backfill (the fix is correct but cannot take effect on a VM until UAC propagates).

## Fix direction

- **(a) Pin `UAC_TARBALL_SHA` in the launcher** (mirror the existing `UTL_TARBALL_SHA`/`MDPS_TARBALL_SHA` passthrough,
  `launch-mdps-backfill-vm.sh:276-277,284-285`), stamped to the current UAC LDR tip at launch — so the setup's line-667
  pin path installs the exact fresh UAC. Do the same for the other service launchers (features, mtds, instruments) —
  this is a shared launcher-lib concern.
- **(b) Make the editable code-repo install beat the wheel cache** for internal packages: either exclude
  `unified_api_contracts`/`unified_trading_library`/service packages from the GCS wheel cache, or install the code repos
  with `--refresh`/`--reinstall`/`--force-reinstall` AFTER the cached-wheel step so the editable source always wins.
  (The "always fresh" comment is currently aspirational — the cache silently defeats it for same-version changes.)
- **(c) Add a boot-time assertion**: the VM logs the installed UAC commit SHA (e.g. from the tarball manifest) and fails
  loud if it does not match the launch-pinned `UAC_TARBALL_SHA`, so a stale contract can never again validate silently.
  This also makes the exit-code-lies problem (sibling issue) impossible to miss for the schema class.

## Todos

- [ ] 1. [SCRIPT] P0. Pin `UAC_TARBALL_SHA` in `launch-mdps-backfill-vm.sh` (+ the shared launcher lib so all service
      launchers do it), stamped to the current UAC LDR tip. Mirror the UTL/MDPS passthrough exactly.
- [ ] 2. [SCRIPT] P0. Ensure the editable code-repo install shadows the GCS wheel cache for internal packages
      (`--reinstall`/exclude from cache), so a same-`0.x.y`-version contract change is actually reinstalled.
- [ ] 3. [SCRIPT] P1. Boot-time UAC-SHA assertion (installed UAC commit == launch-pinned `UAC_TARBALL_SHA`), fail loud
      on mismatch.
- [ ] 4. [DATA] P0. Re-run the derivative_ticker loop-close after (1)+(2) — confirm the force leg now WRITES objects
    (was 0), closing the derivative_ticker P0 end-to-end on a real VM.
</content>
