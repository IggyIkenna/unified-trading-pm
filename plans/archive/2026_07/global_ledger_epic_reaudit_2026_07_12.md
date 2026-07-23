---
doc_type: plan
title: Global Ledger + PnL Attribution epic — full re-audit vs repo reality
summary: >-
  Operator-ordered (plan-reconciliation finding 366, 2026-07-12) full re-audit of
  plans/epics/global_ledger_pnl_attribution_master.md — the epic is ~7 weeks stale (last_updated 2026-05-23) and this
  session's spot-checks already found evidence that Phase 7 (InstructionLedger writer) and Phase 8 (PassiveLedger
  synthesiser), both claimed "0/27 DEFERRED-POST-CUTOVER," have partially-shipped, unacknowledged code in
  execution-service and strategy-service. Every claim in the epic gets enumerated, verified against repo code + shipped
  SHAs, given a per-phase verdict, and the epic synced with evidence.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    unified-trading-pm,
    execution-service,
    strategy-service,
    unified-api-contracts,
    greeks-service,
    instruments-service,
    alerting-service,
    client-reporting-api,
  ]
scope: [engineer, admin]
tags: [audit, epic-reaudit, global-ledger, pnl-attribution, plan-reconciliation, evidence-verification]
related:
  [
    ../epics/global_ledger_pnl_attribution_master.md,
    issues/plan_reconciliation_operator_decisions_2026_07_11.md,
    ../archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md,
    ../archive/2026_05/global_ledger_pnl_attribution_migration_2026_06_01.md,
  ]
created: "2026-07-12"
last_updated: 2026-07-13
parent_epic: global_ledger_pnl_attribution_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: research
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3.6
assigned_role: review
drift_direction: correct-codex
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "operator ruling 2026-07-12, plan-reconciliation Q&A (finding 366) — see
  plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md §A2"
---

> **Why this plan exists.** `plans/epics/global_ledger_pnl_attribution_master.md` frontmatter reads
> `last_updated: 2026-05-23` — ~7 weeks stale as of this plan's creation (2026-07-12). The epic's own body claims Phase
> 7 (execution-service InstructionLedger writer refactor) and Phase 8 (strategy-service PassiveLedger synthesiser) are
> both "DEFERRED-POST-CUTOVER" with the archived migration plan at literal 0/27 items implemented. A same-session grep
> already found `PassiveLedger` referenced in `strategy-service/strategy_service/engine/backtest/paper_run_passive.py`
>
> - `paper_run_attribution.py`, and `build_attribution_rows`/`InstructionLedger`-adjacent code live in
>   `execution-service/execution_service/pnl_attribution/rows.py` with a passing unit test
>   (`tests/unit/pnl_attribution/test_build_attribution_rows.py`). That is exactly the "Phase-8 partially shipped
>   unacknowledged" pattern the operator flagged — this plan runs the full re-audit, not just that one spot-check.

## Codex SSOTs

Read these before verifying claims — they are the target-state the epic's claims are supposed to match:

