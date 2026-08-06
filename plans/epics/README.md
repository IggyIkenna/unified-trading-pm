---
plan_type: epic-index
asset_group: [cross-cutting]
owner: ikenna
created: 2026-05-08
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-08
name: epics-readme
---

# Epics — SSOT for the planning-orchestrator layer

> **🟡 STALE-CONTENT BANNER — 2026-07-11** (adversarially-verified reconciliation findings 308/309, see
> [`plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md`](../active/issues/plan_reconciliation_operator_decisions_2026_07_11.md)):
>
> **(a) RESOLVED 2026-07-12.** The "20 epics in 5 tiers" table below was INCOMPLETE — it was missing at least
> [`agent_operating_framework_master.md`](agent_operating_framework_master.md) and
> [`escalation_and_disaster_recovery_master.md`](escalation_and_disaster_recovery_master.md) (the drift noted in
> findings 308/309). The table is now regenerated from `epics/*.md` frontmatter as a true closed registry — see "23
> epics in 6 tiers" below and its regeneration note.
>
> **(b) The epic-owns-VM model is SUPERSEDED.** The `assigned_vm: vm-<id>` epic-frontmatter field (below) and the "VM
> topology (10 VMs serving 20 epics)" section (below) describe a per-epic VM-ownership model that no longer governs
> dispatch. It is superseded by: (i) operator-locked decision **D2** in
> [`agent_operating_framework_master.md:129`](agent_operating_framework_master.md) (2026-06-24) — _"`assigned_vm` is a
> mandatory **per-plan** field; epic-to-VM delegation is DROPPED for matching"_; and (ii) the single-VM,
> role-based-dispatch architecture (2026-06-27; central `planning` VM + role dispatch, no per-epic VMs) per
> `cursor-configs/CLAUDE.md` and `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`. The epic-level
> `assigned_vm`/VM-topology content below is retained for archaeology only — do not dispatch or match against it.

**This file is the SSOT** for what epics are, how they relate to audits + active plans, how they map to VMs, and the
canonical frontmatter schema. Pointers from `CLAUDE.md`, `codex/11-project-management/`, and `plans/PLAN_FORMAT.md` all
land here. Update this file when the workflow evolves; codex docs are pointers, not parallel SSOTs.

## What an epic is

An **epic** is the planning orchestrator for one persistent code surface. Every active plan in `plans/active/` is
assigned to exactly one epic via `parent_epic:` frontmatter. **No orphan active plans** — if you can't name the epic,
the plan doesn't belong in `plans/active/`. Epics are everlasting: they have no deadline; there's always more work as
audits surface gaps.

**The model (SSOT: [`/codex/12-agent-workflow/work-philosophy.md`](/codex/12-agent-workflow/work-philosophy.md)).**
Codex docs are the **target state**, the codebase is the **current state**, and an epic is the **gap** between them. The
gap is **bidirectional**: most plans _advance the code toward codex_, but some _correct a stale codex toward the code_
(codex was written day-one; correct it incrementally, never as an up-front rewrite). A **plan** is one small step that
closes part of the gap — sized so a **single agent of one role completes it start-to-finish** (one
`quality-gates.sh`-green quickmerge unit, ~one PR). Cross-role work decomposes into _dependent_ single-role plans at the
epic level, never one mixed-role plan. **The epic (a tracker) may be big; the dispatched plan (a work-order) must be
small** — conflating the two is what produced 1000-line plans and the quality regression this model corrects.

**Three persistent entities**:

| Entity          | Where                                      | Lifecycle                                                      | Carries                                                                                                               |
| --------------- | ------------------------------------------ | -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Epic**        | `plans/epics/<slug>.md`                    | Everlasting (status: active/paused/cancelled — NEVER complete) | `assigned_vm`, `tier`, `priority`, scope, list of all assigned active plans organised in priority blocks              |
| **Audit**       | `plans/audit/results/<slug>_YYYY_MM_DD.md` | One-shot, timestamped                                          | Findings from a periodic review of an epic; produces gap items that become new active plans                           |
| **Active plan** | `plans/active/<slug>_YYYY_MM_DD.md`        | Cycles (active → complete → archive)                           | `parent_epic`, `estimate_class`, `estimate_baseline_ai_days`, `estimate_calibrated_ai_days`; one shippable workstream |

