---
doc_type: issue
title:
  phoenix_orderbook_handler.py adapter-contract-call regression — 3/6 baseline calls missing (classify_venue_error +
  ADAPTER_FETCH_FAILED entirely absent)
summary: |
  MTDS quality-gates.sh STEP 5.83 (`check_adapter_contract_regression.py`, the per-file non-shrinking contract-call
  ratchet built specifically to catch the 2026-05-20 lint-sweep regression class — see
  `plans/active/issues/lint_sweep_774602ea8_regression_audit_2026_05_20.md`) reports `[FAIL]` for
  `market-tick-data-service/market_tick_data_service/cli/handlers/phoenix_orderbook_handler.py`: baseline expects 6
  contract-pattern occurrences (`adapter_contract_baseline.yaml:383-384`), only 3 are present today
  (`record_captured` L458, `record_zero_rows` L468, `record_failed` L498). `classify_venue_error` and
  `ADAPTER_FETCH_FAILED` do not appear in the file AT ALL — meaning error classification on this handler's fetch path
  is currently silent/uncategorized, not just under-counted. **Surfaced 2026-07-26 during an unrelated DeFi-lending QG
  run** (this file was not touched by that session); this STEP 5.83 check runs AFTER the "ALL QUALITY GATES PASSED"
  banner in the current script ordering, so it did NOT block that ship — worth checking separately whether 5.83
  should be moved earlier / made hard-blocking, since as positioned it can pass silently alongside a real regression.
  **Suspect commit** (not confirmed, just the most likely candidate from file history): `cddb1226` "coverage 65→82% +
  codex violations 15→0" — a large sweep commit, the exact shape of regression this checker's docstring cites as its
  motivating incident. Not yet verified via `git log -p` / `git blame` on the removed lines.
