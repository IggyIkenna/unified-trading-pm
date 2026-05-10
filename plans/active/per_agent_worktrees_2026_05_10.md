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

## Phase 0 — Spike: one slot + 3 sub-agents (2h, 1 agent)

- [ ] [SCRIPT] P0. Create `.tabs/` at workspace root; add to top-level `.gitignore`. Manually
      `git -C     unified-trading-pm worktree add ../.tabs/1 -b tab/ikenna/1` (use slot number, not theme tag). Confirm
      Path A works; if Cursor surfaces issues (multi-worktree extension state, etc.) fall back to Path B
      (`git clone     --reference`).
- [ ] [SCRIPT] P0. Open Cursor in `.tabs/1/unified-trading-pm/`. Verify isolated `.git/index` (run `git status` from
      slot 1 worktree AND from the main clone — they're independent).
- [ ] [AGENT] P0. Within the spike Claude Code session, spawn 3 sub-agents in a single message (Task tool, 3 parallel
      blocks): sub-A edits an MTDS file, sub-B edits a UTL file, sub-C edits a PM plan file. All three sub-agents
      operate inside slot 1's worktree.
- [ ] [AGENT] P0. Master reconciles: read all three sub-agents' outputs, commit each as its own shippable unit, push.
      Verify cross-slot isolation by running `git status` in the main clone simultaneously — no cross-contamination.
- [ ] [AGENT] P0. Spike test for prek auto-restore (foot-gun #4): edit a file in slot 1, observe if prek cache
      (`~/.cache/prek/patches/`) is shared across worktrees. If shared, document `PREK_CACHE_DIR` per-slot override as a
      Phase 1 todo.
- [ ] [AGENT] P0. Spike test for slot-reset: simulate "theme switch" — make uncommitted edits in slot 1, attempt
      `--reset-slot 1`, confirm it aborts with clear error. Commit + push, retry `--reset-slot 1`, confirm clean rebase
      onto origin/live-defi-rollout.
- [ ] [SCRIPT] P0. Document spike outcome in this plan's body (chose Path A or Path B; any Cursor / prek / reset
      surprises; foot-gun-shaped behaviour observed or eliminated).

## Phase 1 — Bootstrap script (1d, 1 agent)

- [ ] [SCRIPT] P0. Write `unified-trading-pm/scripts/dev/setup-tab-worktrees.sh` with three sub-commands: -
      `--init --slots <N>`: one-time provisioning. For each slot `i ∈ [1..N]` and each repo in `workspace-manifest.json`
      `repositories` (active only — exclude `archived_into`-flagged entries): runs
      `git -C <repo> worktree add ${WORKSPACE_ROOT}/.tabs/<i>/<repo> -b tab/<operator>/<i>` rebased from
      `live-defi-rollout` (Path A) OR `git clone --reference` (Path B if Phase 0 chose it). Reads operator name from
      `${USER}` or `--operator <name>` override. - `--add-slot <N>`: provision one additional slot (operator grew from 6
      to 7 slots). Same per-repo logic, single slot only. Idempotent (skip-if-exists). - `--reset-slot <N>`: prepare
      slot `N` for new theme. Verify clean `git status` across all repos in the slot; abort with full file-list if
      dirty. Fetch origin; rebase slot branch onto origin/live-defi-rollout (Path A) OR pull --rebase (Path B). Output
      one-line confirmation per repo. - All sub-commands idempotent. Sets
      `PREK_CACHE_DIR=${WORKSPACE_ROOT}/.tabs/<N>/.cache/prek/` in the per-slot `.envrc` / shell hook so each slot has
      its own prek cache (foot-gun #4 mitigation).
- [ ] [SCRIPT] P0. Add `unified-trading-pm/scripts/dev/teardown-tab-worktrees.sh --slot <N>` companion
      (`git worktree     remove` Path A, `rm -rf` Path B). Rarely used — only when shrinking slot count.
- [ ] [SCRIPT] P0. Update `unified-trading-pm/scripts/workspace-bootstrap.sh` to optionally call
      `setup-tab-worktrees.sh     --init --slots <N>` at first-run, with `<N>` defaulted from a per-operator config
      file.
- [ ] [SCRIPT] P0. Add bash-syntax + idempotency tests to PM `scripts/quality-gates.sh`. Tests cover: `--init` twice in
      a row produces no-op; `--add-slot` for an existing slot is no-op; `--reset-slot` on a dirty slot exits non-zero.
- [ ] [SCRIPT] P0. Document the script + the 3-tier hierarchy + the fixed-slot model in
      `codex/05-infrastructure/per-tab-worktrees.md` (NEW codex doc): hierarchy shape + slot-vs-theme decoupling +
      bootstrap recipe + slot-reset discipline + foot-gun mitigation evidence + plan-aware merge resolution protocol
      pointer.

## Phase 2 — Slot init + theme assignment (2-3d, operator-driven, both sides)

- [ ] [AGENT] P0. Ikenna runs `setup-tab-worktrees.sh --init --slots <N>` (operator picks N based on peak parallel
      count; typical 8-10). Adds initial slot↔theme assignment table to
      [`ikenna_orchestrator/LEDGER.md`](../../ikenna_orchestrator/LEDGER.md) bootstrap section. Today's themes carry
      over from the active daily work-split plan.
- [ ] [AGENT] P0. Harsh runs the same `--init --slots <M>` (M may differ from N). Adds initial slot↔theme assignment
      table to [`harsh_orchestrator/LEDGER.md`](../../harsh_orchestrator/LEDGER.md).
- [ ] [AGENT] P0. Update daily work-split plan template ([`plans/PLAN_FORMAT.md`](../PLAN_FORMAT.md) § "Daily Work-Split
      Process") to require a slot↔theme assignment table in each day's split plan. Today's table → carries into LEDGER.
- [ ] [AGENT] P0. Update spawn-prompt templates in CLAUDE.md "Daily Work-Split Process" § "Spawn prompt template (Model
      B)" — add lines: > Your slot is `<N>`. Your worktree is at `${WORKSPACE_ROOT}/.tabs/<N>/`. All work happens in
      that worktree; > sub-agents you spawn share it. Today's theme for slot <N> is `<theme>`; plan-of-record at
      `<path>`.
- [ ] [AGENT] P0. Operator habit: before reassigning a slot to a new theme (typically morning of next day), run
      `setup-tab-worktrees.sh --reset-slot <N>` first. Pin this to the daily work-split plan's "Daily reset" checklist.
- [ ] [AGENT] P0. Verify cross-slot foot-guns #1-#4 fail to fire in 1-week burn-in (each operator runs their normal
      cadence; track any foot-gun-shaped incident in the plan body — within-slot collisions still possible but should be
      master-resolved without escalation).

## Phase 3 — Plan-aware merge resolution protocol (1d, 1 agent)

- [ ] [SCRIPT] P0. Write `codex/05-infrastructure/plan-aware-merge-resolution.md` codex doc — canonical SSOT for how a
      slot master reconciles at `git pull --rebase origin live-defi-rollout` (Path A: merge from slot branch to
      live-defi-rollout) conflicts: 1. **Read the incoming commit** (author slot, commit message, plan reference if
      any). 2. **Read the affected file's plan-of-record context** (which plan owns the file; what stage of
      execution). 3. **Classify conflict shape**: append-section (auto-resolve via union) / checkbox-flip-collision
      (auto-resolve by picking the later flip + appending both evidence lines) / paragraph-rewrite (escalate to operator
      with plan-context recommendation). 4. **For code conflicts** (UAC, UTL, services): identify the consumer plan +
      the upstream contract change. Master cites both plans in the resolution commit message. 5. **Operator escalation
      format**: 5-line summary (incoming commit + sha, my commits + shas, conflict shape, recommended resolution +
      reasoning, ASK).
