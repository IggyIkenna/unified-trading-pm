---
title: "✅ PARTIAL-RESOLVED 2026-05-09 — 4 HARD RULES codified; retroactive sweeps tracked in session_loose_ends"
created: 2026-05-08
partial_resolved: 2026-05-09
author: ikenna-tab1-main
status: partial-resolved
source:
  - plans/active/issues/paper_trade_smoke_blocker_get_strategy_factories_2026_05_08.md (RESOLVED 2026-05-08)
  - cursor-configs/CLAUDE.md § "Citadel-Grade Planning Standards"
  - cursor-configs/CLAUDE.md § "VM launcher script SSOT (codified 2026-05-07)"
  - cursor-configs/CLAUDE.md § "No fire-and-forget VM launches"
  - cursor-configs/CLAUDE.md § "Findings Triage Discipline"
  - master_to_live_defi_2026_05_23.md Group F item 17 (paper-trade smoke gating step)
locked_by: live-defi-rollout
locked_since: 2026-05-08
execution:
  owner: Tab 5 (governance) — meta doc
  cadence: one-shot
  verifier: session_loose_ends_2026_05_08.md items 3-7 all flip to DONE
  last_executed:
    "2026-05-08 (HARD RULES codified PM@1d74f617; retroactive sweeps tracked in session_loose_ends_2026_05_08.md items
    3-7)"
---

## ✅ PARTIAL-RESOLUTION 2026-05-09

Per cluster 9 retry audit 2026-05-09: 4 HARD RULES codified in CLAUDE.md (verified):

- Citadel-Grade Planning § 6 extension (Downstream Consumer Updates includes peripheral scripts)
- Runbook Execution-Owner SSOT
- Peripheral Script Directories Under Primary-Consumer QG
- Master Plan Continuous-Verification Column

The runbook this issue surfaced (paper-trade smoke harness) has been resolved 2026-05-08 (e2e-testing@dfb7abe6).
Retroactive sweeps (per-service QG wiring of e2e-testing/scripts/ peripheral dirs + master plan continuous-verification
column population) tracked in `session_loose_ends_2026_05_08.md` items 3-7.

This issue is **conceptually resolved at the codification layer**; the retroactive-sweep work flows through the named
successor doc. Issue ready for archive once session_loose_ends items 3-7 flip to DONE.

---

# Original issue (codified — kept for archaeology)

# 🚨 4 governance gaps — runbook silent-rot

> **Severity**: P0 — let a 7-day silent breakage of the paper-trade smoke harness go undetected. Same shape will recur
> for any operator-runnable runbook / smoke / harness without continuous execution + downstream-consumer pre-audit.
> **Blast radius**: any "operator runs this when needed" path across the workspace (smokes, demo runs, rehearsal
> procedures, alerting drills, paper-trade harnesses, manifest-rescan scripts). **Suggested owner**: Tab 5 (governance)
> in tomorrow's split + master plan refresh.

## What I found (the rot pattern)

5-step chain that produced the 2026-05-01 → 2026-05-08 silent breakage of `e2e-testing/scripts/defi/run-paper.sh`:

1. **Strategy-service refactor** removed `get_strategy_factories` from `batch_utils.py` (V1-RETIRE Phase 2, 2026-05-01).
2. **Downstream consumer** `e2e-testing/scripts/defi/colocated_engine.py:306` was NOT migrated.
3. **No QG / lint / typecheck caught the broken import** — `e2e-testing/scripts/` is outside strategy-service's QG
   scope; basedpyright never inspected it.
4. **No periodic execution caught the runtime ImportError** — nobody ran the harness for 7 days.
5. **Tab 1 shipped a runbook citing the harness** (PM@b1bd92e6) without verifying it actually worked.

The rot was caught only when Tab 1 forced an execution attempt under "do everything" direction. Without that, the
harness would have silently rotted until the operator panicked at ~May-22 trying to verify Group F item 17.

## Why CLAUDE.md doesn't prevent this today

| Rule                                            | What it covers                           | What it misses                                                                                                                                                                                                                                                                                       |
| ----------------------------------------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Citadel-Grade § 6 "Downstream Consumer Updates" | UAC/UTL/UCI/UEI shared-library refactors | **Service-internal refactors that break non-service consumers** (`e2e-testing/`, `*_service/scripts/`, `deployment-service/scripts/`, sample notebooks). Strategy-service's V1-RETIRE Phase 2 removed a public symbol but the rule didn't fire because strategy-service is a service, not a library. |
| "No fire-and-forget VM launches"                | VM event verification                    | **Scripts/runbooks operators run manually outside VMs** — the harness rot was not a VM rot, it was a script rot.                                                                                                                                                                                     |
| Findings Triage Discipline                      | Case-driven (file when found)            | **Not periodic-check-driven** — silent rot stays silent until someone happens to run the thing.                                                                                                                                                                                                      |
| "Two teammates × multiple parallel agents"      | Non-edit rule                            | Doesn't enforce verify-downstream when the agent doing a refactor breaks downstream non-service consumers.                                                                                                                                                                                           |
| Workspace QG                                    | unit tests + lint + typecheck per repo   | **`e2e-testing/scripts/` is not under any repo's QG.** basedpyright would have caught the ImportError instantly if it ran.                                                                                                                                                                           |
| Master plan Group F success criteria            | May-23 cutover checkpoint                | **Not a continuous heartbeat.** Silent rot between now + then is invisible.                                                                                                                                                                                                                          |

