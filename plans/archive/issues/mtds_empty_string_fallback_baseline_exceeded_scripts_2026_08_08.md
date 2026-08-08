---
doc_type: issue
title: market-tick-data-service empty-string-fallback baseline exceeded (73 > 66) — blocks all future quickmerges
summary: >
  A quickmerge re-gate for an unrelated fix (deleting orphaned alchemy_adapter.py/ thegraph_ws_adapter.py) failed on
  STEP 5.101's empty-string-fallback ratchet, currently 73 sites against a baseline of 66. All 7 over-baseline sites are
  in scripts/ pipeline_e2e_check.py, scripts/rebuild_mtds_manifest.py, scripts/
  reclass_nasdaq_nyse_eu_format_mismatch.py, and scripts/ remediate_risk_params_dishonest_stamps_2026_08_05.py — none
  touched by the deletion that surfaced this. Independently reproduced standalone via the checker's own suggested
  recheck command. Blocks EVERY future code quickmerge to this repo until resolved.
status: resolved # was: open — archived 2026-08-08, sole todo done, baseline verified back to 66
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer]
tags: [quality-gates, empty-string-fallback, ratchet, ci-blocking]
related: [cross_cutting_consolidated_closeout_2026_07_25]
created: "2026-08-08"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
assigned_role: backend_engineer
drift_direction: advance-code
source: >-
  Surfaced while shipping an unrelated operator-approved deletion (alchemy_adapter.py/thegraph_ws_adapter.py,
  interactive session, 2026-08-08) — quickmerge's re-gate step failed on a pre-existing empty-string-fallback ratchet
  violation in files the deletion never touched.
resolved_by:
locked_by:
depends_on: []
---

> **🗄️ ARCHIVED 2026-08-08** — sole todo done, baseline verified back to `66` via `check_no_empty_string_fallback.py`.
> Also the survivor of a duplicate filing (`mtds_empty_string_fallback_baseline_breach_blocks_all_pushes_2026_08_08.md`,
> archived + superseded pointing here). No open work remains.

## Finding

`quickmerge.sh`'s re-gate step failed shipping an unrelated deletion
(`market_tick_data_service/market_interface/adapters/defi_live/{alchemy_adapter,thegraph_ws_adapter}.py` + their package
`__init__.py` + 3 test files — operator-ruled delete 2026-08-08, see
`plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md` §6) with:

```
[FAIL] market-tick-data-service: 73 empty-string-fallback site(s) > baseline 66. New/over-baseline site(s)
(positional tail-slice — git-diff found no new sites still present; may be a move/reformat):
scripts/pipeline_e2e_check.py:1177; scripts/pipeline_e2e_check.py:1180; scripts/pipeline_e2e_check.py:1181;
scripts/rebuild_mtds_manifest.py:153; scripts/reclass_nasdaq_nyse_eu_format_mismatch.py:132;
scripts/remediate_risk_params_dishonest_stamps_2026_08_05.py:174;
scripts/remediate_risk_params_dishonest_stamps_2026_08_05.py:175
```

