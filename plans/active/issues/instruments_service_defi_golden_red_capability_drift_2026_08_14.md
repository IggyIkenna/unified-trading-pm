---
doc_type: issue
title: >-
  instruments-service defi expected-universe GOLDEN red again (2026-08-14) — AAVE_V3 rewards + broader accumulated drift
  since last regen, blocks fleet-wide instruments-service quickmerge
summary: >-
  Same failure class as the 2026-08-05 incident
  (`instruments_service_defi_golden_red_capability_lockstep_gap_2026_08_05.md`, archived-resolved):
  `test_expected_matches_golden[defi]` fails FLEET-WIDE (CI dep-resolution is content-first at UAC LDR HEAD, so local
  red == CI red for everyone). Root UAC commit found this time is a single, settled change
  (`unified-api-contracts@6a001ea4`, "feat(defi): declare AAVE_V3 rewards as a real, wired capture surface",
  2026-08-14T01:13:12Z, no further registry commits since) — but running the sanctioned
  `regenerate_expected_universe_golden.py` bakes in far more than that one change: the full defi diff is 2280 lines
  touching MORPHO/SPARK/oracle_prices/lst_rates/dex_pool_state/etc., not just AAVE_V3 rewards, meaning real accumulated
  drift has built up since the golden was last regenerated (2026-07-21 per the 08-05 doc's citation, or whatever the
  08-05 lockstep regen actually landed). I did NOT ship this regen — verified I cannot confirm all of that broader diff
  is settled/intentional (same "blind regen silently bakes unverified state" risk the 07-10 and 08-05 incidents both
  warn about). Separately confirmed the regen script also touches tradfi.json — running it unscoped would have silently
  resolved the tradfi CBOE futures_chain xfail
  (`mdps_cboe_vx_futures_chain_grain_excluded_from_ohlcv_15m_24h_2026_08_09.md`, an explicitly open `[OPERATOR]` design
  question) by baking in whichever side is currently live in UAC — I reverted that file before it could ship.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [defi, expected-universe, golden-drift, aave-v3, rewards, qg-red, cross-repo, lockstep, tradfi-xfail-near-miss]
related:
  [
    /plans/active/issues/instruments_service_defi_golden_red_capability_lockstep_gap_2026_08_05.md,
    /plans/active/issues/mdps_cboe_vx_futures_chain_grain_excluded_from_ohlcv_15m_24h_2026_08_09.md,
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-14"
author: slot-18 (data_engineering craft)
last_updated: "2026-08-14"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
scope_note: >-
  Filed local-only (assigned_vm: NA) rather than dispatched — this is a triage/handoff doc, not a work item requiring
  its own AO dispatch; whoever owns the DeFi capability audit resolves it inline per the 08-05 precedent's playbook.
priority: P1
drift_direction: advance-code
source: [sports_taxonomy_p2_migration-004 (slot-18), discovered while shipping an unrelated read-only census script]
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    instruments-service/scripts/regenerate_expected_universe_golden.py,
    instruments-service/tests/unit/scripts/test_expected_universe_golden.py,
    instruments-service/tests/unit/scripts/goldens/expected_universe/defi.json,
    unified-api-contracts/unified_api_contracts/registry/(capability registries),
  ]
---

## Finding

Hit while attempting to ship an unrelated 1-file `instruments-service` commit (a read-only sports census script,
`sports_taxonomy_p2_migration-004`). `quickmerge`'s Pass-1 re-gate ran full QG on current HEAD and failed:

```
FAILED tests/unit/scripts/test_expected_universe_golden.py::TestGoldenByteIdentical::test_expected_matches_golden[defi]
E   AssertionError: EXPECTED matrix drift for 'defi': golden=366, actual=382
E   extra (first 10): [('AAVE_V3-ARBITRUM','a_token','rewards'), ('AAVE_V3-ARBITRUM','debt_token','rewards'), ...]
```

This is content-identical to the 2026-08-05 incident's failure mode (same test, same "UAC capability churn outruns the
checked-in golden" mechanism), now resolved-and-archived — this is a **fresh recurrence**, not a re-open.

