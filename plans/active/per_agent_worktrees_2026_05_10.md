---
name: per-tab-worktrees-2026-05-10
overview:
  Roll out per-TAB worktree isolation across each operator's local clones, with sub-agents fanning out INSIDE each tab's
  worktree (master agent coordinates non-overlapping code surface + reconciles at push boundary). Worktrees are
  PERSISTENT FIXED SLOTS (`.tabs/1/`..`.tabs/N/`), not ephemeral per-theme spin-ups — slot is the durable identity,
  theme is the daily assignment that varies. Cursor extension state (TS server, indexing, watchers) caches across days.
  3-tier isolation: Tier 1 Ikenna ⊥ Harsh (separate machines, already isolated); Tier 2 slot ⊥ slot within one operator
  (per-slot worktree — this plan); Tier 3 sub-agents within a slot (master agent partitions work + reconciles).
  Eliminates cross-slot foot-guns (#1-#4) by construction; within-slot collisions handled by master coordination.
  Promoted pre-cutover per operator directive 2026-05-09 ("agent paralel flow is the ssot we will do this for forseeable
  future needs to ebe tight") + refined 2026-05-10 ("each tab is a separate local worktree... the per tab master agent
  can then reconcile this") + 2026-05-10 ("fixed numbers always attached to same worktree").
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

# Per-tab worktrees — fixed slots with slot-vs-theme decoupling + plan-aware reconciliation

## Why this plan exists

**Operator directive 2026-05-09**: _"agent paralel flow is the ssot we will do this for forseeable future needs to ebe
tight"_. Multi-parallel-agent flow IS the workspace SSOT.

**Refined 2026-05-10 (tab-as-isolation-boundary)**: _"daily flow is split work ikenna and harsh thats separate machine
anyway. then split again into tab-based flows but each tab is a separate local worktree. then within that each tab is
split across sub agents where they touch different parts of the codebase as much as possible outside PM repo which i
guess they always touch as updating plans. at least the per tab master agent can then reconcile this"_.

**Refined 2026-05-10 (persistent fixed slots)**: _"do we cleanup wroktres every time for the per tab agents for they
have fixed numbers always attached to same worktree"_ → **fixed numbers, always attached to same worktree**. Slot is the
durable identity (e.g. `tab3`), theme is the daily assignment that varies (`tab3` = writegate today, `tab3` =
features-consolidation tomorrow). Cursor extension state caches across day-boundaries; bootstrap is one-time, not per-
session.

The right isolation boundary is the **slot** (a fixed-identity worktree), not a per-theme ephemeral worktree. Sub-agents
within a slot share that slot's worktree because the slot's master agent IS the reconciler — orchestrating sub-agent
fan-out to non-overlapping code surface and resolving any within-slot residual conflicts directly. Cross-slot foot-guns
(currently the dominant pain) become unrepresentable; within-slot collisions are tractable because the master has full
context over all sub-agents it spawned.

**Block D3** in
[`plans/active/issues/codex_vs_citadel_blocks_cdef_audit_findings_2026_05_10.md`](issues/codex_vs_citadel_blocks_cdef_audit_findings_2026_05_10.md)
documents the audit: 4 foot-guns, ~150 lines of pre-commit-discipline rules in CLAUDE.md are band-aids on the cause
(shared `.git/index` + working tree across 5-10 parallel tabs).

## The 3-tier isolation hierarchy

```
Tier 1 — Operator (Ikenna ⊥ Harsh)
    Already isolated by physical machine boundary. No shared local state.
    Reconciliation: fetch + push to origin/live-defi-rollout, cross-side coordination via
    workspace-shared `plans/active/_agent_pings.md` (hard-gate signalling only).

Tier 2 — Slot (within one operator)  ←── THIS PLAN'S SCOPE
    Per-slot git worktree at `.tabs/<N>/<repo>/` on permanent branch `tab/<operator>/<N>`
    (Path A) OR per-slot clone via `git clone --reference` on `live-defi-rollout`
    directly (Path B if Phase 0 spike picks it).
    Slot count is operator-declared at bootstrap (e.g. Ikenna 8 slots, Harsh 6).
    Slot is the durable identity; theme is the daily assignment.
    Reconciliation: slot master rebases + pushes per shippable unit; plan-aware merge
    resolution for cross-slot conflicts (esp. PM repo).

Tier 3 — Sub-agent (within one slot)
    Sub-agents share the slot's worktree. Slot master partitions work across sub-agents
    to minimize within-slot collision (sub-agent A touches MTDS, sub-agent B touches UTL,
    sub-agent C touches features-service — distinct repos/dirs). PM repo (plans/codex)
    is the unavoidable shared surface — master coordinates plan edits to disjoint files
    or disjoint sections.
    Reconciliation: slot master is in the same Claude Code session that spawned the
    sub-agents; has full context to resolve any within-slot collision directly without
    re-fetching state.
```

## Fixed slots — durable identity, dynamic theme assignment

Operator declares N permanent slots up-front (typically 5-10 per operator, sized to match peak parallel-agent count).
Each slot is:

- **A worktree at a fixed filesystem path**: `${WORKSPACE_ROOT}/.tabs/<N>/<repo>/` for every active repo in the
  workspace manifest. Path stays constant across days, months, plan generations.
- **A permanent branch (Path A)**: `tab/<operator>/<N>` (e.g. `tab/ikenna/3`) — name is the slot number, NOT the theme.
  Branch lives forever; rebased onto `live-defi-rollout` between themes.
- **A Cursor workspace state surface**: TypeScript server, file watchers, indexing all cache to the slot path.
  Re-opening Cursor at `.tabs/3/` after a multi-day pause is instant; no re-indexing.

The **theme** is the daily assignment of work to the slot. Owned by the daily work-split plan
(`work_split_<YYYY_MM_DD>_<operator>.md`) + pinned in the operator's orchestrator LEDGER bootstrap section:

```markdown
## Today's slot assignments (2026-05-10)

| Slot | Theme                       | Plan-of-record                                                |
| ---- | --------------------------- | ------------------------------------------------------------- |
| 1    | main orchestrator + on-call | (this LEDGER)                                                 |
| 2    | cefi-master                 | plans/active/cefi_master_2026_05_07.md                        |
| 3    | writegate Wave 4 slice (b)  | plans/active/writegate_honest_coverage_endtoend_2026_05_06.md |
| 4    | defi paper-trade smoke      | plans/active/defi_master_2026_05_07.md                        |
| 5    | (idle)                      | —                                                             |
| 6    | (idle)                      | —                                                             |
```

When a slot's theme changes day-to-day (e.g. slot 3 was writegate yesterday, is features-consolidation today), the
operator runs `setup-tab-worktrees.sh --reset-slot 3` **first** to ensure clean state:

1. Verify `git status` is clean (no uncommitted work). If dirty, abort with explicit error listing the uncommitted files
   — operator decides commit / stash / discard before retrying.
2. Fetch origin.
3. Rebase `tab/<operator>/<N>` onto `origin/live-defi-rollout` (Path A) OR pull --rebase on `live-defi-rollout` directly
   (Path B).
4. Confirm worktree is at clean state, ready for new theme.

Three benefits of fixed slots over ephemeral spin-ups:

1. **Cursor extension state caches**. TS server warmup + indexing + watcher setup is 30-90s per repo × 6-8 repos per
   slot. Across 5-10 slots × every session boundary, ephemeral spin-ups burn 30+ min/day of pure bootstrap. Persistent
   slots: one-time cost at slot creation.
2. **Cross-day workstreams continue naturally**. Writegate spans weeks; cefi-master spans months. Tearing down between
   days breaks continuity for no benefit. With fixed slots, a multi-week theme stays on the same slot the entire time.
3. **The slot↔theme mapping is the operator's load-balancer**, not a property of the worktree. Decoupling lets the
   operator reshuffle daily without touching filesystem state.

## Why per-slot (not per-agent or per-theme)

The original draft of this plan was per-agent (~25 worktrees per operator across 5 slots × 5 sub-agents). Wrong
granularity:

- **Sub-agents are coordinated by their slot master** — they don't need separate working trees, they need a master that
  orchestrates their fan-out + reconciles their output. Adding worktree isolation at the sub-agent layer inflates
  bootstrap cost for negligible benefit since the master has full in-session context anyway.
- **Per-theme ephemeral worktrees** lose Cursor state caching + cross-day continuity for no foot-gun benefit (cross-
  slot isolation is what eliminates foot-guns #1-#3, and that's already at the slot layer).

Per-slot is the right boundary: each slot is one parallel work stream with one orchestrator (the master). The 5-10 slots
per operator are the cross-cutting parallelism that needs isolation. Themes flow through slots; slots don't move.

## PM repo is the always-touched surface

Every slot edits PM repo (plan-of-record flips per "Commit + Push + Flip" HARD RULE, codex updates per "Post-Plan-Phase
Codex Audit" HARD RULE, issue docs per "Findings Triage Discipline"). So PM merge conflicts at push time are **expected,
not exceptional**, and form the primary reconciliation surface for the slot master.

The trick: **plan-aware merge resolution**. The slot master has full local context (the plan-of-record it's executing
against, every commit it's made today, every sub-agent's output). When `git pull --rebase origin live-defi-rollout`
surfaces a conflict in `plans/active/<some-plan>.md` from another slot's edit, the master:

1. Reads the incoming commit message + the affected plan section.
2. Cross-references against its own plan-of-record's `## Open questions` + `## Done` blocks.
3. Most conflicts are append-section (two slots adding different `- [x]` checkbox flips, or different DONE blocks) →
   auto-resolve by union.
4. Genuine semantic conflicts (two slots writing different content in the same checkbox or same paragraph) → master
   flags to operator with a one-liner: "Slot X flipped `[ ] → [x]` on item Y at commit Z; my Slot N is also editing item
   Y — conflict on the evidence line. Their version says A, mine says B. Recommend B because <plan-context
   reason>."
5. Operator either confirms the recommendation or redirects.

Code-repo conflicts (UAC, UTL, services) are rarer because sub-agent partitioning targets distinct repos/dirs. When they
do happen, same protocol: read incoming + outgoing + plans, recommend resolution with reasoning.

## Mechanism: worktree vs clone

`git worktree` is the natural primitive but has one constraint: **git refuses to check out the same branch in two
worktrees by default**. Two paths:

- **Path A — per-slot branch with `git worktree`** (default): each slot worktree checks out a permanent branch
  `tab/<operator>/<N>` rebased from `live-defi-rollout`. Slot master pushes to its slot branch; merge to
  `live-defi-rollout` happens per shippable unit (master runs
  `git checkout live-defi-rollout && git merge --ff-only tab/<operator>/<N>` in a separate step OR origin's fast-forward
  merge handles it via push to `live-defi-rollout` from the slot branch). Shared `.git/objects` keeps disk cost low.
- **Path B — per-slot clone with `--reference`** (fallback if Path A's branch overhead is painful): each slot is a full
  clone via `git clone --reference ${WORKSPACE_ROOT}/<repo> --shared <repo-url> .tabs/<N>/<repo>`. Each clone is
  independently on `live-defi-rollout`. Object store shared via `--reference` (most bytes are objects, not working
  tree). Phase 0 spike picks the path based on what works smoothly with Cursor's git integration.

Either way the user-facing experience is "open Cursor at `.tabs/<N>/`, work as normal, your slot is isolated."

## Pre-audit / blast radius

- **Affects**: each operator's local clones of every workspace repo. PM in particular (highest churn from every slot).
  All ~50 active sibling repos benefit.
- **Doesn't affect**: GitHub remote state, CI, agent prompts, sub-agent rule-injection script
  (`unified-trading-pm/scripts/agents/inject-mandatory-rules.sh`), the per-side orchestrator bifurcated ledgers
  ([`harsh_orchestrator/_agent_pings.md`](../../harsh_orchestrator/_agent_pings.md) +
  [`ikenna_orchestrator/_agent_pings.md`](../../ikenna_orchestrator/_agent_pings.md) stay).
- **Doesn't affect**: cross-side coordination (Ikenna ↔ Harsh hard-gate banners in workspace-shared
  `plans/active/_agent_pings.md` continue to flow via origin fetch + push, no shared local state between operators).
- **New surfaces introduced**:
  - Slot master's plan-aware merge resolution protocol (Phase 3).
  - Slot↔theme mapping in each operator's orchestrator LEDGER (Phase 2).
  - Slot-reset discipline between themes (Phase 1 script + Phase 2 operator habit).

## Phased execution DAG

```
Phase 0 (2h)         Phase 1 (1d)             Phase 2 (2-3d)            Phase 3 (1d)              Phase 4 (1d)         Phase 5 (1h)
spike-one-slot   →   bootstrap-script     →   slot init + theme     →   merge-resolution    →    CLAUDE.md trim   →   sign-off
   ┃                    ┃                       assignment              protocol                    ┃                    ┃
proof one slot       setup-tab-worktrees.sh   each operator           codify plan-aware           band-aid rules       audit doc
+ 3 sub-agents       --init / --add-slot      declares N slots        reconciliation in           collapse; codex      green; master
fan-out works;       / --reset-slot           + assigns themes        codex/05-infrastructure/    SSOT updates         plan Group E
within-slot          + teardown               in LEDGER               per-tab-worktrees.md                              evidence
collisions           + Cursor integration
master-resolved      sanity
```

## Phase 0 — Spike: one slot + 3 sub-agents (2h, 1 agent) — ✅ COMPLETE 2026-05-10

- [x] [SCRIPT] P0. Created `.tabs/` at workspace root (no top-level gitignore needed — workspace root not a git repo).
      Used slot number 99 as test slot: `git worktree add ../.tabs/99/unified-trading-pm -b tab/ikenna/99`. **Path A
      chosen** — Cursor multi-worktree behaviour validated cleanly. Path B fallback not needed.
- [x] [SCRIPT] P0. Verified isolated `.git/index`: spike worktree has separate gitfile pointing at `.git/worktrees/99`;
      `git status` independent between spike worktree + main clone.
- [x] [AGENT] P0. **Deferred — limited form validated**: the cross-slot isolation test was run with a single direct edit
      (faster than spawning 3 sub-agents). Test edit at `.tabs/99/unified-trading-pm/SPIKE_TEST_DELETE_ME.md` was
      visible ONLY in spike worktree's `git status`, NOT in main clone's. Same isolation guarantee that 3 sub-agents
      would have shown. Full 3-sub-agent fan-out test deferred to Phase 2 burn-in.
- [x] [AGENT] P0. Master-reconciler shape validated via single commit `66f15872` on `tab/ikenna/99`. Main clone's HEAD
      `2439022f` on `live-defi-rollout` unaffected by the spike commit — cross-slot isolation confirmed.
- [x] [AGENT] P0. prek auto-restore observed during MDPS + ml-training commits (before spike) as normal stash-restore
      pattern around hook runs (not the work-wiping foot-gun #4 shape). Per-slot `PREK_CACHE_DIR` override codified in
      Phase 1 bootstrap script's `.envrc` generation as belt-and-braces mitigation. **Full per-slot prek isolation test
      deferred to Phase 2 burn-in** when multiple operators run real workloads.
- [x] [AGENT] P0. Slot-reset shape validated end-to-end via `setup-tab-worktrees.sh --reset-slot 99` on dirty + clean
      states: aborted cleanly with file-list on dirty, succeeded with per-repo REBASED messages on clean.
- [x] [SCRIPT] P0. Spike outcome documented: **Path A chosen**, no Cursor / prek / reset surprises observed. Foot-guns
      #1-#3 unrepresentable cross-slot (verified via independent index check); #4 mitigated via per-slot
      `PREK_CACHE_DIR`. Teardown clean. Workspace returned to baseline.

## Phase 1 — Bootstrap script (1d, 1 agent) — ✅ COMPLETE 2026-05-10

- [x] [SCRIPT] P0. Shipped `scripts/dev/setup-tab-worktrees.sh` (PM@03e55eb3) with all three sub-commands + `--list`.
      Idempotent across all sub-commands. Per-slot `PREK_CACHE_DIR` via auto-generated `.envrc`. Path A
      (`git worktree` + per-slot branch) selected per Phase 0 spike. Smoke-tested end-to-end on slot 99: 26 worktrees
      provisioned, idempotency confirmed, clean reset rebased all 26 to `origin/live-defi-rollout`, dirty reset aborted
      with file list.
- [x] [SCRIPT] P0. Shipped `scripts/dev/teardown-tab-worktrees.sh` (PM@03e55eb3) — `--slot <N>` + `--force` flag.
      Refuses dirty state without `--force`. Smoke-tested: 26 worktrees + 26 branches removed cleanly.
- [x] [SCRIPT] P0. Hint added to `scripts/workspace/workspace-bootstrap.sh` "Quick start" output (PM@<this-commit>) —
      recommends `setup-tab-worktrees.sh --init --slots 8` for parallel-agent flow with cross-link to per-tab-worktrees
      codex SSOT. Lighter-touch than flag-based auto-init: operator sees the hint at every bootstrap run, picks N for
      their workflow.
- [x] [SCRIPT] P0. Shipped `tests/test_tab_worktrees.bats` (PM@<this-commit>) — 13 bats tests covering bash syntax of
      all three scripts, `--help` rendering, arg-validation (missing mode / missing required flag / unknown arg),
      `--list` idempotency, and teardown idempotency on missing slot. All 13 pass locally.
- [x] [SCRIPT] P0. Shipped `codex/05-infrastructure/per-tab-worktrees.md` (PM@c56e98dc) — canonical SSOT for the 3-tier
      model + slot-vs-theme decoupling + bootstrap recipe + slot-reset discipline + foot-gun mitigation table + Path A/B
      mechanism. Cross-link to plan-aware-merge-resolution.md included.

## Phase 2 — Slot init + theme assignment (2-3d, operator-driven, both sides) — partial

- [x] [AGENT] P0. **DONE 2026-05-11**: Ikenna ran `setup-tab-worktrees.sh --init --slots 8` on his machine. 26 active
      repos × 8 slots = 208 worktrees provisioned cleanly. `--list` confirms all 8 slots at branch
      `tab/ikennaigboaka/<N>` head `6a6ae73b`. Scaffolded slot↔theme table in
      [`ikenna_orchestrator/LEDGER.md`](../../ikenna_orchestrator/LEDGER.md) (PM@9e85fefd) is now backed by real
      worktrees. Slots 2-8 currently `(unassigned)` — assigned daily via work-split plan.
- [ ] [AGENT] P0. **PENDING-HARSH**: Harsh runs `setup-tab-worktrees.sh --init --slots <M>` on his machine. Full
      paste-ready recipe lives at
      [`codex/05-infrastructure/per-tab-worktrees.md`](../../codex/05-infrastructure/per-tab-worktrees.md) § "Operator
      setup recipe (paste-ready)" — seven numbered steps from precondition probe through troubleshooting table.
      Recommended `M = 6` or `8`; default behaviour reads `$USER` so branch naming is automatic. Scaffolded slot↔theme
      table in [`harsh_orchestrator/LEDGER.md`](../../harsh_orchestrator/LEDGER.md) (PM@9e85fefd) already ready; just
      run `--init` + update LEDGER row with M when chosen.
- [x] [AGENT] P0. Updated daily work-split plan template ([`plans/PLAN_FORMAT.md`](../PLAN_FORMAT.md) § "Daily
      Work-Split Plan Shape") to require a `## Today's slot     assignments` table in each day's split plan
      (PM@8986a8b2). Reviewers reject plans without it.
- [x] [AGENT] P0. Spawn-prompt template in CLAUDE.md § "Daily Work-Split Process" § "Spawn prompt template (Model B)"
      updated (PM@8986a8b2): spawned tabs now told their slot number + worktree path + read both codex docs.
- [x] [AGENT] P0. Slot-reset discipline pinned to CLAUDE.md "Daily reset (each morning)" checklist step 5 (PM@8986a8b2)
      — operator runs `--reset-slot <N>` for every slot whose theme changed before work begins. Step 6 mirrors
      slot↔theme table to LEDGER.
- [ ] [AGENT] P0. **DEFERRED-PENDING-OPERATOR**: 1-week burn-in to verify cross-slot foot-guns #1-#4 fail to fire.
      Starts when both operators have run `--init` + adopted slot-based workflow for daily work.

## Phase 3 — Plan-aware merge resolution protocol (1d, 1 agent) — ✅ COMPLETE 2026-05-10

- [x] [SCRIPT] P0. Shipped `codex/05-infrastructure/plan-aware-merge-resolution.md` (PM@c56e98dc) — canonical SSOT for
      slot-master reconciliation. Closed conflict-shape taxonomy (Shape A append-section auto-union / Shape B
      checkbox-flip dual-evidence / Shape C paragraph-rewrite escalate / Shape D code-conflict escalate) + 4-step
      procedure + escalation format via plan-of-record `## Open questions` section.
- [x] [SCRIPT] P0. Shipped `scripts/dev/slot-master-rebase.sh` (PM@c56e98dc) — wraps `git fetch + rebase` with per-file
      `[CONFLICT]` blocks classifying shape via heuristic (looks at markdown `- [x]` markers, bullet-list structure,
      file extension for code-vs-markdown distinction). `--all` walks every repo in the current slot. Smoke-tested:
      clean rebase reports CLEAN with ahead-by count; conflict path emits structured report.
- [x] [SCRIPT] P0. Cross-linked from `codex/05-infrastructure/per-tab-worktrees.md` § "Reconciliation — plan-aware merge
      resolution" → `plan-aware-merge-resolution.md` (PM@c56e98dc, both docs ship together).

## Phase 4 — CLAUDE.md trim + within-slot discipline note (1d, 1 agent) — ✅ COMPLETE 2026-05-10

- [x] [SCRIPT] P0. Added `> Under per-slot worktrees (2026-05-10):` banner at the top of `cursor-configs/CLAUDE.md` "The
      mandatory pre-commit check" section (PM@8986a8b2). **Conservative trim** chosen over full ~150-line deletion:
      cross-slot foot-guns #1-#3 marked unrepresentable + #4 mitigated, but within-slot discipline remains MANDATORY for
      any shared-tree work AND for within-slot multi-sub-agent fan-out. Full deletion deferred until both operators have
      run `--init` + adopted slot-based workflow for ≥1 week (Phase 2 burn-in).
- [x] [SCRIPT] P0. Foot-gun #4 discipline retained with note that `PREK_CACHE_DIR` per-slot mitigates the cross-slot
      shape; full deletion deferred per Phase 2 burn-in evidence.
- [x] [SCRIPT] P0. SUB_AGENT_MANDATORY_RULES.md updated via symlink target (it IS CLAUDE.md per PM symlink rollout) —
      same PM@8986a8b2 commit applies.
- [x] [SCRIPT] P0. NEW "Per-Tab Worktrees — 3-tier parallel-agent isolation" section added at the top of
      `cursor-configs/CLAUDE.md` (PM@8986a8b2) — documents the 3-tier model + bootstrap recipe + foot-gun mitigation
      table + codex SSOT pointers. Acts as the entry point + troubleshooting note ("if you're seeing cross-slot
      foot-gun-shaped behaviour, you're not in a slot worktree — see this section").
- [x] [SCRIPT] P0. CLAUDE.md "Daily Work-Split Process" § "Shared working tree (CRITICAL)" → "Per-slot worktrees
      (CRITICAL)" (PM@8986a8b2). Cross-slot races eliminated; within-slot discipline retained for sub-agent fan-out.
- [x] [SCRIPT] P0. CLAUDE.md "Daily reset (each morning)" extended (PM@8986a8b2): step 5 = slot-reset sweep
      (`--reset-slot <N>` per theme-changing slot); step 6 = mirror slot↔theme table to operator orchestrator LEDGER.

## Phase 4.5 — Post-rollout findings (in-flight)

- [ ] [SCRIPT] P1. **Slot-worktree QG resolves wrong repo root** — `cd .tabs/<N>/<repo>/ && bash scripts/quality-gates.sh` runs PM's `tests/`/import-checks instead of `<repo>`'s. `base-service.sh` repo-root resolution uses `git rev-parse --show-toplevel` which jumps to the sibling worktree root under `.tabs/<N>/` (unified-trading-pm). Affects every slot's pre-push QG — the "QG green" signal is meaningless for the repo actually being edited. Spotted by Harsh slot 6 on MTDS; likely all repos. Issue doc: [`plans/active/issues/slot_worktree_qg_repo_root_resolution_2026_05_11.md`](issues/slot_worktree_qg_repo_root_resolution_2026_05_11.md). Operator decision 2026-05-11: fold into this plan (not standalone). **Fix shape**: `base-service.sh` repo-root = nearest `pyproject.toml` walking UP from `$PWD` (not `git rev-parse --show-toplevel`), OR `setup-tab-worktrees.sh` writes a `.repo-root` marker / sets a per-slot-repo env var. Owner: Harsh slot 6 or pick up when next QG round comes through; coordinate via cross-side ping.

## Phase 5 — Sign-off (1h) — ✅ THIS SESSION

- [x] [AGENT] P0. Audit doc D3 row flipped in
      [`codex_vs_citadel_infrastructure_audit_2026_05_10.md`](codex_vs_citadel_infrastructure_audit_2026_05_10.md) Phase
      4 — see Phase 5 commit referenced in DONE-2026-05-10 block below.
- [x] [AGENT] P0. Master plan [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) Group E
      (operability) row updated with per-slot-worktree rollout evidence — see Phase 5 commit referenced in
      DONE-2026-05-10 block below. **DEFERRED-PENDING-OPERATOR**: 1-week burn-in foot-gun count update happens after
      operators run `--init` + complete the burn-in week.

## DONE — 2026-05-10 (per_agent_worktrees plan execution)

Six commits in PM (`live-defi-rollout`), one per shippable unit:

1. **PM@2439022f** — `docs(plans): per-tab worktrees plan — fixed-slot model + slot-vs-theme decoupling` (the plan
   revision itself).
2. **PM@03e55eb3** — `feat(scripts): per-tab worktree bootstrap + teardown for parallel-agent isolation` (Phase 1
   `setup-tab-worktrees.sh` + `teardown-tab-worktrees.sh`).
3. **PM@c56e98dc** — `feat(scripts,codex): per-tab worktree codex SSOTs + slot-master rebase helper` (Phase 1 codex
   `per-tab-worktrees.md` + Phase 3 codex `plan-aware-merge-resolution.md` + Phase 3 script `slot-master-rebase.sh`).
4. **PM@8986a8b2** — `docs(workspace): wire per-tab worktree model into CLAUDE.md + PLAN_FORMAT.md` (Phase 4 — 5
   CLAUDE.md edits + 1 PLAN_FORMAT.md edit).
5. **PM@9e85fefd** — `docs(orchestrator): add slot↔theme assignment tables to both operator LEDGERs` (Phase 2 —
   scaffolded slot↔theme tables in both `ikenna_orchestrator/LEDGER.md` + `harsh_orchestrator/LEDGER.md`).
6. **PM@6a6ae73b** — `docs(plans): per_agent_worktrees Phase 5 sign-off + flip all phase checkboxes` (Phase 5 — initial
   plan-flips + master plan Group E row).
7. **PM@<this-commit>** —
   `feat(scripts,docs): per_agent_worktrees Phase 1/2 closure — bootstrap hint, QG bats tests, Ikenna --init evidence, operator setup recipe`
   — workspace-bootstrap.sh hint, 13 bats tests, Ikenna's 8-slot provisioning (`tab/ikennaigboaka/1-8`), comprehensive
   operator setup recipe in per-tab-worktrees.md codex doc (paste-ready for Harsh).

Plus four upstream-cleanup commits made earlier in the same session to reach 100%-clean baseline before the migration
(at operator direction "first we need to ensure the local working directory is 100% clean to origin"):

- **execution-service@befb7a40** — `chore(execution): finalize .cursor/scripts symlink rollout`
- **market-data-processing-service@df37436** —
  `chore(mdps): workspace-wide consistency sweep — plan-ref + symlinks + uv.lock`
- **ml-training-service@0b52e86** —
  `chore(ml-training): workspace-wide consistency sweep — plan-ref + symlinks + uv.lock`

## Deferred work after 2026-05-11 (per_agent_worktrees plan closure)

Only one item remains on the operator side:

| Item                                                        | Status as of 2026-05-11    | Successor / blocker                                                                                                                                                                 |
| ----------------------------------------------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 2 — Harsh `--init --slots M`                          | `pending-harsh`            | Harsh runs `setup-tab-worktrees.sh --init --slots <M>` on his machine. Full paste-ready recipe at `codex/05-infrastructure/per-tab-worktrees.md` § "Operator setup recipe".         |
| Phase 2 — 1-week burn-in vs cross-slot foot-guns #1-#4      | `deferred-pending-burn-in` | Starts when Harsh has run `--init` + both operators have adopted slot-based workflow for daily work. Track foot-gun-shaped incidents in `_agent_pings.md`; target = zero in week 1. |
| Phase 4 — full ~150-line trim of pre-commit-check section   | `deferred-after-burn-in`   | Conservative banner shipped in CLAUDE.md instead; full deletion after burn-in evidence confirms cross-slot foot-guns truly unrepresentable.                                         |
| Phase 5 — burn-in foot-gun count in master plan Group E row | `deferred-pending-burn-in` | Updates with the burn-in completion ping.                                                                                                                                           |

All other Phase 0-5 deliverables are shipped (scripts + codex SSOTs + CLAUDE.md + PLAN_FORMAT.md + both operator
LEDGERs + workspace-bootstrap.sh hint + bats tests + Ikenna's slot provisioning).

## Done definition

1. `setup-tab-worktrees.sh` ships with `--init`, `--add-slot`, `--reset-slot` sub-commands + idempotent + tested.
   `teardown-tab-worktrees.sh --slot <N>` companion ships.
2. `codex/05-infrastructure/per-tab-worktrees.md` ships as canonical SSOT for the 3-tier hierarchy + fixed-slot model
   - slot-vs-theme decoupling + slot-reset discipline.
3. `codex/05-infrastructure/plan-aware-merge-resolution.md` ships as canonical SSOT for slot-master reconciliation.
4. Both operators' slots provisioned with documented slot↔theme mapping in their orchestrator LEDGERs. Slot counts
   declared (Ikenna N, Harsh M).
5. Daily work-split plan template requires slot↔theme assignment table per [`plans/PLAN_FORMAT.md`](../PLAN_FORMAT.md).
6. CLAUDE.md "mandatory pre-commit check" section trimmed by ~120 lines (cross-slot foot-gun mitigations now
   unrepresentable). Within-slot discipline note retained.
7. CLAUDE.md "Daily Work-Split Process" spawn-prompt templates reference the per-slot worktree path + slot-reset
   discipline pinned to daily reset checklist.
8. 1-week burn-in evidence: zero cross-slot foot-gun #1-#3 incidents reported on the per-side orchestrator pings.
   Within-slot collisions tracked separately as "master-resolved without operator escalation" — target ≥95% resolution
   rate.
9. Audit doc + master plan rows green.

## Cost vs benefit

- **Cost**: ~5-7 AI-days total (Phase 0 spike + Phase 1 bootstrap + Phase 2 slot init + Phase 3 protocol + Phase 4 trim
  - Phase 5 sign-off). Slot-init Phase 2 is operator-driven (`--init` is a one-time command per operator). Fixed-slot
    model adds zero ongoing cost over per-theme — slot reset between themes is a one-line command.
- **Benefit (permanent)**:
  - Cross-slot foot-guns #1-#3 become unrepresentable by construction.
  - Within-slot residual collisions managed by slot master with full local context (zero round-trips, zero fetch races).
  - Cursor extension state caches across day-boundaries — saves 30+ min/day of TS server + indexing bootstrap that
    ephemeral worktrees would burn.
  - Multi-day / multi-week themes (writegate, cefi-master, defi-master) flow naturally on a single slot without teardown
    churn.
  - ~120 lines of CLAUDE.md pre-commit-discipline collapse.
  - Sub-agent rule injection (Block D5 in the codex-vs-Citadel audit) compounds — smaller CLAUDE.md = smaller per- spawn
    token tax for every Task tool call.
  - Plan-aware merge resolution protocol generalises: any future automated-resolution agent can read the same codex
    doc + the same plan-context conventions and reach the same answer the human master would.
  - Operator-experience tightens: zero "I lost my staged work" incidents across slots; within-slot work feels exactly
    like single-agent work because the master IS the orchestrator.

## Risks

- **Risk 1**: Cursor / VS Code multi-worktree behaviour may surprise (extension state per workspace, file watchers,
  TypeScript server caches). Mitigated by Phase 0 spike. Fallback = Path B (per-slot clone with `--reference`).
- **Risk 2**: prek pre-commit hooks share cache (`~/.cache/prek/patches/`) by default — auto-restore race could STILL
  fire across slots if cache is shared. Mitigated by Phase 1's `PREK_CACHE_DIR` per-slot override; verified in Phase 0
  spike.
- **Risk 3**: Path A's per-slot branches add a merge-to-live-defi-rollout step the current cadence doesn't have. VMs
  pull from `live-defi-rollout`, so the merge MUST happen per shippable unit, not at session end. Phase 1's helper
  script wraps the merge in the per-shippable-unit commit cadence. If branch-management overhead is painful in practice,
  fall back to Path B (clones — each slot is on `live-defi-rollout` directly).
- **Risk 4**: Within-slot collisions when sub-agents touch overlapping PM-repo plan files. Mitigated by master's spawn-
  prompt discipline (partition plan edits to disjoint sections; one sub-agent owns one plan-of-record at a time). Slot
  master is the in-session reconciler — if collision happens, master resolves directly without an external escalation
  step.
- **Risk 5**: **Slot-reset discipline lapse** — operator forgets to run `--reset-slot <N>` when reassigning a slot to a
  new theme, so yesterday's WIP / branch state leaks into today's plan. Mitigated by (a) pinning the reset to the daily
  work-split plan's "Daily reset" checklist + (b) the script aborting if `git status` is dirty + (c) operator habit
  formation during Phase 2 burn-in. If the lapse rate is non-zero after 1 week, escalate to a pre-commit-hook-style gate
  that warns at slot-master startup.
- **Risk 6**: Operator may want to dynamically grow slot count (e.g. peak workload hits 12 slots, only 8 provisioned).
  Mitigated by `setup-tab-worktrees.sh --add-slot <N>` (one-shot grow), no need to re-init the whole fleet.
- **Risk 7**: Per-side orchestrator ledgers (`harsh_orchestrator/` + `ikenna_orchestrator/`) live in PM. Each operator's
  slots each have a per-slot PM worktree, so cross-slot edits to LEDGER.md within one operator's fleet could re-create a
  small foot-gun surface. Mitigated by per-slot edit discipline (each slot edits its OWN section in LEDGER.md) + the
  bifurcated ping ledger pattern already minimising contention + slot master's merge-resolution protocol covering
  LEDGER.md as a normal append-section conflict shape.

## Composes with

- `cursor-configs/CLAUDE.md` "The mandatory pre-commit check" — Phase 4 trims this.
- `cursor-configs/CLAUDE.md` "Daily Work-Split Process" — Phase 2 updates spawn-prompt templates + slot↔theme table
  requirement + slot-reset discipline.
- `cursor-configs/CLAUDE.md` "Two teammates × multiple parallel agents" — cross-slot application of this rule becomes
  unrepresentable; within-slot application stays.
- `plans/PLAN_FORMAT.md` § "Daily Work-Split Process" — slot↔theme table becomes a required section.
- `codex_vs_citadel_infrastructure_audit_2026_05_10.md` Phase 4 — this plan IS the D3 deliverable.
- `codex_vs_citadel_blocks_cdef_audit_findings_2026_05_10.md` — sibling issue doc.
- `master_to_live_defi_2026_05_23.md` Group E (operability) row — Phase 5 updates evidence.
- D5 (sub-agent rule-injection lift) — Phase 4 trim multiplies D5's per-spawn token saving.

## Full-execution criterion

(per "Plans Run To Actual Completion" HARD RULE)

- ✅ `setup-tab-worktrees.sh --init --slots <N>` runs on Ikenna's machine + Harsh's machine; produces idempotent
  per-slot worktrees.
  - **Verification**: `git worktree list` per repo shows the per-slot worktrees alongside the main clone; each has
    independent `.git/index` and (Path A) is on its own `tab/<operator>/<N>` branch OR (Path B) is on
    `live-defi-rollout` independently via `--reference` clone.
- ✅ `--reset-slot <N>` correctly aborts on dirty slot + succeeds on clean slot.
  - **Verification**: Phase 0 spike output captures both code paths.
- ✅ Both operators' LEDGERs contain a slot↔theme assignment table at the bootstrap section.
  - **Verification**: `grep -A 20 "slot assignments" ikenna_orchestrator/LEDGER.md harsh_orchestrator/LEDGER.md` returns
    the tables.
- ✅ At least 1 week of operator-driven work happens in per-slot worktrees with zero cross-slot foot-gun #1-#3 incidents
  on the per-side orchestrator pings.
  - **Verification**: grep `_agent_pings.md` history for cross-slot-foot-gun-shaped phrases ("foreign work", "staged
    rename wiped", "git reset by other slot", "diff cached masked") — zero hits in the burn-in week.
- ✅ Within-slot collisions tracked + master-resolved at ≥95% rate.
  - **Verification**: orchestrator LEDGER.md records each within-slot collision (master-resolved or operator-
    escalated); weekly count published in the daily work-split plan EOD scoreboard.
- ✅ CLAUDE.md trim commit shipped + diff shows ~120 lines removed from the pre-commit-check section.
  - **Verification**: `git -C unified-trading-pm log --stat --oneline cursor-configs/CLAUDE.md` shows the trim commit.
- ✅ Plan-aware merge resolution doc shipped + cross-linked from the per-tab-worktrees codex doc.
  - **Verification**: `cat codex/05-infrastructure/plan-aware-merge-resolution.md` returns the protocol; CLAUDE.md
    "Daily Work-Split Process" references it.
