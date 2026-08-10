---
doc_type: issue
title:
  Recovery defence-in-depth Layer-1 PRODUCER deleted as AO-role-cleanup collateral — consuming half (signoff ingest +
  DISPUTE→SAFE_MODE + DART feed) still live but mock-fed; re-home a standalone producer (operator ruling B, DEFERRED)
summary: |
  Surfaced 2026-07-15 during the AO documentation reconciliation (ao_docs_reconciliation_2026_07_15, finding X2).
  `/codex/04-architecture/recovery-defence-in-depth-layers.md` documents Layer-1 of the incident-recovery ladder as a
  live "LLM Recovery-Audit-Signoff agent" — an agent-orchestrator `role: custom, label: recovery-audit-signoff` backed by
  the boot template `agent-orchestrator/agents/recovery-audit.md`. That backing file was **deleted end-to-end**:
  `agents/recovery-audit.md` does not exist, `server/prompts.py`'s `NEVER_LAUNCH` is now `frozenset()` (its only member's
  file is gone), and the sibling SSOT `/codex/04-architecture/agent-orchestrator-overview.md` explicitly documents the
  removal ("the `recovery_audit` kind was removed end-to-end … `agents/recovery-audit.md` deleted"). So two codex SSOTs
  directly contradict each other on a load-bearing recovery/kill-switch component, and the code sides with "removed."
  This is a governance/safety-domain SSOT contradiction, not a cosmetic drift — flagged to the operator per the
  findings-triage HARD RULE. Read-only investigation; no code or contract changed.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [recovery, kill-switch, defence-in-depth, codex-drift, agent-role, ssot-contradiction, operator-decision]
related:
  [
    /plans/archive/2026_08/ao_docs_reconciliation_2026_07_15.md,
    /codex/04-architecture/recovery-defence-in-depth-layers.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
  ]
created: 2026-07-15
author: unknown
last_updated: 2026-07-16
parent_epic: agent_operating_framework_master
priority: P1
source:
  - ao_docs_reconciliation_2026_07_15 Wave-2 (codex/04) agent, code-verified
  - /codex/04-architecture/recovery-defence-in-depth-layers.md (Layer 1)
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
context_scope:
  [
    /codex/04-architecture/recovery-defence-in-depth-layers.md,
    unified-trading-library/unified_trading_library/recovery/agent_action.py,
    alerting-service/alerting_service/api/routes/safety_ops.py,
    alerting-service/alerting_service/gateway/gateway_state.py,
    unified-api-contracts/unified_api_contracts/incident.py,
  ]
---

> **🟢 EXECUTION CONSOLIDATED 2026-07-17** — this doc's open items are now tracked and executed via
> [`ao_open_issues_consolidated_close_out_2026_07_17`](../ao_open_issues_consolidated_close_out_2026_07_17.md)
> (operator-session local plan; verified-live classification table there). Do NOT start work from this doc alone — flip
> items in the plan and mirror them here. This doc stays the detail/evidence record.

