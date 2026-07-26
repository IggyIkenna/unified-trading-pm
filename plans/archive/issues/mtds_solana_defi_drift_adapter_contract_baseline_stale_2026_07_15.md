---
doc_type: issue
title:
  market-tick-data-service QG WARN — solana_defi_drift.py adapter-contract baseline stale since the 2026-07-14 Helius
  split
summary: >
  check_adapter_contract_regression (quality-gates.sh 5.70/6) flags
  market_tick_data_service/cli/handlers/solana_defi_drift.py at 10 tracked contract calls
  (classify_venue_error/ADAPTER_FETCH_FAILED/record_captured/record_empty/record_zero_rows/record_failed) against a
  stale baseline of 12. Verified pre-existing and unrelated to any in-flight change: git show HEAD on this file (before
  any edits this session) already shows 10 matches, and git diff on the session's edits adds zero/removes zero matching
  lines. Root cause: the file's own docstring documents a 2026-07-14 code-motion — "the Helius batch-resolve
  retry/rate-limit mechanics ... were split further into solana_defi_drift_helius.py" (commit 7a8bc43c) — which moved
  contract calls out of solana_defi_drift.py into the new sibling file (which now carries 9 matching calls of its own)
  without regenerating adapter_contract_baseline.yaml afterward. Same class of issue as the resolved
  mtds_adapter_contract_regression_stale_baseline_2026_07_13.md precedent (legitimate refactor, baseline never
  regenerated). WARN-ONLY today — quality-gates.sh still exits 0 (the check downgrades to a printed ⚠️, does not
  hard-fail the script) — so it did not block shipping the
  defi_perp_funding_canonicalisation_derivative_ticker_all_perps work.
status: resolved
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [qg-warn, adapter-contract-regression, stale-baseline, drift]
related:
  [
    plans/active/issues/mtds_adapter_contract_regression_stale_baseline_2026_07_13.md,
    plans/active/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md,
  ]
created: 2026-07-15
parent_epic: defi_master
priority: P3
source: [defi_perp_funding_canonicalisation_derivative_ticker_all_perps work, quality-gates.sh --no-fix run 2026-07-15]
assigned_vm: NA
resolved_by: unified-trading-pm@6c5cfa812 (incidental — see 2026-07-26 re-triage)
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-26
locked_since:
---

# solana_defi_drift.py adapter-contract baseline stale (2026-07-15)

## Facts

- `check_adapter_contract_regression` (quality-gates.sh 5.70/6) FAILs `solana_defi_drift.py`: "10 contract calls <
  baseline 12."
- `git show HEAD:market_tick_data_service/cli/handlers/solana_defi_drift.py | grep -c 'classify_venue_error\|ADAPTER_FETCH_FAILED\|record_captured\|record_empty\|record_zero_rows\|record_failed'`
  = 10 — already true before any 2026-07-15 edits.
- `git diff` on this session's edits (removing the Drift-only funding_rate_24h/7d/30d aggregates from `_collect_drift`,
  todo 3 of the derivative_ticker canonicalisation issue) touches zero lines matching these patterns — confirmed via
  `git diff ... | grep -E '^-.*(classify_venue_error|ADAPTER_FETCH_FAILED|record_captured|record_empty|record_zero_rows|record_failed)'`
  = no output.
- `solana_defi_drift_helius.py` (split out of `solana_defi_drift.py` 2026-07-14, commit 7a8bc43c per this file's own
  module docstring) carries 9 matching calls of its own — consistent with contract calls having moved OUT of
  `solana_defi_drift.py` during that split, with `adapter_contract_baseline.yaml`'s `solana_defi_drift.py: count: 12`
  entry never regenerated afterward to reflect the new split.
- The check is WARN-ONLY in current quality-gates.sh output (prints `⚠️  Adapter contract-call regression`, does not set
  a non-zero exit) — this did not block the derivative_ticker canonicalisation shipping commit.

## Recommended fix (not actioned here — outside this session's scope)

