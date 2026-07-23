---
doc_type: codex-ssot
title: Data Pipeline Correctness Is The Heartbeat — Hard Rule SSOT
summary:
  The "data-pipeline correctness is the heartbeat" HARD RULE SSOT (codified after the 2026-05-20 mega-audit — 96.34%
  MISSING_EXPECTED, 0% v8 of 7.4M rows) — 5 invariants (universal scope, closed-set BLOCKED-* deferral, coverage-matrix
  transparency, layer-N+1 freeze on RED, code+data audits compose), the slot-freeze protocol, and the banned deferral
  phrases.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [data-correctness, data-pipeline, audit, escalation, plan-hygiene, data-quality]
related:
  [
    /codex/11-project-management/foundation-completion-gate-discipline.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    ../../plans/epics/mtds_mdps_master.md,
  ]
created: 2026-05-20
authoritative_for: [data-pipeline-correctness heartbeat hard rule]
referenced_by:
  [
    /codex/02-data/external-data-always-available-rule.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/shard-coverage-classification.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    plans/archive/2026_07/honest_coverage_v2_instrument_denominator_2026_06_28.md,
    plans/active/issues/vm_backfill_data_correctness_findings_2026_06_29.md,
    plans/epics/mtds_mdps_master.md,
  ]
owner:
last_reviewed: 2026-06-25
code_refs:
---

# Data Pipeline Correctness Is The Heartbeat — Hard Rule SSOT

> **CLAUDE.md anchor**: "Data Pipeline Correctness Is The Heartbeat — No Exceptions, No Cutbacks (HARD RULE — codified
> 2026-05-20)".
>
> Codified after the 2026-05-20 mega-audit Phase A surfaced 765 `DIVERGENT_EMPTY` + 236,892 `MISSING_EXPECTED` cells +
> 0% of 7.4M prod manifest rows at v8 + 1.3M NULL-schema-version rows. Operator directive: "having data, both batch and
> live" is the heartbeat — no paper-trade / strategy / execution work is real until the data audit is GREEN for the
> asset_groups that work touches.

## What this rule replaces

Prior to this codification, the workspace had three implicit assumptions that produced the 2026-05-20 audit findings:

1. **"The constant is bumped → the data is migrated"** — false. Bumping `MANIFEST_SCHEMA_VERSION = 8` in code doesn't
   migrate the 7.4M rows already at v4/v5/v6/v7. The code-side QG step (A1.2) only catches constants; the data-side
   audit (A4) is required.
2. **"Most-cells-captured is good enough for the deadline"** — false. Strategy + paper-trade fits on the holes too. A
   96.34% MISSING_EXPECTED rate (the workspace state on 2026-05-20) means the workspace is strategising on 3.66% of the
   actual market — not a usable signal.
3. **"Layer-N+1 work can proceed in parallel while data audits run"** — false. The foundation-completion-gate rule
   existed but didn't bite hard enough; agents continued building execution / paper-trade scaffolding on top of
   unaudited data, producing the audit-undo cost that triggered this rule.

This SSOT is the canonical answer to all three.

## The rule (formal statement)

For every data-pipeline audit (manifest schema compliance, expected-coverage divergence, dependency-fail propagation,
batch-live adapter parity, or any sibling diagnostic), the following invariants hold:

### Invariant 1 — Universal scope

Every (asset_group × venue × data_type × time-range × batch/live) cell is in audit scope. Specifically:

- Every asset_group: `cefi`, `defi`, `tradfi`, `sports`, `prediction`.
- Every venue declared in `EXPECTED_COVERAGE_BY_ASSET_GROUP` per asset_group.
- Every data_type in that venue's scope entry.
- Every date from earliest plausible start (e.g. 2020-01-01 default) to today.
- Both batch + live modes (per `Batch = Live (CRITICAL)` workspace rule).

**Auditing agents cannot remove cells from scope** without an operator-acked ping. Agent's role: surface every gap +
propose options. Operator's role: decide scope.

### Invariant 2 — Closed-set deferral status

When an audit gap exists, it gets ONE of three statuses (no other):