The continuous loop: audits identify gaps → active plans spawn to close them → epics absorb the new active plans into
their priority blocks → epic VMs continuously work the items → audits run again periodically (Ikenna + Harsh) and the
cycle continues.

## The audit → active plan → epic flow

```
PLANNING VM (Ikenna + Harsh interactive, Opus 4.7 1M context)
   │
   ├── reads human_led_audit_pool issue doc
   ├── picks audit row → conducts audit (Opus 4.7 1M cross-code + cross-plan + cross-codex)
   ├── audit doc lands in plans/audit/results/<slug>_YYYY_MM_DD.md
   ├── upgrades existing active plans (favoured) OR creates new active plans for gap items
   │      → each carries parent_epic: <epic-slug>
   │      → each carries estimate_class + estimate_baseline_ai_days + estimate_calibrated_ai_days
   ├── wrapper remediation plan in plans/active/<slug>_remediation_YYYY_MM_DD.md
   │      → carries parent_epic: + assigned_vm: vm-<epic>
   └── epic file body absorbs new active plans into its priority blocks
                │
                ▼
EPIC VM (one per epic; main slot 1 Opus + review slot 2 + workers slots 3-18 Sonnet)
   │
   ├── main agent polls registry every 60s → re-reads assigned epic + wrapper plans
   ├── regen_backlog_from_plan.py expands `- [ ]` items into VM backlog
   ├── review agent validates worker commits + FF-merges to LDR
   ├── workers pick up backlog items → ship per Half-1+2 commit pattern (CLAUDE.md)
   └── plan-flips back into the epic's priority blocks as items complete
                │
                ▼
EPIC stays put (everlasting). ACTIVE PLAN archives on completion. AUDIT DOC archives in plans/audit/results/.
```

VM orchestrator + worker + review agents work the items continuously per
[`/plans/epics/orchestrator_master.md`](/plans/epics/orchestrator_master.md). Ikenna + Harsh continuously feed the loop
by running audits + spinning new plans/epics from issues identified.

**Rule**: no orphan active plans. Every file in `plans/active/*.md` declares `parent_epic:` in frontmatter. The
inventory regenerator flags orphans as review-blocking.

## Epic frontmatter (canonical schema)

Every epic file in `plans/epics/<slug>.md` MUST carry:

```yaml
---
name: <slug> # kebab-case, matches filename, NO date suffix
title: "<human-readable title>" # REQUIRED (2026-05-21+)
type: epic
tier: L0|L1|L2|L3|L4|L5 # which layer this epic sits in (see registry below)
status: active|paused|cancelled # NEVER "complete" — epics are everlasting
priority: P0|P1|P2|P3 # rolls up to cutover master scoring
# > SUPERSEDED — see top banner (D2, 2026-06-24: assigned_vm is per-plan, not per-epic; epic-to-VM delegation dropped)
assigned_vm: vm-<id> # registry-resolved VM that owns this epic
parent: master_to_live_defi_2026_05_23 # always the cutover master (until cutover ships)
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
locked_by: live-defi-rollout
locked_since: YYYY-MM-DD
related_plans:
  - plans/active/<sub-plan>.md # the list grows continuously as audits spawn new active plans
  - plans/active/<another-sub-plan>.md
---
```

**Required**: `name`, `title`, `priority`, `status`. All other fields are strongly recommended.

**Forbidden on epics**: `deadline:`, `estimate_class:`, `estimate_baseline_ai_days:`, `estimate_calibrated_ai_days:`.
Epics are everlasting — they have no deadline. AI-day estimation lives on the active plans they reference.

**Deprecated on epics** (2026-05-21): `owner:`. This field is deprecated workspace-wide as part of the plan hygiene
automation sweep. Remove it from existing epics when touching the file; do not add to new ones. `check_frontmatter.sh`
flags it as a violation. (`asset_group:` was previously listed here too, but `check_frontmatter.sh`'s
`DEPRECATED_FIELDS` array never actually included it, and every currently-active epic still carries
`asset_group: [cross-cutting]` in frontmatter unflagged — corrected 2026-07-25, plan-reconcile.)

## Active plan frontmatter (must declare parent_epic)

Every file in `plans/active/*.md` MUST carry:

