---
doc_type: issue
title: 774602ea8 lint sweep blast-radius audit — adapter contract-call regressions
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, features-service, instruments-service, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-20
author: ikenna-main (slot 1)
source:
  - { execution-service@774602ea8 (chore(lint): add }
  - {
      execution-service@a2b5eef46 (feat(sports):
        add classify_venue_error + ADAPTER_FETCH_FAILED to kalshi + polymarket_clob adapters),
    }
  - { execution-service@195cf6829 (fix(execution): restore classify_venue_error regressed by 774602ea8 lint sweep) }
locked_by: live-defi-rollout
foundation_gate_class: C7/C8
---

> **🟢 RESOLVED 2026-05-20** — both regressed files restored at execution-service@195cf6829. Reference incident for the
> foundation-completion-gate mega-audit (/codex/11-project-management/foundation-completion-gate-discipline.md).

## What I found

**execution-service@774602ea8** (Sonnet 4.6, slot S7, 2026-05-18) titled "chore(lint): add # noqa justification comments
across execution-service" silently removed `classify_venue_error()` + `ADAPTER_FETCH_FAILED` event emissions from two
sports prediction-market adapter files while resolving merge conflicts during a workspace-wide noqa-justification sweep.

The merge-conflict-resolution path resolved 8 files; the conflict resolution for kalshi.py + polymarket_clob.py
discarded the SP-12(a) error-classification block in favor of the simpler pre-fix `raise BookmakerUnavailableError(...)`
pattern, silently undoing the layer-N adapter contract that had landed at a2b5eef46 (2026-05-18, 2 hours earlier).

This is exactly the foundation-completion-gate failure mode named in
`/codex/11-project-management/foundation-completion-gate-discipline.md` — a layer-N+1 hygiene commit (noqa comments)
silently breaking a layer-N contract guarantee (adapter error-classification).

## Why it matters

Per CLAUDE.md "Every adapter MUST classify errors via UAC `classify_venue_error()` + emit `ADAPTER_FETCH_FAILED`."

Without the restoration:

- Kalshi + Polymarket exchange-level errors surface as unclassified `BookmakerUnavailableError`
- No `ADAPTER_FETCH_FAILED` metric emitted → alerting/monitoring blind on these two venues
- May-23 prediction-markets coverage cell (Polymarket vs Kalshi spreads) silently degraded
- QG STEP adapter-contract enforcement gap

## Blast-radius audit method

```bash
# Per-file delta: before-vs-after 774602ea8 for any of:
# classify_venue_error | ADAPTER_FETCH_FAILED | record_captured | record_empty | record_failed

for f in $(git show --name-only 774602ea8 | grep -E '\.py$'); do
  before=$(git show 774602ea8^:"$f" | grep -cE "<contract pattern>")
  after=$(git show 774602ea8:"$f" | grep -cE "<contract pattern>")
  [ "$before" != "$after" ] && echo "DELTA $f $before→$after"
done
```

## Files touched by 774602ea8

82 .py files modified (Python source + scripts + tests). Full list captured by
`git show --name-only 774602ea8 | grep -E '\.py$'`.

## Per-file contract-call delta — files with ≥1 contract call

| File                                                                        | Before (774602ea8^) | After (774602ea8) | HEAD (post-fix) | Status                                                                                   |
| --------------------------------------------------------------------------- | ------------------- | ----------------- | --------------- | ---------------------------------------------------------------------------------------- |
| `execution_service/defi_execution/protocols/aave.py`                        | 1                   | 1                 | 1               | OK                                                                                       |
| `execution_service/sports_execution/adapters/aggregator/odds_api.py`        | 4                   | 4                 | 4               | OK                                                                                       |
| `execution_service/sports_execution/adapters/bookmaker_api/api_football.py` | 4                   | 4                 | 4               | OK                                                                                       |
| `execution_service/sports_execution/adapters/bookmaker_api/onexbet.py`      | 7                   | 7                 | 7               | OK                                                                                       |
| `execution_service/sports_execution/adapters/exchanges/betfair.py`          | 8                   | 8                 | 8               | OK                                                                                       |
| `execution_service/sports_execution/adapters/exchanges/kalshi.py`           | **20**              | **0**             | **20**          | **REGRESSED → RESTORED @195cf6829**                                                      |
| `execution_service/sports_execution/adapters/exchanges/matchbook.py`        | 4                   | 4                 | 4               | OK                                                                                       |
| `execution_service/sports_execution/adapters/exchanges/polymarket_clob.py`  | **5**               | **0**             | **14**          | **REGRESSED → RESTORED to a2b5eef46 baseline (was already partially lost in 6ba53d526)** |

**Net regressions**: 2 files. Both restored.

Note on polymarket_clob.py: before-count was 5 (not the a2b5eef46 baseline of 26) because an intermediate refactor
`6ba53d526 refactor(method-size): tick-67` had already silently lost ~21 of the 26 calls during method-extraction. The
restoration to HEAD targets the a2b5eef46 baseline (full 4-site SP-12(a) pattern at all `except aiohttp.ClientError`
sites in `place_bet`/`cancel_bet`/`place_order`/`list_open_orders`) — 14 contract-call refs in HEAD reflect 4 catch
sites × ~3-4 refs each + imports.

## Restorations made

1. `execution_service/sports_execution/adapters/exchanges/kalshi.py`
   - Added imports: `from unified_api_contracts import (... ErrorAction, classify_venue_error)` (root facade per
     CLAUDE.md UAC import rule, not the deep `canonical.crosscutting.errors` path used at a2b5eef46);
     `from unified_trading_library.events import ADAPTER_FETCH_FAILED, UNKNOWN_VENUE_ERROR_RECEIVED, log_event`
   - All 6 `except aiohttp.ClientError` sites in `_submit_order`, `cancel_bet`, `get_balance`, `_submit_order_post`,
     `get_positions`, `list_open_orders` now follow SP-12(a): extract `raw_code`/`raw_message`, call
     `classify_venue_error("kalshi", raw_code)`, emit `ADAPTER_FETCH_FAILED` + `UNKNOWN_VENUE_ERROR_RECEIVED`, then
     `raise BookmakerUnavailableError("kalshi", raw_message) from exc`.
   - Final counts: `classify_venue_error=7` (6 calls + 1 import), `ADAPTER_FETCH_FAILED=13`.

2. `execution_service/sports_execution/adapters/exchanges/polymarket_clob.py`
   - Added `ErrorAction` + `classify_venue_error` to existing UAC root-facade import block; added `ADAPTER_FETCH_FAILED`
     to existing UTL events import.
   - All 4 `except aiohttp.ClientError` sites in `place_bet`, `cancel_bet`, `place_order`, `list_open_orders` now follow
     SP-12(a) with full classify + emit + raise pattern. The existing `except Exception` re-raise branches retained.
   - Final counts: `classify_venue_error=5`, `ADAPTER_FETCH_FAILED=9`.

## Foundation-completion-gate flag for mega-audit

This incident is the canonical reference for the C7/C8 contract-audit category in the foundation-gate mega-audit
(`plans/active/issues/mega_audit_and_plan_beefup_progression_2026_05_20.md`). The pattern was:

1. Layer-N contract introduced at SHA A (a2b5eef46, 2026-05-18 sports adapter SP-12(a))
2. Layer-N+1 hygiene sweep at SHA B (774602ea8, lint noqa comments, 2 hours later)
3. SHA B includes merge-conflict resolution touching SHA A's files; resolver picks the simpler pre-A code
4. No QG step catches the regression (no count-of-classify-calls smoke at the file level)
5. Layer-N+1 sweep ships green; layer-N contract silently broken

**Hypothesis for QG coverage gap**: QG STEP for "adapter error-classification present" needs to be _additive_ — once a
file has classify_venue_error sites, it must keep ≥N sites in subsequent commits. Equivalent to a regression test
counting non-zero contract-call density per adapter file. Recommend codification in
`unified-trading-pm/scripts/quality-gates-base/no_adapter_contract_regression.sh` per the mega-audit C7/C8 phase.

### QG check — SHIPPED 2026-05-20 as STEP 5.83

The proposed QG check is now LIVE:

- Scanner: `unified-trading-pm/scripts/quality_gates/check_adapter_contract_regression.py` — Python AST-light scanner;
  walks every workspace repo `.git` subdir, counts the 5 contract patterns per `.py` file, compares against the per-file
  baseline.
- Baseline: `unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml` — 168 files seeded at
  execution-service post-restoration HEAD `195cf6829`; includes the canonical kalshi.py=20 + polymarket_clob.py=14.
- Wrapper: `unified-trading-pm/scripts/qg/no_adapter_contract_regression.sh` — single-arg `<workspace_root>` wrapper
  mirroring `no_silent_absence_handlers.sh` shape.
- QG STEP number: 5.71 (next-after STEP 5.70 IS-MTDS contract integrity bundle).
- Per-service wire-in: execution-service, market-tick-data-service, instruments-service, features-service all invoke
  `no_adapter_contract_regression.sh "${WORKSPACE_ROOT}"` as STEP 5.83 in their `scripts/quality-gates.sh`.
- Synthetic regression test 2026-05-20: deleted all 7 `classify_venue_error` lines from `kalshi.py` (20→13 contract
  calls); check exits 1 with diagnostic "[FAIL] execution-service/.../kalshi.py: 13 contract calls < baseline 20".
- Baseline update path: `--regenerate-baseline` flag rewrites the YAML with current observed counts (operator runs ONLY
  after legit refactor that intentionally changes counts — never to mask a regression).
- Foundation-completion-gate value: catches the layer-N+1 hygiene-commit regression pattern at file-level granularity,
  complementing the file-LEVEL `no_silent_absence_handlers.sh` (≥1 call per handler file) with a per-file MINIMUM count
  ratchet (≥N for every adapter file).

## QG status

- execution-service `bash scripts/quality-gates.sh` post-restore: **7514 passed, 43 skipped, 1 xfailed**.
- 2 pre-existing failures in
  `tests/unit/test_mock_data_provider.py::TestGetWorkspaceRoot::{test_from_env_var,test_from_unified_env_var}`
  (workspace_root env-var resolution; unrelated to adapter changes — verified pre-existing by stashing the adapter
  changes and rerunning).
- Coverage: 83.69% (≥70% gate).

## Restoration commit

`execution-service@195cf6829` (2026-05-20, branch `live-defi-rollout`).

## Related plans / SSOTs

- `plans/active/issues/kalshi_polymarket_classify_venue_error_missing_2026_05_18.md` (re-resolved 2026-05-20)
- `/codex/11-project-management/foundation-completion-gate-discipline.md` (canonical reference for this incident class)
- `plans/active/issues/mega_audit_and_plan_beefup_progression_2026_05_20.md` (master tracker)
- CLAUDE.md "Every adapter MUST classify errors via UAC `classify_venue_error()` + emit `ADAPTER_FETCH_FAILED`"
