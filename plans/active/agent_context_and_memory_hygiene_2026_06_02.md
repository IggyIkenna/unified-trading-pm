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

## Phases

### Phase 1 — Map the actual context-feed graph (audit-first, no edits) [P0]

- [ ] [DOC] P0. Determine exactly which files land in a fresh agent's context, per repo + for the orchestrator slot
      bootstrap. Resolve the two-path question (`/active/...` vs `/home/hk/...` checkouts) and whether `.claude/rules/*`
      are symlinks to PM `cursor-configs/` (`setup-workspace-config-symlink.sh`) or independent copies. Output a
      one-screen table: file → source-of-truth → is-symlink → is-fed-to-agents.
- [ ] [DOC] P0. Diff `cursor-configs/CLAUDE.md` vs `.claude/rules/CLAUDE.md`. Decide SSOT. If the root copy is a rotted
      duplicate, the fix is a symlink (or deletion + regen via the symlink script), **not** hand-editing both —
      eliminate the second source of truth entirely. No parallel copies (universal rule).

### Phase 2 — Trim `cursor-configs/CLAUDE.md` to budget [P0]

- [ ] [DOC] P0. Section-by-section: keep the 1-line essence + SSOT pointer, push detail to the named codex doc (the
      file's own stated method). Target ≤400 lines / ≤25 KB. Do NOT delete a rule — relocate its body to its codex SSOT
      and leave the pointer. Fix the false "now ~400 lines" self-description in the header.
- [ ] [DOC] P1. While trimming, flag any pointer to a deleted/renamed file or flag (grep-verify each path/script named
      in a rule still exists — the "verify before recommending" discipline). Dead pointer → fix or drop.

### Phase 3 — Contradiction sweep [P0]

- [ ] [DOC] P0. Grep CLAUDE.md + `.claude/rules/*.md` + `SUB_AGENT_MANDATORY_RULES.md` + `cursor-rules/*.mdc` for facts
      the recent churn invalidated. Known candidates to verify: (a) **agent-orchestrator branch** — chat confirms AO
      targets `main` not LDR and this is now codified; ensure no rule still says the opposite. (b) **bucket naming /
      data_type names** post-v9-canonical (`pipeline_mode=`, `asset_group=`, dex pool/swap on-disk names). (c) removed
      DeFi venues (SOLAYER/PICASSO/CAMBRIAN) not still listed as supported. (d) any `category=` vs `asset_group=`
      residue. (e) **merge flow** (verified 2026-06-02) — `quickmerge.sh` now routes ALL commits → `staging` by default
      (`--to-staging` is a no-op) → SIT → `main`, yet `.claude/rules/workspace-workflow.md` still says "staging =
      breaking changes" and `cursor-configs/CLAUDE.md` says "quickmerge for promotion-to-main" + "DO NOT quickmerge
      dirty deps → push live-defi-rollout"; reconcile to the live staging-first model + the LDR dual-path (continuous
      push to LDR vs quickmerge→staging on unit-done). Each contradiction → fix at SSOT + note in this plan.

### Phase 4 — `SUB_AGENT_MANDATORY_RULES.md` drift check [P1]

- [ ] [SCRIPT] P1. Diff all 21 repo copies against the cursor-configs SSOT; any drift → re-run the rollout/inject
      mechanism (`scripts/agents/inject-mandatory-rules.sh` lineage) so all copies match. Confirm content is still
      current after the v9 / AO-auth / quickmerge changes.

### Phase 5 — User-level memory prune [P1] _(local-only; not git-tracked)_

- [ ] [DOC] P1. Walk the 42 memory files. **Delete** status/rot memories (my own `feedback_no_status_memories` rule):
      e.g. `project_sports_vms_in_flight` (2026-05-01, almost certainly stale), and any reference-baseline memory whose
      numbers have since moved. **Verify** every memory that names a file/flag still resolves; fix or delete if not.
      Reconcile `MEMORY.md` index to match the surviving files. Keep durable `user`/`feedback` facts. This is a local op
      — report the before/after count, nothing to commit.

### Phase 6 — `cursor-rules/*.mdc` relevance pass [P2]

- [ ] [DOC] P2. Audit the large `.mdc` rules (`component-patterns` 273L, `dimensional-grid-spec` 130L,
      `ui-quality-gates` 169L) for staleness vs current UI/SSOT. Trim or repoint; don't delete a live rule.

## Full-execution criterion (PLAN_FORMAT §8)

- `cursor-configs/CLAUDE.md` ≤ 400 lines / 25 KB, header self-description accurate.
- Exactly **one** CLAUDE.md source of truth (root duplicate resolved to symlink or removed).
- A re-grep contradiction sweep returns **zero** invalidated facts across the context-feed set.
- 21 `SUB_AGENT_MANDATORY_RULES.md` copies byte-identical to SSOT.
- Memory folder pruned, `MEMORY.md` reconciled (before/after counts reported).
- All repo-tracked edits committed + pushed to `live-defi-rollout`; plan checkboxes flipped same turn.

## Continuous verification

- Add/confirm a QG or pre-commit guard that fails if `cursor-configs/CLAUDE.md` exceeds the hard cap (1500L/90KB) — the
  budget regressed once, so enforce it. (Check whether such a guard already exists before adding.)
