---
doc_type: issue
title:
  Plan-reconciler doc-hygiene findings 2026-06-17 — stale codex pnl-attribution pointer (4 referrers) + abandoned
  plans/active/INDEX.md (99-entry drift)
summary:
  Filed by the daily plan-reconciler (dispatch `agt-3591cc`). Both are reader-verifiable, chronic doc/index drifts
  surfaced deterministically by the hygiene sweep + health digest. Neither is mechanic...
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [plan-hygiene, ssot-audit, orchestrator, docspec, verification]
related: []
created: 2026-06-17
parent_epic: plan_hygiene_master
priority: P3
source:
  [
    daily plan-reconciliation pass agt-3591cc 2026-06-17,
    "scripts/plan-hygiene/run_hygiene_sweep.sh — check_codex_refs: 1 broken ref",
    "scripts/plan-hygiene/build_health_digest.sh — INDEX.md ↔ active-plans drift: 99",
  ]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

# Plan-reconciler doc-hygiene findings (2026-06-17)

Filed by the daily plan-reconciler (dispatch `agt-3591cc`). Both are reader-verifiable, chronic doc/index drifts
surfaced deterministically by the hygiene sweep + health digest. Neither is mechanically fixable by `fix_frontmatter.py`
/ `fix_todo_format.sh`, and the primary referrers sit outside `plans/**` (workspace rule docs) — so they need a human /
follow-up rather than an autonomous reconciler edit.

This run otherwise found a clean corpus: 0 hard hygiene failures, no missed flips (every `repo@sha` / ✅ evidence token
traced to a genuinely-open todo — a done prerequisite is not a done todo), and no clear plan-vs-plan / plan-vs-epic
contradictions.

## Finding 1 — stale codex pointer `/codex/09-strategy/operational/pnl-attribution.md` (4 referrers)

> _(Corrected 2026-07-12, finding 231, §A2 B-queue ruling: this section's "does not exist" path and the "Recommended
> decision" rewrite line below both showed the CORRECT path on both sides of the X → X arrow, a copy-paste artifact —
> the true stale path, confirmed by the checked-off todo two lines below, was `operational/pnl-attribution.md`. Restored
> below; the "actual doc lives at" sentence was already correct and is unchanged.)_

### What I found

The SSOT pointer `/codex/09-strategy/operational/pnl-attribution.md` **does not exist** — it was never committed at that
path (`git log --all -- /codex/09-strategy/operational/pnl-attribution.md` is empty). The actual doc lives at
**`/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`** (64 KB, the canonical PnL-attribution SSOT),
referenced correctly by `/codex/09-strategy/README.md`, `/codex/04-architecture/client-reporting-architecture.md`, the
epic `plans/epics/global_ledger_pnl_attribution_master.md`, and the `codex_ssots:` of
`plans/active/global_ledger_pnl_attribution_migration_2026_06_01.md`.

Four referrers still point at the stale `operational/` path:

- `cursor-configs/CLAUDE.md:654` — workspace rule doc (out of reconciler scope; authoritative fix)
- `cursor-configs/SUB_AGENT_MANDATORY_RULES.md:326` — workspace rule doc (out of reconciler scope)
- `plans/active/engine_findings_remediation_2026_06_15.md:262` — in the 12 h grace window this run (not editable)
- `plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md:436` — inside an open `[AUDIT] P1` todo

`check_codex_refs` flags the `engine_findings_remediation` reference as the single broken codex ref on every hygiene
sweep.

### Why it matters

A reader/agent following the pointer 404s; the HWM/PnL-attribution rule in CLAUDE.md (the authoritative copy) points
nowhere. Blast radius is low (a doc pointer, no code), but it re-trips the hygiene gate every run and erodes trust in
the SSOT pointers.

### Recommended decision

Rewrite all four referrers `operational/pnl-attribution.md` → `architecture-v2/cross-cutting/pnl-attribution.md`. The
two rule-doc edits (CLAUDE.md, SUB_AGENT_MANDATORY_RULES.md) are the authoritative fix and need a human/operator (they
govern every agent); the two plan edits are mechanical once their constraints clear.

