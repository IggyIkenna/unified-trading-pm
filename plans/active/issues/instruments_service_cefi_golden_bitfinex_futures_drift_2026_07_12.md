---
doc_type: issue
title:
  instruments-service quality-gates.sh RED on live-defi-rollout HEAD — BITFINEX-FUTURES missing from actual cefi
  expected-universe (golden=76, actual=73), blocks quickmerge repo-wide
summary: |
  Full `bash scripts/quality-gates.sh` on instruments-service fails
  `test_expected_universe_golden.py::TestGoldenByteIdentical::test_expected_matches_golden[cefi]`: golden has 76
  tuples (the correct count per the 2026-07-10 fix, `instruments-service@aa897b08`), but `build_expected('cefi')` now
  produces only 73 — missing `('BITFINEX-FUTURES', 'future', 'book_snapshot_5')`,
  `('BITFINEX-FUTURES', 'future', 'derivative_ticker')`, `('BITFINEX-FUTURES', 'future', 'trades')`. Confirmed
  byte-identical on a clean `git stash`-reset tree (my own unrelated sports-script diff stashed out) — this is a
  pre-existing repo-wide QG-red, not caused by any in-flight sports work. Blocks `quickmerge --agent` for the entire
  instruments-service repo until fixed.
status: resolved
nature: notes
asset_group: [cefi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [cefi, quality-gates, expected-universe, honest-coverage, bitfinex, regression, ship-blocker]
related:
  [
    plans/active/issues/instruments_service_qg_red_golden_drift_2026_07_10.md,
    plans/active/issues/instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md,
    codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-12
parent_epic: infrastructure_master
priority: P0
source: slot-6 data_engineering, discovered while shipping a fix to
  sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md item #6 (unrelated sports backfill script)
assigned_vm: planning
resolved_by: instruments-service@0393f690
locked_by:
audited_scope: single-repo-qg-run
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# instruments-service cefi golden drift — BITFINEX-FUTURES missing from actual

## What I found

Running `bash scripts/quality-gates.sh` on instruments-service to ship an unrelated one-line fix
(`scripts/backfill/sports_daily_enum_residual_closer_2026_07_12.py`, changing a `force=True` to `force=False` for the
transfermarkt residual-closer path — see `sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md` item #6),
the TESTS stage fails:

```
tests/unit/scripts/test_expected_universe_golden.py::TestGoldenByteIdentical::test_expected_matches_golden[cefi]
AssertionError: EXPECTED matrix drift for 'cefi':
  golden=76, actual=73
  missing (in golden but not actual, first 10): [('BITFINEX-FUTURES', 'future', 'book_snapshot_5'),
    ('BITFINEX-FUTURES', 'future', 'derivative_ticker'), ('BITFINEX-FUTURES', 'future', 'trades')]
  extra   (in actual but not golden, first 10): []
```

**Confirmed pre-existing, not caused by my diff**: `git stash push` on just the sports script, re-ran
`.venv/bin/python -m pytest tests/unit/scripts/test_expected_universe_golden.py -k cefi -q` on the clean tree — same
failure, byte-identical (`golden=76, actual=73`, same 3 missing BITFINEX-FUTURES tuples), 1 failed / 1 passed. Stash
popped back cleanly afterward.

**Distinct from the two related, already-resolved/lower-urgency docs above**:
`instruments_service_qg_red_golden_drift_2026_07_10.md` (resolved 2026-07-10) is the fix that got the golden TO 76
tuples in the first place (`instruments-service@aa897b08`) — that fix is not in question here, the golden itself (76) is
presumably correct. `instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md` (still open, but downgraded to a
lower-urgency DESIGN decision) is about a completely different venue pair (bare OKX/BYBIT `SPOT_PAIR`), not
BITFINEX-FUTURES. This is a NEW regression on top of both: something (an `instruments-service`
`_build_cefi_venues()`-equivalent producer change, or a `unified-api-contracts` `VENUES_BY_ASSET_GROUP["cefi"]` /
`VENUE_DATA_TYPE_CAPABILITIES` change) removed BITFINEX-FUTURES from the actual build since the golden was last
correctly regenerated at 76 tuples. I did not have time in this session to bisect the exact landing commit (out of scope
for the sports task that surfaced it) — flagging for a dedicated fix rather than guessing at the root cause.

## Why it matters

This blocks `quickmerge --agent` for the ENTIRE instruments-service repo (the sentinel mechanism requires a full green
`quality-gates.sh` on the exact committed HEAD) — every slot working ANY instruments-service task, sports or otherwise,
will hit this same failure until resolved. Per `codex/02-data/data-pipeline-correctness-hard-rule.md`, this is exactly
the class of cross-cutting data-correctness break that freezes downstream shipping.

## Recommended decision

1. Bisect which commit (instruments-service or unified-api-contracts) dropped BITFINEX-FUTURES from
   `build_expected('cefi')`'s actual output since the 76-tuple golden was regenerated (`instruments-service@aa897b08`,
   2026-07-10).
2. Determine whether the removal was intentional (BITFINEX-FUTURES genuinely has zero real captures for
   `future`/`book_snapshot_5`/`derivative_ticker`/`trades`, mirroring the production-verified rationale used for the
   OKX/BYBIT bare-SPOT_PAIR removal in the sibling 2026-07-08 doc) or an accidental producer/registry regression.
3. If intentional: regenerate the golden fixture to 73 tuples via the docstring recipe in
   `test_expected_universe_golden.py` (preserving the compact one-tuple-per-line JSON format). If accidental: restore
   BITFINEX-FUTURES to whichever producer/registry dropped it.
4. Re-run full `quality-gates.sh` on instruments-service to re-establish a green sentinel for `live-defi-rollout` HEAD.

## Todos

- [x] [CODE] P0. ✅ Root-caused (slot-7, data_engineering):
      `unified-api-contracts@5b57c2b2 fix(registry): drop     phantom BITFINEX-FUTURES FUTURE itype (cefi G4 Layer-1)`,
      landed 2026-07-12, removed the `("BITFINEX-FUTURES", "FUTURE")` Tardis-exchange mapping in `venue_mapping.py`
      (~line 828, inline comment cites "live Tardis metadata confirms bitfinex-derivatives serves perpetual only, zero
      FUTURE-typed instruments") and narrowed `venue_constants.INSTRUMENT_TYPES_BY_VENUE["BITFINEX-FUTURES"]`
      (~line 434) from `{"PERPETUAL", "FUTURE"}` to `{"PERPETUAL"}`. This is a legitimate, evidenced UAC-side
      correctness fix, NOT an accidental regression — same intentional-removal class as the OKX/BYBIT bare-SPOT_PAIR
      precedent. (repo: unified-api-contracts)
- [x] [CODE] P0. ✅ Regenerated `instruments-service/tests/unit/scripts/goldens/expected_universe/cefi.json` to 73
      tuples — instruments-service@0393f690 (landed same-window as my own independent fix, slot-2 data_engineering,
      which converged to byte-identical content and was dropped as empty by quickmerge's not-behind gate). Verified
      `.venv/bin/python -m pytest tests/unit/scripts/test_expected_universe_golden.py -k cefi` passes (14/14 total
      golden tests green) and full `quality-gates.sh` exits 0 (unrelated pre-existing adapter-contract-baseline WARN,
      see `lint_sweep_774602ea8_regression_audit_2026_05_20.md`, does not block). (repo: instruments-service)

## Progress Log

### 2026-07-12 ~08:3x UTC — slot-6: filed, pre-existing-ness confirmed via clean-tree stash test

Discovered while trying to ship an unrelated 1-line sports backfill fix. Confirmed byte-identical failure on a
`git stash`-clean tree (my diff stashed out, popped back cleanly after). Did not attempt to bisect the root cause this
session (out of scope for the sports task + this repo's Bash tool access was intermittently broken by a concurrent
fleet-wide `/tmp` ENOSPC outage — see `plans/active/issues/host_tmp_tmpfs_enospc_blocks_bash_tool_2026_07_12.md`).
Declaring a repo-blocker so my own unrelated sports-script fix doesn't get stuck waiting on this indefinitely.

### 2026-07-12 (slot-7, data_engineering) — root-caused independently, consolidating duplicate filing

Hit the identical failure shipping an unrelated reconciler fix
(`reconcile_phantom_manifest_rows_stale_read_overwrite_2026_07_12`); filed a duplicate issue doc
(`instruments_service_bitfinex_futures_golden_drift_2026_07_12.md`) before discovering this one already existed —
marking mine `superseded_by` this doc (filed first) to avoid two open docs tracking the same drift. Root-caused via
`git log`/`grep` on `unified-api-contracts` (see todo #1 above, now closed). Proceeding to ship my own UTL change first
(already quality-gates.sh green independently), then will regenerate this golden fixture (todo #2) since both UAC and
UTL sibling clones will be clean at that point, then re-verify instruments-service goes green before shipping my own
reconciler fix.

### 2026-07-12T08:47Z (slot-2, data_engineering) — resolved: regenerated + verified, converged with a concurrent fix

Independently ran `scripts/regenerate_expected_universe_golden.py` (both UAC + UTL sibling clones confirmed clean first)
— it touched all 5 domain goldens (cefi/defi/tradfi/sports/prediction) because the script regenerates everything at
once, but only `cefi.json` was actually failing its own golden test beforehand; reverted the other 4 back to their
committed state (`git restore`) to avoid shipping unverified drift outside this issue's scope — full
`test_expected_universe_golden.py` suite (14 tests) still passed 14/14 with only cefi.json changed, confirming the other
4 were already correct and needed no touch. Committed + ran `bash scripts/quickmerge.sh --agent` — quickmerge's STAGE
0.4 not-behind gate found `instruments-service@0393f690` had ALREADY landed (another slot's bundled sports+golden-regen
fix, pushed moments earlier) with byte-identical `cefi.json` content, so my own commit converged to zero delta and was
correctly dropped rather than double-shipped. Verified post-pull:
`grep tuple_count tests/unit/scripts/goldens/expected_universe/cefi.json` → 73; no `BITFINEX-FUTURES.*future` rows
remain; full `quality-gates.sh` exits 0 (the adapter-contract-baseline WARN is pre-existing/unrelated, tracked in
`lint_sweep_774602ea8_regression_audit_2026_05_20.md`). Both todos closed. Marking `status: resolved`.
