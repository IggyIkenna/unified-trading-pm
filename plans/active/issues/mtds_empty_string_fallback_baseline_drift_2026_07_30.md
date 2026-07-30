---
doc_type: issue
title: "market-tick-data-service empty-string-fallback baseline drift (93 > baseline 89) blocks quickmerge"
summary:
  "quality-gates.sh STEP 5.101 (no_empty_string_fallback) failed a quickmerge Pass-1 re-gate for an unrelated tradfi fix
  with 93 empty-string-fallback sites vs the repo baseline of 89 — a repeat of the fleet-drift oscillation pattern
  documented (and closed as resolved) in the archived
  plans/archive/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md. Verified pre-existing and
  not introduced by my change: the 5 new/over-baseline sites are in
  market_tick_data_service/market_interface/adapters/tradfi/tardis_cefi_shards.py:710,716,717,718 (landed via 064f872a,
  unrelated cefi manifest-recording fix) and scripts/verify_kamino_solend_lending_relabel_2026_07_30.py:67,68 (landed
  via f9222f78, unrelated defi verify-script fix) — neither file is one I touched. My own Pass-1 quality-gates.sh had
  run clean moments earlier; these commits landed on live-defi-rollout in between and the quickmerge auto-rebase (STAGE
  0.4) picked them up before the Pass-1 re-gate."
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [quality-gates, empty-string-fallback, ci-blocking, fleet-drift]
related: [/plans/archive/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md]
created: 2026-07-30
priority: P1
parent_epic: instruments_master
source: "tradfi_recovery_quarantine_registration_gap-003 (slot 14), 2026-07-30"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by: "data_pipeline_alert_substrate_residual-001 (slot 7), 2026-07-30 — market-tick-data-service@6efb252b"
locked_by: ""
---

# market-tick-data-service empty-string-fallback baseline drift (93 > baseline 89)

## What I found

`bash scripts/quality-gates.sh` STEP 5.101 (`check_no_empty_string_fallback.py`) failed a quickmerge Pass-1 re-gate with
93 empty-string-fallback sites against the repo's ratchet baseline of 89. My own local Pass-1 `quality-gates.sh` run (on
the same HEAD sans a moment's worth of upstream commits) had passed clean minutes earlier — the violation was introduced
by two OTHER slots' commits that landed on `live-defi-rollout` in the interim and were pulled in by quickmerge's
auto-rebase (STAGE 0.4) before the Pass-1 re-gate ran. Neither flagged file is one I touched:

- `market_tick_data_service/market_interface/adapters/tradfi/tardis_cefi_shards.py:710,716,717,718` — landed via
  `064f872a` ("fix(cefi): self-record captured manifest rows for LIGHTER-ZKSYNC derivative_ticker delegated Tardis
  path"). 4 `.get("key", "")` sites inside the per-shard manifest-recording loop (`_rk.get("venue", "")`,
  `_rk.get("data_type", "")`, `_rk.get("instrument_type", "")`, and the `_raw_sym` fallback via
  `_rk.get("instrument_id", "")`).
- `scripts/verify_kamino_solend_lending_relabel_2026_07_30.py:67,68` — landed via `f9222f78` ("fix(defi): dedupe verify
  script by dest object before re-download"). 2 `.get("key", "")` sites reading `instrument_type`/`instrument_id` off a
  parquet row for a verify-report field.

This is a repeat of the exact fleet-drift oscillation pattern the now-archived (`status: resolved`)
`mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md` already documented and partially remediated via
per-site `# noqa: qg-empty-fallback` annotations — the baseline is a ratchet (never raised), so each new slot's
unrelated `.get(..., "")` convenience call keeps nudging the live count back over it.

## Why it matters

Every quickmerge push to `market-tick-data-service` is blocked while the repo-wide count sits above baseline, regardless
of whether the pushing change touches the offending files — this is currently blocking an unrelated, already-QG-green
tradfi manifest-registration correctness fix (slot 14) from landing.

## Recommended decision

- [x] ✅ [SCRIPT] P1. Annotate the 4 new sites in
      `market_tick_data_service/market_interface/adapters/tradfi/tardis_cefi_shards.py` (lines 710, 716, 717, 718 as of
      2026-07-30 — re-verify line numbers before editing, the file may have moved) with `# noqa: qg-empty-fallback` + a
      one-line reason (each field is read from a manifest-recording row_key dict where an absent key legitimately means
      "not applicable to this shard" and the empty-string fallback is the existing, intentional not-present sentinel) OR
      rewrite to fail fast if the field is actually required at that call site — read the surrounding function to judge
      which. Repo: market-tick-data-service. — DONE `market-tick-data-service@6efb252b`. Confirmed via
      `tardis_batch_download.py:58` (the literal row_key builder) that venue/data_type/instrument_type/instrument_id are
      set unconditionally, so the `.get(key, "")` fallbacks are defensive-typing only for the `dict(_rk_tuple)`
      round-trip (mirrors the pre-existing `date` noqa on the same function) — annotated all 4 sites accordingly.
- [x] ✅ [SCRIPT] P1. Same treatment for the 2 sites in `scripts/verify_kamino_solend_lending_relabel_2026_07_30.py`
      (lines 67-68 as of 2026-07-30). Repo: market-tick-data-service. — DONE `market-tick-data-service@6efb252b`. A
      genuinely absent column here correctly falls through to the script's own MISMATCH branch
      (`"" != "solana_lending"`) — the intended honest-failure signal, not a masked one — so annotated rather than
      rewritten.
- [x] ✅ [SCRIPT] P1. After both fixes land, `bash scripts/quality-gates.sh` STEP 5.101 must report the repo-wide count
      back at or below the current ratchet baseline (89, per
      `unified-trading-pm/scripts/quality_gates/no_empty_string_fallback_baseline.yaml` — confirm the live value at fix
      time, never raise it). Repo: market-tick-data-service. — DONE. `check_no_empty_string_fallback.py` now reports
      `87 < baseline 89` (WARN to ratchet the baseline down, non-blocking) and the full `quality-gates.sh` run's STEP
      5.101 line is green (confirmed in the same run that also cleared the sibling STEP 5.83 adapter-contract-baseline
      blocker, `mtds_adapter_contract_baseline_stale_after_manifest_fn_move_2026_07_30.md`).
