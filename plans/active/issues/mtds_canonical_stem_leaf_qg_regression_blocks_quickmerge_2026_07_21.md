---
doc_type: issue
title:
  market-tick-data-service HEAD has 3 pre-existing test failures (canonical stem / leaf-byte-match / catalog decompose)
  that block EVERY quickmerge in the repo — unrelated to any single agent's in-flight diff
summary: >-
  While shipping an unrelated one-line-docstring fix in
  `scripts/fold_legacy_solana_defi_to_consolidated_canonical_2026_07_21.py` (per
  `defi_fold_manifest_registration_pending_2026_07_21.md` todo 3), `bash scripts/quality-gates.sh --no-fix` on the
  current `live-defi-rollout` HEAD (`f6176e8b` at time of writing) reproducibly fails 3 tests, deterministic across two
  independent full runs (~2min apart, same failures both times):
  `tests/unit/test_canonical_stem_live_batch_parity.py::test_slash_id_never_forges_a_path_segment`,
  `tests/unit/scripts/test_migrate_defi_batch_to_per_instrument.py::TestLeafByteMatchWithR1::test_decoded_leaf_equals_r1_forward_writer_leaf[WETH:USDC]`,
  `tests/market_interface/adapters/cefi/test_catalog_decompose_all_venues.py::test_disabled_by_default_output_is_byte_identical[...]`.
  None of the 3 touch DeFi-fold/manifest-registration code — all three are about canonical leaf/stem/symbol-sanitization
  byte-identity. The two most recent commits on that theme (`781204d8 fix(defi): harden _sanitize_defi_symbol against
  zalgo spam-token symbols…` and `56d39325 fix(mtds): tradfi equity/etf/index manifest record uses raw bare-symbol id…`)
  are the most plausible culprits by subject-matter overlap, but this was NOT root-caused in depth (out of scope for the
  fold-registration task; the touched files are inside another concurrent agent's active DeFi-canonicalization track per
  the collision-avoidance briefing for that task). Because `quickmerge.sh`'s Pass-1 sentinel is written ONLY on a fully
  green `quality-gates.sh` run, this repo-wide regression blocks `quickmerge --agent` for ANY file in
  market-tick-data-service until fixed — not just the one this issue was found from.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [quality-gates, sentinel, quickmerge-blocked, canonical-stem, leaf-byte-match, regression, defi]
related: [defi_fold_manifest_registration_pending_2026_07_21.md, defi_consolidated_closeout_2026_07_18.md]
created: "2026-07-21"
parent_epic: defi_master
priority: P1
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
source: [found while shipping the defi_fold_manifest_registration_pending_2026_07_21 fold-script docstring fix]
resolved_by:
locked_by:
depends_on: []
---

# MTDS quality-gates regression blocks quickmerge (canonical stem / leaf-byte-match / catalog decompose)

## Evidence

Two independent full `bash scripts/quality-gates.sh --no-fix` runs on `live-defi-rollout` (HEAD `f6176e8b`, ~2 min
apart), both: `3 failed, 6605 passed, 17 skipped` — same 3 tests both times:

```
FAILED tests/unit/test_canonical_stem_live_batch_parity.py::test_slash_id_never_forges_a_path_segment
FAILED tests/unit/scripts/test_migrate_defi_batch_to_per_instrument.py::TestLeafByteMatchWithR1::test_decoded_leaf_equals_r1_forward_writer_leaf[WETH:USDC]
FAILED tests/market_interface/adapters/cefi/test_catalog_decompose_all_venues.py::test_disabled_by_default_output_is_byte_identical[BITFINEX-FUTURES-PERPETUAL-ADAF0:USTF0-BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0]
```

`test_slash_id_never_forges_a_path_segment` asserts a DeFi oracle id containing `/` (e.g. `eth/usd`) stays one path
segment (`eth_usd.parquet`) via `live_tick_blob_path`. The other two assert byte-identical leaf naming / catalog
decompose output. All three are about canonical leaf/stem/symbol sanitization — the exact theme of the two most recent
related commits at time of writing:

- `781204d8 fix(defi): harden _sanitize_defi_symbol against zalgo spam-token symbols exceeding GCS object-name limit`
- `56d39325 fix(mtds): tradfi equity/etf/index manifest record uses raw bare-symbol id + lowercase hive-token type…`

Neither commit's test suite (per its own diff --stat) touches the 3 failing test files directly, so this is most likely
an indirect regression through shared sanitization/canonicalization helpers — NOT confirmed root-caused here.

## Why this wasn't fixed in-place

The touched files (`build_instrument_catalogue.py`'s `_defi_pool_dual_form`, DeFi canonical-write helpers, instrument
catalogue leaf-naming) are inside an ACTIVE, concurrent DeFi-canonicalization track (token-resolver wiring +
`defi_consolidated_closeout_2026_07_18.md`) that a sibling agent session was explicitly briefed to own, with an explicit
collision-avoidance instruction to any other agent NOT to touch those files. Diagnosing and fixing a 3-test regression
in that exact surface without that session's context risks colliding with in-flight work or mis-fixing the actual root
cause. Filed here instead so whichever agent owns that track (or the next one) picks it up with full context, per the
findings-triage HARD RULE ("fits another plan → annotate it, don't fix").

## Impact

**Every** `quickmerge --agent` in market-tick-data-service is blocked until this is fixed — the sentinel
(`.qg_last_passed_sha`) can only be written by a fully green run, and the failure is deterministic (not flaky), so
retrying quickmerge without a code fix will not help. Confirmed concretely: a one-line-docstring fix in
`scripts/fold_legacy_solana_defi_to_consolidated_canonical_2026_07_21.py` (zero behavioral change, verified unrelated to
any of the 3 failing modules) could not be shipped via quickmerge because of this — see
`defi_fold_manifest_registration_pending_2026_07_21.md` todo 3's Progress Log.

## Todos

- [ ] 1. [DATA] P1. Root-cause which commit(s) regressed the 3 failing tests (bisect `781204d8` / `56d39325` / any
      commit since, or re-run each test against each commit's tree) and fix the underlying canonicalization bug.
- [ ] 2. [REVIEW] P1. Once green, sweep for any other quickmerge attempts in this repo that were silently blocked by
      this same regression window and ship them.