```yaml
---
title: <human-readable title>
parent_epic: <epic-slug> # REQUIRED; absence = ORPHAN = review-blocking
priority: P0|P1|P2|P3
status: draft|active|blocked|paused|complete|cancelled # draft ⇒ orchestrator does NOT ingest (WIP); flip to active when finalised
estimate_class: refactor|design|infra|brand-new|research
estimate_baseline_ai_days: <N>
estimate_calibrated_ai_days: <N> # baseline × class multiplier per /codex/08-workflows/estimation-calibration.md
locked_by: live-defi-rollout
locked_since: YYYY-MM-DD
related_plans:
  - ...
---
```

**Orphan = review-blocking**. `regenerate_active_plan_inventory.py` flags any active plan without `parent_epic:` as an
orphan. Resolve before next PR merge — assign the right epic OR file the plan in `plans/active/issues/` if scope is
unclear.

## Priority blocks within an epic

Epic body MUST organise its referenced active plans into priority-grouped sections (NOT a flat list):

```markdown
## P0 — must complete before next foundation gate

### Active plan: <slug>

- [x] [SCRIPT] P0.1. ...
- [ ] [AGENT] P0.2. ...

## P1 — important; post-current-gate

### Active plan: <slug>

- [ ] [HUMAN] P1.1. ...

## P2 — useful; opportunistic

## P3 — backlog; revisit quarterly
```

The VM main agent reads priority blocks in order — workers pick up P0 items first, P1 only when P0 is empty. Without
priority blocks, workers cannot self-direct.

## 23 epics in 6 tiers (regenerated 2026-07-12)

| #   | Tier | Epic slug                                 | Assigned VM            | Owns                                                                                                           |
| --- | ---- | ----------------------------------------- | ---------------------- | -------------------------------------------------------------------------------------------------------------- |
| 1   | L0   | `defi_master`                             | `vm-defi`              | DeFi adapters + on-chain execution + Copper custody + DeFi archetypes                                          |
| 2   | L0   | `cefi_master`                             | `vm-cefi`              | CeFi adapters + CCXT + CEFFU + perp hedge legs + CeFi archetypes                                               |
| 3   | L0   | `tradfi_master`                           | `vm-tradfi`            | TradFi adapters + dated futures + TradFi archetypes                                                            |
| 4   | L0   | `sports_master`                           | `vm-sports`            | Sports adapters + GBP settlement + sports archetypes                                                           |
| 5   | L0   | `predictions_master`                      | `vm-prediction`        | Polymarket + Kalshi + binary-outcome archetypes                                                                |
| 6   | L1   | `instruments_master`                      | `vm-cefi` (co-located) | instruments-service IS reference + universe SSOT                                                               |
| 7   | L1   | `mtds_mdps_master`                        | `vm-ml`                | MTDS adapters + MDPS candles + writegate + raw market data                                                     |
| 8   | L1   | `features_and_ml_master`                  | `vm-ml`                | features-service (8 families) + ml-service (inference + training)                                              |
| 9   | L1   | `manifest_master`                         | `vm-defi` (co-located) | Manifest v9 + honest absence + backfill + evolution discipline                                                 |
| 10  | L2   | `strategy_master`                         | `vm-trading-core`      | strategy-service post-consolidation; 53 archetypes; portfolio_allocator; risk; position; pnl                   |
| 11  | L2   | `execution_master`                        | `vm-trading-core`      | execution-service handlers + transfers + treasury + custody + flash loan + matching engine                     |
| 12  | L2   | `trading_agent_master`                    | `vm-trading-core`      | trading-agent-service closed-loop allocator                                                                    |
| 13  | L2   | `global_ledger_pnl_attribution_master`    | `vm-trading-core`      | Global ledger SSOT (Instruction/Passive/Treasury/Pricing) + derived PnL/Position/Exposure/Attribution views    |
| 14  | L3   | `dart_and_promote_master`                 | `vm-operator-ops`      | DART + ManualTradeGateDialog + promote workflow + state machine                                                |
| 15  | L3   | `deployment_and_user_management_master`   | `vm-operator-ops`      | deployment-api + deployment-ui + user-management                                                               |
| 16  | L4   | `infrastructure_master`                   | `vm-cross-cutting`     | Shard-axis + data-status umbrella; VM launcher/deployment-build maturity; AWS↔GCP parity; LDR→main CI/CD       |
| 17  | L4   | `observability_master`                    | `vm-cross-cutting`     | alerting-service + monitoring/telemetry; Incident Gateway 13-state + 5-layer recovery; kill-switch alerting    |
| 18  | L4   | `batch_live_symmetry_master`              | `vm-cross-cutting`     | Per-service batch=live audit; reconciliation                                                                   |
| 19  | L4   | `client_isolation_and_governance_master`  | `vm-cross-cutting`     | Per-client isolation + funds isolation + jurisdiction + share-class + UAC schema                               |
| 20  | L4   | `escalation_and_disaster_recovery_master` | `vm-cross-cutting`     | Escalation pipeline (blocked→Slack→human-resolve→UI) + self-healing/auto-recovery substrate                    |
| 21  | L5   | `orchestrator_master`                     | `vm-orchestrator`      | agent-orchestrator multi-VM runtime + planning VM + dashboard + self-healing safety                            |
| 22  | L5   | `agent_operating_framework_master`        | `planning`             | Agent dispatch (assigned_vm fail-closed matcher) + grep-native retrieval + role charters + retrieval-eval loop |
| 23  | L5   | `plan_hygiene_master`                     | `planning`             | Continuous plan-corpus hygiene: check scripts + hygiene sweep + codex-alignment audit                          |

