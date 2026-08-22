---
doc_type: issue
title: Two client-artefact sections map to superseded epics with zero active child plans — PnL attribution and promote workflow have no live owner
summary: >-
  `platform-external-api-walkthrough.html` carries a "PnL attribution, across every dimension" section and the strategy
  artefacts cover the promote workflow, but `global_ledger_pnl_attribution_master` and `dart_and_promote_master` are
  both `status: superseded` with ZERO active child plans. Either a successor epic exists and was not located, or two
  client-facing artefact sections have no owning epic — meaning nothing tracks keeping them true.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [epics, ownership, client-artefacts, orphan, plan-hygiene]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/state_fabric_artefacts_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
    /codex/04-architecture/cross-domain-state-fabric.md,
  ]
context_scope:
  [
    /plans/epics/global_ledger_pnl_attribution_master.md,
    /plans/epics/dart_and_promote_master.md,
    /plans/active/state_fabric_artefacts_2026_08_20.md,
  ]
created: 2026-08-20
last_updated: "2026-08-21"
parent_epic: system_readiness_master
assigned_vm: planning
locked_by:
locked_since:
resolved_by:
execution_scope: orchestrator-agent
priority: P1
severity: P1
source: >-
  Found 2026-08-20 while measuring which epics gate a complete presentation of the client artefact set. Surfaced by
  the mapping exercise, not by a hygiene sweep — which is itself the point, since no machine-readable artefact-to-epic
  relation exists to catch it.
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
---

# Two artefact sections, no live owning epic

## Measured 2026-08-20

| Artefact section | Mapped epic | Epic status | Active child plans |
| ---------------- | ----------- | ----------- | -----------------: |
| Walkthrough — "PnL attribution, across every dimension" | `global_ledger_pnl_attribution_master` | **superseded** | **0** |
| Strategy artefacts — promote workflow | `dart_and_promote_master` | **superseded** | **0** |

Both are real documents (250L and 149L), not stubs — but superseded, with nothing hanging off them.

For contrast, the other two zero-todo epics in the same measurement are healthy: `uac_master` (`active`, 6 active
child plans) and `batch_live_symmetry_master` (`active`, 15 active child plans). Their work lives one level down,
which is correct. These two have neither.

## Why it matters

These are **client-facing** sections. If no live epic owns them, nothing tracks keeping them true as the platform
changes — precisely the failure mode that left the artefacts stating a coverage picture the system had outgrown. It
also means T7b will try to reconcile these sections against an owner that does not exist.

## Todos

- [x] ✅ [REVIEW] P1. Per D38 ruling (2026-08-21, autonomous-dispatch authority): check `superseded_by` frontmatter on
      both `global_ledger_pnl_attribution_master` and `dart_and_promote_master` for a successor epic first. Done when:
      for each epic, either a successor is named and cited here, or its absence is confirmed by stating exactly what
      was checked (not inferred from the absence of child plans).
      **Resolved 2026-08-22**: both epic files carry an explicit `⚠️ SUPERSEDED-BY 2026-08-18` banner (checked
      directly in each doc body, not inferred): `global_ledger_pnl_attribution_master.md` and
      `dart_and_promote_master.md` were both folded into
      [`plans/epics/strategy_master.md`](/plans/epics/strategy_master.md) per
      `/codex/11-project-management/epic-taxonomy-2026-08-18.md` (0 corpus references at fold time). `strategy_master`
      is confirmed `status: active` and its own summary explicitly states it "also owns (folded 2026-08-18) the DART
      operator UX cockpit + promote workflow, and the global-ledger + PnL-attribution architecture." A successor
      exists for BOTH epics — same successor for both.
- [x] ✅ [REVIEW] P1. Per D38 ruling (2026-08-21): if no successor exists for either epic (per the todo above), assign
      PnL-attribution/promote-workflow ownership to the shared-mechanism owning epic per the epic-assignment rule
      (asset-group-specific work → the asset-group epic; shared-mechanism work, even found via one asset group → the
      owning epic). Done when: the chosen owning epic is named and cited here, and its frontmatter updated if
      reassigned.
      **N/A 2026-08-22** — the prerequisite condition ("if no successor exists") is false per the prior todo: both
      epics already name `strategy_master` as their live successor, so no shared-mechanism fallback assignment is
      needed. No frontmatter reassignment made; the artefact sections' owning epic is `strategy_master` (already
      declared in that epic's own frontmatter/summary, not newly set here).
- [ ] [DOC] P2. **Record the resolution in the artefact-to-epic coverage map** once that map exists
      ([state_fabric_artefacts](/plans/active/state_fabric_artefacts_2026_08_20.md)), so the next orphan is caught by
      the map rather than by someone re-deriving the mapping by hand.

## Progress Log

**2026-08-20 — filed.** Nothing changed. Found by deriving an artefact-section-to-epic mapping by hand; there is no
machine-readable relation that would have surfaced it automatically, which is tracked separately as the coverage-map
todo on the artefacts plan.

- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — all 3 open todos are genuine judgment work (establish
  whether a successor epic exists per the two superseded epics' `superseded_by` frontmatter, assign an owner per
  the epic-assignment rule, record the resolution once the artefact-to-epic map exists) — none is a bounded,
  worker-determinable outcome without an epic-ownership decision first. Cross-cutting tranche, batch 2 of 3.

**2026-08-21 — ruling D38 (Superseded-epic artefact ownership)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
authority, AUTONOMOUS_AGENT_RULES rule 2): Check for successors first, fall back to shared-mechanism epic
assignment. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.

**2026-08-22 — review, D38 resolved.** Checked both epics' `superseded_by` banners directly (not inferred from
zero child plans): both `global_ledger_pnl_attribution_master` and `dart_and_promote_master` were folded into
`strategy_master` on 2026-08-18, which is `status: active` and explicitly claims both scopes in its own summary.
Successor exists for both — the shared-mechanism-fallback todo is therefore N/A, no frontmatter changed. The
orphan is resolved: the walkthrough's PnL-attribution section and the strategy-artefacts' promote-workflow
coverage are both owned by `strategy_master` going forward. Remaining open todo (record this in the
artefact-to-epic coverage map) stays open — that map is itself still an unbuilt todo on
[state_fabric_artefacts_2026_08_20.md](/plans/active/state_fabric_artefacts_2026_08_20.md) as of this check, so
there is nothing to record into yet.

**2026-08-22 — worker re-check (slot 9), todo 3 confirmed still gated.** Independently re-verified beyond the note
above (which was made in passing while resolving todo 2, not a targeted check of this todo): grepped the full
`unified-trading-pm` corpus for the map artifact under every name variant (`artefact-to-epic`, `artefact_epic_map`,
`owns_artefact`, `artefact_sections`, `feeds_artefact`, and the `artifact`-spelling equivalents) and checked
`strategy_master.md` — the confirmed successor epic for both orphaned sections — directly for an
`artefact_sections`-style field. Zero hits anywhere in the corpus beyond this issue doc,
`state_fabric_artefacts_2026_08_20.md`, and the two dispatch-tracking docs that merely reference this todo;
`strategy_master.md` carries no such field. The gating BACKEND P1 todo ("Declare which epic owns which artefact
section") on [state_fabric_artefacts](/plans/active/state_fabric_artefacts_2026_08_20.md) is still `- [ ]`
unchecked as of this check — the map does not exist. Todo left open (flipping it would misrepresent a nonexistent
map as populated); this dispatch skipped with `reason_code: GATED` rather than forced to a false completion.
