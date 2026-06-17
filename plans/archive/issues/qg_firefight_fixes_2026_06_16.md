---
title: QG firefight one-off fixes (2026-06-16) — deployment-api QG-allow, stale sports coverage tests, e2e [5.5a] escape
created: 2026-06-16
locked_by: live-defi-rollout
priority: P3
status: resolved
source:
  - QG-agent fork 2026-06-16 (fleet CVE/starlette propagation + e2e triage-queue firefight)
  - operator request 2026-06-17 — give the tracker-only one-offs a plan-of-record home
---

# QG firefight one-off fixes (2026-06-16)

> **Purpose:** plan-of-record for three small, SHIPPED QG/CICD fixes made during the 2026-06-16 fleet-propagation +
> e2e-triage firefight that previously lived only in the local `REMAINING_SCOPE_TRACKER.md` + commit messages. All three
> are done; this doc exists so they are traceable in `plans/` (no grep-miss). No open work.

## Shipped fixes

- [x] ✅ [SCRIPT] **deployment-api QG fix** — `deployment-api@cafb686`
      (`fix(qg): QG-allow legacy-bucket marker     (pipeline_uat) + cloud-SDK gate exclusion for GCE-specific vm_utils.py`).
      (1) `pipeline_uat.py` `instruments-store-` download is a legacy bucket pending migration → swapped the stale
      `# CORRECT-LOCAL` marker for the canonical `# QG-allow: legacy-bucket-name-migration`. (2) `vm_utils.py` uses
      `google.cloud.compute_v1` (GCE instance listing) which has no `unified_cloud_interface` equivalent → excluded from
      the cloud-SDK gate, paralleling execution's `cloud_kms.py`. QG-green, landed on LDR + drained.

- [x] ✅ [TEST] **Stale sports coverage-start tests** — UTL `unified-trading-library@cb373da` (2 tests in
      `test_legacy_reason_classifier.py`) + features-service `features-service@7c4e9b0` (2 tests in
      `test_coverage_gate.py` + `test_run_new_calculators_coverage_gate.py`). The UAC `SOURCE_COVERAGE_START`
      reconciliation **2018→2015** (`uac@bb7bf64`) left these pre-launch tests asserting the OLD 2018 boundary → a 2017
      date is now in-coverage, so they went **red on LDR**. Moved each pre-coverage test date to **pre-2015 (2014)** +
      corrected the `2018`→`2015` comments — preserves the original `EXPECTED_PRE_SOURCE_COVERAGE_START` /
      `OUT_OF_COVERAGE` intent. All pass; shipped (rode the dep-floor bumps in the same commits). **Note:** no plan
      tracks the `SOURCE_COVERAGE_START` 2018→2015 reconciliation itself (it was `uac@bb7bf64`, upstream of this fix) —
      flagged here in case a downstream consumer still encodes the old boundary.

- [x] ✅ [SCRIPT] **e2e-testing `[5.5a]` escape** — `e2e-testing@3c6b45d` (PR #292). `semver-agent.yml:159` carried a
      literal empty `${{ }}` inside an explanatory COMMENT ("never inline `${{ }}` in run:"); the `[5.5a]`
      empty-expression guard flags it as a parse-break even in a comment → failed the lint-codex QG slice → **blocked
      staging→main PR #290 for ~5h** (the "triage-queue stuck" incident). LDR already had the escaped form; this
      back-filled the escape onto staging (`${{ }}`→`$\{\{ \}\}`). PR #290 re-checked green + merged. (Same `[5.5a]`
      stale-escape class as the fleet-wide semver-brake escape — see `REMAINING_SCOPE_TRACKER.md` DONE.)

## Why filed

Findings-Triage + "Capture Discoveries as plan todos" — shipped one-offs should be traceable in a plan-of-record, not
only a local tracker. P3 / resolved: nothing open; archive on next sweep.

## Related

- `starlette_cve_2026_54282_fleet_alignment_2026_06_16.md` — the propagation these rode alongside.
- `qg_base_service_ratchet_exit_code_2026_06_11.md` — the ratchet hardening (separate, now unblocked).
- `REMAINING_SCOPE_TRACKER.md` (root, local) — where these were first logged.