| Doc                                                                   | Owns                                                                                                                                                                                                                                                                                                                                                 |
| --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/codex/04-architecture/global-ledger-architecture.md`                | 4-SSOT-+-4-derived ledger model; universal PnL recipe; per-service writer/reader gap status                                                                                                                                                                                                                                                          |
| `/codex/02-data/ledger-event-taxonomy.md`                             | `EventOrigin`/`EventType`(39, was: 37 — corrected 2026-07-14, doc-reconciliation finding 71: AST-verified HEAD count per this plan's own todo/verdict-table row 2 above, `unified-api-contracts@a2751f36`; the codex doc itself still says 37, CODEX-GATED, not edited here)/`AssetClass`(17)/`Direction`/`OptionRight` enum SSOT + invariant tables |
| `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` | Carry-as-theta-family attribution framing; ledger→factor decomposition                                                                                                                                                                                                                                                                               |
| `/codex/04-architecture/client-funds-isolation.md`                    | Cross-client transfer HARD RULE — `client_id == counterparty_client_id` on every transfer/bridge row                                                                                                                                                                                                                                                 |
| `plans/PLAN_FORMAT.md`, `plans/active/task_template.md`               | Plan/epic authoring format this re-audit's output must conform to                                                                                                                                                                                                                                                                                    |

## Pre-audit manifest — claims to verify (seed; todo 1 finalizes)

| #   | Claim (epic location)                                                                                | Spot-check status this session                                                                                                                                   |
| --- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Frontmatter `last_updated: 2026-05-23`, `status: active`, `locked_by: live-defi-rollout`             | Stale by construction — 7 weeks with zero updates while dependent code shipped                                                                                   |
| 2   | "UAC schemas SHIPPED — `LedgerRow` + 5 enums + `CrossClientTransferForbiddenError` validator landed" | CONFIRMED present: `unified_api_contracts/canonical/crosscutting/ledger/_ledger_row.py` exists — verify enum counts + validator behavior, not just file presence |
| 3   | "Discovery plan 36/38 BACKED + 2/38 PARTIAL... operator [ack] pending"                               | Unverified — check for any ack since 2026-05-23                                                                                                                  |
| 4   | "Migration plan 0/27 — gated on operator [ack]... target window post-cutover 2026-06-01"             | CONTRADICTED by spot-check: `PassiveLedger` (Phase 8) + attribution-row code (Phase 7) already exist in strategy-service/execution-service                       |
| 5   | P2 item: greeks cross-check "shipped at `greeks-service@b0b702d`"                                    | Unverified — confirm SHA + that the Pub/Sub sub + IS API integration + write-back are still live at HEAD                                                         |
| 6   | "Anticipated net-new VM prefixes... ABSORB-into-existing for all... No new prefixes added"           | Unverified against live `VM_PREFIX_TO_BUCKET` registry                                                                                                           |
| 7   | 4 Codex SSOT docs cited as owning docs                                                               | Unverified whether these docs exist / reflect current ledger state (epic flags them "DEFERRED-POST-CUTOVER")                                                     |

## Todos

- [x] [AUDIT] P0. **Finalize the claim manifest** — walked `plans/epics/global_ledger_pnl_attribution_master.md` line by
      line (frontmatter + body: status line, "Assigned active plans," "Archived plans," "VM assignment notes,"
      "Continuous-verification path"). Full claim-by-claim checklist is the Per-Phase Verdict Table in the Progress Log
      below (10 distinct claims + 2 epic-internal-consistency findings).
- [x] [AUDIT] P0. **Verify claim #2 (UAC schema-shipped)** — read
      `unified-api-contracts/unified_api_contracts/canonical/crosscutting/ledger/` in full. Verdict: **PARTIAL/STALE** —
      `LedgerRow` + `CrossClientTransferForbiddenError` BACKED as described, but `EventType` is now **39** values at
      HEAD (`unified-api-contracts@a2751f36`), not 37 (`+2` from margin-traceability PR `dc67ae6f`, additive);
      `AssetClass` still 17. See verdict table row 2.
- [x] [AUDIT] P0. **Verify claim #4 Phase 8 (PassiveLedger)** — read
      `strategy-service/strategy_service/engine/backtest/paper_run_passive.py` +
      `strategy_service/engine/backtest/paper_run_attribution.py` + their tests in full. Verdict: **CONTRADICTED-BY-CODE
      (paper/backtest leg) / PARTIAL overall** — the paper-mode PassiveLedger synthesiser is REAL (constructs canonical
      `event_origin=PASSIVE` `LedgerRow`s, writes via UTL `write_run_passive_ledger`, tested) and shipped via
      `plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md`, NOT the frozen migration plan. The LIVE
      per-event divergence-check listener is genuinely NOT shipped (grepped strategy-service for a live
      on-chain/venue-emission listener; none found). See verdict table row 4b.
- [x] [AUDIT] P0. **Verify claim #4 Phase 7 (InstructionLedger writer)** — read
      `execution-service/execution_service/pnl_attribution/rows.py` + `build_attribution_rows` +
      `tests/unit/pnl_attribution/test_build_attribution_rows.py` in full, plus the actual InstructionLedger write path
      (`unified-trading-library/unified_trading_library/ledger/run_writer.py` +
      `strategy-service/strategy_service/engine/backtest/ledger_emit.py`). Verdict: **CONTRADICTED-BY-CODE** — real
      InstructionLedger/PricingLedger/TransferLedger GCS writers are shipped + wired live (paper leg), plus a real,
      tested `build_attribution_rows` (the derived PnLAttribution view, a related but distinct artifact from the
      InstructionLedger SSOT writer). All shipped via the Citadel plan, not the frozen migration plan. See verdict table
      row 4a.
- [x] [AUDIT] P0. **Verify claim #3 — operator-[ack] gate status.** Searched `plans/active/_agent_pings.md` (retired +
      emptied 2026-07-04 — history is in git),
      `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md`, the Citadel plan, AND (post-restart
      continuation) the PM git history (`git log --grep`). **VERDICT REVERSED from the initial pass**: the operator ACK
      **EXISTS** — `unified-trading-pm@351a47b61` (2026-05-23 20:42 +0100, "6 operator-ACK'd decisions... Per operator")
      recorded ALL gated decisions in `plans/archive/2026_05/pricing_ledger_carry_rates_mtds_2026_06_01.md` § "Operator
      decisions (ACK'd 2026-05-23)": Phase 3 → Option A event-sourced append-only; Phase 4/6 treasury → separate
      `ledger_type=treasury/` partition (writer fund-administration-service); Phase 5a greeks home → new greeks-service
      repo; + 5b cadence + 5c dividend_yield/rebase_rate. The ack landed the same evening the epic's "pending" status
      line was written and was never synced back — a doc-sync failure, NOT a governance breach. (Also corrected an
      epic-internal numbering error: the epic mixed "Phase 3/4/5" and "Phase 3/5/6" — the archived discovery plan's own
      phase headers confirm 3/5/6 is correct.)
- [x] [AUDIT] P1. **Verify claim #5 (greeks P2 item)** — confirmed `greeks-service@b0b702d` exists (`git cat-file -t` +
      `git merge-base --is-ancestor` against `origin/live-defi-rollout` both pass); read HEAD (`ac4ed0f`) state of
      `mark_update_sub.py` / `pricing_ledger_writer.py` / `mark_update_handler.py`, all wired live in `__main__.py`;
      only touched since by an unrelated typecheck fix (`f41a12d`). Verdict: **BACKED**.
- [x] [AUDIT] P1. **Verify claim #6 (VM prefixes)** — grepped the live `VM_PREFIX_TO_BUCKET` registry
      (`deployment-service/scripts/vm/vm_zombie_watchdog.py`): zero `ledger-reconcile-` / `passive-listener-` entries
      (BACKED, no net-new prefixes); `strategy-paper-` / `strategy-live-` / `client-reporting-cutover-` all present.
      Found + corrected one naming error: registry key is `batch-live-recon-`, not `batch-live-recon-cron-` (that's the
      launcher script's name). Verdict: **BACKED with 1 cosmetic correction**.
- [x] [AUDIT] P1. **Verify claim #7 (4 Codex SSOTs)** — confirmed all 4 exist at HEAD, `status: current`, substantial
      (185-864 lines, not stubs), last git-touched 2026-07-04. Found ONE residual codex-internal staleness:
      `global-ledger-architecture.md`'s own "Current-State Gaps" table still calls `build_attribution_rows()` a "stub" —
      contradicted by the real, tested 140-line implementation found in the Phase-7 check above. Verdict: **docs
      exist/current (CONTRADICTS epic's "DEFERRED-POST-CUTOVER" framing); 1 codex-internal stale sub-claim flagged
      CODEX-GATED** (new todo below, not edited by this audit).
- [x] [AUDIT] P0. **Produce the per-phase verdict table** — embedded in the Progress Log below (10 claim rows + 2
      epic-internal-consistency findings, each with repo@sha or file:line evidence).
- [x] [CODE] P0. **Sync the epic** — edited `plans/epics/global_ledger_pnl_attribution_master.md`: bumped `last_updated`
      2026-05-23→2026-07-12, corrected the summary + status line + Codex-SSOTs section + P2 item + Archived-plans
      Phase-7/8/numbering claims + VM-assignment-notes naming, all with "(was: …)" originals + inline evidence
      citations, and added a new P3 forward-carry todo for the live PassiveLedger listener gap. Evidence:
      `unified-trading-pm` working tree edit (uncommitted at authoring time — orchestrator commits per this plan's
      instructions).
- [x] [CODE] P1. **Un-gate or forward-carry real shipped scope.** Decision: **(b) folded into this epic's existing
      sections directly** — added TWO new `- [ ] [CODE] P3` todos to the epic's P3 section ("Live (non-paper)
      PassiveLedger per-event divergence-check listener", strategy-service; + post-restart discovery "TreasuryLedger
      SSOT partition `ledger_type=treasury/`", fund-administration-service), plus inline "CORRECTED 2026-07-12" credit
      notes on the Phase 7/8 Archived-plans bullets crediting the Citadel plan's shipped scope. No new sibling plan
      spawned (each residual is a single well-scoped component, trackable as an epic-level todo rather than warranting
      its own plan doc).
- [x] [AUDIT] P1. **Escalate any governance-gate breach found in todo 5** — **CLOSED: NO BREACH** (post-restart
      continuation). The initial pass provisionally escalated a suspected breach; deeper verification (PM git-history
      search) found the operator ack landed 2026-05-23 (`pm@351a47b61`) — the gate was properly cleared BEFORE any Phase
      7/8 code shipped (Citadel plan created 2026-06-19). The escalation is WITHDRAWN; what remains is a doc-sync
      finding (the epic + discovery archival banner never recorded the ack), which this audit fixed directly in the
      epic. No operator adjudication required.
- [x] [DOCS] P1. **Post-phase codex-alignment check** — filed the corrective follow-up as a new todo immediately below
      (codex doc `global-ledger-architecture.md`'s stale `build_attribution_rows()` "stub" claim + its
      "DEFERRED-POST-CUTOVER" framing needs a sync pass) — not closing this plan with the gap silently undocumented.
- [x] [DOCS] P2. **NEW (discovered this audit) — codex-alignment follow-up**:
      `/codex/04-architecture/global-ledger-architecture.md` needs a sync pass (operator-gated codex edit, out of this
      plan's authority per the task brief's "No codex edits" instruction): (a) its "Current-State Gaps (Audit
      2026-05-23)" table's `execution-service` row still says `build_attribution_rows() stub` — false at HEAD, it's a
      real 140-line tested implementation; (b) the doc doesn't yet document the Citadel-plan-shipped
      InstructionLedger/PricingLedger/TransferLedger/PassiveLedger(paper) writers living in
      `unified-trading-library/unified_trading_library/ledger/` + `strategy-service` `engine/backtest/`; (c) the "VM
      Prefix Additions" section's `batch-live-recon-cron-` naming should match the real registry key
      `batch-live-recon-`. **CODEX-GATED, actioned 2026-07-13** — operator authorization granted 2026-07-13 (chat ruling
      "can we do that" approving this CODEX-GATED leftover). Edited
      `/codex/04-architecture/global-ledger-architecture.md`: bumped `last_reviewed` 2026-05-22→2026-07-13; added a
      dated `[DELTA 2026-07-13]` banner citing this plan + the operator authorization; corrected (a) the
      Current-State-Gaps `execution-service` row with a `(was: …)` annotation + evidence
      (`execution-service@a4145838`→`49f42f77`, `tests/unit/pnl_attribution/test_build_attribution_rows.py`); added (b)
      a new "Shipped Writers (Citadel Plan, Paper Leg)" section documenting the
      InstructionLedger/PricingLedger/TransferLedger writers (`unified-trading-library@41d50461`) + PassiveLedger
      paper-leg synthesiser, with the live-leg gap called out as still unshipped; corrected (c) the VM Prefix Additions
      row with a `(was: batch-live-recon-cron-)` annotation citing the live registry key `batch-live-recon-`
      (`deployment-service/scripts/vm/vm_zombie_watchdog.py:632`). All shas/paths re-verified read-only immediately
      before writing. Evidence: `unified-trading-pm` working tree edit (this session ships it).
- [x] [DOCS] P0. **Wire findings into the reconciliation issue doc** — appended a dated Progress Log entry to
      `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 citing finding 366 and this plan's
      verdict table.