Regenerate `unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml` for `solana_defi_drift.py` (and add
a fresh baseline entry for the new `solana_defi_drift_helius.py` file, which appears to have none) via
`--regenerate-baseline`, AFTER confirming the current split reflects intentional design (no calls were actually lost,
only moved) — per the baseline tooling's own guidance ("re-run with --regenerate-baseline ONLY after legit refactor that
intentionally changes counts — never to mask a regression").

## RE-TRIAGE (2026-07-26, slot 4) — RESOLVED, but not the way this doc expected

**Verdict: RESOLVED — both files no longer exist; the "regenerate the baseline" fix this doc recommended never happened
and is no longer applicable.** Traced what actually happened to `solana_defi_drift.py` / `solana_defi_drift_helius.py`
since this doc was filed:

- `git log --follow` on both files shows commit **`2e674d1f`** — "refactor(defi): remove DRIFT + PACIFICA Solana perp
  DEXes — adapters, handlers, connectors, scripts, routers (operator ruling 2026-07-16)" — **deleted both files
  entirely**, one day after this doc was filed. This is the SAME operator-ruled DRIFT/PACIFICA removal referenced
  elsewhere in the corpus (e.g. the UAC `DRIFT` registry purge). Neither file exists anywhere in the current tree
  (`find . -iname "solana_defi_drift*.py"` — 0 hits).
- The stale-baseline WARN this doc tracked was closed as an incidental side effect: commit **`6c5cfa812`** ("chore(qg):
  drop culled DRIFT/PACIFICA entries from the adapter contract baseline + cursor-configs Tardis-exempt list",
  2026-07-16, same day as the file deletion) dropped the `solana_defi_drift.py`/`solana_defi_drift_helius.py` entries
  from `adapter_contract_baseline.yaml` entirely — not by regenerating them to the split's new 10/9 counts (this doc's
  recommended fix), but by removing the entries outright, since there's nothing left to baseline.
- **Confirmed live**: `grep -n "solana_defi_drift" scripts/quality_gates/adapter_contract_baseline.yaml` — 0 hits. Ran
  `check_adapter_contract_regression.py --workspace-root .` (correct root = the slot's `.tabs/<N>/` sibling-repo parent,
  NOT the individual repo — the tool's paths are workspace-relative) — the only 3 files currently regressed are
  `_defi_manifest.py`, `dex_pools_handler.py`, `lst_rates_handler.py` (unrelated, tracked by their own docs, e.g.
  `mtds_dex_pools_adapter_contract_baseline_stale_2026_07_26.md`). No `solana_defi_drift*` WARN fires.
- **This doc's original "confirm no calls were lost" question is now moot**, not answered in the direction it expected:
  the split (`7a8bc43c`) DID move contract calls cleanly (verified via `git show 7a8bc43c^:...` / `7a8bc43c:...` —
  parent had 12, `solana_defi_drift.py` dropped to 10, `solana_defi_drift_helius.py` gained 9, a real code-motion
  consistent with the docstring's own claim), but that question is irrelevant now since the ENTIRE feature (both files,
  and DRIFT-Solana support generally) was removed one day later for an unrelated operator decision. No action needed on
  this doc; no code change required (already shipped, `6c5cfa812`).

## Progress log

- 2026-07-15: Filed while shipping `defi_perp_funding_canonicalisation_derivative_ticker_all_perps` — discovered as a
  pre-existing, unrelated QG WARN while running `quality-gates.sh --no-fix` on `market-tick-data-service`. Verified not
  caused by this session's changes (see Facts above). Left open at P3 since it is warn-only and does not block shipping.
- 2026-07-26 (slot 4): Re-triaged per `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s dispatched todo. Found both
  files were deleted entirely on 2026-07-16 (operator-ruled DRIFT/PACIFICA removal, `2e674d1f`) and their stale baseline
  entries were separately dropped the same day (`6c5cfa812`) — the WARN this doc tracked no longer fires. Flipped
  `status: resolved`; no code change needed (already resolved incidentally by an unrelated commit).