- [x] ✅ [DOCS] P3. Rewrite the stale codex pointer `operational/pnl-attribution.md` →
      `09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` in all referrers — DONE 2026-06-21 (8 referrers
      fixed: CLAUDE.md, SUB_AGENT_MANDATORY_RULES.md, engine_findings_remediation, utl_uac_reuse_consolidation,
      citadel_paper_batch_live_reconciliation, plan_reconciler + the 2 ping ledgers; 0 stale `operational/` refs
      remain). Correct doc is 64 KB at the architecture-v2 path. Provenance: plan-reconciler agt-3591cc 2026-06-17.

## Finding 2 — `plans/active/INDEX.md` is abandoned (99-entry drift vs the live plan set)

### What I found

`plans/active/INDEX.md` self-describes as "the canonical index of all active plans", but it is hand-maintained with no
regenerator — the only scripts touching `INDEX.md` are read-only checkers — so it drifts monotonically against the live
plan set. Entries point at plans already archived (e.g. `cme_polymarket_arb_2026_05_08.md`, `instruments_master.md`,
`market_tick_data_to_100pct_2026_05_05.md`). **Re-derive the drift rather than trusting a number pinned here**:
`bash scripts/plan-hygiene/build_health_digest.sh` → the `INDEX drift` field.

> **Corrected 2026-07-26 (`/plan-reconcile` infra shard — three facts in this section were provably stale; all
> re-measured this turn).** (1) _Was_ "its header reads 'Last Updated: 2026-05-08' and the file has not changed since
> 2026-05-22" — the header now reads **"Last Updated: 2026-07-12"** (fixed in-place by doc-reconciliation finding 4, §A2
> B-queue ruling), so the specific staleness symptom cited is gone even though the underlying no-regenerator problem is
> not. (2) _Was_ "(24 KB)" / "drift = 99" / "~90 current active plans are absent" — measured 2026-07-26: the file is
> **361 lines / 31,515 bytes** and `build_health_digest.sh` reports **`INDEX drift 226`** against 224 active plans. The
> hardcoded 99 was re-staling on every corpus change, so it is replaced above with the command that derives it. (3)
> _Was_ "The live, maintained index is the `<!-- AUTO-INVENTORY -->` block in
> `plans/archive/2026_07/master_to_live_defi_2026_05_23.md`" — that host was ARCHIVED 2026-07-24 and the live block
> **moved to `/plans/active/active_plan_inventory_dashboard_2026_07_24.md`**; ground truth is the regenerator's own
> constant, `scripts/plans/regenerate_active_plan_inventory.py:38` →
> `MASTER_FILE = PLANS_DIR / "active_plan_inventory_dashboard_2026_07_24.md"`. (The archived doc still contains a frozen
> copy of the block, which is why a grep alone does not disambiguate — read the constant.) The finding's conclusion is
> UNCHANGED and if anything stronger: an auto-regenerated inventory already occupies the canonical-index role, so
> INDEX.md's self-description is the thing that is wrong.

### Why it matters

A reader trusting INDEX.md's "canonical index of all active plans" claim gets a badly wrong picture (hundreds of entries
out of sync, plus dangling links to archived plans). It is a reader trap the digest flags every run, and the drift has
grown, not shrunk (99 at filing → 226 measured 2026-07-26).

### Recommended decision

Operator call — either (a) formally deprecate `plans/active/INDEX.md`: banner it as superseded by the auto-regenerated
inventory and drop it from the digest's drift check; or (b) add a regenerator and reconcile it. (a) looks correct given
the auto-inventory already serves the canonical-index role.

- [ ] [DOCS] P3. Decide + execute: deprecate `plans/active/INDEX.md` (superseded by the auto-regenerated inventory now
      hosted at `/plans/active/active_plan_inventory_dashboard_2026_07_24.md` — target corrected 2026-07-26, was "the
      master-plan AUTO-INVENTORY", whose host `master_to_live_defi_2026_05_23.md` archived 2026-07-24) OR add a
      regenerator + reconcile the drift (re-derive the live count via
      `bash scripts/plan-hygiene/build_health_digest.sh`; 226 as of 2026-07-26, was 99 at filing). Currently
      hand-maintained, no regen script. Provenance: plan-reconciler agt-3591cc 2026-06-17.
