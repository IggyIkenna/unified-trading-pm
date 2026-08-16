---
doc_type: issue
title: plan_reconciler findings — cross-cutting tranche — 2026-08-16
summary: >-
  Daily deep plan-reconciliation run-findings doc for the cross-cutting topic tranche, dispatch agt-3cc834 (slot 11).
  Records hunter-detected candidates, adversarial-verification outcomes, applied fixes, routed operator questions, and
  coverage for this run. Also the progress journal for the run itself.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [role, plan_reconciler, reconciliation, plan-hygiene, cross-cutting, sharded-run]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md,
    /plans/active/issues/plan_reconciler_blocked_answer_and_result_post_gaps_2026_08_16.md,
    /plans/active/issues/plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md,
  ]
created: "2026-08-16"
author: plan_reconciler
source: agt-3cc834
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline: 0.1
calibrated_ai_days: 0.1
assigned_role: backend_engineer
drift_direction: fix
resolved_by:
locked_by: "plan_reconciler (agt-3cc834) since 2026-08-16T17:36:33Z"
locked_since: "2026-08-16T17:36:33Z"
depends_on: []
context_scope: [/plans/active/cross_cutting_consolidated_closeout_2026_07_25.md]
---

# plan_reconciler findings — cross-cutting tranche — 2026-08-16

Dispatch `agt-3cc834`, slot 11, tranche `cross-cutting`. PM head at run start: `effde0f7d5`.

## Scope

150 docs carry `asset_group: cross-cutting` in `plans/active/` (incl. `issues/`). **36 of 150 are inside the 12-hour
grace window** — read-only context this run, not written. **114 are workable** (~3.39MB), partitioned into 10
size-balanced batches (~285-415KB / 11-12 docs each) for full-coverage hunter reading, 2 waves of ≤5 parallel (see
Phase -1 note on the stale "≤10 parallel" figure below).

## Phase -1 (prior findings reconciliation)

- `plan_reconciler_findings_cross_cutting_2026_08_10.md` — extensively closed out by a 2026-08-15 follow-up session,
  but its own 2026-08-15 Progress Log claim **"Every open todo in this doc is now closed; 0 remaining" is FALSE**:
  `Item C` (`- [ ] [DOC] P2. Item C — rewrite /codex/02-data/external-data-always-available-rule.md`) is still
  visibly unchecked in the doc's own Todos section. A false-closure contradiction — exactly the class this skill
  exists to catch, just aimed at its own prior output. Not archived (still has 1 genuinely open item). Item C itself
  is a codex-SSOT multi-part rewrite (explicitly "not a single substitution" per its own text) — does not qualify for
  the STEP-5.f2 mechanical carve-out, so it stays operator-gated regardless of trust mode. Routing via `/blocked` this
  run with a drafted recommendation (see Filed).
- `plan_reconciler_blocked_answer_and_result_post_gaps_2026_08_16.md` (same-day, `ao` tranche, agt-3eb42b/slot 28) —
  documents 2 live infra gaps this run must work around: (1) `/api/plan-health/result` may reject an empty/omitted
  `X-Orchestrator-Secret` despite documented loopback-trust; (2) a `/blocked` answer may not reliably surface via
  `GET /api/slots/<N>/messages`. This run will not treat either as blocking — STEP 7's result POST failure (if
  reproduced) will not gate `/done`, and STEP 8 will re-check target docs directly rather than relying solely on
  `/messages` polling.
- `plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md` — dead-lock auto-clear was RULED (Option A, 2026-08-15) but
  the backend wiring is still an open `[BACKEND] P1` todo (not yet implemented). If this run hits a locked doc, will
  verify liveness manually (no live tmux session / no recent commits / AO-confirmed reaped-stale) before treating a
  lock as dead, per the same precedent prior sessions used.
