---
name: per-agent-worktrees-2026-05-10
overview:
  Roll out per-agent `git worktree` isolation across each operator's local PM clone so the 4 documented multi-parallel-
  agent foot-guns (#1 foreign work bundled in, #2 path-arg masking on diff --cached, #3 concurrent-agent reset wiping
  staged renames, #4 prek auto-restore race wiping in-flight Edits) become unrepresentable by construction. Promoted
  pre-cutover per operator directive 2026-05-09 ("agent paralel flow is the ssot we will do this for forseeable future
  needs to ebe tight").
type: infra
plan_type: infra
asset_group: cross-cutting
owner: ikenna
status: draft
priority: P0
created: 2026-05-10
last_updated: 2026-05-10
deadline: 2026-05-23
parent: codex_vs_citadel_infrastructure_audit_2026_05_10
related_plans:
  - plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md
  - plans/active/issues/codex_vs_citadel_blocks_cdef_audit_findings_2026_05_10.md
related_codex:
  - cursor-configs/CLAUDE.md
locked_by: live-defi-rollout
locked_since: 2026-05-10
---

# Per-agent worktrees — eliminate the 4 multi-parallel-agent foot-guns by construction

## Why this plan exists

**Operator directive 2026-05-09**: *"agent paralel flow is the ssot we will do this for forseeable future needs to ebe
tight"*. Multi-parallel-agent flow IS the workspace SSOT. The foot-guns documented in CLAUDE.md "The mandatory
pre-commit check" + "Foot-gun #4 — auto-revert hook racing your edits" exist because all agents on one operator's
machine share the same `.git/` + `.git/index` + working tree. Per-agent `git worktree` isolation eliminates the shared-
index + shared-working-tree race surface entirely.

**Block D3** in [`plans/active/issues/codex_vs_citadel_blocks_cdef_audit_findings_2026_05_10.md`](issues/codex_vs_citadel_blocks_cdef_audit_findings_2026_05_10.md)
documents the audit: 4 foot-guns, ~150 lines of pre-commit-discipline rules in CLAUDE.md + per-shippable-unit commit
cadence + pathspec commit form + EOD scoreboard discipline are all band-aids on the cause. Worktrees are the cause-
side fix.

## Pre-audit / blast radius

- **Affects**: each operator's local clone of every workspace repo (PM in particular, since PM is the most contested
  due to plans/ + codex/ + cursor-configs/CLAUDE.md churn from every parallel agent). Other repos benefit too.
- **Doesn't affect**: GitHub remote state, CI, agent prompts, sub-agent inheritance, the per-side orchestrator
  ledgers (those bifurcated ledgers per
  [`harsh_orchestrator/_agent_pings.md`](../../harsh_orchestrator/_agent_pings.md) +
  [`ikenna_orchestrator/_agent_pings.md`](../../ikenna_orchestrator/_agent_pings.md) stay).
- **Doesn't affect**: cross-side coordination (Ikenna ↔ Harsh banners, hard-gate handshakes — those happen via origin
  fetch + push, no shared local tree between operators).

## Phased execution DAG

```
Phase 0 (1h)        Phase 1 (1d)         Phase 2 (2-3d)             Phase 3 (1d)         Phase 4 (1h)
spike-on-PM   →   bootstrap-script  →   per-agent-rollout       →   CLAUDE.md trim  →   sign-off
   ┃                  ┃                      ┃                          ┃                  ┃
proof one         add-worktree.sh        operator switches all    delete band-aid       audit doc
agent runs        + per-side             tabs to per-agent        rules; codify         green
in worktree;      directory layout       worktrees                worktrees as SSOT
foot-guns
unrepresentable
```

## Phase 0 — Spike on PM (1h, 1 agent)

- [ ] [SCRIPT] P0. Create `.cursor-worktrees/` at workspace root; add to top-level `.gitignore` if not already.
      Manually `git -C unified-trading-pm worktree add ../.cursor-worktrees/agent-spike live-defi-rollout`.
