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
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [quality-gates, sentinel, quickmerge-blocked, canonical-stem, leaf-byte-match, regression, defi]
related:
  [
    /plans/archive/issues/defi_fold_manifest_registration_pending_2026_07_21.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-07-21"
parent_epic: defi_master
priority: P1
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
source: [found while shipping the defi_fold_manifest_registration_pending_2026_07_21 fold-script docstring fix]
resolved_by:
  "slot-4, 2026-07-21 — root-caused + fixed all 3 (2 converged with a concurrent agent's independent fix);
  market-tick-data-service@7ce100f9"
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

## Corroborating evidence (2026-07-21, independent repro)

Hit the same `test_slash_id_never_forges_a_path_segment` failure while trying to ship an unrelated
`lst_rate_honest_coverage_2026_07_21.md` Phase 1+2 change (Chainlink weETH/ezETH feeds + a new AAVE oracle collection
branch, both in `oracle_prices_handler.py`/`_oracle_prices_constants.py`). Confirmed via `git stash` isolation (my 3
files fully removed) that the failure reproduces byte-identically on the clean-pulled tree at HEAD `d8efc6d6` — same
error, same `defi/CHAINLINK/oracle_prices/eth/usd` id, same `eth_usd.parquet` message. This is further evidence the
regression is genuinely diff-independent (a third unrelated change now corroborates it), not specific to any one agent's
in-flight work — strengthens the "shared canonicalization helper" hypothesis over a one-off collision. Not fixed here
for the same reason as above (another agent's active, briefed-off-limits track); this plan's own MTDS Phase 1+2 ship
(`_oracle_prices_constants.py`/`oracle_prices_handler.py`/ `tests/unit/test_oracle_prices_handler.py`, otherwise fully
green) is now ALSO blocked pending this fix — see `plans/active/lst_rate_honest_coverage_2026_07_21.md` Progress Log.
**UPDATE: fixed below (Resolution) — market-tick-data-service@7ce100f9 — this ship should now be unblocked; re-run
`quality-gates.sh` on that tree and retry the quickmerge.**

## Resolution (slot-4, 2026-07-21)

Root-caused precisely (this issue's earlier "NOT confirmed root-caused here" is now closed) — all 3 were caused by
**`unified-api-contracts@502ef57e`** ("widen ID-FORM oracle to defi + fail-loud on embedded ':' in
build_instrument_id"), an inherited-dirty-WIP commit landed the same day, NOT by `781204d8`/`56d39325` (the two
candidates this issue originally named — both cleared; unrelated theme overlap, not the actual cause).

1. **`test_slash_id_never_forges_a_path_segment`** — `502ef57e` widened `_ID_FORM_CHECKED_ASSET_GROUPS` to include
   `"defi"`, and that commit's OWN docstring explicitly says this is expected to flag today's DeFi corpus non-canonical
   (bare-`symbol` leaves, not yet the wrapped `VENUE-CHAIN:TYPE:SYMBOL` id) — "the same honest-disclosure outcome the
   CeFi widening produced… NOT a bug in this checker." `live_tick_blob_path`
   (`market_tick_data_service/live/ websocket_runner.py`) was calling `canonical_path_violations()` with the DEFAULT
   (both STRUCTURAL+ID_FORM) check, so it started hard-raising on every DeFi live write the moment defi's
   known-non-canonical-today leaf shape got checked. **Fix**: restrict this ONE call site to
   `violation_classes={STRUCTURAL}` for `asset_group="defi"` only — cefi keeps the full check (its own regression test,
   `test_live_cefi_object_name_equals_canonical_id`, requires ID_FORM stay enforced there).
   market-tick-data-service@7ce100f9.
2. **`WETH:USDC` leaf-byte-match parametrize case** — `502ef57e` ALSO made `build_instrument_id` fail loud on any symbol
   carrying an embedded `':'` for non-sports/prediction asset groups (a DELIBERATE operator ruling,
   `canonical_path_oracle_blind_to_filename_stem_2026_07_20.md` §7 — stops silently minting a double-wrapped id).
   `"WETH:USDC"` was never a valid canonical POOL symbol anyway (the ratified grammar glues legs with a HYPHEN,
   `defi_consolidated_closeout_2026_07_18.md`) — this parametrize case was exercising exactly the malformed input the
   ruling exists to reject. **Fix**: removed the case (kept `"st ETH/x"` covering the same space+slash sanitizer
   characters). **Converged independently with a concurrent agent** (slot-3, `market-tick-data-service@08f15f26`, landed
   first) — same root cause, same fix; no conflict, the landed version was kept as-is.
3. **`ADAF0:USTF0` disabled-by-default byte-identical case** — same `build_instrument_id` ruling; `"ADAF0:USTF0"`
   (Bitfinex's real colon-delimited funding-pair wire notation) is literally the motivating example `502ef57e`'s own
   docstring cites for "silently polluted the CeFi corpus." The disabled-by-default (no catalogue resolver registered)
   fallback used to legitimately produce the double-wrapped `"BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0"` string; the new
   ruling correctly stops that. **Fix**: removed this ONE case from the byte-identical parametrize list, added a
   dedicated `test_disabled_by_default_raises_on_embedded_colon_symbol` documenting the intentional behavior change (no
   source-code change needed — `derive_row_instrument_id` never caught this ValueError, so it already propagated; only
   the STALE test assertion needed updating). **Converged independently with the same concurrent agent** (slot-3,
   `market-tick-data-service@08f15f26`, landed first) — kept as-is.

Verified: full `quality-gates.sh` green on market-tick-data-service post-fix (6621 passed, 0 failed), sentinel
`.qg_last_passed_sha` matched HEAD. No other quickmerge attempts found silently blocked by this window (todo 2 below
folded into this resolution — the window was short, ~1-2 hours, same-day).

## Todos

- [x] 1. [DATA] P1. Root-cause which commit(s) regressed the 3 failing tests (bisect `781204d8` / `56d39325` / any
      commit since, or re-run each test against each commit's tree) and fix the underlying canonicalization bug. — DONE,
      see Resolution above. `unified-api-contracts@502ef57e` is the actual cause (not the 2 originally-named
      candidates); market-tick-data-service@7ce100f9 (test #1, unique fix) + market-tick-data-service@08f15f26 (tests
      #2/#3, concurrent-agent fix, converged independently).
- [x] 2. [REVIEW] P1. Once green, sweep for any other quickmerge attempts in this repo that were silently blocked by
      this same regression window and ship them. — Swept; window was short (same-day), no other blocked attempts found.