| Status                      | Trigger                                                                                                                                                          | Operator ack required?                           |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| `BLOCKED-CREDENTIALS`       | The data exists but a credential is needed; per `External Data Is Always Available`, the adapter scaffold ships immediately + a credential ping goes to operator | YES (operator must ack the ping)                 |
| `BLOCKED-OPERATOR-DECISION` | A scope-removal call is needed (e.g. "should we ingest BARCHART after they discontinued?")                                                                       | YES (operator articulates why + names successor) |
| `BLOCKED-UPSTREAM-OUTAGE`   | Third-party degraded; ping logged; auto-resumes                                                                                                                  | NO (transient, self-clearing)                    |

`DEFERRED` without one of these statuses + an operator ack is **banned**.

### Invariant 3 — Audit transparency section (REQUIRED)

Every audit deliverable MUST include a "Coverage matrix" section that declares per sub-audit:

- **What was walked exhaustively** (every file / every row / every cell).
- **What was sampled** (subset reason + sample size).
- **What was approximated** (regex vs AST, etc.).
- **What was not audited at all** (explicit list with follow-up estimate).

Audits without this section are review-blocked.

Reference template:
[plans/audit/results/mega_audit_phase_a_issues_human_readable_2026_05_20.md](../../plans/audit/results/mega_audit_phase_a_issues_human_readable_2026_05_20.md)
§ "Coverage matrix (sampling vs comprehensive)".

### Invariant 4 — Layer-N+1 freeze on RED audit

When a data audit is RED for an asset_group:

1. Plan reviewer rejects new plans proposing layer-N+1 changes for that asset_group.
2. Orchestrator (slot 1 main) reassigns in-flight slots from layer-N+1 to data-fix work until audit is GREEN.
3. Slots doing layer-N+1 work on RED asset_groups have their current item marked `🔴 FROZEN — data audit RED` in
   work_split + are reassigned the next dispatch cycle.

The freeze is not optional + not deprioritised — slots that "double down on bad code" produce audit-undo cost.

### Invariant 5 — Data-side + code-side audits compose

Code-shape audits (regex/AST scan of source for hardcoded constants, patterns, etc.) are **insufficient on their own**.
Every code-side audit must be paired with a data-side audit that reads the actual artefacts (GCS manifest rows, parquet
schema versions, on-disk shard counts, etc.).

Concrete pairings (canonical, locked 2026-05-20):