status: resolved
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [quality-gates, contract-regression, error-handling, phoenix, adapter-contract-baseline]
related:
  [
    /plans/active/issues/lint_sweep_774602ea8_regression_audit_2026_05_20.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-27
last_updated: 2026-07-27
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
resolved_by: interactive session 2026-07-27, market-tick-data-service@bab22376
source:
  chat finding during defi_lending_writer_retire_prerequisite_2026_07_20.md session-3, flagged to operator, fix
  requested 2026-07-27
depends_on: []
---

# phoenix_orderbook_handler.py adapter-contract-call regression

## Todos

- [x] [CODE] P2. **Root-cause the regression** — ✅ `cddb1226` is a RED HERRING: it only extracted a helper
      (`_record_phoenix_todo`) from the STUB decode path, count unchanged at 6 (verified
      `git show cddb1226 -- ... |     grep`). The real regression commit is `ee49a76d` ("feat(defi): implement Phoenix
      DEX radix-slab top-of-book decode", slot-3, 2026-07-26) — it replaced the STUB (`collect_state` always returned an
      empty DataFrame + `record_failed`) with the real decode. **`classify_venue_error`/`ADAPTER_FETCH_FAILED` never
      existed in this file's history at all** (`git log -p --follow | grep` confirms zero hits, ever) — the baseline-6
      count was an artifact of stub-era DOCSTRING PROSE (`git show cddb1226:...phoenix_orderbook_handler.py` shows the
      pre-ee49a76d file's 6 matches were 5×`record_failed` + 1×`record_captured`, 4 of those 6 inside
      comments/docstrings like "Routes via `record_failed`..." — only 2 were real code calls). The new (real)
      implementation naturally has LESS repetitive prose, hence the raw regex undercount despite being MORE functional
      (genuine capture/zero-rows/fail branches vs. an always-fails stub). (repo: market-tick-data-service)
- [x] [CODE] P2. **Restore proper error classification on the fetch path** — ✅ SHIPPED
      `market-tick-data-service@bab22376`. Checked `position_data_handler.py` (the doc's original comparison) but it
      turned out to be a weaker match (it's a `record_shard_failure`-routed DeFi-lending writer, a different family);
      the real structural siblings are `orca_whirlpool_state_handler.py` / `raydium_classic_amm_handler.py` (same Solana
      on-chain-RPC-fetch + per-day-sample-loop shape) — **neither of those calls `classify_venue_error` either** today.
      Given CLAUDE.md's blanket "classify via UAC `classify_venue_error()`" rule and the codex SSOT's canonical Error
      Handling Pattern template (both apply workspace-wide, not just to CeFi/EVM venues), added
      `classify_venue_error("PHOENIX", err_token)` + `log_event("ADAPTER_FETCH_FAILED", ...)` to the except-Exception
      branch, matching `lending_indices_handler.py`'s exact idiom (`classify_venue_error(venue, token)` called for its
      classification side-effect before `record_failed`). Extracted `_record_fetch_failure()` to keep
      `ingest_market_day()` under the 50-line method-size QG gate. orca/raydium's own lack of `classify_venue_error` is
      a separate, out-of-scope pre-existing gap — NOT fixed here (different files, would need its own scoped review).
      (repo: market-tick-data-service)
- [x] [TEST] P2. **Verify STEP 5.83 goes green** — ✅ Confirmed: live count now 6/6 (exactly matches baseline, no
      baseline regeneration needed — `classify_venue_error` counts twice: once in the import, once in the real call).
      `check_adapter_contract_regression.py --workspace-root <ws>` → `OK — 332 baselined file(s) at or above minimum` (0
      failures fleet-wide). Full `quality-gates.sh` run → exit 0. Strengthened the existing
      `test_ingest_market_day_handles_collect_exception` unit test to assert `classify_venue_error` and
      `log_event("ADAPTER_FETCH_FAILED", ...)` are actually invoked with the right args (previously only asserted
      `record_failed.called`) — 20/20 tests pass. (repo: market-tick-data-service)
- [x] [PM] P3. **Check STEP 5.83's ordering in `quality-gates.sh`** — ✅ Diagnosed + fixed the REAL bug (not the
      ordering itself): STEP 5.83 was `|| log_warn "..."` (advisory-only), unlike its 5.86/5.87 siblings in the SAME
      block which are `|| { log_fail ...; exit 1; }` — meaning a real per-file regression here could NEVER fail the gate
      regardless of ordering (this session's incident is the direct proof: it sailed through silently). Flipped to
      hard-fail (`market-tick-data-service@bab22376`) now that the fleet-wide scan is clean (0 files below baseline,
      verified before flipping). Scoped to MTDS's own `scripts/quality-gates.sh` copy only — 4 other repos
      (`execution-service`, `instruments-service`, `features-service`, plus MTDS-family worktree checkouts) share the
      same `no_adapter_contract_regression.sh` call-site pattern with the identical `log_warn`-only wiring; NOT touched
      here (different repos, would need their own current-baseline-compliance check before flipping — out of this
      issue's scope, which is MTDS/phoenix only). **Separately**: the banner-before-repo-steps ORDERING itself
      (`base-service.sh`'s "ALL QUALITY GATES PASSED" prints at its own STEP 6, before the calling `quality-gates.sh`
      appends MTDS-specific STEP 5.70+ checks) is a workspace-wide, by-design composition pattern (source base gates
      first, append repo-specific extensions after) — cosmetic-only now that exit codes are correct (bash's own exit
      code, not banner text, is what quickmerge/CI actually gate on), and NOT changed here; flagged below as a genuinely
      separate, bigger-blast-radius follow-up. (repo: market-tick-data-service)
- [ ] [PM] P3. **Follow-up (new, discovered during the fix above): audit the other 4 repos'
      `no_adapter_contract_regression.sh` call-sites** (`execution-service`, `instruments-service`,
      `features-service`, + MTDS-family worktree copies —
      `grep -rln "no_adapter_contract_regression.sh" --include=quality-gates.sh .`) for the same warn-only wiring; flip
      each to hard-fail (matching this issue's MTDS fix) ONLY after confirming that repo's current fleet-wide baseline
      compliance is clean (re-run `check_adapter_contract_regression.py --workspace-root <ws>` — it's a single
      fleet-wide scan, not per-repo, so one clean run covers all of them) so the flip doesn't retroactively break
      someone else's already-green CI. (repo: unified-trading-pm, execution-service, instruments-service,
      features-service)

## Evidence

```
[0;34m── [5.70/6] IS-MTDS CONTRACT INTEGRITY ──[0m
...
[FAIL] market-tick-data-service/market_tick_data_service/cli/handlers/phoenix_orderbook_handler.py: 3 contract calls < baseline 6. Patterns tracked: classify_venue_error | ADAPTER_FETCH_FAILED | record_captured | record_empty | record_zero_rows | record_failed | record_catalog_unavailable | record_shard_failure.
```

Baseline (`scripts/quality_gates/adapter_contract_baseline.yaml:383-384`):

```yaml
market-tick-data-service/market_tick_data_service/cli/handlers/phoenix_orderbook_handler.py:
  count: 6
```

Current file (533 lines) — only 3 of the 8 tracked patterns present: `record_captured` (L458), `record_zero_rows`
(L468), `record_failed` (L498).

## Resolution (2026-07-27)

Shipped `market-tick-data-service@bab22376` (full quickmerge, quality-gates.sh exit 0):

- `phoenix_orderbook_handler.py`: except-Exception fetch-failure branch now calls
  `classify_venue_error("PHOENIX", err_token)` + `log_event("ADAPTER_FETCH_FAILED", ...)` before
  `recorder.record_failed(...)`, extracted into a new `_record_fetch_failure()` helper (keeps `ingest_market_day()`
  under the 50-line method-size gate).
- `tests/unit/test_phoenix_orderbook_handler.py`: `test_ingest_market_day_handles_collect_exception` now asserts
  `classify_venue_error` + `log_event("ADAPTER_FETCH_FAILED", ...)` fire with the expected args, not just
  `record_failed.called`.
- `scripts/quality-gates.sh` (MTDS only): STEP 5.83 flipped `log_warn` → `log_fail` + `exit 1`, matching its 5.86/5.87
  siblings — verified fleet-wide-safe first (`check_adapter_contract_regression.py --workspace-root` returned 0 failures
  before the flip).
- Live contract-call count is now 6/6 — exactly matches the existing baseline, no `--regenerate-baseline` needed.

Root cause was NOT the suspected `cddb1226` (a pure refactor, count unchanged) but `ee49a76d` (the real radix-slab
decode implementation replacing the STUB) — and even then, `classify_venue_error`/`ADAPTER_FETCH_FAILED` had never
existed in this file; the old baseline-6 was inflated by stub-era docstring prose. Full root-cause trail + design
reasoning in the flipped todos above.