- [ ] [SCRIPT] P0. Add a helper script `unified-trading-pm/scripts/dev/slot-master-rebase.sh` that wraps
      `git pull --rebase origin live-defi-rollout` with structured conflict reporting (parses `git status` after rebase
      pause, surfaces the conflict shape to the master agent's terminal in machine-readable form).
- [ ] [SCRIPT] P0. Document the protocol in `codex/05-infrastructure/per-tab-worktrees.md` § "Reconciliation" with a
      cross-link to the merge-resolution doc.

## Phase 4 — CLAUDE.md trim + within-slot discipline note (1d, 1 agent)

- [ ] [SCRIPT] P0. Edit `cursor-configs/CLAUDE.md` "The mandatory pre-commit check" section: replace the ~150 lines of
      cross-slot foot-gun #1/#2/#3 mitigation discipline with a ~30-line shape: > Each slot operates in its own worktree
      at `${WORKSPACE_ROOT}/.tabs/<N>/` per > `codex/05-infrastructure/per-tab-worktrees.md`. Cross-slot foot-guns #1
      (foreign bundling), #2 (path-arg > masking), #3 (concurrent reset wipe) are unrepresentable in a per-slot worktree
      because no other slot can > touch your `.git/index`. Pre-commit check is `git status` only (full). > Within-slot
      discipline: sub-agents share their slot's worktree, so if you spawn 3 sub-agents fanning out to > distinct
      repos/dirs, the within-slot residual collision surface is small + master-resolved.
- [ ] [SCRIPT] P0. Keep foot-gun #4 (prek auto-restore) discipline IF Phase 0 spike found per-slot prek cache doesn't
      fully mitigate. If Phase 1's `PREK_CACHE_DIR` override does mitigate, trim #4 too.
- [ ] [SCRIPT] P0. Update `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` (symlink target → same edit applies via
      symlink).
- [ ] [SCRIPT] P0. Add a 1-line "if you're seeing cross-slot foot-gun-shaped behaviour, you're not in a slot worktree —
      re-bootstrap via `setup-tab-worktrees.sh --init`" troubleshooting note in CLAUDE.md.
- [ ] [SCRIPT] P0. Cross-link from CLAUDE.md "Daily Work-Split Process" § "Shared working tree (CRITICAL)" → updated
      section: "Per-slot worktrees per `codex/05-infrastructure/per-tab-worktrees.md`. Cross-slot races eliminated;
      within-slot race surface managed by master. Slot = durable identity; theme = daily assignment in the work-split
      plan + LEDGER bootstrap section."
- [ ] [SCRIPT] P0. Add slot-reset discipline note to CLAUDE.md "Daily Work-Split Process" § "Daily reset (each
      morning)": "Before reassigning a slot's theme, run `setup-tab-worktrees.sh --reset-slot <N>` to verify clean
      state + rebase onto origin/live-defi-rollout."

## Phase 5 — Sign-off (1h)

- [ ] [AGENT] P0. Audit doc green: spawned audit plan
      [`codex_vs_citadel_infrastructure_audit_2026_05_10.md`](codex_vs_citadel_infrastructure_audit_2026_05_10.md) Phase
      4 row for D3 flips to `- [x]` with this plan's sha.
- [ ] [AGENT] P0. Master plan [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) Group E
      (operability) row updated with per-slot-worktree rollout evidence + 1-week burn-in foot-gun count (target: 0
      cross-slot incidents).

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
