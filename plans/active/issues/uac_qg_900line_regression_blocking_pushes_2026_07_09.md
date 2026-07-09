---
doc_type: issue
title:
  "unified-api-contracts quality-gates.sh is red repo-wide (pre-existing, 4 files regressed past the 900-line cap) —
  blocks ALL quickmerge pushes to this repo"
summary:
  "While shipping a real, additive, fully-tested BINANCE-FUTURES/BINANCE-DELIVERY instrument_id @LIN/@INV
  canonicalization fix (canonical_id_builder.py margin_marker kwarg + tests, see
  instrument_id_format_canonicalization_2026_07_08.md finding 1), `bash scripts/quality-gates.sh --no-fix` failed on '❌
  Files exceed 900 lines' for 4 files none of which this session touched: mvp_scope.py (1479L), honest_coverage.py
  (1067L), source_priority.py (1009L), tradfi_ticker_universe.py (916L). Verified via `git status` that all 4 are 100%
  clean/unmodified in this working tree (not this session's or any sibling's dirty WIP), and via `git log -1` per file
  that each was pushed over 900 lines by an already-merged commit (89b16943, d71f3228/844c5ee6, cbaa7560) unrelated to
  this session. Same failure class as [[mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08]] (a hard,
  zero-tolerance file-size cap with NO baseline-ratchet mechanism, unlike
  DTZ/TID251/fallback-import/empty-string-fallback which explicitly allow existing debt as long as it doesn't grow) —
  but for the `MAX_FILE_LINES=900` check instead of empty-string-fallback. There is currently no sanctioned way to
  quickmerge ANY change to unified-api-contracts, including changes fully unrelated to these 4 files. Separately, the
  SAME run also failed '❌ Quality gates must complete in <720s (took 807s)' — likely a transient host-contention
  artifact (5 concurrent quality-gates.sh runs observed from other slots/sessions at the time), not re-verified in
  isolation."
status: open
nature: issue
asset_group: [cefi, defi, tradfi]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer]
tags: [quality-gates, file-size, ci-blocking, technical-debt, ratchet]
related:
  [
    mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md,
    ../issues/instrument_id_format_canonicalization_2026_07_08.md,
  ]
created: 2026-07-09
parent_epic: instruments_master
priority: P1
source:
  "Discovered while shipping instruments-service/unified-api-contracts changes for the BINANCE-FUTURES/BINANCE-DELIVERY
  leg of instrument_id_format_canonicalization_2026_07_08.md finding 1 — the UAC-side canonical_id_builder.py
  margin_marker addition is complete, unit-tested (own tests pass, type-check clean, codex-compliance clean), and cannot
  currently be pushed via the mandatory quickmerge.sh path because the repo's quality gate is independently red for
  unrelated pre-existing reasons."
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
last_updated: 2026-07-09
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **CI-BLOCKING finding — every quickmerge push to `unified-api-contracts` is currently blocked**, not just the author's
> own change. Same failure family as [[mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08]], different
> check (`MAX_FILE_LINES=900`, no ratchet) — this class of gate (hard zero-tolerance cap, no baseline-ratchet mechanism)
> is evidently repeatable across checks, matching that doc's own P2 todo #3 prediction ("check whether other
> repos/checks have the same latent gap").

## What was found

Shipping the UAC leg of a real, additive, fully-tested fix
(`unified_api_contracts/internal/reference/canonical_id_builder.py` — new opt-in `margin_marker` kwarg on
`build_instrument_id`/`build_canonical_instrument_id`/`build_leg`, backward compatible, 245 new lines total across the
module + its test file), `bash scripts/quality-gates.sh --no-fix` failed:

```
❌ Files exceed 900 lines:
  ./unified_api_contracts/canonical/crosscutting/mvp_scope.py: 1479 L
  ./unified_api_contracts/canonical/crosscutting/honest_coverage.py: 1067 L
  ./unified_api_contracts/canonical/crosscutting/source_priority.py: 1009 L
  ./unified_api_contracts/registry/tradfi_ticker_universe.py: 916 L
```

None of these 4 files are in `canonical_id_builder.py`'s own diff, and none are `SIZE_EXTRA_EXCLUDES`-listed in
`scripts/quality-gates.sh` (that list already carries ~60 legitimate large-file carve-outs with individual audit
comments — `canonical_id_builder.py` itself is one of them — these 4 are not).

**Verified 100% pre-existing, not this session's or any sibling's dirty WIP** — `git status --short` for all 4 files
returns nothing (clean):

```
git status --short -- unified_api_contracts/canonical/crosscutting/mvp_scope.py \
  unified_api_contracts/canonical/crosscutting/honest_coverage.py \
  unified_api_contracts/canonical/crosscutting/source_priority.py \
  unified_api_contracts/registry/tradfi_ticker_universe.py
# (empty output)
```

**Verified via `git log -1` per file that each was pushed over 900 lines by an already-merged commit**, unrelated to
this session's BINANCE-FUTURES/BINANCE-DELIVERY task:

