---
doc_type: issue
title: "Plan-reconciler findings — tradfi tranche 2026-08-07"
created: 2026-08-07
author: plan_reconciler
source: agt-ec6642
locked_by: none
asset_group: tradfi
status: open
nature: issue
tags: [plan_reconciler, tradfi, reconciliation, auto-generated]
parent_epic: plan_hygiene_master
summary:
  "Automated plan_reconciler run for the tradfi topic tranche — fan-out DETECT + adversarial VERIFY. 61 docs in scope
  (27 grace, 34 non-grace)."
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
related: []
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-07
resolved_by: ""
---

## Flips verified

Missed-flip hunter completed (34/34 non-grace docs read, full corpus). **No P0/P1 missed flips.** Every P0/P1 open
checkbox is genuinely open: operator-gated (`[OPERATOR-REVIEW]` retire-phase `--apply`), KEEP-NA'd, machine-gated
(`gate_on_depends: true`), or re-verified with restated real-remaining-gap text.

### P2 candidates — work demonstrably shipped, checkboxes never flipped

1. **`tradfi_manifest_content_recovery_completion_2026_07_24.md` line 505 — P2.** Todo (code-quoted): "The true
   legacy-content population (FUTURE/OPTION per-contract chain-bundle content) still needs its own rewrite pass…"
   **Evidence it's done**: the follow-up shipped as `scripts/rewrite_tradfi_chain_bundle_content_id_2026_07_25.py`
   (mtds@a23dd8bd, "SHIPPED+MEASURED 2026-07-25"); `--apply` at scale launched 2026-07-27 (8 SPOT VMs, run-id
   20260727-041704). **The plan's own `[VERIFY] P0 GATE` todo (lines 238-241) is flipped `[x]`**: "GATE CLOSED
   2026-07-27… assert_tradfi_derivative_ids_canonical over the live manifest's chain-bundle scope: checked=961
   canonical=961 violations=0". The checkbox at 505 never flipped. **Note**: this line is inside a code-quoted span
   (`` `- [ ] [DATA] P1. …` ``) — not a real mechanical checkbox, but the documented state is stale and misleading.

2. **Same doc, line 681 — P2.** Todo (code-quoted): "Finish the CME monolith investigation: fix the pip/venv bootstrap…
   reconcile the 30-vs-107 count discrepancy, inspect real content structure, THEN design the migration tool. Clean up
   the investigation VM when done." **Evidence**: the immediately following section documents every sub-step complete
   (bootstrap fixed via `apt-get update`; 30-vs-107 thoroughly investigated with 30 accepted as ground truth; content
   inspected; VM deleted); the migration-tool todo it gates (line 731) is flipped `[x]`: "TOOL DONE 2026-07-26
   (mtds@02284f8e)". Checkbox at 681 never flipped. Also code-quoted.

