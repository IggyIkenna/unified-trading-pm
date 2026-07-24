---
doc_type: issue
title: MDPS canonical_writer.py adapter-contract-call baseline regression (warn-only, pre-existing)
summary:
  check_adapter_contract_regression (STEP 5.70, warn-only) reports market-data-processing-service's canonical_writer.py
  at 17 contract calls < committed baseline 18. Confirmed pre-existing via git diff (identical raw pattern count at HEAD
  and HEAD~1) — not caused by the sports_closeout_batch1_ao_ready_2026_07_24.md todo-2 fix that surfaced it.
status: resolved
nature: record
asset_group: [meta]
stage: [data]
repos: [market-data-processing-service, unified-trading-pm]
scope: [engineer, admin]
tags: [adapter-contract, baseline-regression, warn-only, mdps]
related: [mtds_uac_adapter_contract_baseline_regression_2026_07_09, lint_sweep_774602ea8_regression_audit_2026_05_20]
created: 2026-07-24
parent_epic: sports_master
assigned_vm: planning
resolved_by: unified-trading-pm@<pending-sha>
source:
  [
    market-data-processing-service quality-gates.sh STEP 5.70 check_adapter_contract_regression (warn-only post-gate,
    observed from an instruments-service QG run that cross-checks MDPS),
  ]
priority: P2
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

## What I found

While shipping `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 2 (the sports positional-parse-bug fix in
`market-data-processing-service`'s `canonical_writer_shaping.py` + call sites), the `instruments-service`
`quality-gates.sh` run's STEP 5.70 (`check_adapter_contract_regression`, warn-only — does NOT fail QG, exit stays 0)
reported:

```
[FAIL] market-data-processing-service/market_data_processing_service/app/core/canonical_writer.py: 17 contract calls
< baseline 18. Patterns tracked: classify_venue_error | ADAPTER_FETCH_FAILED | record_captured | record_empty |
record_zero_rows | record_failed | record_catalog_unavailable | record_shard_failure.
```

**Confirmed pre-existing, not caused by this session's fix**: a raw pattern grep across the same 8 tracked names returns
an IDENTICAL count for `canonical_writer.py` at HEAD (my commit `market-data-processing-service@69bfab1`) and at HEAD~1
(immediately before it) — 16 either way. My diff to this file was exactly 2 lines (threading `asset_group=asset_group`
into two existing `_infer_instrument_type`/`_infer_chain` calls, neither of which is a tracked contract-call pattern),
so it could not have changed this count. The 17-vs-18 baseline drift already existed on `live-defi-rollout` before this
session touched the file. Baseline SSOT: `unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml`
(`canonical_writer.py: count: 18`).

Not independently re-diagnosed here (out of scope for the sports parse-bug fix that surfaced it) — needs the same
diagnose-before-fix treatment as the linked 2026-07-09/2026-05-20 precedents: confirm whether the missing call is a
legitimate refactor (a contract call moved to a different file/function, baseline should be regenerated) or a real
regression (an error-classification/record_* call actually dropped from an error path).

## Why it matters

Same rationale as the linked precedents — this ratchet exists to catch the lint-sweep class of bug
(`lint_sweep_774602ea8_regression_audit_2026_05_20.md`, now archived: a sweep silently wiped 31 contract calls from
kalshi.py + polymarket_clob.py). A genuine drop below baseline on MDPS's canonical write path means a shard may no
longer classify errors / emit failure manifest rows on every path — a data-pipeline-correctness-adjacent risk, even
though this specific instance is warn-only and does not block shipping.

## Recommended decision

Diagnose-before-fix: `git log -p -- market_data_processing_service/app/core/canonical_writer.py` on
`market-data-processing-service` to find which commit dropped the count from 18 to 17, then either regenerate the
baseline (`--regenerate-baseline`, if the call legitimately moved/consolidated) or restore the missing contract call (if
a real regression). Non-urgent (warn-only, does not block QG/commits), but should not sit indefinitely.

- [x] [DIAG] P2. Root-cause the `canonical_writer.py` 17<18 adapter-contract-call baseline drift in
      `market-data-processing-service` — git-bisect the commit that dropped the count, then regenerate the baseline or
      restore the missing call. **Done when**: a written conclusion states which, with the commit SHA cited, and
      `check_adapter_contract_regression` reads clean (or the baseline is regenerated to the new correct count) for this
      file. ✅ — unified-trading-pm@\<pending-sha\>

## Resolution

**Legitimate refactor, not a regression.** Walked every commit touching `canonical_writer.py` from the baseline commit
(`5d86787`, count=18) forward:

- `5d86787` (baseline) → 18 = 10 real `record_captured` call sites + **2 docstring prose mentions** of the string
  `record_captured` inside `_resolve_candle_source_from_pipeline_mode`'s docstring + 3 `record_empty` + 3
  `record_failed`. The regex-based counter intentionally does not distinguish code from comments/docstrings (documented
  behavior in `check_adapter_contract_regression.py`), so those 2 prose mentions were always counted as if they were
  contract calls.
- `market-data-processing-service@752eaff` ("canonical single-derivation writer") → 19 (one genuine new
  `record_captured` call added: 11 real + 2 docstring + 3 + 3).
- `market-data-processing-service@2d720b4` ("fix(candles): manifest source= resolution keyed on the AGGREGATED
  data_type, not SOURCE") → **17**. This commit moved `_resolve_candle_source_from_pipeline_mode` wholesale (function +
  its docstring) out of `canonical_writer.py` into `canonical_writer_shaping.py`, renaming it to the public
  `resolve_candle_source_from_pipeline_mode`. `git show 2d720b4 -- canonical_writer.py` confirms exactly 2 pattern
  matches removed, 0 added — both were the docstring's `record_captured` prose references (e.g. "that `record_captured`
  would otherwise reject", "so `record_captured`'s registry guard accepts it"), now present in
  `canonical_writer_shaping.py`'s relocated docstring instead. No `classify_venue_error` / `ADAPTER_FETCH_FAILED` /
  `record_*` **call site** was removed from any error-handling path — the real invocation count for `record_captured`
  only ever went up (10→11) across this whole range; `record_empty`/`record_failed` stayed at 3/3 throughout.
- Current HEAD (`51502c3`): 17 = 11 real `record_captured` + 3 `record_empty` + 3 `record_failed`, confirmed via direct
  grep — matches the reported 17.

**Fix applied**: surgical single-entry edit to `unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml`
(`canonical_writer.py` `count: 18` → `count: 17`), following the established precedent (`unified-trading-pm@0996c5e44`:
"surgical 2-line edit; --regenerate-baseline avoided — it would ratchet up every other file"). A full
`--regenerate-baseline` run was deliberately NOT used — it would have silently accepted every other tracked file's
current count (raising or lowering ~333 baselines) with no per-file diagnosis, which is exactly the masking behavior the
ratchet exists to prevent.
`market-data-processing-service/market_data_processing_service/app/core/canonical_writer_shaping.py` (the file that now
carries the relocated docstring, 5 contract calls observed) is a new file not yet in the baseline — it reports as
`[INFO]` only (does not fail the gate) and is left for a future `--regenerate-baseline` pass to adopt, not in scope for
this diagnose-only fix.

**Verified**: `python3 scripts/quality_gates/check_adapter_contract_regression.py --workspace-root <workspace>` now
exits 0 — `canonical_writer.py` no longer appears in the failure list.