Regenerated 2026-07-12 from `epics/*.md` frontmatter per operator ruling (plan-reconciliation finding 339, see
[`plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md`](../active/issues/plan_reconciliation_operator_decisions_2026_07_11.md)
§A2). Superseded/archived epic files excluded: `cross_cutting_may_23_SUPERSEDED_2026_05_21.md`,
`manifest_evolution_SUPERSEDED_2026_05_21.md`, `manifest_migration_SUPERSEDED_2026_05_21.md`,
`strategy_and_dart_master_SUPERSEDED_2026_05_21.md`. Tier count also corrected 5→6 in the heading: the table has always
spanned `L0`–`L5` (six distinct tiers); the pre-existing "5 tiers" phrasing undercounted.

**Caveat (added 2026-07-25, plan-reconcile)**: this "Assigned VM" column is NOT kept in sync with per-epic `assigned_vm`
frontmatter corrections made after 2026-07-12 (e.g. `escalation_and_disaster_recovery_master` and `trading_agent_master`
both had `assigned_vm` corrected to `planning` on 2026-07-21) — consistent with the epic-owns-VM model already being
SUPERSEDED/archival-only per the top banner. Treat this table's VM column as a 2026-07-12 snapshot, not a live registry.

- [ ] [SCRIPT] P2. Script this regeneration (scripts/plan-hygiene or scripts/docs) so the registry can't drift again —
      wire into the hygiene sweep.

**Cutover master (NOT an epic)**: `plans/archive/2026_07/master_to_live_defi_2026_05_23.md` is a dated, one-shot plan
tracking the May-23 live DeFi rollout across all 20 epics. Archives after cutover. Not in `plans/epics/`.

> SUPERSEDED — see top banner (single-VM, role-based-dispatch architecture, 2026-06-27; no per-epic VMs)

## VM topology (10 VMs serving 20 epics)

Multiple epics can share a VM if workload is bounded; one epic never spans multiple VMs.

| VM                 | Epics owned                                                                                                             | Reason                                            |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| `planning-vm`      | (none — interactive)                                                                                                    | Ikenna + Harsh planning + audit work              |
| `vm-defi`          | `defi_master`, `manifest_master`                                                                                        | DeFi cutover anchor; manifest backfill co-located |
| `vm-cefi`          | `cefi_master`, `instruments_master`                                                                                     | CeFi hedge legs + universe SSOT                   |
| `vm-tradfi`        | `tradfi_master`                                                                                                         | Standalone                                        |
| `vm-sports`        | `sports_master`                                                                                                         | Standalone                                        |
| `vm-prediction`    | `predictions_master`                                                                                                    | Standalone                                        |
| `vm-ml`            | `mtds_mdps_master`, `features_and_ml_master`                                                                            | Data → features → ML chain co-located             |
| `vm-trading-core`  | `strategy_master`, `execution_master`, `trading_agent_master`, `global_ledger_pnl_attribution_master`                   | Tightly coupled trading machinery                 |
| `vm-operator-ops`  | `dart_and_promote_master`, `deployment_and_user_management_master`                                                      | Operator surfaces                                 |
| `vm-cross-cutting` | `infrastructure_master`, `observability_master`, `batch_live_symmetry_master`, `client_isolation_and_governance_master` | Workspace-wide audit cadence                      |
| `vm-orchestrator`  | `orchestrator_master`                                                                                                   | Self-managing                                     |