- **Doc-drift noted, not self-fixed**: `agents/plan_reconciler.md` STEP 0/3 and
  `cursor-configs/skills/plan-reconcile/SKILL.md` Phase 1 both still say "≤10 parallel" for hunter/verifier fan-out.
  `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` § "When YOU spawn sub-agents" caps it at **5**, citing an explicit
  2026-08-10 operator ruling on host oversubscription (shared ~10-core box, ~4 concurrent slots). This run follows
  the more recent, more specific, safety-motivated cap (5) and flags the stale "10" in the two former docs as a
  finding rather than self-editing them (outside `plans/**`, barred by this skill's own STEP-0 rule).

## Flips verified

(in progress — see Progress Log)

## Contradictions

(in progress)

## Doc-drift

(in progress)

## Codex corrections applied (mechanical, evidence-cited)

(none yet)

## Hygiene fixes

(in progress)

## Filed

1. **Item C from `plan_reconciler_findings_cross_cutting_2026_08_10.md`** —
   `/codex/02-data/external-data-always-available-rule.md` step 2 (lines 64-72) still prescribes filing a
   `pings/slot_<N>.md` operator-credential request. **Confirmed stale**: `unified-trading-pm/agents/RULES.md` § 6
   ("Orchestrator HTTP surface — what you do NOT do anymore") explicitly states file-based orchestration
   (`pings/slot_<N>.md`) was REPLACED by the HTTP surface — `POST /api/slots/<N>/blocked` is the current mechanism
   (used live by this very run). **[WORKER REC] concrete replacement for step 2**:

   ```
   2. **File a credential request via `POST /api/slots/<N>/blocked`** (the ping-file mechanism -- `pings/slot_<N>.md`
      -- was RETIRED; file-based orchestration was replaced by the agent-orchestrator HTTP surface, see
      `unified-trading-pm/agents/RULES.md` § 6). Use the standard escalation shape (options + a marked
      recommendation, per `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` § "When escalating a question to the
      operator"):
      ```
      {
        "task_id": "<dispatch_id>",
        "question": "CREDENTIAL APPROVAL REQUEST -- <adapter_name>. Vendor: <name + tier + cost estimate>. What I
          need: <API key | OAuth flow | account email + signup | hardware-2FA setup>. Account to use: <existing
          operator email | new account needed>. Unblocks: <asset_group x archetype combos + which gate>. Without
          it: integration tests skip; unit + scaffold ship + adapter is dormant.",
        "options": ["A: approve -- <shortest safe path> [WORKER REC]", "B: use an alternative vendor: <name>"],
        "recommendation": "A",
        "can_continue": true,
        "continue_on": "<what proceeds while waiting>"
      }
      ```
   ```

   **NOT independently confirmed this run**: Item C's second claim (a "stale cross-link to an archived doc") — the
   only cross-link in the current doc body is `master_to_live_defi_2026_05_23.md` (line 75), which this run's own
   STEP 1 observed as still `plans/active/` (a grace-window plan, not archived). Not proposing a fix for this half
   without independent confirmation — routing as-is via `/blocked` for the operator to confirm/correct.
   Multi-part (mechanism rewrite + an unconfirmed second claim) — does not qualify for the STEP-5.f2 mechanical
   carve-out, routed via `/blocked` per Modes § Calibration ("blast radius" gate on any codex/CLAUDE.md edit, applies
   regardless of trust mode). **RESOLVED 2026-08-16T18:04Z**: operator answered `BLK-a8e6b715` = **A** (via
   `/api/activity`, not `/messages` — reproduces the known Gap 2 retrieval issue live, see Phase -1 note above).
   Applied: rewrote `/codex/02-data/external-data-always-available-rule.md` step 2 per the drafted text above;
   flipped Item C `[x]` in the 2026-08-10 doc with citation. Left the master_to_live_defi cross-link untouched per
   the ruling.

## Archive candidates (operator review)

1. `plan_reconciler_findings_cross_cutting_2026_08_10.md` — Item C (its last open todo) flipped this run (see Filed
   #1 / Progress Log below); doc now has 0 open todos, unlocked. ARCHIVE-READY — deferred to later in this run's
   STEP 5 pass (referrer sweep not yet done).

## Refuted (dropped by verify)

(none yet)

## Coverage (hunters / batches / docs)

10 batches prepared (114 non-grace docs, ~3.39MB), 2 waves of ≤5 parallel hunters planned. Wave status tracked in
Progress Log as it proceeds.

## Plans not reached

(none yet)

## Progress Log

- **2026-08-16T17:36Z (run start)**: dispatch `agt-3cc834`, slot 11. RULES.md + plan_reconciler.md read. STEP 1
  hygiene inputs gathered: corpus-wide hygiene sweep shows 2 hard ratchet failures (reference-path-convention,
  assigned_vm:NA corpus size) + 1 soft warning (delete/VM-launch tagging) — all 3 are standing, previously-tracked
  ratchets/ candidate-signals, not new regressions introduced by this run (confirmed via digest re-run). INDEX.md ↔
  active-plans drift (17 docs) noted from the digest but none of the 17 filenames match this tranche's inventory —
  not chased. Phase -1 prior-findings check complete (see section above): 1 false-closure contradiction found in the
  cross-cutting 2026-08-10 doc, 2 live infra gaps + 1 stale-lock-mechanism note absorbed as run-conduct context, 1
  parallel-cap doc-drift flagged. Tranche inventory: 150 docs, 36 grace, 114 workable. Bin-packed into 10 batches.
  About to launch Wave 1 (5 batch hunters).
- **2026-08-16T17:46Z (lock commit landed + near-miss recovered)**: `unified-trading-pm@08a5cfe934` (this doc) landed
  via `scripts/dev/safe-doc-push.sh` under heavy fleet churn (branch moved twice in ~90s; the script's own
  contention-hardening handled it after 2 plain-git attempts failed on branch-drift). The push run reported exit 9
  (orphaned prek patch, a documented near-miss class per
  `safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md`): a patch containing a DIFFERENT slot's
  small in-progress edit (`drift_direction`/`depends_on` frontmatter additions to
  `plan_reconciler_findings_prediction_2026_08_16.md` and `prosewrap_padding_baseline_climbing_recheck_2026_08_16.md`
  — neither owned by this run) had not been restored to the working tree after this run's own prek hook cycle.
  Verified `git status --porcelain` was otherwise clean (this run's own content intact), then `git apply --check` +
  `git apply` restored the foreign patch to the working tree only (left uncommitted, unstaged — not this run's work
  to commit), then removed the now-applied patch file. No content lost; flagging as a live recurrence of the known
  class for whoever next reads that tracked issue doc.