- [ ] [SCRIPT] P0. Open Cursor in `.cursor-worktrees/agent-spike/`; verify it's a separate working tree with isolated
      `.git/index` (run `git status` from both — they're independent).
- [ ] [SCRIPT] P0. Edit a file in spike worktree; commit; push. Verify it lands on origin without affecting the main
      clone's index.
- [ ] [SCRIPT] P0. Document spike outcome (success/failure + any surprises) in this plan's done-block.

## Phase 1 — Bootstrap script (1d, 1 agent)

- [ ] [SCRIPT] P0. Write `unified-trading-pm/scripts/dev/setup-agent-worktrees.sh`:
      - Takes `--agent-tag <tag>` (e.g. `tab1-cefi-master`).
      - Creates `${WORKSPACE_ROOT}/.cursor-worktrees/${AGENT_TAG}/` for each repo in `workspace-manifest.json`
        `repositories` (active only — exclude `archived_into`-flagged entries).
      - Each repo's worktree points at the same `live-defi-rollout` branch with isolated index.
      - Idempotent — re-running doesn't double-create or corrupt existing worktrees.
- [ ] [SCRIPT] P0. Add `unified-trading-pm/scripts/dev/teardown-agent-worktrees.sh` companion (same contract;
      `git worktree remove`).
- [ ] [SCRIPT] P0. Update `unified-trading-pm/scripts/workspace-bootstrap.sh` to optionally provision a default
      operator-tag worktree at first-run.
- [ ] [SCRIPT] P0. Add bash-syntax + idempotency tests to PM `scripts/quality-gates.sh`.
- [ ] [SCRIPT] P0. Document the script in `codex/05-infrastructure/per-agent-worktrees.md` (NEW codex doc — single
      page: shape + bootstrap recipe + foot-gun mitigation evidence).

## Phase 2 — Per-agent rollout (2-3d, operator-driven, both sides)

- [ ] [AGENT] P0. Ikenna's main + each spawned tab: switch to its own `.cursor-worktrees/<tab-tag>/` worktree.
      Document the per-tab tag mapping in
      [`ikenna_orchestrator/LEDGER.md`](../../ikenna_orchestrator/LEDGER.md) bootstrap section.
- [ ] [AGENT] P0. Harsh's main + each spawned tab: same — document in
      [`harsh_orchestrator/LEDGER.md`](../../harsh_orchestrator/LEDGER.md).
- [ ] [AGENT] P0. Verify foot-guns #1-#4 fail to fire in 1-week burn-in (each operator runs their normal cadence;
      track any foot-gun-shaped incident in the plan body).

## Phase 3 — CLAUDE.md trim (1d, 1 agent)

- [ ] [SCRIPT] P0. Edit `cursor-configs/CLAUDE.md` "The mandatory pre-commit check" section: replace ~150 lines of
      foot-gun #1/#2/#3/#4 mitigation discipline with a ~30-line shape: "Each agent operates in its own worktree per
      `codex/05-infrastructure/per-agent-worktrees.md`. Pre-commit check is `git status` only (full); the foreign-
      bundling foot-guns are unrepresentable in a per-agent worktree."
- [ ] [SCRIPT] P0. Update `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` (symlink target — same edit applies via
      symlink).
- [ ] [SCRIPT] P0. Add a 1-line "if you're seeing foot-gun-shaped behaviour, you're not in a worktree — re-bootstrap
      via `setup-agent-worktrees.sh`" troubleshooting note.

## Phase 4 — Sign-off (1h)

- [ ] [AGENT] P0. Audit doc green: spawned audit plan
      [`codex_vs_citadel_infrastructure_audit_2026_05_10.md`](codex_vs_citadel_infrastructure_audit_2026_05_10.md)
      Phase 4 row for D3 flips to `- [x]` with this plan's sha.
- [ ] [AGENT] P0. Master plan
      [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) Group E (operability) row updated
      with worktree-rollout evidence.