Registry SSOT: [`../../orchestrator_vm_registry.yaml`](../../orchestrator_vm_registry.yaml). Full VM topology spec:
[`/plans/epics/orchestrator_master.md`](/plans/epics/orchestrator_master.md).

## Filename rules

- **Epics**: `plans/epics/<slug>.md` — kebab-case slug, **NO date suffix**. Everlasting. Examples: `defi_master.md`,
  `strategy_master.md`, `batch_live_symmetry_master.md`.
- **Active plans + wrapper plans**: `plans/active/<slug>_YYYY_MM_DD.md` — date suffix MANDATORY (dated work units).
- **Audit docs**: `plans/audit/results/<slug>_YYYY_MM_DD.md` — timestamped output of an audit-pool row.
- **Issue docs / audit pool**: `plans/active/issues/<slug>_YYYY_MM_DD.md` — surfaces UNACKED scope.
- **Archive**: `plans/archive/<slug>.plan.md` — frozen historical state; DO NOT rename (breaks archaeology in commit
  messages + external refs).

**Deprecated**: `.epic.md` double-extension form was the 2026-05-08 May-23 deadline-specific naming; superseded by the
everlasting epic model 2026-05-21. New epics use plain `.md`. Existing `.epic.md` files (currently only
`cross_cutting_may_23_SUPERSEDED_2026_05_21.epic.md`) rename to `.md` during the consolidation sweep.

## Historical: May-23 deliverables folded 2026-05-08 (archaeology)

The original layer model (2026-05-08) had 7 May-23 deliverable epics folded into per-domain master plans. The current
model supersedes that — every domain master is now a full L0 epic in its own right. The folding table is preserved here
for archaeology; the folded archive entries are unchanged.

| Folded May-23 deliverable               | Now lives in                                                      | Archived as                                                                                           |
| --------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Live DeFi rollout (carry archetypes)    | `defi_master.md` (L0)                                             | [`archive/live_defi_rollout_may_23_2026.epic.md`](../archive/live_defi_rollout_may_23_2026.epic.md)   |
| CeFi ML                                 | `cefi_master.md` (L0)                                             | [`archive/cefi_ml_may_23_2026.epic.md`](../archive/cefi_ml_may_23_2026.epic.md)                       |
| S&P prediction (CME)                    | `tradfi_master.md` (L0) deliverable A                             | [`archive/sp_prediction_may_23_2026.epic.md`](../archive/sp_prediction_may_23_2026.epic.md)           |
| Price arbitrage (CME futures + ETFs)    | `tradfi_master.md` (L0) deliverable B                             | [`archive/price_arbitrage_may_23_2026.epic.md`](../archive/price_arbitrage_may_23_2026.epic.md)       |
| Sports ML                               | `sports_master.md` (L0)                                           | [`archive/sports_ml_may_23_2026.epic.md`](../archive/sports_ml_may_23_2026.epic.md)                   |
| Prediction markets                      | `predictions_master.md` (L0)                                      | [`archive/prediction_markets_may_23_2026.epic.md`](../archive/prediction_markets_may_23_2026.epic.md) |
| Cross-cutting (catalogue / IDs / infra) | `client_isolation_and_governance_master.md` (L4) — scope extended | (was `cross_cutting_may_23_SUPERSEDED_2026_05_21.epic.md` — renamed)                                  |

## How to use these epics

**Read first.** Every epic has the same shape: end-state at May 23, IN/OUT scope, sub-plans consumed, cross-epic
handshakes, cross-cutting inherited. Reading the epic in 5 minutes gives you the orchestration picture; the sub-plans
hold the tactical work.

**Don't duplicate.** If you need to add a new todo, it goes in the relevant sub-plan (or a new sub-plan in
`plans/active/`), and the epic updates only its **sub-plans consumed** table to reference it. Epics are **read-mostly**
— the only writes are: (a) updating the consumed-plans table when a sub-plan is added/removed; (b) updating the
end-state at May 23 if scope changes (operator-approved); (c) closing open questions.

**Status flow.** Sub-plan checkboxes flip in their own files per the workspace `Commit + Push + Flip Plan Checkboxes`
HARD RULE. Epics do not track per-sub-plan checkbox state — they track **completion of the May-23 deliverable** as a
whole, evaluated against the end-state criteria.