> **✅ OPERATOR RULING 2026-07-16 — Option B (re-home the producer). DEFERRED, not descoped.** Layer-1 is being KEPT and
> WILL be rewired: stand up a standalone recovery-audit-signoff **producer** (NOT an AO worker-role) that consumes
> PubSub `agent-recovery-actions` and POSTs to the already-live `POST /safety-ops/signoffs`. **Scheduled LAST** — after
> the in-flight AO dispatch-correctness work (operator 2026-07-16: "that is an important one, we are going to rewire it
> but we will do it at last, not right now"). Codex docs updated 2026-07-16 to state current runtime honestly. This doc
> stays `open` as the tracking item for the rewire.

> **⚠️ The original A/B/C framing below rested on a FALSE premise** ("removed end-to-end") — see **Corrected finding
> (2026-07-16)**. Only the AO worker-role producer was deleted; the entire consuming half of Layer-1 is still live.

## What the docs say vs what the code says

- **`/codex/04-architecture/recovery-defence-in-depth-layers.md` (Layer 1)** — documents a live "LLM
  Recovery-Audit-Signoff agent (agent-orchestrator `role=custom`, `label: recovery-audit-signoff`)", "Agent template:
  `agent-orchestrator/agents/recovery-audit.md`. Registered as `role: custom, label: recovery-audit-signoff`."
- **Code (agent-orchestrator)** — `agents/recovery-audit.md` **does not exist** (directory listing of all 14
  `agents/*.md` role files has no `recovery-audit.md`); `server/prompts.py` —
  `NEVER_LAUNCH: frozenset[str] = frozenset()` (now empty since its only member's backing file is gone);
  `server/routes/agents.py` still name-drops "recovery-audit" in a stale code comment (consistent with a deletion that
  never got a full doc/comment sweep).
- **`/codex/04-architecture/agent-orchestrator-overview.md`** — independently documents the removal: "the
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

## Corrected finding (2026-07-16) — the deletion was NOT end-to-end

Deeper code verification (2026-07-16) shows the original framing above was **incomplete**. What was actually deleted is
**only the agent-orchestrator `recovery-audit` worker-role boot template** — i.e. the Layer-1 **producer**. The
`agent-orchestrator-overview.md` "removed end-to-end" claim is scoped to the **AO agent-kind roster** (it sits in the
same paragraph as `escalate`→`cicd` and the `usage_reporter` deletion) — it is about AO plumbing, not the safety layer.

**The entire consuming half of Layer-1 is still live:**

| Component                        | Where                                                                              | State                                                     |
| -------------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------------------- |
| Signoff **ingest**               | alerting-service `POST /safety-ops/signoffs` (`api/routes/safety_ops.py`)          | LIVE — "Ingest a RecoveryAuditSignoff from the LLM agent" |
| DISPUTE / ESCALATE **actuation** | alerting-service `gateway/gateway_state.py` (`DISPUTE_AUTOMATED_ACTION`→SAFE_MODE) | LIVE                                                      |
| Signoff **contract**             | UAC `RecoveryAuditSignoff` / `SignoffVerdict` (4-value closed set)                 | LIVE                                                      |
| DART **verdict feed**            | `GET /safety-ops/recovery-audit-signoffs` + `llm-audit-verdicts-feed.tsx`          | LIVE but returns `_mock_signoffs()`                       |
| Layer-0 action publish           | UTL `recovery/agent_action.py` → PubSub `agent-recovery-actions`                   | LIVE                                                      |
| **Producer (the audit agent)**   | was AO role `agents/recovery-audit.md`                                             | **DELETED — no replacement**                              |

**Net runtime impact:** Layer-0 still acts and still publishes actions; nothing AI-audits them in real time; the DART
verdict feed shows mock data. A wrong automated recovery action is caught only at **Layer-5 human audit-ack** — the
automated `DISPUTE`→SAFE_MODE tripwire does not fire. This is a **half-dismantled safety layer (regression)**, not a
clean intentional descope — which is why the ruling is B, not A.

## Options (operator decision) — RESOLVED 2026-07-16 → **B**

- ~~**A — Intentional drop**~~ — REJECTED: rests on the false "removed end-to-end" premise; would ratify a producer-less
  safety layer and contradict the live alerting-service gateway.
- **B — Re-implement / re-home the producer** ✅ **CHOSEN (deferred to last)**. Note the corrected shape: do **not**
  re-create `agents/recovery-audit.md` or restore the AO worker-role (dropping it from the AO fleet roster was correct).
  Stand up a **standalone** producer that consumes `agent-recovery-actions`, decides a `SignoffVerdict`, and POSTs to
  the existing `/safety-ops/signoffs`. The expensive ~90% (contract, ingest, actuation, UI) already exists.
- ~~**C — Defer**~~ — superseded; the docs now carry an accurate banner and B is committed (just scheduled last).

## Mitigation applied 2026-07-16

The 2026-07-15 Progress-Log entry below claimed a `⚠️ CODE-DRIFT` banner was added to
`recovery-defence-in-depth-layers.md` — that edit **never landed** (local-only, unpushed; `rg CODE-DRIFT` on that file
returned zero hits on 2026-07-16). An accurate banner has now been added for real, plus a scope-clarifier in
`agent-orchestrator-overview.md` so its "removed end-to-end" line can no longer be misread as retiring the Layer-1
function.

**Deferred to the B rewire** (deliberately not done now): clean the stale
`agent-orchestrator/server/routes/agents.py:146` comment that still name-drops `recovery-audit`.

## Todos

- [ ] [BACKEND] P2. **Re-home the recovery-audit-signoff producer (Option B)** — stand up a standalone producer (NOT an
      AO worker-role) that consumes PubSub `agent-recovery-actions`, decides a `SignoffVerdict`, and POSTs to the
      already-live `POST /safety-ops/signoffs`; scheduled LAST, after the in-flight AO dispatch-correctness work (see
      "Operator ruling 2026-07-16" above).

## Progress Log

- **2026-07-15** — Filed from the AO doc reconciliation (X2). Code-verified the deletion (`agents/recovery-audit.md`
  absent; `NEVER_LAUNCH=frozenset()`; `overview.md` documents removal). Banner added to the codex Layer-1 section.
  Routed to operator as A/B/C. No code/contract changed.
- **2026-07-16** — **Re-audited before acting on the ruling; the A/B/C premise was FALSE.** The operator initially chose
  A (fix docs / retired-by-design) on the strength of the "removed end-to-end" framing. Pre-edit verification found the
  deletion was scoped to the AO worker-role only: the whole consuming half of Layer-1 is LIVE (alerting-service
  `POST /safety-ops/signoffs` ingest + `gateway_state.py` `DISPUTE`→SAFE_MODE actuation, UAC `RecoveryAuditSignoff`/
  `SignoffVerdict` contract, strategy-service subscriber, DART `llm-audit-verdicts-feed.tsx` — the feed serving
  `_mock_signoffs()`), with only the producer gone. Writing "Layer-1 retired" would have contradicted live code and
  masked a real safety gap, so the doc edit was HALTED and the corrected facts re-escalated. See **Corrected finding
  (2026-07-16)**.
- **2026-07-16** — **Operator ruling: B (re-home the producer), DEFERRED to last.** Rationale: the automated
  DISPUTE→SAFE_MODE tripwire is a genuine safety cross-check that was lost as collateral to an AO-roster cleanup, and
  ~90% of the layer (contract + ingest + actuation + UI) is already built — so re-homing a standalone producer is the
  cheap path back to a whole Layer-1. Sequenced AFTER the AO dispatch-correctness work (operator: current scope is "make
  the AO work properly"). Docs updated to reflect true runtime: accurate CODE-DRIFT banner on
  `/codex/04-architecture/recovery-defence-in-depth-layers.md` § Layer 1 (replacing the 2026-07-15 banner that never
  landed) + scope-clarifier on `/codex/04-architecture/agent-orchestrator-overview.md`'s "removed end-to-end" line. This
  doc stays `open` as the rewire's tracking item. No code/contract changed.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — two established rulings, both confirmed present in the doc: an
  explicit dated **operator ruling 2026-07-16 (Option B, re-home the producer) scheduled LAST** ('we are going to rewire
  it but we will do it at last, not right now'), and a `🟢 EXECUTION CONSOLIDATED 2026-07-17` banner routing execution
  through `/plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md` ('Do NOT start work from this doc alone').
  Not re-litigated.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: trimmed context_scope 7→5 entries (prior pass was over this skill's 2-6 target) —
  dropped `autonomous-recovery-matrix.md` and `agent-orchestrator-overview.md` (background/scope-clarifier reading, not
  build targets) and kept the codex doc the sole open todo updates plus the 4 live components the standalone producer
  (Option B) must integrate with (Layer-0 publish, the ingest endpoint, the actuation gateway, the signoff contract).
  Checked `ao_orphan_audit_followup_triage_2026_07_30.md`'s claim that `ao_satellite_ao_dispatch_batch2_2026_07_30.md`
  already carries a fix for this doc — grep against the live batch2 doc found zero mentions of recovery-audit/this doc,
  so that candidate was NOT added (flagged as a stale pointer on the triage doc instead, not fixed here).
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **fixed 2026-08-06 (/plan-reconcile ao)**: this doc had `## Todos` after `## Progress Log` (inverted vs. corpus
  convention) and the 2026-08-06 na-eligibility-audit entry orphaned after the Todos checkbox, outside any heading.
  Reordered to `## Todos` then `## Progress Log`, and moved the orphaned entry into this log alongside its siblings. No
  content changed, only structure.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (5 entries), still accurate.

- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — explicit dated operator ruling 2026-07-16 (Option B, re-home the
  producer, deliberately sequenced LAST after AO dispatch-correctness work) re-confirmed present and current; sole open
  todo is that deferred rewire, not re-litigated.
- **na-eligibility-audit 2026-08-09 (round11)**: KEEP-NA, valid — checked whether "Option B formally retired" (round7-10
  precedent) applies here: verified it does NOT — that ruling is
  `/plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md`'s unrelated semver-reconciler-mint "Option
  B" (CI/CD release tooling), a same-label coincidence, not the same decision. THIS doc's own Option B (re-home the
  recovery-audit-signoff producer) remains the live, un-retired, operator-chosen path, still deferred pending AO
  dispatch-correctness work. Also re-confirmed: this doc's sole todo is fully claimed by
  `ao_open_issues_consolidated_close_out_2026_07_17.md`'s Phase-LAST `[BACKEND] P0` todo (operator-sequenced),
  consistent with `/ag-closeout-audit ao` batch12's same-day "Covered by an existing active plan (2) — not orphaned"
  verdict for this doc.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` =
  **1**, matching. Explicit, dated operator ruling 2026-07-16 (Option B, re-home the recovery-audit-signoff producer,
  deliberately sequenced LAST after AO dispatch-correctness work) remains current and un-retired — confirmed distinct
  from the unrelated same-label "Option B" semver-reconciler retirement (round11 already ruled this out). Sole todo
  remains fully claimed by `ao_open_issues_consolidated_close_out_2026_07_17.md`'s Phase-LAST todo. Not re-litigated.