| Code audit                                            | Data audit                                                                     | What divergence looks like                                               |
| ----------------------------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| A1 `manifest_v8` (code: `schema_version = N`)         | A4 data side (`_index/availability_index.parquet` schema_version distribution) | Code constant says 8 but data is at v4/v5/v6/v7 (the 2026-05-20 finding) |
| A1 `record_emission` (code: handler emits `record_*`) | A3 (manifest divergence per cell)                                              | Code emits but cells are `MISSING_EXPECTED`                              |
| A1 `classify_venue_error` (code: adapter classifies)  | A3 (`ATTEMPTED_FAILED` distribution + `error_reason` taxonomy)                 | Code classifies but reasons are blank / freeform                         |
| A1 `resolve_bucket_name` (code: no inline gs://)      | (no direct data-side — bucket-name SSOT is config-only)                        | n/a                                                                      |

## Slot-freeze protocol

When an audit lands with P0 findings for asset_group X, slot 1 main:

1. Reads current daily work_split for X.
2. For every slot working on layer-N+1 (N = whatever data layer is RED for X):
   - Marks slot's current item `🔴 FROZEN — data audit P0 for X`.
   - Reassigns slot to the corresponding remediation plan (per the audit's remediation roadmap section).
3. Updates `master_to_live_defi_2026_05_23.md` `## Slots frozen pending data audits` section (auto-create if absent).
4. Posts ping to `plans/active/_agent_pings.md` cross-side so harsh's side also reassigns.
5. Does NOT unfreeze until audit re-runs GREEN OR operator explicitly approves a `BLOCKED-OPERATOR-DECISION` for the
   remaining cells.

## Plan-reviewer recipe

For any incoming plan, plan-reviewer agent checks:

```bash
# 1. Which asset_groups does this plan touch?
rg "asset_group" path/to/plan.md | head

# 2. For each asset_group, what's the latest A1-A6 audit status?
# Check master tracker for GREEN/RED state.

# 3. If RED + plan ships layer-N+1 changes for that asset_group → REJECT.
#    Plan must either:
#      (a) be re-scoped to layer-N data-fix work, or
#      (b) wait for audit to land GREEN.
```

## Banned phrases (closed-set, 2026-05-20)

The following phrases are **explicitly banned** when an agent or plan is discussing a data-pipeline audit gap. Any plan
or review comment containing one of these is automatically review-blocking:

| Banned phrase                           | Why it is banned                                                                                                                                                                          |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `"skip for the deadline"`               | Deadlines do not override data correctness. Strategy + paper-trade fits on the holes; a deadline built on missing data is not a real deadline.                                            |
| `"post-cutover"`                        | Without a named successor plan in `plans/active/` + operator ack, "post-cutover" is indistinguishable from "never". Permitted only when the successor plan is cited inline.               |
| `"most cells captured, rest later"`     | "Most" masks the specific gap. The 2026-05-20 audit showed 96.34% MISSING_EXPECTED — "most" was meaningless. Every uncaptured cell must be status-tagged (`BLOCKED-*` or backfilled).     |
| `"the constant says v8 so good enough"` | Read the ACTUAL `schema_version` distribution in the data, not the code constant. Incident: `MANIFEST_SCHEMA_VERSION = 8` was set in code while 0% of 7.4M prod rows were at v8.          |
| `"do A5/A6 later"`                      | Sub-audit items (A1–A6) are coupled. Skipping A5 (batch/live adapter parity) or A6 (dependency-fail propagation) leaves the audit incompletely green. All sub-audits must close together. |

These map to Invariant 1 (universal scope) and Invariant 2 (closed-set deferral status) above. An agent encountering one
of these phrases in a plan MUST flag it to the plan reviewer before the plan enters active dispatch.

## QG-sweep batching — detail pointer

> The canonical detail for QG-sweep batching lives in
> [`/codex/06-coding-standards/quality-gates.md`](/codex/06-coding-standards/quality-gates.md) § "QG-sweep batching".
> The summary below is a cross-reference so this SSOT is self-contained for agents auditing the data pipeline.

**Batch the GATE, not the commits (codified 2026-06-02)**: for a batch of related edits, make ALL edits first, then run
`quality-gates.sh` ONCE per repo over the batch, then make per-shippable-unit commits + plan-flips from that green tree.
The gate is per-batch; the Commit+Push+Flip discipline (one flip per shipped item) is preserved.

**Shared-host concurrency limit (HARD)**: ≤2 full quality-gate runs at once host-wide (raised from 1 → 2, operator
2026-06-05; `qg-host-governor.sh` token floor = `max(2, floor(cores/4))`). RAM rationale: UTL's 5.27 GB peak × 2 ≈ 10.6
GB fits a 16 GB worker. Beyond the limit, runs serialize. Exceeding OOM-kills the gate process at **exit 144**.

**NEVER bulk-kill `pytest` / `quality-gates.sh` / `basedpyright`** — the process may belong to another slot.

**Sanctioned overrides** (for the META-gate `<300s` time check only, when substantive gates are green):
`IGNORE_TIMEOUT=true` / `PYRIGHT_TIMEOUT=<n>`. These do NOT bypass coverage, type-check, or lint gates.

## Generated artifacts — gitignore and determinism

> The canonical source for the generated-artifact gitignore list is
> [`/codex/08-workflows/ci-cd-flow.md`](/codex/08-workflows/ci-cd-flow.md). The summary below is a cross-reference so
> this SSOT is self-contained for agents working the data pipeline.

### Generated artifacts are gitignored, NEVER committed (HARD RULE, codified 2026-06-03)

Every file that `quality-gates.sh` or `quickmerge` regenerates from a tracked SSOT is `.gitignore`'d +
`git rm --cached`'d. Committing a generated artefact only churns the worktree → jams `slot-cron-ff-pull.sh` → slot
drift.

**Canonical ignore set (PM)**:

| Artefact                                            | Source SSOT                     | Why gitignored                        |
| --------------------------------------------------- | ------------------------------- | ------------------------------------- |
| `docs/repo-management/CI-CD-PIPELINE.svg` / `.html` | `cicd-pipeline-definition.yaml` | Regenerated on every QG run           |
| `WORKSPACE_MANIFEST_DAG.svg`                        | `workspace-manifest.json`       | Regenerated on every manifest parse   |
| `DATA_FLOW_DAG.svg`                                 | `workspace-manifest.json`       | Regenerated on every manifest parse   |
| `derived-dependency-manifest.json`                  | all `pyproject.toml` files      | Regenerated per-promotion             |
| `coverage.xml`                                      | pytest coverage run             | Local-only artefact, never cross-repo |
| `.qg_last_passed_sha`                               | `quality-gates.sh`              | Local sentinel, per-clone cache       |
| `.qg_content_sentinel`                              | `quality-gates.sh`              | Local sentinel, per-clone cache       |

Every consumer regenerates from the SSOT before reading — a committed copy is always a stale cache; nothing imports an
SVG (zero logic blast radius).

**Generators MUST emit deterministically** — `sorted()` any set/map before rendering. Incident:
`generate-cicd-diagram.py` iterated a `set()` of marker colours → byte-churned the SVG on every run with no real content
change.

**If you see a generated artefact dirty/`??` after a QG run, do NOT stage it** — it is regen churn; gitignore +
`git rm --cached` it, and add the pattern to the canonical template `scripts/propagation/templates/gitignore-python.txt`
for fleet rollout.

### Orphan-ping cron — RETIRED 2026-07-04

The `_agent_pings.md` ping-ledger channel and its every-4h orphan-ping audit cron
(`scripts/agents/audit_ping_orphans.sh` + GCP `uts-prod-orphan-ping-audit` job/scheduler/terraform) were decommissioned
2026-07-04 — nobody read the ledgers after the 2026-06-27 single-VM AO migration. Do not write pings; route
agent↔agent/operator comms through the agent-orchestrator HTTP server, and track work as plan todos (`plans/active/…`) —
the underlying "every notification must reference a plan item" intent lives on in the plan-todo discipline, not in a
ledger cron.

## Composition with other rules

- **`Foundation-Completion-Gate Discipline`**
  ([foundation-completion-gate-discipline](/codex/11-project-management/foundation-completion-gate-discipline.md)): this
  rule is the data-correctness expansion. The gate already says "no layer-N+1 until layer-N GREEN" — this rule says when
  "GREEN" is itself in doubt due to data-state divergence, the gate is automatically RED.
- **`External Data Is Always Available`**: the per-data-source case. A credential gap doesn't justify scope removal; the
  adapter scaffold ships
  - credential ping goes to operator.
- **`Plans Run To Actual Completion`**: operationally-shipped = every cell. Not "most cells".
- **`Manifest + Honest Absence`**: the per-cell expression. Every cell is either `captured` (data present) or
  `empty_confirmed[reason=<typed>]` (operator-acked honest empty). Silent gaps (`MISSING_EXPECTED`) are always
  review-blocking.

## Reference incidents

- **2026-05-20 mega-audit Phase A** — the codifying event. 765 `DIVERGENT_EMPTY` + 236,892 `MISSING_EXPECTED` + 0% v8
  across 7.4M rows. Operator directive that produced this SSOT.
- **2026-05-19 Drift S3 silent-absence** — the per-adapter bug class that the `DIVERGENT_EMPTY` classification catches.
- **2026-05-19 14-launcher EXIT-trap fix** — code-side fix that A1 surfaces.

## When this rule itself updates

- When a new data-audit sub-dimension is identified, add it to Invariant 5.
- When the BLOCKED-\* status taxonomy needs a new status, propose to operator
  - extend Invariant 2.
- When the freeze protocol's mechanics change (e.g. orchestrator UI replaces ledger files), update the slot-freeze
  protocol section.

Do NOT update Invariant 1 (universal scope) without operator approval — that's the canonical
scope-removal-requires-operator clause.

## Canonical execution-ordering coordinator

`plans/epics/mtds_mdps_master.md` is the operator-handoff entry point for migration sequencing. It encodes the
phase-ordering (Phase -2 through Phase 14) and owns broadcast + ACK tracking for the cross-slot freeze protocol (§
Invariant 4). When a slot needs to understand the execution order for data-pipeline migration items, that plan is the
canonical reference — not agent memory, not inline comments.