Confirmed reproducible standalone (not specific to my working tree): re-ran the checker's own suggested recheck —
`.venv-workspace/bin/python unified-trading-pm/scripts/quality_gates/check_no_empty_string_fallback.py --workspace-root <ws> --scope market-tick-data-service`
— outside quickmerge entirely, identical result. None of the 4 flagged files are in the deletion's diff
(`git status --porcelain` on all 4 returns empty — clean, not someone's uncommitted WIP either).

The checker's own note — "positional tail-slice — git-diff found no new sites still present; may be a move/ reformat" —
flags genuine uncertainty in its own attribution: it cannot cleanly diff-attribute which commit(s) added the 7
over-baseline sites (possibly several small additions across different sessions each individually under the radar, or
line-number drift from an unrelated reformat). Worth a human read of the 4 files before concluding these are all genuine
new violations vs. some being the checker's own attribution noise.

## Impact

Hard ratchet gate (never-raise-baseline convention, SSOT
`plans/active/issues/ mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md`) — blocks ANY future code
commit to this repo, not just the one that found it. Currently blocking:

- The alchemy/thegraph adapter deletion above (code complete, QG-verified standalone earlier, blocked only at re-gate).

## Recommendation

Read the 4 flagged files at the cited lines. For each site: either rewrite to fail-fast (raise / return None + caller
decides), or if genuinely deliberate-safe, add `# noqa: qg-empty-fallback` with a one-line reason (per this repo's own
established convention, see the SSOT issue doc). Do NOT bump the baseline YAML — the rule is explicit that it only ever
goes down.

## Todos

- [x] ✅ [SCRIPT] P1. Fix or annotate the 7 over-baseline empty-string-fallback sites in `scripts/pipeline_e2e_check.py`
      (3 sites, ~L1177-1181), `scripts/rebuild_mtds_manifest.py` (1 site, ~L153),
      `scripts/reclass_nasdaq_nyse_eu_format_mismatch.py` (1 site, ~L132), and
      `scripts/remediate_risk_params_dishonest_stamps_2026_08_05.py` (2 sites, ~L174-175) so the count drops back to
      ≤66. Unblocks all future market-tick-data-service ships, including the alchemy/thegraph deletion parked pending
      this (see Progress Log for the exact diff still sitting uncommitted, safe to re-apply). — **DONE 2026-08-08,
      `market-tick-data-service@505959b0f`** (fixed by a different session that hit the same block). **No `# noqa` was
      needed and the baseline was NOT touched** — on reading each site, all 7 defaults were already dead: 3 in
      `pipeline_e2e_check.py` were `str(row.get(k, "") or "")` where the `or ""` already handles `None` (the `, ""` was
      redundant); `rebuild_mtds_manifest.py` and `reclass_nasdaq_nyse_eu_format_mismatch.py` were both guarded by a
      column-presence / `pd.notna` check that made the default unreachable; and the 2 in
      `remediate_risk_params_dishonest_stamps_2026_08_05.py` read from dicts built by `to_dict(orient="records")` over
      an EXPLICITLY-requested column list containing both keys. That last pair was not harmless: `venue` degrading to
      `""` falls through to the existing `not candidates` skip, but `date_str` had NO guard — it would have appended a
      worklist entry with an empty date and written it under `--apply`. Verified
      `check_no_empty_string_fallback.py --scope market-tick-data-service` -> `[OK] 66 (== baseline)`. Also cleared 6
      PRE-EXISTING ruff errors in `reclass_nasdaq_nyse_eu_format_mismatch.py` (4x RUF002 `x`, B905 `strict=`, F841
      unused local) that blocked the commit hook; confirmed pre-existing by stashing first. **Your parked
      alchemy/thegraph deletion is now unblocked** — re-run the quickmerge in your Progress Log.

## Progress Log

- **2026-08-08**: found while shipping an unrelated deletion. The deletion itself (8 files, net -933 lines) is complete
  and QG-verified in isolation — sitting as an uncommitted local working-tree diff in this repo's clone, not lost, just
  blocked. Once this ratchet clears, re-run `bash scripts/quality-gates.sh` +
  `quickmerge.sh "refactor: delete orphaned alchemy_adapter.py/thegraph_ws_adapter.py — resolves the 2026-08-07 further-operator-decision carve-out, operator confirmed delete 2026-08-08 after tracing zero real callers and confirming the batch_live_symmetry_master per-venue WSFeedConnector pattern supersedes them" --agent --files 'market_tick_data_service/market_interface/__init__.py market_tick_data_service/market_interface/adapters/defi/canonical_write.py market_tick_data_service/market_interface/adapters/defi_live/__init__.py market_tick_data_service/market_interface/adapters/defi_live/alchemy_adapter.py market_tick_data_service/market_interface/adapters/defi_live/thegraph_ws_adapter.py tests/market_interface/unit/test_defi_live_tradfi_adapters.py tests/market_interface/unit/test_tradfi_adapters_extra.py tests/unit/test_adapter_watchdog_wiring.py'`.