## Progress Log

- **2026-07-13** — **Status-flip note**: the final open todo (CODEX-GATED `global-ledger-architecture.md` sync) was
  actioned under explicit operator authorization (chat ruling 2026-07-13, "can we do that," approving this CODEX-GATED
  leftover) and flipped `[x]`. All todos in this plan now confirmed `[x]` with cited evidence. Flipped `status: active`
  → `complete`.
- **2026-07-12** — Plan authored per operator ruling 2026-07-12 (finding 366,
  `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2: "FULL RE-AUDIT of global_ledger
  epic... authored as HUMAN plan (assigned_vm: NA)"). Seed claim table populated from this session's read of the epic
  - a same-session grep confirming `PassiveLedger` in strategy-service and `build_attribution_rows` in execution-service
    — both areas the epic claims are 0% shipped. No verification or epic edits performed yet; that is this plan's scope.

- **2026-07-12 (full re-audit executed)** — All todos completed except the newly-filed CODEX-GATED follow-up (left open
  by design — operator-gated). Method: grep-then-READ every claim, verify every cited sha via read-only
  `git cat-file`/`git log`/`git merge-base --is-ancestor` in the named repos, live-grep infra registries. **Per-Phase
  Verdict Table** (primary deliverable):

  | #   | Claim (epic location)                                                                                                                       | Verdict                                                                | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
  | --- | ------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | 1   | Frontmatter `last_updated: 2026-05-23`, `assigned_vm: vm-trading-core`                                                                      | STALE                                                                  | 7 weeks stale; `vm-trading-core` references a per-epic VM model superseded 2026-06-27 (already partially corrected in-body 2026-07-12, frontmatter date was not). FIXED: `last_updated` bumped to 2026-07-12.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
  | 2   | "UAC LedgerRow + EventType(37)/AssetClass(17) + CrossClientTransferForbiddenError SHIPPED"                                                  | PARTIAL/STALE                                                          | `LedgerRow` + validator BACKED (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/ledger/_ledger_row.py:399-403` matches `/codex/04-architecture/client-funds-isolation.md` HARD RULE). `EventType` = **39** at HEAD `a2751f36` (AST-counted), not 37 (`+2` via `dc67ae6f` margin-traceability, additive). `AssetClass` = 17, unchanged.                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
  | 3   | "Discovery 36/38 BACKED+2/38 PARTIAL, operator [ack] pending on Phase 3/5/6"                                                                | STALE ("[ack] pending" is FALSE — ack EXISTS) + internal numbering bug | **REVERSED post-restart** (initial pass wrongly concluded "no ack found"): the ack EXISTS at `unified-trading-pm@351a47b61` (2026-05-23 20:42 +0100) — all 6 gated decisions recorded in `plans/archive/2026_05/pricing_ledger_carry_rates_mtds_2026_06_01.md` § "Operator decisions (ACK'd 2026-05-23)". The epic + discovery archival banner were never synced with it (pure doc-sync failure). Epic also internally said both "Phase 3/4/5" (2 places) and "Phase 3/5/6" (2 places) — archived discovery plan's own headers confirm 3/5/6 is correct; "3/4/5" occurrences fixed.                                                                                                                                                                                                                         |
  | 4a  | "Phase 7 (execution-service InstructionLedger writer) DEFERRED-POST-CUTOVER, gate Phase 3/4/5"                                              | CONTRADICTED-BY-CODE                                                   | Real, tested, shipped: `unified-trading-library@41d50461` `ledger/run_writer.py` (`write_run_ledger`/`write_run_pricing_ledger`/`write_run_transfer_ledger`/`write_run_passive_ledger`) wired live via `strategy-service/strategy_service/engine/backtest/ledger_emit.py::write_paper_run`; plus `execution-service/execution_service/pnl_attribution/rows.py::build_attribution_rows` (`execution-service@a4145838`→`49f42f77`, tested `tests/unit/pnl_attribution/test_build_attribution_rows.py`, 342 lines) — the derived PnLAttribution view, distinct from but related to the InstructionLedger writer. **Shipped via `plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md`** (`parent_epic: batch_live_symmetry_master`), NOT the frozen migration plan (which correctly stays 0/27). |
  | 4b  | "Phase 8 (strategy-service PassiveLedger synthesiser) DEFERRED-POST-CUTOVER, per-event divergence check"                                    | PARTIAL — paper leg CONTRADICTED-BY-CODE, live leg genuinely missing   | `strategy-service/strategy_service/engine/backtest/paper_run_passive.py::build_paper_run_passive`/`emit_paper_run_passive` build real `event_origin=PASSIVE` `LedgerRow`s (STAKING_REWARD/LENDING_INTEREST/FUNDING_ACCRUAL), write to `ledger_type=passive/{run_id}.jsonl`, tested (`test_paper_run_passive.py`) — shipped via the same Citadel plan. The LIVE per-event divergence-check listener (epic's own VM-notes: "runs inside `StrategySupervisor` per-client subprocess") was NOT found anywhere in strategy-service — genuinely unshipped, forward-carried as a new epic P3 todo.                                                                                                                                                                                                                 |
  | 5   | "greeks-service@b0b702d shipped: Pub/Sub sub + IS API + PricingLedger write-back"                                                           | BACKED                                                                 | sha exists (`git cat-file -t`), is ancestor of `origin/live-defi-rollout` (`git merge-base --is-ancestor`); commit msg matches exactly. At HEAD `ac4ed0f`, `mark_update_sub.py`/`pricing_ledger_writer.py`/`mark_update_handler.py` still wired live in `__main__.py`; only touched since by unrelated typecheck fix `f41a12d` — no regression.                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
  | 6   | "No new VM prefixes; ledger-reconcile-/passive-listener- ABSORB into batch-live-recon-cron-/strategy-live-\*"                               | BACKED, 1 naming correction                                            | Live grep of `deployment-service/scripts/vm/vm_zombie_watchdog.py`: zero `ledger-reconcile-`/`passive-listener-` entries. Real registry key is **`batch-live-recon-`**, not `batch-live-recon-cron-` (that's the launcher script's filename). `strategy-paper-`/`strategy-live-`/`client-reporting-cutover-` all confirmed registered.                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
  | 7   | "4 Codex SSOT docs DEFERRED-POST-CUTOVER"                                                                                                   | CONTRADICTED-BY-CODE (docs exist), 1 stale sub-claim found             | All 4 exist at HEAD, `status: current`, 185-864 lines (non-stub), last git-touched 2026-07-04. `global-ledger-architecture.md`'s own "Current-State Gaps" table still calls `build_attribution_rows()` a "stub" — itself stale per row 4a's evidence. Flagged CODEX-GATED (new plan todo, not edited — out of this plan's authority).                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
  | 8   | Cross-epic handshake table (`execution_master`: "InstructionLedger + PassiveLedger writers (`attribution_builder.build_attribution_rows`)") | BACKED (module path nuance)                                            | The function name/purpose match exactly what shipped; the module is `execution_service/pnl_attribution/rows.py`, not literally a file named `attribution_builder.py` — a naming shorthand, not a false claim.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
  | 9   | VM-assignment-notes tier/epic-count self-correction (finding 10003)                                                                         | BACKED (already fixed)                                                 | Verified current; no further action needed.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
  | 10  | Continuous-verification path table (5 rows, post-migration)                                                                                 | UNVERIFIED/aspirational, out of required scope                         | The Citadel plan's `batch-live-reconciliation-service@7a84db8c` `reconcile_day` (9 tests) is a real, shipped determinism-PROOF mechanism (paper≡batch), which substantially realizes the SPIRIT of rows 1/4 but proves a different pair (paper vs batch-rerun, not InstructionLedger vs venue execution reports). Not row-by-row verified; not adjudicated.                                                                                                                                                                                                                                                                                                                                                                                                                                                 |

  **GOVERNANCE-GATE FINDING — RESOLVED: NO BREACH (initial suspicion overturned by deeper verification post-restart)**:
  the discovery plan required operator [ack] on 3 decision axes — Phase 3 (late-arriving-data handling), Phase 5
  (greeks-computation home), Phase 6 (TreasuryLedger own-table-vs-filter-view) — before migration implementation. The
  initial audit pass found no ack in `_agent_pings.md` (retired + emptied 2026-07-04), the Citadel plan, or the
  2026-07-11 issue doc, and provisionally escalated a suspected breach. The post-restart continuation searched the PM
  git history (`git log --grep`) and FOUND the ack: **`unified-trading-pm@351a47b61`** (2026-05-23 20:42 +0100, commit
  message "Per operator... 6 operator-ACK'd decisions"), which wrote the section "Operator decisions (ACK'd 2026-05-23 —
  folded from archived discovery plan Phase 11)" into the then-active MTDS carry-rates plan (now
  `plans/archive/2026_05/pricing_ledger_carry_rates_mtds_2026_06_01.md`): Phase 3 → **Option A event-sourced
  append-only** (+ pre-join view at API boundary, closed enrichment set); Phase 4/6 → **separate partition
  `ledger_type=treasury/client_id={cid}/`, writer = fund-administration-service**; Phase 5a greeks home → **new
  `greeks-service/` repo**; Phase 5b cadence per-asset_group; Phase 5c dividend_yield + rebase_rate BOTH-paths. The gate
  was therefore properly cleared ~4 weeks BEFORE the Citadel plan (created 2026-06-19) shipped any Phase 7/8 code, and
  the shipped code is CONSISTENT with the acked decisions (append-only enrichment convention in the `LedgerRow`
  docstring; greeks in greeks-service; treasury as its own partition). **The real finding is doc-sync, not governance**:
  the ack was recorded ONLY in the MTDS plan — the epic, the discovery plan's archival banner, and the migration plan's
  deferral bullets all kept saying "[ack] pending" for 7 weeks (and the initial pass of THIS audit was itself misled by
  that, wrongly concluding "no ack found" until the git-history search — a live demonstration of why the doc-sync
  failure matters). Epic now corrected with the ack citation. Two genuine residual implementation gaps forward-carried
  as epic P3 todos: (1) the live PassiveLedger per-event divergence-check listener; (2) the acked
  `ledger_type=treasury/` partition (fund-administration-service writer) — zero code hits for `ledger_type=treasury` at
  HEAD across UTL / strategy-service / execution-service / fund-administration-service / client-reporting-api (the
  shipped `ledger_type=transfer` run tape is a distinct run-scoped construct). Escalation WITHDRAWN — no operator
  adjudication required.