**UAC-side root commit**: `unified-api-contracts@6a001ea4` ("feat(defi): declare AAVE_V3 rewards as a real, wired
capture surface", 2026-08-14T01:13:12Z). Checked for continued churn (`git log --since="2 hours ago" -- registry/`): 0
further registry commits — **this specific change is settled, not mid-flight**, unlike the 08-05 case's 12-commits-
in-83-minutes churn.

**Attempted the sanctioned fix, did NOT ship it**: ran
`instruments-service/scripts/regenerate_expected_universe_golden.py` (UAC/UTL both clean, so the script's own dirty-tree
guard passed). Result:

- Correctly scoped test-wise: `test_expected_matches_golden[defi]` → green; `[tradfi]` stayed `xfail` (not silently
  resolved) **only because I reverted `tradfi.json` before committing** — the unscoped regen run had ALSO rewritten
  `cefi.json` / `tradfi.json` / `sports.json` / `prediction.json`, and `[tradfi]` **xpassed** in that unscoped run,
  meaning a blind regen would have silently baked in the CBOE futures_chain admission side of an explicitly open
  `[OPERATOR]` design question (`mdps_cboe_vx_futures_chain_grain_excluded_from_ohlcv_15m_24h_2026_08_09.md`) without
  that question being resolved. Caught by reading the pytest output (`1 xpassed` where `1 xfailed` was expected), not by
  any automated gate — **the regen script's own dirty-tree guard does not protect against this**, since it only checks
  git cleanliness, not per-asset-group semantic scope.
- Even scoped to just `defi.json`: the diff is **2280 lines**, not a small AAVE_V3-only delta.
  `git diff | grep -oE '"[a-z_]+"' | sort | uniq -c` shows large blocks of `oracle_prices` (142), `lending_indices`
  (92), `risk_params` (72), `liquidations` (72), `lst_rates` (60), `dex_pool_state` (60), plus MORPHO-_/SPARK-_ venue
  additions — i.e. **substantial accumulated drift beyond the one AAVE_V3-rewards commit**, most likely un-regenerated
  since whatever the last defi golden regen actually was. I have not audited whether all of this broader state is itself
  settled/intentional (same class of question the 08-05 doc explicitly reserves for the capability-work owner, not a
  golden-regen operator).

**Did not ship the regen.** Reverted both files
(`git checkout -- defi.json tradfi.json cefi.json sports.json prediction.json`), tree confirmed clean.

## Why this blocks the fleet

Identical mechanism to the 08-05 precedent: CI's dep resolution is content-first at UAC LDR HEAD
(`python-quality-gates-v2.yml::clone_repo`), so this red is fleet-wide, not local-ahead-of-CI. Any `instruments-service`
quickmerge re-gates on the current red tree and fails Pass-1, regardless of what the shipping commit itself touches.
Currently blocking: my own unrelated census-script commit (`instruments-service@3fbcf108`, **committed locally, NOT
pushed** — sitting ahead=1 in slot-18's checkout pending this clearing).

## Why this is not fixable by a unilateral golden regen (same rule as 08-05)

- The golden's own docstring + both incidents (07-10, 08-05) forbid regenerating while capability content may not be
  fully settled — a regen silently bakes whatever state is live, correct or not.
- I can positively confirm ONE contributing commit (`6a001ea4`) is settled (>1hr old, no further registry churn) — but
  the diff is far larger than that one commit's scope, and I have not audited the rest.
- The regen tool is **not asset-group-scoped in its blast radius** — running it for "just defi" still rewrites every
  other asset group's golden file, which is how the tradfi near-miss happened. Whoever does own this fix should be aware
  of that and diff EVERY file the script touches before committing, not just the one they intended.

## Recommendation

Same resolution shape as 08-05: whoever owns (or can quickly audit) the current DeFi capability registry state should
confirm the accumulated diff (AAVE_V3 rewards + the MORPHO/SPARK/oracle_prices/lst_rates/etc. additions) is intentional,
then run the regen and **commit only the asset-group file(s) actually intended** (discard any incidental
cefi/tradfi/sports/prediction rewrites the tool also produces, exactly as this session did) — do not commit the tool's
full unscoped output.

## Todos

- [ ] [DATA] P1. **Audit + lockstep-regen the defi expected-universe golden** — confirm the accumulated diff (AAVE_V3
      rewards `unified-api-contracts@6a001ea4` + MORPHO/SPARK/oracle_prices/lst_rates/dex_pool_state additions) is
      intentional/settled, then run `regenerate_expected_universe_golden.py` and commit ONLY
      `tests/unit/scripts/goldens/expected_universe/defi.json` (revert every other file the script also rewrites).
      Unblocks fleet-wide `instruments-service` quickmerge. SSOT: this doc + the 08-05 precedent.
- [ ] [SCRIPT] P3. **Scope `regenerate_expected_universe_golden.py` to `--asset-group=<ag>`** (or add an explicit
      warning banner) so a future operator regenerating one asset group's golden can't silently also rewrite an
      unrelated asset group carrying its own open `[OPERATOR]`-gated xfail (as `tradfi.json` nearly was here).

## Progress Log

- **2026-08-14 (slot-18)**: discovered while attempting to ship an unrelated census script; root-caused the UAC commit,
  attempted + reverted the regen after finding (a) it silently would have resolved an unrelated open tradfi design
  question, and (b) the defi-scoped diff is far broader than the one settled commit. Filed this doc; my own
  census-script commit stays local-only (`instruments-service@3fbcf108`, ahead=1) until this clears — the actual
  valuable output of that work (the 15.9M-row census numbers + risk analysis) is already durably shipped separately via
  `unified-trading-pm@974700fc98`, so nothing load-bearing is at risk from the script itself waiting.