3. **Same doc, line 843 — P3 (cosmetic).** QG-sentinel diagnostic ("Diagnose why unified-api-contracts' full
   quality-gates.sh run… printed ALL QUALITY GATES PASSED but never wrote .qg_last_passed_sha"). The doc's own next
   section ("2026-07-22 continuation") states: "Root cause of the QG-sentinel friction above was NOT purely contention —
   found and fixed a second, real bug. Shipped: uac@68c4c371d". Checkbox never flipped. Also code-quoted.

### P3 candidates (cosmetic)

4. **`backfill_smoke_write_path_canonical_audit_2026_07_20.md` lines 284-286 — P3.** `[DOCS] P2` — correct three in-repo
   comments asserting the IS live writer emits the hive layout. **Evidence**: all three sites corrected —
   `instrument_availability_paths.py:19` and `repair_tradfi_instrument_type_counts_2026_07_17.py:29` each carry an
   explicit "CORRECTION (2026-07-30, per …)" annotation, and `DEFI_INSTRUMENTS.md` no longer contains any hive-layout
   assertion (0 grep hits). Checkbox never flipped.

5. **`tradfi_master.md` line 478 — P3 (context-dependent).** "TradFi 5,212 legacy-blank apply-flips run…" — work
   confirmed complete in its archived home `plans/archive/2026_06/tradfi_cme_event_contract_backfill_2026_06_20.md`
   (`[x]`: "RECONCILER_COMPLETED 77,766 rows upgraded", status: complete). **Caveat**: these markers sit in sections
   explicitly SUPERSEDED 2026-06-20 ("Do NOT pick work directly from the blocks below") — archaeology-only leftovers,
   not live flips. The work is not lost, but the inline checkboxes were never updated.

### Checked and dropped

- `candle_feature_canonical_path_divergence_2026_07_20.md` todo 9 — carries explicit 2026-08-03 annotation: gate cleared
  but deliverable (corpus-wide count of `pipeline_mode`-less candle objects) never independently produced; deliberately
  kept open.
- `estate_orphan_assessment_2026_07_21.md` todo 7 — already `[x]` (retagged resolved-by-reference 2026-07-29).
- `adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md` [DECISION] P2 — KEEP-NA'd 2026-07-30;
  pilot-trace precondition not landed, decision genuinely unmade.
- `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` line-85 tradfi rollup — self-corrected 2026-07-26; remaining
  gates (billable-venue guard, KRX calendar, `available_to`, depth oracle, trigger-PAUSED check) genuinely open.
- `tradfi_phase_d_terminal_gate_2026_07_24.md` P3 test-add todo (line 409) — gate
  (`mtds_deployment_env_race_survives_single_worker_2026_07_23.md`) confirmed still `status: open`.
- All finalize plans (docs 28, 30, 31, 32) — `[REVIEW]`/`[DOC]` todos with genuinely ungated prerequisites.

**Action taken on P2/P3**: none — all 5 candidates are code-quoted documentation spans (`` `- [ ] …` ``) or in
SUPERSEDED epic sections, not real mechanical checkboxes. No mechanical flip possible; the real tracking gates are
already `[x]` elsewhere in the same docs. These are documentation-artifact staleness, not missed work.

## Contradictions

(Pending — contradiction hunter still running)

## Doc-drift

(Pending — contradiction hunter covers this dimension)

## Hygiene fixes

1. **Zero-checkbox doc → canonical todos** (`mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md`):
   Converted 3 prose follow-up items into canonical `- [ ] [INFRA] P1.` todos (strace/py-spy reproduction, systemd
   cgroup reaper check, pkill-guard host-wide install). Commit: `bacb5ed66`.

## Filed

## Archive candidates (operator review)

4 fully-done docs identified (0 open todos, all `[x]`):

| Doc                                                      | Open | Done | Locked?                   | Cross-refs | Verdict                                                                                    |
| -------------------------------------------------------- | ---- | ---- | ------------------------- | ---------- | ------------------------------------------------------------------------------------------ |
| `instruments_satellite_ao_dispatch_batch1_2026_07_27.md` | 0    | 5    | No                        | 4          | **Deferred** — 4 cross-refs in other tranches; sharded run can't verify all referrers safe |
| `autonomous_session_operator_decisions_2026_07_25.md`    | 0    | 2    | No                        | 42         | **Deferred** — 42 cross-references; too risky in a sharded run                             |
| `tradfi_backfill_oom_remediation_2026_06_24.md`          | 0    | 12   | YES (`live-defi-rollout`) | 8          | **BLOCKED** — locked plan, never auto-archive                                              |
| `tradfi_canonical_path_migration_design_2026_07_19.md`   | 0    | 1    | YES (`live-defi-rollout`) | 9          | **BLOCKED** — locked plan, never auto-archive                                              |

## Refuted (dropped by verify)

## Coverage (hunters / batches / docs)

- Tranche: tradfi
- Docs in scope: 61 (20 active plans + 37 issues + 1 epic + 3 normative refs)
- Grace (read-only): 27
- Non-grace (editable): 34
- Normative refs: PLAN_FORMAT.md, task_template.md, INDEX.md, ACTIVE_INDEX.md
- Hunters dispatched: 2
  - **Missed-flip hunter** ✅ complete — 34/34 docs read, 0 P0/P1, 2 P2 + 3 P3 code-quoted documentation artifacts
  - **Contradiction hunter** — still running
- Direct scan: 4 archive candidates checked, 1 zero-checkbox converted

## Deferred work after 2026-08-07

| Item                                                                                         | State / why deferred                                                                                                                                                                             | Blocked on                  |
| -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------- |
| Contradiction hunter results                                                                 | Background agent dispatched but not yet returned. Findings, if any, should be folded into this doc or the next reconciler run.                                                                   | Background agent completion |
| Archive: `instruments_satellite_ao_dispatch_batch1_2026_07_27.md` (0 open, 5 done, unlocked) | Deferred — 4 cross-refs in other tranches (INDEX.md, defi parked, batch1 false-completion claim, honest-coverage). Needs an `all`-tranche run or manual verification that referrers won't break. | Cross-tranche verification  |
| Archive: `autonomous_session_operator_decisions_2026_07_25.md` (0 open, 2 done, unlocked)    | Deferred — 42 cross-references. Too risky in a sharded run.                                                                                                                                      | Cross-tranche verification  |
| Archive: `tradfi_backfill_oom_remediation_2026_06_24.md` (0 open, 12 done)                   | BLOCKED — `locked_by: live-defi-rollout`. Operator must unlock before archival.                                                                                                                  | Operator `[unlock-plan]`    |
| Archive: `tradfi_canonical_path_migration_design_2026_07_19.md` (0 open, 1 done)             | BLOCKED — `locked_by: live-defi-rollout`. Operator must unlock before archival.                                                                                                                  | Operator `[unlock-plan]`    |

**Recommended next item**: Await contradiction hunter result; re-run `all`-tranche reconciliation on Saturday (per the
weekly cadence) to handle the 2 deferred cross-tranche archives and catch any cross-tranche contradictions a single
shard structurally cannot see.

## Lessons

- **Sharded run limitation**: With 27/61 docs in the grace window (<12h old), the non-grace corpus was only 34 docs —
  small enough that a direct scan was more efficient than the full 10-agent fan-out.
- **Archive candidates in sharded runs**: The cross-tranche archival caution check (grep other tranches' closeout docs)
  correctly blocked 2 archives that an unscoped run could have handled. The Saturday `all` run is the right place to
  clear these.
- **`locked_by: live-defi-rollout`** blocked 2 more archives. This is the most common lock value in the tradfi tranche —
  the `tradfi_master` epic and several children carry it. Archive-clearing these needs explicit operator action.
- **Missed-flip P2s are code-quoted documentation artifacts**: All 5 hunter-confirmed "missed flips" are inside backtick
  code spans (`` `- [ ] …` ``) or SUPERSEDED epic sections — not real mechanical checkboxes. The real tracking gates are
  already `[x]` elsewhere. This is a recurring pattern: docs that inline-quote their own todo text for narrative flow
  create false-positive "stale checkbox" signals for any mechanical or human scanner. Worth noting for future hunter
  prompt design.
