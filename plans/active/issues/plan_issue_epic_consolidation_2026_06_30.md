---
doc_type: issue
title: "Plan / Issue / Epic Consolidation — content-verified archive / slim / merge / link + a navigable ordering map"
summary:
  "The active plan + issue set (123 plans, 88 issue docs, + epics) is too large and partly stale/done to navigate or
  trust. This is the master consolidation exercise: CONTENT-verify each doc end-to-end (never trust frontmatter status),
  classify truly-done vs bandaid/partial/stale, then archive / SLIM (preferred) / merge / supersede / link-and-track /
  keep — and produce a single ordering map (do-now / parallel / blocked-by-gate) for the remaining active work.
  Read-and-verify is fanned out to background agents in waves; synthesis + operator-approval + execution stay with the
  main loop. AWAITING OPERATOR AGREEMENT on this plan-of-work before execution starts."
status: draft
nature: audit
asset_group: cross-asset
stage: [meta]
repos: [unified-trading-pm]
scope: [admin]
tags: [consolidation, plan-hygiene, issue-triage, archival, ordering-map, ssot-audit]
related:
  [
    ./instruments_service_plan_reconciliation_2026_06_29.md,
    ./mtds_plan_reconciliation_2026_06_29.md,
    ../../PLAN_FORMAT.md,
    ../../../codex/11-project-management/doc-frontmatter-schema.md,
  ]
created: 2026-06-30
last_updated: 2026-06-30
assigned_vm: NA
execution_scope: local-only
priority: P1
source: [operator request 2026-06-30]
drift_direction: advance-code
depends_on: []
locked_by: NA
locked_since: 2026-06-30
---

# Plan / Issue / Epic Consolidation (2026-06-30)

> **Goal:** turn an un-navigable pile (123 active plans · 88 issue docs · epics) into a lean, trustworthy set + ONE
> ordering map. Every disposition is backed by an **end-to-end content check**, not a frontmatter status. **AWAITING
> AGREEMENT** — nothing is archived/edited until the operator signs off on this plan-of-work.

## 0. Why (operator framing 2026-06-30)

Too many plans/issues/epics, much of it stale or already-done, so: (a) navigation is impossible; (b) there is no clear
"what to do now / what's parallel / what's gated"; (c) it's hard to confirm a plan was *actually* implemented
end-to-end. This exercise fixes all three.

## 1. The HARD verification rule (the heart of this)

**Frontmatter status (`resolved` / `complete` / `[x]`) is a CLAIM, not proof.** For every doc an agent MUST read the
full content and verify the claim against live reality before any disposition:

