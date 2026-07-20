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

> **⚠️ CORRECTION (2026-07-20 ~22:45Z, after the fix + a loop-close re-run):** the propagation gap this issue describes
> is REAL and is now FIXED (deployment@e978f32d — see todo 4). BUT the original framing below ("the ONLY thing wrong is
> the VM's UAC contract copy") turned out to be INCOMPLETE. The re-run VM installed the CORRECT UAC (pinned ad317c32,
> boot assert passed) and STILL failed the same schema validation — because the `nullable_ohlcv` fix was applied to the
> AGGREGATED contract key (`deriv_ohlcv_{tf}`) while the writer queries the enforcer with the SOURCE key
> (`derivative_ticker`). That is a SEPARATE bug (an enforcer key mismatch), tracked in
> `mdps_derivative_ticker_candle_schema_violation_2026_07_20.md` todo 5. The narrative below is preserved as the
> historical filing; read todo 4 for the reconciled outcome.

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

- [x] 1. ✅ [SCRIPT] P0. SHIPPED deployment-service@e978f32d + published to GCS. `launch-mdps-backfill-vm.sh` +
      `launch-features-vm.sh` auto-pin `UAC_TARBALL_SHA` via new `lc_resolve_tarball_sha` (shared
      `lib/launcher_common.sh`) — reads the floating tarball manifest's `commit_sha`, emits it ONLY when the `@<sha>`
      pair provably exists (else floats, never bricks boot), stamps it into VM metadata + the durable pin record.
      Mirrors the UTL/MDPS passthrough.
- [x] 2. ✅ [SCRIPT] P0. SHIPPED @e978f32d + published. `setup-data-pipeline-vm.sh` `_purge_internal_wheels` deletes
      internal-package wheels (UAC/UTL/service, computed from the editable dirs' pyproject names + uac/utl anchors) from
      the GCS find-links cache BOTH after the cache download (before the editable install) AND after `uv pip wheel`
      (before re-upload), so a static-0.99.0 stale wheel can no longer shadow the `-e` source. External C-extension
      wheels untouched. Published setup script is byte-identical on GCS (md5 f242a3aa…).
- [x] 3. ✅ [SCRIPT] P1. SHIPPED @e978f32d + published. Boot-time assertion: `unified_api_contracts.__file__` MUST
      resolve under `$WORKSPACE` (editable source), else `exit 1`. Chose editable-vs-wheel provenance over SHA-equality
      because internal packages carry no per-commit SHA (`SETUPTOOLS_SCM_PRETEND_VERSION=0.99.0`). Verified LOCALLY that
      an editable install resolves `__file__` under the project dir (`direct_url` editable:true) — so it passes on a
      correct VM and fires only in the bug case (no fleet-brick risk). QG green (--no-fix, 22s) + 2 new
      `test_tarball_pins.py` assertions.
- [x] 4. ✅ [DATA] P0. Re-run DONE — and it DISENTANGLED propagation from the residual bug. The re-run VM
    (`…-213641-a63425`) pinned `UAC_TARBALL_SHA=ad317c32` (git-proven descendant of the nullable fix), the boot
    assertion did NOT fire (correct editable UAC installed), so **THIS propagation P0 is CONFIRMED FIXED** — the correct
    UAC now reaches the VM. The force leg still wrote 0 objects, but for a SEPARATE reason (an enforcer key mismatch:
    `nullable_ohlcv` is on the aggregated `deriv_ohlcv_{tf}` key while the writer queries the source `derivative_ticker`
    key) tracked in `mdps_derivative_ticker_candle_schema_violation_2026_07_20.md` todo 5 + workflow w6kkdobay — NOT a
    propagation problem. Close this issue once the sibling key-mismatch fix lands and a re-run writes objects.
</content>