| File                        | Lines | Last commit                                                                                                           |
| --------------------------- | ----- | --------------------------------------------------------------------------------------------------------------------- |
| `mvp_scope.py`              | 1479  | `89b16943` "feat(defi): define DeFi MVP scope as full IS-producible capture universe ... wire MARGINFI/SOLEND-SOLANA" |
| `honest_coverage.py`        | 1067  | `d71f3228` "fix(honest-coverage): add EXPECTED_WRITE_GATE_NAN_THRESHOLD_EXCEEDED to EmptyConfirmedReason"             |
| `source_priority.py`        | 1009  | `844c5ee6` "feat(tradfi): close-out — KRX/Yahoo venue + parity gate + Barchart removal + databento floor precision"   |
| `tradfi_ticker_universe.py` | 916   | `cbaa7560` "feat(tradfi): expand SP500_TICKERS to full current S&P 500 membership"                                    |

An OLDER, related issue (`plans/archive/issues/uac_qg_preexisting_size_violations_2026_05_14.md`) already covered
`honest_coverage.py`/`source_priority.py` once — that doc is ARCHIVED (implying resolved at the time: both were split
under 900L per `scripts/quality-gates.sh`'s own header comments, "honest_coverage.py (was 1,141 → 788 +
\_honest_coverage_logic.py), source_priority.py (was 1,018 → 562 + \_source_priority_data.py)"). Both have since
**regressed back over 900 lines** via ordinary feature growth on the un-split facade file, and `mvp_scope.py` /
`tradfi_ticker_universe.py` are newly over the cap for the first time (not previously tracked). This is the same "split
once, regrows unbounded, no ratchet re-enforces the cap going forward" failure mode already predicted in the MTDS
empty-string-fallback doc's todo #3.

Separately, the same run also failed on run duration:

```
❌ Quality gates must complete in <720s (took 807s)
```

5 concurrent `quality-gates.sh` processes were observed running from other slots/sessions on this shared host at the
time (`ps aux | grep -c quality-gates.sh` → 5) — plausible host-contention cause, not re-verified in isolation (a re-run
on a quieter host was not attempted in this pass; if it recurs on a quiet host, it's a separate, real finding).

## Why this matters

`quickmerge.sh` re-runs the FULL `quality-gates.sh` before allowing any push (same `--skip-codex`-disabled policy as the
MTDS finding, WS-L #1014). There is currently **no sanctioned way to quickmerge any change** to `unified-api-contracts`
— not just changes that touch these 4 files — until either (a) the 4 files are split back under 900 lines (matching the
prior 2026-05-14 precedent for 2 of them), or (b) they get an audited `SIZE_EXTRA_EXCLUDES` carve-out (only appropriate
if a real audit confirms they're legitimately comprehensive declarative/registry content, matching the bar every
existing `SIZE_EXTRA_EXCLUDES` entry already meets — not a default-safe assumption for these 4 specifically without
checking).

## Todos

- [ ] [DECISION] P1. **Per-file: split back under 900L (re-apply the 2026-05-14 pattern) vs. audit-and-exclude** — for
      `honest_coverage.py`/`source_priority.py` specifically, the prior split module names (`_honest_coverage_logic.py`,
      `_source_priority_data.py`) may already exist and just need the newer growth moved into them (verify first — they
      may have been re-merged, or the new growth may be genuinely new surface not covered by the old split).
      `mvp_scope.py`/`tradfi_ticker_universe.py` need a first-time declarative-vs-logic AST audit (matching the audit
      already done for the ~60 existing `SIZE_EXTRA_EXCLUDES` entries, per `scripts/quality-gates.sh`'s own ">900-line
      audit 2026-06-11" comment block) before excluding either.
- [ ] [SCRIPT] P1. **Execute the decided fix per file** and get `bash scripts/quality-gates.sh` exiting 0 on
      `unified-api-contracts`'s `live-defi-rollout` tip.
- [ ] [VERIFY] P2. **Consider whether `MAX_FILE_LINES=900` needs the same baseline-ratchet treatment as
      `check_no_empty_string_fallback.py`/STEP 5.101** (seeded per-repo baseline, shrink-only, "NEVER raise a count")
      rather than a flat zero-tolerance cap — the split-then-regrow-then-block cycle already observed twice for
      `honest_coverage.py`/`source_priority.py` suggests the cap alone doesn't durably prevent regrowth; a ratchet at
      least stops it from silently exceeding whatever the last-known-good split achieved.
- [ ] [VERIFY] P3. **Re-run quality-gates.sh on a quiet host** (0-1 other concurrent `quality-gates.sh` processes) to
      confirm whether the 807s/720s duration failure is genuinely host-contention-caused (transient) or a real,
      independent budget regression needing its own fix (`MAX_DURATION` bump or suite speed-up).

## Progress Log

- **2026-07-09** — Filed while shipping the UAC leg of a real BINANCE-FUTURES/BINANCE-DELIVERY instrument_id
  canonicalization fix (`canonical_id_builder.py` `margin_marker` kwarg, additive/backward-compatible, own tests +
  type-check + codex-compliance all pass). Not attempting the 4-file split/audit in this pass — out of scope for the
  BINANCE task, and 3 of the 4 files (DeFi MVP scope, TradFi source-priority, TradFi ticker universe) are unrelated
  domains this session has no context on. Filed here per the "outside every plan" triage path (matching the sibling MTDS
  finding's precedent) instead of silently skipping, force-pushing around the gate, or hand-editing
  `SIZE_EXTRA_EXCLUDES` without a real audit. The BINANCE fix itself is left uncommitted in the working tree
  (`unified_api_contracts/internal/reference/canonical_id_builder.py` +
  `tests/internal/unit/test_canonical_id_builder.py`) pending this gate clearing.
