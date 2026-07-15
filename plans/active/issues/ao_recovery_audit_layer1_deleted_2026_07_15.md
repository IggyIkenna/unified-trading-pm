---
doc_type: issue
title:
  Recovery defence-in-depth Layer-1 (recovery-audit-signoff agent) documents a DELETED agent — codex says live, code
  says removed end-to-end (operator decision — intentional-drop vs re-implement)
summary: |
  Surfaced 2026-07-15 during the AO documentation reconciliation (ao_docs_reconciliation_2026_07_15, finding X2).
  `codex/04-architecture/recovery-defence-in-depth-layers.md` documents Layer-1 of the incident-recovery ladder as a
  live "LLM Recovery-Audit-Signoff agent" — an agent-orchestrator `role: custom, label: recovery-audit-signoff` backed by
  the boot template `agent-orchestrator/agents/recovery-audit.md`. That backing file was **deleted end-to-end**:
  `agents/recovery-audit.md` does not exist, `server/prompts.py`'s `NEVER_LAUNCH` is now `frozenset()` (its only member's
  file is gone), and the sibling SSOT `codex/04-architecture/agent-orchestrator-overview.md` explicitly documents the
  removal ("the `recovery_audit` kind was removed end-to-end … `agents/recovery-audit.md` deleted"). So two codex SSOTs
  directly contradict each other on a load-bearing recovery/kill-switch component, and the code sides with "removed."
  This is a governance/safety-domain SSOT contradiction, not a cosmetic drift — flagged to the operator per the
  findings-triage HARD RULE. Read-only investigation; no code or contract changed.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [recovery, kill-switch, defence-in-depth, codex-drift, agent-role, ssot-contradiction, operator-decision]
related:
  [
    ao_docs_reconciliation_2026_07_15.md,
    ../../codex/04-architecture/recovery-defence-in-depth-layers.md,
    ../../codex/04-architecture/autonomous-recovery-matrix.md,
  ]
created: 2026-07-15
last_updated: 2026-07-15
parent_epic: agent_operating_framework_master
priority: P1
source:
  - ao_docs_reconciliation_2026_07_15 Wave-2 (codex/04) agent, code-verified
  - codex/04-architecture/recovery-defence-in-depth-layers.md (Layer 1)
  - agent-orchestrator/server/prompts.py (NEVER_LAUNCH), agent-orchestrator/agents/ (recovery-audit.md absent)
assigned_vm: NA
execution_scope: local-only
resolved_by:
locked_by:
locked_since:
estimate_class: design
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.6
supersedes:
superseded_by:
depends_on:
assigned_role: backend_engineer
drift_direction: advance-code
---

> **🔴 NOTIFY-OPERATOR — recovery/kill-switch domain SSOT contradiction (BLOCKED-OPERATOR-DECISION).** Two codex SSOTs
> disagree on whether the Layer-1 recovery-audit-signoff agent exists; the code says it was deleted. Needs an operator
> ruling: was Layer-1 dropped on purpose, or does it need re-implementing? No code/contract touched by this filing.

## What the docs say vs what the code says

- **`codex/04-architecture/recovery-defence-in-depth-layers.md` (Layer 1)** — documents a live "LLM
  Recovery-Audit-Signoff agent (agent-orchestrator `role=custom`, `label: recovery-audit-signoff`)", "Agent template:
  `agent-orchestrator/agents/recovery-audit.md`. Registered as `role: custom, label: recovery-audit-signoff`."
- **Code (agent-orchestrator)** — `agents/recovery-audit.md` **does not exist** (directory listing of all 14
  `agents/*.md` role files has no `recovery-audit.md`); `server/prompts.py` —
  `NEVER_LAUNCH: frozenset[str] = frozenset()` (now empty since its only member's backing file is gone);
  `server/routes/agents.py` still name-drops "recovery-audit" in a stale code comment (consistent with a deletion that
  never got a full doc/comment sweep).
- **`codex/04-architecture/agent-orchestrator-overview.md`** — independently documents the removal: "the
  `recovery_audit` kind was **removed end-to-end** (`agents/recovery-audit.md` deleted, `NEVER_LAUNCH=frozenset()`, no
  `agent_kind` refs)."

So `overview.md` + code agree the agent is gone; `recovery-defence-in-depth-layers.md` still presents it as a live layer
of the recovery ladder. A reader consulting the recovery SSOT would believe an automated Layer-1 audit-signoff runs — it
does not.

## Why it matters

Layer 1 sits in the incident-recovery / kill-switch defence-in-depth stack (the domain the autonomous-recovery-matrix +
kill-switch rules govern). A documented-but-absent safety layer is a silent gap: either the layer was intentionally
descoped (and the SSOT must say so, so no one relies on it) or it regressed/was dropped and should be rebuilt. Both are
operator calls, not an agent's to silently reconcile.

## Options (operator decision)

- **A — Intentional drop (recommended if descope was deliberate):** confirm Layer-1 automated audit-signoff was removed
  by design; then FIX the doc — rewrite `recovery-defence-in-depth-layers.md` Layer-1 to state the automated agent was
  retired and describe the current (human/other) signoff path, and clean the stale `routes/agents.py` comment. No code.
- **B — Re-implement:** if Layer-1 audit-signoff is still wanted, re-create `agents/recovery-audit.md` + re-register the
  role (restore `NEVER_LAUNCH` membership if that was its guard) — a code+charter task in agent-orchestrator.
- **C — Defer:** leave as-is with a banner (already added to the codex Layer-1 section pointing here) until the recovery
  epic is revisited.

## Immediate mitigation applied 2026-07-15

A `⚠️ CODE-DRIFT` banner was added to the Layer-1 section of `recovery-defence-in-depth-layers.md` pointing at this doc,
so a reader is warned it is not a runnable component pending the operator ruling. (Local edit — not pushed.)

## Progress Log

- **2026-07-15** — Filed from the AO doc reconciliation (X2). Code-verified the deletion (`agents/recovery-audit.md`
  absent; `NEVER_LAUNCH=frozenset()`; `overview.md` documents removal). Banner added to the codex Layer-1 section.
  Routed to operator as A/B/C. No code/contract changed.