1. **Claimed state** — frontmatter `status`, checkbox ratio, any "DONE/RESOLVED/G-gate-complete" banners.
2. **Verified state** — pick the doc's core claims/items and CHECK them against the live tree:
   - cited evidence resolves (commit exists + does what's claimed; `cloudbuild=<id>` is SUCCESS; manifest rows present);
   - the change is in **live code/data** (grep the symbol, read the consumer, query the manifest) — grep-0 ≠ done;
   - **quality gate**: is it a real root-fix or a **bandaid** (shim / `# type: ignore` / disabled test / `try/except
     ImportError` / TODO / "tracked separately")? Did it introduce a **regression**?
   - for an **issue**: is the ROOT CAUSE fixed in live code, or merely patched/worked-around?
3. **Verdict** — `TRULY-DONE` · `DONE-BUT-BANDAID` (works, carries tech-debt) · `PARTIAL` · `STALE` (newer code already
   moved past it) · `SUPERSEDED` (replaced by another doc) · `ACTIVE` (genuine open work).
4. **Evidence** — the agent records the exact checks (files/commands/symbols/build-ids) so the operator can trust the
   verdict without re-doing it. **No verdict without evidence.**

## 2. Disposition vocabulary (operator preference: SLIM > supersede+archive for low-value)

| disposition         | when                                                                 | action                                                                                          |
| ------------------- | -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **ARCHIVE**         | `TRULY-DONE`, end-to-end verified, little residual reference value   | 5-step ritual → move to archived, done/superseded banner, clear lock (`[unlock-plan]` batch)    |
| **SLIM** _(prefer)_ | done but worth keeping as reference; bloated with completed detail   | trim completed sections to a 1-line summary + durable contract; KEEP active but lean            |
| **MERGE**           | duplicate / overlapping plans                                        | fold into one canonical; archive the merged-away as `superseded_by`                             |
| **SUPERSEDE+arch.** | replaced by a newer/better plan AND a fresh plan is warranted (high value) | new plan carries the open work; old → `superseded_by` + archive                            |
| **LINK-AND-TRACK**  | OPEN issue whose fix IS covered by an active plan's tasks            | cross-link issue↔plan + set issue `status: tracked` (or note the covering plan); do NOT archive |
| **KEEP**            | genuine active work, not bloated                                     | leave as-is (± trivial hygiene)                                                                  |

## 3. Phasing + ordering (operator-specified)

**Scope = ALL plans + ALL issues first; epics as an explicit follow-up.**

- **Phase A — Issues (88 docs).**
  - **A1** content-verify each: `TRULY-RESOLVED` → ARCHIVE; else → open.
  - **A2** for each still-open issue: does an **active plan already carry tasks** that solve it? **YES** → LINK-AND-TRACK
    (cross-link + status `tracked`); **NO** → KEEP as-is (flag any that need a new task/plan).
- **Phase B — Active plans (123 docs).**
  - **B1** content-verify done-ness end-to-end (the §1 rule).
  - **B2** disposition: TRULY-DONE → ARCHIVE; low-value-done → **SLIM** (preferred); duplicates → MERGE; replaced(high
    value) → SUPERSEDE+archive; active → KEEP. Carry the IS/MTDS reconciliation Section-G/F decisions through (e.g.
    `mvp_*_v10` family now that the closeout is verified).
- **Phase C — Epics (follow-up).** Same rubric on epics once A+B land.
- **Phase D — The ORDERING MAP (the navigability deliverable).** From the surviving active work, produce one ranked map:
  **DO-NOW** (unblocked, high-priority) · **PARALLEL** (independent, safe concurrently) · **BLOCKED/GATED** (name the
  gate + what unblocks it). This is the "what should we do now" the operator asked for.

## 4. Background-agent fan-out (read-only verify; synthesis + execution stay here)

Scale (211 docs) needs parallelism. Agents VERIFY + PROPOSE; they never edit/archive. **Each agent gets
`SUB_AGENT_MANDATORY_RULES.md` at spawn top** (if injection fails, the agent must not proceed); ≤10 parallel; batched by
DOMAIN for coherent context (cefi · defi · tradfi · sports · prediction · honest-coverage · infra/cicd · ui · ml/strategy
· pm/meta).

- **Wave A (issues):** ~88 issues → ~9 agents (~10 each), one ≤10-wide wave. Each returns a structured per-issue verdict
  (claimed / verified / evidence / disposition / covering-plan-if-any).
- **Wave B1–B2 (plans):** ~123 plans → ~18 agents (~7 each), two ≤10-wide waves. Same structured per-plan verdict.
- **Output schema (every agent, per doc):** `{slug, claimed_status, verified_verdict, evidence[], disposition,
  links[], lock, notes}` → I merge into the **§6 disposition ledger**.
- **Then:** I synthesize → present each domain batch for operator approval → execute the approved dispositions (archival
  ritual / slim edits / merges / links) in slot 1, local-only until you say push.

## 5. Guardrails

- **Verify, don't trust** (§1) — the whole point; a flipped checkbox is not evidence.
- **Locks are boilerplate** (`locked_by: live-defi-rollout` on 98 plans) — per operator, archive only AFTER end-to-end
  verification; clear the lock via a batched `[unlock-plan]` commit (human-gated; I prepare, operator authorizes).
- **SLIM is preferred** over supersede+archive for low-value done plans.
- **Archival = the 5-step ritual** (migrate DEFERRED → banner → codex-alignment check → update CLAUDE.md/codex on a
  changed contract → clear lock). No silent deletes; never `git reset --hard`/`clean`.
- **Operator approves dispositions before execution** (per domain batch); main loop executes, doesn't auto-archive in bulk.
- **Local-only** until the operator says push (consistent with the current hold).

## 6. Disposition ledger (filled during execution)

> One row per doc. Populated by the agent waves + synthesis. Empty until execution is greenlit.

_(Phase A — issues, Phase B — plans tables go here.)_

## 7. Ordering map (Phase D output)

_(DO-NOW / PARALLEL / BLOCKED-BY-GATE — filled after A+B.)_

## Progress Log

- **2026-06-30** — Doc created as the consolidation plan-of-work (status `draft`, AWAITING AGREEMENT). Inventory taken:
  **123 active plans** (~30 at 100% checkboxes, ~40 at 80–99%), **88 issue docs**, + epics. Lock reality surfaced: **98
  plans `locked_by: live-defi-rollout`** (operator confirms boilerplate — archivable after end-to-end verification via a
  batched `[unlock-plan]`), **22 `NA`**. Methodology (content-verify, not frontmatter), disposition vocabulary
  (SLIM-preferred), phasing (issues → plans → epics → ordering map), and the background-agent fan-out plan drafted. No
  docs archived/edited yet — execution starts on operator agreement.