- **2026-07-12 (epic synced)** — `plans/epics/global_ledger_pnl_attribution_master.md` edited in place: frontmatter
  `last_updated` bumped; summary + status line + Codex-SSOTs section + P2 greeks item + Archived-plans Phase 7/8/9 +
  phase-numbering + VM-assignment-notes all corrected with "(was: …)" originals + inline evidence citations; new P3 todo
  added (live PassiveLedger listener, forward-carried). Decision executed for todo 11: folded residual scope into the
  epic directly (option b) rather than spawning a new plan — the one remaining real gap (live listener) is small enough
  to track as a single epic todo. `unified-trading-pm` working tree — commit is the orchestrator's per this plan's
  operating instructions (no git commands run by this agent).

- **2026-07-12 (post-restart continuation — governance verdict REVERSED, residual verifications closed)** — a session
  restart interrupted the run; on resume, all prior file edits were verified intact on disk, then the four verification
  gaps the initial pass had left were closed: (1) `unified-trading-library@41d50461` git-verified (exists,
  "feat(ledger): Phase 3 — materialize InstructionLedger + PositionLedger from fills", ancestor of
  `origin/live-defi-rollout`); (2) both test suites READ, confirmed real + substantive (9 tests in
  `test_paper_run_passive.py` incl. funds-isolation + honest-zero + UTL-writer wiring; 15+ tests in
  `test_build_attribution_rows.py` incl. signed-slippage semantics both sides); (3) live-path grep-then-READ
  (`client_worker.py` / `colocated_engine.py` / `supervisor/`) — zero passive-accrual synthesis in the live path,
  live-listener-absent conclusion CONFIRMED; (4) the ack search extended to PM git history — **found `pm@351a47b61`
  (2026-05-23), the operator ACK of all Phase 3/5/6 gated decisions**, REVERSING the initial "no ack found" verdict:
  **no governance breach — escalation withdrawn** (see the corrected GOVERNANCE-GATE paragraph above). New discovery
  from the ack record: the acked `ledger_type=treasury/` partition (fund-administration-service writer) is itself still
  unimplemented at HEAD — added as a second forward-carried P3 todo in the epic. Epic re-corrected accordingly (ack
  citations replace the escalation framing in the correction callout, the Archived-plans Phase 3/5/6 bullets, both
  discovery status lines, and the frontmatter summary); issue-doc entry updated to match. NOTE for the record:
  mid-session the epic + this plan were re-wrapped by prettier and the checkout was ff-advanced
  (`234445078`→`94ae1f24b`) by concurrent workspace activity; content re-verified intact both times.
