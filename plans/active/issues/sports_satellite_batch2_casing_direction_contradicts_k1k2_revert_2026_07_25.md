---
doc_type: issue
title:
  "sports_satellite_ao_dispatch_batch2_2026_07_24.md's league_id-casing-migration todo targets UPPER-case
  (`instrument_type=ODDS/data_type=TRADES`), contradicting the operator's FINAL 2026-07-23 lower-case ruling that
  explicitly REVERTS this exact migration direction"
summary: >-
  Found by the full-corpus `/plan-reconcile` run (2026-07-24/25), confirmed P0 (the only P0 finding across 246 confirmed
  findings). `sports_satellite_ao_dispatch_batch2_2026_07_24.md` (an AO-dispatchable plan, `assigned_vm: planning`)
  carries a todo instructing a worker to run `migrate_sports_league_id_casing_2026_07_21.py --apply-prod` to
  copy+CAS-verify ~139,155 raw `batch_odds_api/odds/trades` objects to UPPER-case canonical paths
  (`league_id=<CANON>/instrument_type=ODDS/data_type=TRADES/`). But `sports_consolidated_closeout_2026_07_19.md`'s
  "Canonical target" section states, verbatim: "data_type = LOWER-case everywhere for sports — FINAL, reconciled
  2026-07-23 ... This REVERTS Track C's K1/K2 work below (market-tick-data-service@2536b91c / @ad4f1872, ~260,298 GCS
  objects physically copied to uppercase paths + manifest-swapped, 'shipped+verified' 2026-07-22) — that migration must
  be undone, not extended." The satellite-batch2 todo, if dispatched and executed, would copy ~139,155 MORE objects into
  the exact upper-case shape the operator has already ruled must be reverted — actively extending the problem, not just
  repeating a stale claim. A prior plan-reconcile pass already fixed this same class of stale-UPPER reference elsewhere
  (`sports_master_closeout_2026_07_21.md`, codex docs) per `sports_plan_and_docs_reconcile_findings_2026_07_24.md`, but
  this newer satellite-batch2 doc was never checked against the revert.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [sports, league-id-casing, ao-dispatch, contradiction, data-correctness, plan-reconcile, prod-migration-risk]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
    /plans/active/issues/sports_plan_and_docs_reconcile_findings_2026_07_24.md,
    /codex/02-data/sports-data-types-catalog.md,
  ]
created: "2026-07-25"
parent_epic: sports_master
priority: P0
source: >-
  Full-corpus /plan-reconcile run (background Workflow task wmkz9g9jq, run wf_a5681818-eef), 2026-07-24/25 — 74 hunters,
  246 confirmed findings, adversarially verified. This is the SOLE P0 among all 246.
resolved_by:
locked_by:
assigned_vm:
code_refs: [market-tick-data-service/scripts/sports/league_id_relocation/migrate_sports_league_id_casing_2026_07_21.py]
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

# sports_satellite_ao_dispatch_batch2's casing-migration todo targets the WRONG (already-reverted) direction

## Why this wasn't fixed inline

`plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md` had a live mtime (<120s old) at discovery time —
another concurrent session was actively editing it. Per this workspace's shared-checkout safety rules, a live file is
PROTECT-only: this issue doc is filed standalone (touches no live file) so the finding survives regardless of which
session next touches that plan, and the fix is queued as a todo below for whoever picks it up next (possibly this same
session, once the file is no longer live-locked).

## What was verified directly (not just the hunter's claim)

1. `plans/active/sports_consolidated_closeout_2026_07_19.md` lines 118-124, verbatim: **"data_type = LOWER-case
   everywhere for sports — FINAL, reconciled 2026-07-23 ... This REVERTS Track C's K1/K2 work below
   (market-tick-data-service@2536b91c / @ad4f1872, ~260,298 GCS objects physically copied to uppercase paths +
   manifest-swapped, 'shipped+verified' 2026-07-22) — that migration must be undone, not extended."** This is an
   explicit, dated, well-evidenced operator ruling (cites a 7-agent GCS audit finding zero uppercase `ODDS` objects on
   disk), not an ambiguous or ambiguously-worded claim.
2. `plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md` (as of 2026-07-25T02:32Z, line ~714-720) instructs:
   `migrate_sports_league_id_casing_2026_07_21.py --apply-prod --confirm-prod-write --index ...` to copy ~139,155 raw
   objects to `league_id=<CANON>/instrument_type=ODDS/data_type=TRADES/` — **UPPER-case `ODDS`/`TRADES`**, the exact
   shape the ruling above says must be UNDONE, not extended.
3. This specific todo is currently gated behind a SEPARATE, unrelated blocker (a `gsutil` credential failure documented
   in the same plan, needing human 2FA reauth) — so it is not executable RIGHT NOW, which is why this hasn't already
   caused prod damage. **This is not a reason to deprioritize the fix** — once the credential issue resolves, this todo
   becomes immediately dispatchable in its current (wrong-direction) form unless fixed first.

## What is NOT yet verified

- Whether `migrate_sports_league_id_casing_2026_07_21.py` (the executor script) has the casing HARDCODED to upper-case
  internally, or whether it's parameterized/configurable — this determines whether the fix is a plan-text edit (repoint
  the invocation + target path description to lower-case) or also requires a code change in the script itself. **Check
  this before editing the plan**, since fixing only the prose while the script still emits upper-case would be a false
  sense of security.
- Whether the ALREADY-SHIPPED K1/K2 migration (260,298 objects, market-tick-data-service@2536b91c/@ad4f1872) has an
  actual revert/undo plan tracked anywhere, or whether that's a separate open gap this finding surfaces as a
  side-effect.

## Todos

- [ ] [CODE] P0. Read
      `market-tick-data-service/scripts/sports/league_id_relocation/migrate_sports_league_id_casing_2026_07_21.py` to
      determine whether upper-case is hardcoded or parameterized. Repo: market-tick-data-service.
- [ ] [DOC] P0. Once `sports_satellite_ao_dispatch_batch2_2026_07_24.md` is not live-locked by another session, fix its
      league_id-casing-migration todo to target LOWER-case (`instrument_type=odds/data_type=trades`) per the FINAL
      2026-07-23 ruling, or — if the script itself can't easily be re-pointed — mark the todo BLOCKED-NEEDS-
      SCRIPT-UPDATE rather than leaving it silently dispatchable in the wrong direction. Repo: unified-trading-pm.
- [ ] [DATA] P1. Confirm whether the already-shipped K1/K2 upper-case migration (260,298 objects) has its own tracked
      revert/undo plan; if not, that's a second, separate gap this finding surfaces. Repo: unified-trading-pm.

## Progress log

- 2026-07-25: Filed by this session as a direct follow-up to the full-corpus `/plan-reconcile` run's sole P0 finding.
  Verified independently (not just trusting the hunter's quote) against both the ruling doc and the satellite-batch2
  doc's live current content. Not fixed inline — target file was live-locked by a concurrent session at discovery time.