**Plan format.** Epics follow the same Cursor-checkbox format (`- [x]` / `- [ ]`) as other plans for any leaf
deliverables they own directly (typically the end-state criteria + cross-epic handshakes), per
[`plans/PLAN_FORMAT.md`](../PLAN_FORMAT.md).

## Composition with workspace rules

- **Capture discoveries as plan todos** (CLAUDE.md HARD RULE). Discoveries during epic execution go into the relevant
  sub-plan, NOT the epic. Epic stays clean.
- **Cross-Plan Coordination Banners.** When a VM launches or an in-flight refactor starts, the banner lands on every
  affected sub-plan AND on every affected epic that consumes those sub-plans.
- **Findings Triage Discipline.** Findings from epic-execution sessions follow the case-1-to-5 routing. Issues that span
  multiple sub-plans get an issue doc under `plans/active/issues/`.
- **Daily work-split.** The two-side daily splits (Ikenna ↔ Harsh) reference epics for the day's domain target +
  reference sub-plans for the tactical scope.

## Lifecycle

Epics are **everlasting**. They are created once when a persistent code surface emerges that doesn't fit any existing
epic. They never archive on a deadline — there is always more work as audits surface gaps.

| Transition             | When                                               | Action                                                                                                                               |
| ---------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **Create**             | New persistent code surface emerges; operator acks | File lands in `plans/epics/<slug>.md` with `status: active`                                                                          |
| **Pause**              | Product strategy de-prioritises temporarily        | `status: paused`; epic file stays; assigned VM may be retired temporarily                                                            |
| **Cancel**             | Product strategy permanently drops the scope       | `status: cancelled`; epic stays in `plans/epics/` with SUPERSEDED-BY banner if scope absorbed elsewhere; NEVER deleted (archaeology) |
| **`status: complete`** | **Not used.** Epics are everlasting.               | —                                                                                                                                    |

Active plans under an epic cycle normally — they archive when complete. The epic itself stays put and accumulates new
active plan references in its `related_plans:` frontmatter over time.

The May-23 cutover master (`plans/archive/2026_07/master_to_live_defi_2026_05_23.md`) is the only dated, one-shot plan
tracking cross-epic readiness — it archives after May-23 cutover. Epics persist.

## Migration discipline (when reorganising epics)

Splits, consolidates, promotes, renames are operator-acked operations. Every move MUST:

1. Update every reference to the old slug (grep workspace-wide; quickmerge sweep recommended).
2. Update [`../../orchestrator_vm_registry.yaml`](../../orchestrator_vm_registry.yaml).
3. Update every active plan's `parent_epic:` field if it pointed at the old epic.
4. Update this README's 19-epic registry table.
5. Verify zero orphan active plans via `regenerate_active_plan_inventory.py`.
6. Banner the old epic file with SUPERSEDED-BY (don't delete — archaeology) if the old name was widely referenced.

## Cross-references

This file is the SSOT. Other docs point here:

- [`../../cursor-configs/CLAUDE.md`](../../cursor-configs/CLAUDE.md) — workspace project instructions; pointers from
  "Plan Format + Filename Convention" + "Daily Work-Split Process" sections
- [`/codex/11-project-management/epic-execution-with-sub-agents.md`](/codex/11-project-management/epic-execution-with-sub-agents.md)
  — codex pointer
- [`/codex/11-project-management/README.md`](/codex/11-project-management/README.md) — codex section index with epic
  registry
- [`../PLAN_FORMAT.md`](../PLAN_FORMAT.md) — plan format schema (references epic frontmatter rules here)
- [`/codex/11-project-management/active-plan-inventory-tracker.md`](/codex/11-project-management/active-plan-inventory-tracker.md)
  — orphan detection logic
- [`/codex/08-workflows/estimation-calibration.md`](/codex/08-workflows/estimation-calibration.md) — epic-exempt
  estimation rule

If you change this file, audit the above for staleness. If you change any of the above, update this file too.

## Cross-reference verification — 2026-05-22

Verified all section links and references. No broken links found. No "Audit instructions per epic" section exists in
this file — audit instructions are embedded in each epic file directly. No links to archived issue docs found (all issue
doc links in this file are pattern descriptions, not specific file paths). No changes required to fix broken links.