## The 4 specific gaps (in priority order)

### Gap 1 — Pre-Audit § 6 doesn't extend to non-library refactors

**Fix shape**: extend Citadel-Grade § 6 to "ANY refactor that removes/renames a publicly-imported symbol — service or
library — must pre-audit ALL workspace consumers including `e2e-testing/`, `*_service/scripts/`,
`deployment-service/scripts/`, sample notebooks, ad-hoc one-off scripts." Codify in CLAUDE.md + add a QG step that walks
AST of removed symbols + greps the workspace for stale imports.

**Implementation hint**: workspace-wide grep on every PR that removes a public function/class symbol. Existing precedent
for symbol-walking: workspace QG STEP 5.64 already AST-walks `record_captured(` callsites.

### Gap 2 — No runbook-execution-owner SSOT

**Fix shape**: every runbook in `plans/active/issues/` (or as a master-plan success criterion) MUST declare:

- **Periodic execution path**: cron VM, daily Tab assignment, or QG-wired smoke.
- **Owner**: explicit named Tab or service for the periodic execution.
- **Done definition** that is verifiable from event-stream alone (per CLAUDE.md "No fire-and-forget VM launches"
  extended to scripts).

Runbooks without an execution path are review-blocking. Codify in `plans/PLAN_FORMAT.md` + add a QG step that walks
issue docs / master plan body + asserts every runbook reference has an `Owner: ` + `Cadence: ` line.

### Gap 3 — `e2e-testing/` and other peripheral script dirs aren't under any QG

**Fix shape**: add `e2e-testing/scripts/` (and similar peripheral script dirs that import from services) to either:

- (a) The primary consumer service's QG (e.g. `colocated_engine.py` → strategy-service QG since it imports from
  `strategy_service.cli.handlers.batch_utils`), OR
- (b) A new `e2e-testing` repo QG that runs basedpyright + ruff + smoke-execute the harness.

Probably (a) — fewer moving parts; the consumer's QG already runs basedpyright + has access to the imports.

**Implementation hint**: extend `strategy-service/scripts/quality-gates.sh` to include
`basedpyright ../e2e-testing/scripts/defi/colocated_engine.py` — the import chain will surface immediately.

### Gap 4 — Master plan success criteria are checkpointed at cutover, not continuously

**Fix shape**: master plan Group F + G items each get a "continuous verification" column listing what cron / wakeup /
Tab runs to keep this green between checkpoints. Without it, a 7-day rot like 2026-05-01 → 2026-05-08 is invisible.

**Implementation hint**: add a row to the master plan readiness checklist per item:

| Item                         | Cutover Success Criterion | Continuous Verification  |
| ---------------------------- | ------------------------- | ------------------------ |
| F.17 paper-trade smoke green | green at May-23           | daily cron + Tab 5 sweep |
| F.18 batch-vs-live recon     | green at May-23           | daily cron               |
| ...                          |                           |                          |

## Why it matters

- **Master plan May-23 cutover** depends on 6 Group F + 1 Group G runbook-style success criteria being green. If ANY of
  them rot 7 days before the deadline, we discover it 7 days too late.
- **The rot pattern is generalisable** — anywhere a script imports from a service + the service refactors + the script
  isn't under QG + nobody runs the script = silent breakage. There are ~30 launchers under `e2e-testing/scripts/`
  - features-sports-service + intra-repo deployment-service that fit this pattern (per CLAUDE.md "Migration in flight
    2026-05-07").
- **The fix cost is low** — extending Pre-Audit § 6 + adding a periodic-execution rule + adding e2e-testing/ to
  strategy-service QG are each ~1-2 AI-day items. Together they prevent the entire rot class.

## Recommended decision

1. **Operator immediate**: file this issue doc into Tab 5 (governance) for tomorrow's `work_split_2026_05_09_ikenna.md`
   as a P0 item. ~3 AI-days total to ship all 4 fixes.
2. **Tab 5 owner**: codify the 4 fixes in CLAUDE.md + plans/PLAN_FORMAT.md + master plan template. Lift e2e-testing/
   into strategy-service QG. Add periodic-execution rule.
3. **Cross-reference**: link this doc from the master plan's Group F section header so anyone reading the readiness
   checklist sees the governance dependency.

## Companion: VM-launcher consolidation gap

While auditing for this finding, Tab 1 confirmed CLAUDE.md "VM launcher script SSOT" rule's pending migration is still
in flight: ~30 ad-hoc launchers under `e2e-testing/scripts/` + `features-sports-service/scripts/` + intra-repo
`deployment-service/scripts/deploy-dashboard-gce-vm.sh`. Filed as a separate issue doc + migration plan
(`vm_launcher_consolidation_audit_2026_05_08.md`).
