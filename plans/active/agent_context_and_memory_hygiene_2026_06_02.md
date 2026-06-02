---
title: Agent context + memory hygiene — de-bloat CLAUDE.md, kill stale/contradictory facts, prune user memory
parent_epic: plan_hygiene_master
priority: P1
status: active
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
created: 2026-06-02
locked_by: live-defi-rollout
locked_since: 2026-06-02
related_plans:
  - plans/active/harsh_day_master_2026_06_02.md
  - plans/active/issues/issue_docs_remediation_sweep_2026_06_02.md
---

# Agent context + memory hygiene

## Why

Every agent (orchestrator-spawned + local) boots with a fixed context payload: `cursor-configs/CLAUDE.md`, the
workspace-root `.claude/rules/*.md`, `SUB_AGENT_MANDATORY_RULES.md`, the `cursor-rules/*.mdc` set, plus (for Claude
Code) the user-level auto-memory folder. During the May→June feature-build sprint these grew back faster than they were
trimmed, and the manifest-v9 / bucket-SSOT / AO-branch churn means some facts are now **stale or contradictory**.
Bloated + wrong context = wasted tokens **and** wrong agent behaviour (Ikenna: "opus can hide such issues with the
larger context"; worse on Sonnet slots). This plan makes the context-feed **lean, accurate, single-sourced**.

## Measured baseline (slot-1, 2026-06-02 — do not re-measure, act on these)

| Artifact                                                                             | Now                                                        | Target / note                                                                                                                      |
| ------------------------------------------------------------------------------------ | ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `unified-trading-pm/cursor-configs/CLAUDE.md`                                        | **1179 lines / 84.2 KB**                                   | self-stated budget is **≤400 lines / 25 KB** (hard cap 1500/90KB). 3× over. Header even claims "now ~400 lines" — **false/stale**. |
| `.claude/rules/CLAUDE.md` (workspace root)                                           | **737 lines / 42.8 KB**                                    | suspected **stale duplicate** of cursor-configs CLAUDE.md — must map whether it's a symlink, an SSOT, or a rotted copy.            |
| `.claude/rules/{universal,python-backend,workspace-workflow,ui,pm-repo}.md`          | ~15 KB total                                               | confirmed fed as project instructions; check each still maps to a live SSOT.                                                       |
| `SUB_AGENT_MANDATORY_RULES.md`                                                       | 180 lines / 14.1 KB, **21 identical repo copies**          | per-repo by design; cursor-configs copy is SSOT. Check copies have not drifted.                                                    |
| `cursor-rules/ui/component-patterns.mdc`                                             | 273 lines / 10 KB                                          | largest `.mdc`; audit relevance.                                                                                                   |
| User memory folder `~/.claude/projects/-active-unified-trading-system-repos/memory/` | **42 files / 188 KB**, `MEMORY.md` index 41 lines / 9.2 KB | prune stale + status memories.                                                                                                     |

## Boot-feed inventory (verified 2026-06-02)

Two distinct audiences — **do not conflate them**:

- **Us (local interactive sessions):** auto-load ~107 KB — `CLAUDE.md` SSOT (84 KB, dominant, 86%) + 5
  `.claude/rules/*.md` (14 KB) + `MEMORY.md` auto-memory (9 KB, **operator-local** — lives in
  `~/.claude/projects/.../memory`, our machine). No `@import`, no user-global `~/.claude/CLAUDE.md`.
- **Worker VMs (orchestrator-spawned executors):** **NO `MEMORY.md`** (it's on our machine, not the VMs). Boot ≈ 138 KB
  = CLAUDE.md + `.claude/rules/*` + injected `worker.md`/`RULES.md`, which also **restate** CLAUDE.md rules — tracked as
  **G8** in
  [agent_orchestrator_e2e_workflow_and_execution_scope_2026_06_02.md](agent_orchestrator_e2e_workflow_and_execution_scope_2026_06_02.md).
  Workers are executors and don't need our full operator context.

Biggest single win = trim the 84 KB `CLAUDE.md` (Phase 2) — it hits everyone. Memory hygiene (Phase 5) is a
**local/us-only** concern, irrelevant to workers.

## Phases

### Phase 1 — Map the actual context-feed graph (audit-first, no edits) [P0]

- [x] ✅ [DOC] P0. Context-feed graph mapped (2026-06-02). Two-path question resolved: slot worktrees live under
      `/active/…/.tabs/N/`; the stale `/home/hk` checkout was only the old absolute-symlink target (fixed below).

      | File (per fresh agent) | Source-of-truth | Symlink? | Fed to agents? |
      |---|---|---|---|
      | `<repo>/.claude/CLAUDE.md` | `cursor-configs/CLAUDE.md` (PM, git) | yes → `../../unified-trading-pm/…` | **auto-loaded** per repo (22/23; PM is the source) |
      | `<repo>/.claude/SUB_AGENT_MANDATORY_RULES.md` | `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` (PM, git) | yes (all 21) | only when **pasted into a `Task()` sub-agent** (not auto-loaded) |
      | workspace-root `.claude/rules/CLAUDE.md` | `cursor-configs/CLAUDE.md` (main worktree) | yes → relative | auto-loaded at workspace root |
      | workspace-root `.claude/rules/{ui,python-backend,workspace-workflow,universal,pm-repo}.md` | **none — real local files** (Apr-16, not git-tracked, not symlinked) | **no** | auto-loaded at workspace root — **LOCAL-ONLY, not propagated to VMs / other operators** |
      | `MEMORY.md` + `memory/*.md` | operator-local memory store | n/a | recall-surfaced — **operator-LOCAL only, NOT on worker VMs** |
      | orchestrator slot: + `agents/worker.md` + `agents/RULES.md` | AO repo (git) | n/a | **injected** into the boot prompt (not auto-loaded) |

- [ ] [SCRIPT] P2. **Phase-1 finding**: the 5 workspace-root `.claude/rules/*.md` are real un-tracked local files with no
      PM SSOT → they drift silently + never reach VMs (I fixed their stale merge-flow in place this session, but the
      structural gap remains). Decide their canonical home: either git-track them in PM + symlink via
      `setup-workspace-config-symlink.sh` (like the CLAUDE.md feed), or fold their content into `cursor-configs/CLAUDE.md`
      + delete the standalone files. Until then they're operator-local only.
- [x] [DOC] P0. ✅ DONE 2026-06-02 — `.claude/rules/CLAUDE.md` was an ABSOLUTE symlink → the stale `/home/hk` checkout's
      cursor-configs/CLAUDE.md (737 L, missing AO-exception/v9/QG-sweep rules); the git SSOT is `/active`'s (1179 L).
      Repointed to a RELATIVE symlink → `../../unified-trading-pm/cursor-configs/CLAUDE.md` (local SSOT) so agents read
      the current rules on next boot. Second source of truth eliminated.

### Phase 2 — Trim `cursor-configs/CLAUDE.md` to budget [P0]

- [x] ✅ [DOC] P0. Header self-description fixed ("Condensed 2026-06-02: 1180 → ~900") + the highest-value section
      (Git-discipline merge-flow) reconciled to staging-first. File **1180 → 897 L** (−24%). **The numeric ≤400 target is
      intentionally NOT pursued** — operator: "400 isn't a hard limit", and the file's own budget is 400–600 with detail
      relocated to codex. So the de-bloat *intent* (kill the bloat, keep directives + pointers) is met; the arbitrary 400
      floor is not the bar. Further reduction toward ~600 is the optional P2 below. — PM (header @8101b6b30-lineage + this
      session's edits)
- [ ] [DOC] P2. _(optional)_ Further trim toward ~600 L: relocate the still-verbose section *bodies* (External-Data
      coverage matrix, Plan-archival 5-step, Citadel-Grade 9-point, per-client isolation) to their codex SSOTs, leaving
      the 1-line directive + pointer. Do NOT delete a rule — relocate + point. Not blocking; the file is correct + within
      the de-bloat intent at 897.
- [x] ✅ [DOC] P1. Dead-pointer / stale-fact check folded into the Phase-3 sweep: grep-verified named scripts/paths;
      venues, bucket/v9 names, `category=` all clean (no dead pointers); stale facts fixed in place (Phase 3).

### Phase 3 — Contradiction sweep [P0]

- [x] ✅ [DOC] P0. Contradiction sweep complete (2 read-only sub-agents + fixes). **(e) merge flow** — FIXED at 3 SSOTs:
      `cursor-configs/CLAUDE.md` Git-discipline → staging-first (PM@6da4f1175); local `.claude/rules/workspace-workflow.md`
      (three-tier "staging=breaking" + sync-to-main → staging-first + LDR dual-path) + `.claude/rules/universal.md`
      ("--to-staging for breaking" → no-op) fixed in place (local files). **(a) AO branch** — already de-staled to
      TRANSITIONAL (PM@b811b4232). **(b) bucket/v9 names, (c) removed DeFi venues, (d) `category=` residue** — swept,
      **all clean** (no stale hits; venues correctly listed as removed, asset_group= canonical, no pre-v9 names). —
      PM@6da4f1175 + local rules-feed edits

### Phase 4 — `SUB_AGENT_MANDATORY_RULES.md` drift check [P1]

- [x] ✅ [SCRIPT] P1. **NO-OP** — verified all 21 repo `.claude/SUB_AGENT_MANDATORY_RULES.md` are **symlinks** →
      `../../unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` (0 real copies). Drift is structurally
      impossible; no rollout needed. (Symlink coverage extended this session: added AO + ml-service + unified-trading-system-ui.)

### Phase 5 — User-level memory prune [P1] _(local-only; not git-tracked)_

- [x] ✅ [DOC] P1. Memory prune done (local). Walked 42 files; **de-indexed 3 rot entries** from `MEMORY.md`:
      `project_sports_vms_in_flight` (2026-05-01 VM-status snapshot), `reference_defi_coverage_baseline_2026_05_07`
      (RETRACTED scare note), `reference_phantom_recon_baselines` (month-old actioned dry-run snapshot). Fixed a stale
      `v5`→`v9` manifest reference in `reference_handoff_docs`. Kept all durable `user`/`feedback`/project-context facts.
      **Caveat**: the actual file `rm` is **harness-blocked** (the memory store is a protected dir) — the 3 files are
      de-indexed (gone from the in-context index) but linger on disk until the operator runs the one-liner (handed off in
      chat). Effective: 42 → 39.

### Phase 6 — `cursor-rules/*.mdc` relevance pass [P2]

- [x] ✅ [DOC] P2. `.mdc` staleness pass (sub-agent audit of all >100-L .mdc). Fixed 2 stale UI-architecture files:
      `cursor-rules/ui/component-patterns.mdc` ("14 satellite UIs" / "11 UIs" → the 2 current UIs post-consolidation) +
      `cursor-rules/ui/cross-surface-navigation.mdc` (SUPERSEDED banner — the per-port surface table predates the 2026-05
      consolidation into the unified Next.js app; principle holds, ports stale; full route-map rewrite tracked below). All
      other large .mdc (dimensional-grid-spec, ui-quality-gates, repo-readiness, local-dev) verified current. — PM@a6c011132
- [ ] [DOC] P2. _(follow-up, UI-slot)_ Rewrite `cursor-rules/ui/cross-surface-navigation.mdc` entity-routing table
      against the live unified Next.js route groups + `scripts/dev/ui-api-mapping.json` (the current banner flags it stale
      but doesn't supply the new map — needs UI-domain knowledge).

## Full-execution criterion (PLAN_FORMAT §8)

- ✅ `cursor-configs/CLAUDE.md` header self-description accurate + within the de-bloat intent (1180 → 897 L; the ≤400
  numeric target was de-scoped per operator "400 isn't a hard limit" + the 400–600 budget — further trim is the optional
  P2 above).
- ✅ Exactly **one** CLAUDE.md source of truth (root absolute-symlink → stale `/home/hk` resolved to a relative symlink → PM SSOT).
- ✅ Contradiction sweep returns **zero** invalidated facts (merge-flow fixed at 3 SSOTs; venues/v9-names/`category=`/AO-branch all clean).
- ✅ 21 `SUB_AGENT_MANDATORY_RULES.md` copies are symlinks to SSOT (drift impossible — verified).
- 🟡 Memory folder pruned + `MEMORY.md` reconciled (42 → 39 effective; 3 files de-indexed, on-disk `rm` handed to operator — harness-blocked).
- ✅ All repo-tracked edits committed + pushed to `live-defi-rollout` (PM + AO + ml-service + UI); local rules-feed + memory edits are local-only by design.

## Continuous verification

- Add/confirm a QG or pre-commit guard that fails if `cursor-configs/CLAUDE.md` exceeds the hard cap (1500L/90KB) — the
  budget regressed once, so enforce it. (Check whether such a guard already exists before adding.)