## Done definition

1. `setup-agent-worktrees.sh` ships + idempotent + tested.
2. `codex/05-infrastructure/per-agent-worktrees.md` ships as canonical SSOT.
3. Both operators' per-agent tabs run in their own worktrees with documented tag mapping in their orchestrator
   LEDGERs.
4. CLAUDE.md "mandatory pre-commit check" section trimmed by ~120 lines (the band-aid mitigations of the now-
   unrepresentable foot-guns).
5. 1-week burn-in evidence: zero foot-gun #1-#4 incidents reported on the per-side orchestrator pings.
6. Audit doc + master plan rows green.

## Cost vs benefit

- **Cost**: ~3-5 AI-days total (Phase 0-4). One operator drives Phase 1; both operators drive Phase 2; one agent
  drives Phase 3.
- **Benefit (permanent)**:
  - 4 foot-guns become unrepresentable by construction.
  - ~120 lines of CLAUDE.md pre-commit-discipline collapse.
  - Sub-agent rule injection (Block D5) compounds — smaller CLAUDE.md = smaller per-spawn token tax.
  - Operator-experience tightens: zero "I lost my staged work" incidents, zero "git status from another tab swept up
    my files" incidents.

## Risks

- **Risk 1**: Cursor / VS Code multi-root behaviour with worktrees may surprise (e.g. extension state per workspace).
  Mitigated by Phase 0 spike.
- **Risk 2**: prek pre-commit hooks may have shared cache (`~/.cache/prek/patches/`) across worktrees — auto-restore
  race could STILL fire if the cache is shared. Mitigated by Phase 0 spike specifically testing prek behaviour;
  fallback = per-worktree prek cache via `PREK_CACHE_DIR` env override.
- **Risk 3**: Operator may want to switch tab/worktree assignments dynamically. Mitigated by `--agent-tag`
  parameterisation + `setup-agent-worktrees.sh` idempotent re-runs.
- **Risk 4**: Per-side orchestrator ledgers (`harsh_orchestrator/` + `ikenna_orchestrator/`) live in PM — each
  operator's worktrees share PM via the worktree mechanism. Cross-tab concurrent edits to LEDGER.md within the same
  operator's worktree fleet could re-create a small foot-gun surface. Mitigated by per-tab edit discipline (each tab
  edits its OWN LEDGER section) + the bifurcated ping ledger pattern already minimising contention.

## Composes with

- `cursor-configs/CLAUDE.md` "The mandatory pre-commit check" — Phase 3 trims this.
- `codex_vs_citadel_infrastructure_audit_2026_05_10.md` Phase 4 — this plan IS the D3 deliverable.
- `codex_vs_citadel_blocks_cdef_audit_findings_2026_05_10.md` — sibling issue doc.
- `master_to_live_defi_2026_05_23.md` Group E (operability) row — Phase 4 updates evidence.
- D5 (sub-agent rule-injection lift) — Phase 3 trim multiplies D5's per-spawn token saving.

## Full-execution criterion

(per "Plans Run To Actual Completion" HARD RULE)

- ✅ `setup-agent-worktrees.sh` runs on Ikenna's machine + Harsh's machine; produces idempotent worktrees.
  - **Verification**: `git worktree list` per repo shows the agent-tag worktrees alongside the main clone; each has
    independent `.git/index`.
- ✅ At least 1 week of operator-driven work happens in worktrees with zero foot-gun #1-#4 incidents on the per-side
  ping ledgers.
  - **Verification**: grep `_agent_pings.md` history for foot-gun-shaped phrases ("foreign work", "staged rename
    wiped", "prek auto-restore", etc.) — zero hits in the burn-in week.
- ✅ CLAUDE.md trim commit shipped + diff shows ~120 lines removed from the pre-commit-check section.
  - **Verification**: `git -C unified-trading-pm log --stat --oneline cursor-configs/CLAUDE.md` shows the trim
    commit.
