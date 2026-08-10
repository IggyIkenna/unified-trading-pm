---
doc_type: codex-ssot
title: Model Tier Selection — Sonnet 5 vs Opus 4.8
summary: >-
  Model-tier + effort selection SSOT — model tier (sonnet/opus/fable) and effort (low<medium<high<xhigh<max) are
  INDEPENDENT axes (ground truth: agent-orchestrator/server/model_tier.py, 2026-07) — effort is the primary reasoning
  control on every adaptive-reasoning model (sonnet/opus/fable alike, Haiku excluded), NOT opus-gated. Model tier:
  default Sonnet for EVERY role including the main orchestrator (operator ruling 2026-08-07, cost-driven — main moved
  `model: opus` → `model: sonnet` + `sonnet_variant: default` via the dashboard's Switch Model lever, see
  agent-orchestrator/server/main_agent_keeper.py::switch_main_model). Opus is no longer a standing role declaration for
  ANYTHING — it survives only as a manual, operator-triggered emergency escalation (dashboard Switch Model / Switch
  Account-style lever, kill+resume, context intact) for a session visibly struggling on Sonnet, never a spawn-time
  default. This supersedes the 2026-08-04 ruling below, which had already narrowed Opus from three qualitative
  categories to one (main orchestrator role); that last category is now ALSO retired as a default. Model tier is also
  NOT a function of raw context size (Sonnet's 1M context matches Opus; operator ruling 2026-07-23 retired the old
  ">200k ctx" / ">50KB plan" opus triggers). **Within the sonnet tier, a second axis picks the concrete snapshot**:
  sonnet-5 is the default for ALL AO dispatch (operator ruling 2026-08-08 — smarter, 1M-vs-200K context AND cheaper than
  sonnet-4.6 through end of August 2026, so the light snapshot wins on no axis while that pricing holds; INVERTS the
  2026-08-04 "light by default, target >=80%" posture). sonnet-4.6 survives only as an explicit `sonnet_variant: light`
  opt-in, which nothing declares today — set via a plan's/role's `sonnet_variant: light | default` frontmatter, resolved
  at spawn by `agent-orchestrator/server/model_tier.py::resolve_sonnet_snapshot`. **Every AO planning-VM-eligible plan
  (`assigned_vm: planning`) defaults to Sonnet**, with effort set by a separate todo-count-derived ladder, not a flat
  max: a plan declaring no tier gets xhigh baseline, max past model_tier.LARGE_PLAN_TODO_THRESHOLD open todos (operator
  ruling 2026-07-22), not a silent "medium". Covers the mandatory task-start self-check (model + effort mismatch →
  STOP/FLAG), always-set sub-agent model=, and the orchestrator's frontmatter-driven autospawn tier enforcement.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [model-tier, orchestrator, role-registry, escalation, model-tier-selection]
related: [/codex/12-agent-workflow/local-slot-host-symmetric-worker-model.md]
created: 2026-05-12
authoritative_for: [model-tier selection (Sonnet vs Opus), thinking-effort tier selection]
referenced_by: [/codex/12-agent-workflow/work-philosophy.md, /plans/archive/issues/human_led_audit_pool_2026_05_21.md]
owner:
last_reviewed:
code_refs:
---

# Model Tier Selection — Sonnet 5 vs Opus 4.8

**Rule**: Default to Sonnet 5 — for EVERY role, including the main orchestrator (operator ruling 2026-08-07). Opus 4.8
is no longer a standing spawn-time declaration for anything; it survives only as a manual, operator-triggered emergency
escalation lever (dashboard Switch Model, kill+resume, context intact) for a session visibly struggling on Sonnet. Every
work-split MUST classify each plan/slot as Sonnet-doable — `opus-required` is now a manual/operational lever, not a
classification any plan or role file should declare going forward.

**Operator ruling (2026-07-23)**: Sonnet 5 has a **1M context window — the same size as Opus 4.8.** This retires context
SIZE as an opus-escalation reason entirely: the old ">200k context provably required" and ">50KB plan + multiple full
files" triggers below are **RETIRED**, not just softened. Opus is now a PURELY QUALITATIVE escalation (main orchestrator
role, genuine cross-repo architecture judgment, trading judgment calls) — never a function of how large the plan or how
many files are in context. **Every plan eligible for AO planning-VM dispatch (`assigned_vm: planning`) defaults to
Sonnet 5** — model tier itself has no size trigger left. Effort is a separate axis (see "Effort ladder" below): the
STANDARD configuration for a plan declaring no tier is the todo-count-derived default (xhigh baseline, max past the
10-todo threshold), not an unconditional `effort: max` and not a silent fallback either. The `audit_model_tier.py`
heuristic's size-based signal (`SIZE_OPUS_BYTES`) is removed to match.

**Operator ruling (2026-08-08) — the sonnet sub-tier default INVERTS: sonnet-5 everywhere, sonnet-4.6 opt-in only.**
Sonnet 5 is simultaneously smarter, 1M-context (vs sonnet-4.6's 200K — see `_CONTEXT_WINDOW_200K` in `model_tier.py`,
measured over 17,974 transcripts), and **cheaper than sonnet-4.6 through end of August 2026**. There is no axis on which
the light snapshot still wins, so routing ~80% of the fleet to it became a pure downgrade. Absent or
`sonnet_variant: default` → **sonnet-5**; only an EXPLICIT `sonnet_variant: light` still resolves to sonnet-4.6, and no
role or plan declares it. This supersedes amendment 2 of the 2026-08-04 ruling below (the `>=80% light` dispatch target
is **RETIRED**, not merely relaxed); amendment 1 (opus narrowed, then fully retired 2026-08-07) is untouched. The
mechanism is deliberately KEPT rather than deleted: when the promotional pricing ends, re-arming the cost split is a
frontmatter edit on the roles that should take it, not a code change. Applied in `model_tier.resolve_sonnet_snapshot`
plus its two `prefer_light` derivations (`role_registry.RoleSpec.sonnet_prefer_light`, `autospawn._resolve_task_model`),
which now test for an explicit `== "light"` instead of `!= "default"`; `light` is also preserved verbatim through
`_coerce_sonnet_variant` / `_parse_frontmatter_sonnet_variant`, which previously collapsed it to `None` because `None`
and `light` used to mean the same thing. Shipped: agent-orchestrator@96f6318.

**Operator ruling (2026-08-04) — opus narrowed to ONE category; a new sonnet-4.6/sonnet-5 axis added.** Two amendments,
both cost-driven, both qualitative (neither reintroduces a size trigger — the 2026-07-23 ruling's core point stands):

1. **Opus is main-orchestrator-role ONLY.** The other two 2026-07-23 categories (cross-repo architecture judgment,
   trading judgment) are RETIRED as opus triggers — that work now runs on **sonnet-5** (below), not opus. Every
   `agents/*.md` role that declared `model: opus` for a reason other than being the orchestrator (`ag_closeout_auditor`,
   `docs_reconciler`, `na_eligibility_auditor`, `plan_reconciler` — daily cross-corpus audit/reconciliation roles) was
   moved to `model: sonnet` + `sonnet_variant: default` as part of this ruling.
2. **Within `model: sonnet`, a new `sonnet_variant` axis picks the concrete snapshot** — see "Sonnet sub-tier" below.
   This is additive to the existing `model_tier` field, not a replacement: `model_tier` still decides sonnet vs opus vs
   fable; `sonnet_variant` only matters once that's landed on sonnet.

**Operator ruling (2026-08-07) — the last standing opus category (main orchestrator) is ALSO retired as a default,
cost-driven.** `agents/main.md` moved `model: opus` → `model: sonnet` + `sonnet_variant: default` (sonnet-5, the
"harder/judgment-heavy work" sub-tier — main still gets the strongest available Sonnet snapshot, just not Opus). Applied
live via the dashboard's new Switch Model lever (`main_agent_keeper.switch_main_model` — kills + resumes main's tmux
session on the new model, conversation intact; durably rewrites `agents/main.md` so every OTHER main respawn path —
account failover, stall-watchdog, the keeper's own fresh spawn — picks it up too, not just the one switch action), the
same kill+resume mechanism `switch_main_account` already used for account failover. **Opus 4.8 still exists as a lever,
not a role**: if main is visibly struggling on Sonnet 5 (repeated wrong calls on a genuinely qualitative fleet-wide
tradeoff), the operator can manually switch it back via the same dashboard action — but nothing spawns on Opus by
default anymore, and no role file should declare `model: opus` going forward without that same manual-escalation
framing. `agent-orchestrator/server/main_agent_keeper.py::_main_tier` was also fixed to resolve the sonnet tier to its
CONCRETE snapshot (`resolve_sonnet_snapshot`) instead of the bare `"sonnet"` alias — main had never needed this before
(opus has no variant), so leaving it unfixed would have let a bare alias fall through to the Claude CLI's own default
resolution instead of landing precisely on sonnet-5.

Ground truth: `agent-orchestrator/server/model_tier.py` (`SONNET_LIGHT_MODEL`/`SONNET_DEFAULT_MODEL`/
`CONCRETE_MODELS`/`resolve_sonnet_snapshot`), `role_registry.py` (`RoleSpec.sonnet_variant`, `write_model_frontmatter`),
`main_agent_keeper.py` (`_main_tier`, `switch_main_model`), `regen_backlog_from_plan.py`
(`_parse_frontmatter_sonnet_variant`), `autospawn.py::_resolve_task_model` (where it's actually applied at spawn),
`escalation.py` (CI/escalation defaults), `plan_health.py` (the `smart_tier` scheduled-audit family).

---

## The two tiers

| Tier             | Model             | Context | Cost          | Use when                                                                                                                                                                                                                               |
| ---------------- | ----------------- | ------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Default**      | `claude-sonnet-5` | **1M**  | Low           | Everything — including the main orchestrator role, large plans, multi-file context. The AO standard, no exceptions by default.                                                                                                         |
| **Manual lever** | `claude-opus-4-8` | 1M      | High (~5-10×) | NOT a spawn-time default for anything (retired 2026-08-07 for the last remaining category, main orchestrator). Available only as an operator-triggered dashboard escalation (Switch Model) for a session visibly struggling on Sonnet. |

Both tiers now have the same 1M context ceiling — Opus is never chosen because a plan is "too big to fit," and as of
2026-08-07 it is never chosen by default for ANY role either; it is purely an operator's manual emergency lever.

---

## Decision rule (apply at work-split time, per slot)

```
EVERY slot (including main orchestrator, large plans, multi-file context,   → Sonnet
   cross-repo architecture judgment, trading judgment,                         (effort: max if large/complex)
   AO planning-VM-eligible work of any size)
   ALL sonnet-tier work (2026-08-08: 5 is smarter AND cheaper)             →   sonnet-5 (absent/`default` — declare nothing)
   ONLY if a price change makes 4.6 genuinely cheaper again                →   sonnet_variant: light (explicit opt-in)

Opus is NEVER a plan/role/work-split declaration anymore — only a manual, operator-triggered dashboard
escalation (Switch Model lever) for a session visibly struggling on Sonnet.
```

**Default to Sonnet, full stop — there is no longer a standing qualitative reason to declare Opus anywhere** (the last
one, main orchestrator role, retired 2026-08-07). Pre-escalating to Opus "just in case" was already the anti-pattern
this doc banned; the 2026-07-23 ruling removed the context-ceiling justification, the 2026-08-04 ruling retired
cross-repo/trading judgment as opus triggers, and the 2026-08-07 ruling retired the last category (main orchestrator)
too. If a running session (main or otherwise) is genuinely struggling on Sonnet 5, that's now handled as a manual
operator escalation via the dashboard, not a role/plan declaration.

---

## Sonnet 5 — default for all of these

- Mechanical sweeps (ruff cleanup, pipeline_mode callsite migration, import rename)
- Single-repo implementation from a clear spec
- Running scripts and verifying output (reconciliation, QG, VM event verification)
- Test writing and fixing
- Per-service QG runs and lint fixes
- Codex doc updates (single doc, clear scope)
- Plan checkbox flips and plan body updates
- Manifest reconciliation script execution
- Per-protocol / per-adapter implementation (defi_catalogue Phases 2-6 impl)
- UI component implementation from design brief
- Audit passes (read-only repo analysis, grep-and-report)
- Sub-agent fan-out workers (each worker handles bounded scope)
- Any task where the plan body + one or two files = the full context needed

---

## Opus — a manual lever now, not a role (retired as a default 2026-08-07)

**Zero standing qualitative categories remain.** Every category that used to justify a spawn-time `model: opus`
declaration has been retired in sequence:

- ~~Cross-repo architecture JUDGMENT~~ (design tasks spanning UAC schema + UTL + 3+ services) — retired 2026-08-04, runs
  on `sonnet_variant: default` (sonnet-5).
- ~~Trading judgment calls~~ (position sizing, risk-limit calibration, archetype topology) — retired 2026-08-04, same.
- ~~Slot 1 main orchestrator ROLE~~ (boot checklist, ledger sweep, cross-slot Q&A dispatch, plan curation, ping triage,
  master plan refresh) — retired 2026-08-07, cost-driven operator ruling. `agents/main.md` now declares
  `model: sonnet` + `sonnet_variant: default`; the switch was applied live via the dashboard's Switch Model lever
  (kill+resume, context intact — see the 2026-08-07 ruling above).

**Opus 4.8 still exists, as a manual escalation only**: if a running session (main or otherwise) is genuinely struggling
on Sonnet 5 — repeatedly getting a qualitative fleet-wide/cross-repo/trading-judgment call wrong — the operator can
switch it to Opus via the same dashboard lever (Switch Model). This is an operator-triggered runtime action, not
something any role file or plan should declare by default going forward. Document a manual escalation the same way as
before: `OPUS-REQUIRED: <reason>` in the spawn prompt / dashboard action, vs.
`sonnet_variant: default — REASON: <harder/judgment-heavy | escalation | CI | main orchestrator>` for the sonnet-5
default.

---

## Sonnet sub-tier: 4.6 vs 5 (added 2026-08-04; default INVERTED 2026-08-08)

Within `model_tier: sonnet` (the vast majority of AO dispatch), a second, INDEPENDENT axis picks the concrete snapshot —
this is a cost/capability tradeoff WITHIN the sonnet tier, not a replacement for the model_tier decision above. As of
2026-08-08 that tradeoff is temporarily one-sided: sonnet-5 is better AND cheaper, so it takes everything.

| Value                        | Snapshot            | Default for                                                                                   |
| ---------------------------- | ------------------- | --------------------------------------------------------------------------------------------- |
| `default` (absent = default) | `claude-sonnet-5`   | **Everything** — all AO dispatch, escalation (`server/escalation.py`), CI (`agents/cicd.md`). |
| `light`                      | `claude-sonnet-4-6` | Nothing today. Explicit opt-in, kept armed for when sonnet-5's promotional pricing ends.      |

**How it's set**: a plan's or role's `sonnet_variant: light | default` frontmatter (mirrors `model_tier`'s own
plan-overrides-role-overrides-absent-default precedence — see `_resolve_task_tier` / `_parse_frontmatter_sonnet_variant`
in `regen_backlog_from_plan.py`). Absent → sonnet-5, so **no plan or role needs to declare anything** to get the right
snapshot today. The nine roles carrying an explicit `sonnet_variant: default` (`main`, `cicd`, and the daily
cross-corpus audit/reconcile roles `ag_closeout_auditor`/`docs_reconciler`/`na_eligibility_auditor`/`plan_reconciler`/
`escalation_queue_reconciler`/`cefi_reconciliation_auditor`/`cefi_mtds_smoke_tester`) are now redundant-but-harmless and
are deliberately LEFT in place: they are exactly the roles that must stay on sonnet-5 if the default ever flips back.

**Reversal recipe (when the sonnet-5 promo ends)**: preferred — add `sonnet_variant: light` to the roles that should
take the cheap snapshot (no code change). Wholesale revert — flip the two `prefer_light` derivations back to
`!= "default"` (`role_registry.RoleSpec.sonnet_prefer_light`, `autospawn._resolve_task_model`). Re-check actual
per-token pricing AND the context-window gap first (4.6 is 200K, sonnet-5 is 1M — the 200K ceiling was itself the root
cause of the worker terminal-wedge class); do NOT assume 4.6 is the cheaper one, which is precisely the assumption this
ruling invalidated.

**Where it's actually applied**: `agent-orchestrator/server/model_tier.py::resolve_sonnet_snapshot(prefer_light=...)`,
called from `autospawn.py::_resolve_task_model` (the main per-task dispatch path — reads `BacklogTask.sonnet_variant`),
`escalation.py` (hardcoded `sonnet_variant: default` equivalent — the function defaults changed to
`model_tier.SONNET_DEFAULT_MODEL` directly), and `plan_health.py`'s `smart_tier` branch (same, for the scheduled-audit
family). Before this ruling, AO only ever passed the BARE tier alias (`"sonnet"`) to `--model` and let the Claude Code
CLI silently resolve it — meaning AO's own telemetry never recorded which literal snapshot actually ran. Passing a
concrete snapshot string fixes that as a side effect (a worker's `slot_boot` self-report just echoes its launch value).

**Self-check**: this axis does NOT get its own hard-stop protocol (unlike the model_tier Step 3 check below) — a
sonnet-4.6-vs-5 mismatch is a cost-tuning concern, not a capability-correctness one, so it is not worth interrupting a
worker over. If you notice you're running a snapshot that doesn't match your task's declared `sonnet_variant`, mention
it in your final report; don't stop.

---

## Work-split classification protocol

Every slot in `work_split_<YYYY_MM_DD>_<side>.md` MUST include a `model_tier` field:

```markdown
| Slot | Theme               | Plan-of-record                  | model_tier   | Cal AI-days |
| ---- | ------------------- | ------------------------------- | ------------ | ----------- |
| 1    | Main orchestrator   | LEDGER.md                       | **Sonnet 5** | continuous  |
| 2    | defi_catalogue impl | defi_catalogue_chain_primitives | **Sonnet 5** | ~16         |
| 3    | code_freeze audit   | code_freeze_migrate_backfill    | **Sonnet 5** | ~14         |
```

Classification is the **first thing** the operator or main-orch agent fills in when drafting the split. If model_tier is
absent from a slot row, the agent MUST use Sonnet 5 and flag the omission.

---

## Classifying existing plans

When auditing `plans/active/` before drafting a work-split, classify each plan as one of:

**`sonnet-doable`** — the default for everything, REGARDLESS of size (Sonnet 5's 1M context handles large plans and
multi-file context natively — this is the standard for AO planning-VM-eligible work, not a fallback):

- Mechanical refactors (ruff, pipeline_mode sweep, import rename) — any size
- Per-service impl (adapter, writer, test, codex doc) — any size
- Script execution + verification
- Single-plan phase implementation
- Large trackers/umbrella plans with 100+ todos (e.g. `sports_consolidated_closeout`-style closeouts) — size alone is
  never a reason to escalate; set `effort: max` instead

**`opus-required`** — as of 2026-08-07, this classification has NO standing category left (never "the plan is big" or
"many files are involved" — those stay Sonnet 5 at high effort; cross-repo architecture judgment and trading judgment
were retired 2026-08-04, and main-orchestrator ROLE work was retired 2026-08-07 — see "Opus — a manual lever now, not a
role" above). Work that used to be classified `opus-required` because it's main-orchestrator-role work now classifies
`sonnet-doable` too:

- Master plan refresh + inventory regeneration (main-orchestrator role) — `sonnet-doable`, `sonnet_variant: default`
- Work-split drafting itself (main-orchestrator role — allocating scope across the fleet) — same

`opus-required` still exists as a frontmatter value (the orchestrator still honors it — see "Autonomous enforcement"
below), but declaring it on a plan/work-split slot going forward should be rare and deliberate: a genuine one-off manual
override, not a role-based default. Distinct from the dashboard's live Switch Model lever (which overrides an
ALREADY-RUNNING session's model at runtime, independent of any plan's frontmatter) — this field only affects FUTURE
spawns dispatched from that plan. Add `model_tier: sonnet-doable | opus-required` to each plan's frontmatter on the next
substantive touch (same logical unit as the substantive change — do NOT mass-sweep, per Findings Triage).

### Autonomous enforcement (wired 2026-06-01)

The orchestrator now **reads both tier fields from plan frontmatter and spawns the worker accordingly** — declaring a
tier is no longer advisory-only:

- `model_tier: opus-required` → the regen-derived backlog task gets `model: opus`; else `sonnet`. Effort is a SEPARATE
  decision (below) — it does not follow from model tier in either direction.
- `sonnet_variant: light | default` (2026-08-04, meaningful only when the resolved model is `sonnet`) → the backlog
  task's `sonnet_variant` field; absent → sonnet-5, same as `default` (2026-08-08 inversion). See "Sonnet sub-tier"
  above.
- `thinking_tier: max | high | medium` → task `effort`: `max`→`effort=max`; `high`→`effort=high`; `medium`/absent (and
  no `effort:` frontmatter, no `assigned_role`) → **todo-count-derived default** (operator ruling 2026-07-22): `max` if
  the plan has more than `model_tier.LARGE_PLAN_TODO_THRESHOLD` (10) open todos, else `xhigh` — replacing what used to
  be a silent, bare "medium" spawn default. None of this implies or requires `model: opus`.
- `AutoSpawnLoop` spawns an idle slot's worker at the **top queued task's** model+effort (the worker's model is fixed at
  spawn, before dispatch picks its task — so it's chosen from the highest-priority pending task).

Code: `agent-orchestrator/server/regen_backlog_from_plan.py` (`_parse_frontmatter_model_tier` +
`_parse_frontmatter_sonnet_variant` + `_parse_frontmatter_thinking_tier` + the todo-count-derived default added right
after the explicit-`effort:` override) → `server/backlog.py::BacklogTask` (`model`/`sonnet_variant`/`effort`/`thinking`)
→ `server/autospawn.py::_spawn_param_plan` (per-slot spawn plan, R2 2026-07-16 — NOT the deleted
`_top_queued_task_params`) → `_resolve_task_model` (resolves the concrete snapshot, 2026-08-04). Shared threshold
constant: `server/model_tier.py::LARGE_PLAN_TODO_THRESHOLD` (effort-tier derivation only, above — NOT used by
`context_lifecycle.py` anymore: the 2026-08-05 ruling replaced its old large-plan-only carve-out with unconditional
force-compact coverage for EVERY working task-worker slot, see
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`'s context-lifecycle section). Coverage audit:
`unified-trading-pm/scripts/plans/audit_model_tier.py`. Until a plan declares `model_tier`, it silently defaults to
Sonnet (model tier's silent default is UNCHANGED by the 2026-07-22 ruling — only effort's silent default changed).
Backfilled opus set (2026-06-01): `master_to_live_defi`, `mdps_long_running_multi_shard_architecture_audit`,
`mdps_pure_polars_migration`, `global_ledger_pnl_attribution_migration`, `regime_clustering_structure_allocator`,
`solana_basis_trading_mvp`, `pipeline_mode_audit`.

---

## Continuation prompt template (model tier enforcement)

When spawning a Sonnet 5 agent, start the prompt with:

```
MODEL TIER: Sonnet 5 (1M context). This task does not require Opus — Sonnet 5's context matches
Opus's, and as of 2026-08-07 there is no standing qualitative category left (main orchestrator
included); size alone never justified escalation, and neither does anything else by default now.
```

Opus 4.8 is no longer spawned by declaring a reason in the boot prompt — it is a live, operator-triggered dashboard
action (Switch Model) applied to an ALREADY-RUNNING session, not a spawn-time choice. If you're drafting a spawn prompt
and find yourself reaching for an Opus justification, that's a signal the work is `sonnet-doable`
(`sonnet_variant: default` if it's genuinely harder/judgment-heavy) — flag to the operator instead of declaring opus.

---

## Self-check at task start (MANDATORY)

Every agent MUST perform this check as the **first action** of every task, before reading files or writing code.

### Step 1 — read your own model

The running model is stated in the system prompt: `"You are powered by the model named <X>"`. Read it. You always know
which model you are.

### Step 2 — read the required tier

From (in priority order):

1. The spawn prompt: look for `MODEL TIER: Sonnet 5` or `MODEL TIER: Opus 4.8 — REASON: ...`
2. The work-split slot row: `model_tier: sonnet-doable | opus-required`
3. The plan frontmatter: `model_tier:` field
4. If none of the above: apply the decision rule (everything, including main orchestrator, defaults to Sonnet —
   `opus-required` as of 2026-08-07 is never the silent/no-declaration default for anything)

### Step 3 — check for mismatch and act

| Running model | Required tier     | Action                                                             |
| ------------- | ----------------- | ------------------------------------------------------------------ |
| Sonnet 5      | sonnet-doable     | ✅ Proceed                                                         |
| Opus 4.8      | opus-required     | ✅ Proceed                                                         |
| **Sonnet 5**  | **opus-required** | 🔴 **STOP — flag to operator, do not proceed**                     |
| **Opus 4.8**  | **sonnet-doable** | 🟡 **FLAG to operator, then proceed (don't block on money waste)** |

**When Sonnet 5 detects opus-required task** — output this block and stop:

```
⚠️ WRONG MODEL — CANNOT PROCEED
Task requires: Opus 4.8
Running as: Sonnet 5
Reason this task needs Opus: <state the reason — as of 2026-08-07 there is no standing qualitative category
(main orchestrator / cross-repo / trading judgment all retired), so this should be a RARE, explicit manual
override someone deliberately declared; if you can't find a stated reason, treat it as sonnet-doable instead
of proceeding on Opus. NOT context size — Sonnet 5 also has 1M context.>

ACTION REQUIRED: Please reopen this tab/slot on Opus 4.8.
In Claude Code: use /model claude-opus-4-8 or restart with --model claude-opus-4-8
I will not start the task until the model is correct.
```

**When Opus 4.8 detects sonnet-doable task** — output this block then proceed:

```
💸 WRONG MODEL — PROCEEDING BUT FLAGGING COST WASTE
Task is: sonnet-doable
Running as: Opus 4.8 (unnecessary — ~5-10× more expensive)
Reason I'm not stopping: money waste doesn't break correctness; operator should know.

ACTION FOR NEXT RUN: Use Sonnet 5 for this task.
In Claude Code: /model claude-sonnet-5
Continuing now...
```

### `/autonomous` carve-out (operator ruling 2026-07-12)

Under an `/autonomous` dispatch (`cursor-configs/AUTONOMOUS_AGENT_RULES.md`), a Sonnet agent detecting
opus-required-shaped work does **NOT** hard-stop: it flags the mismatch in the plan's Progress Log, proceeds
decide-and-document, and the operator reviews at report time. This is the ONE exception to the Step 3 HARD STOP above —
the HARD STOP remains in force for **interactive / non-autonomous sessions** (a Sonnet agent outside `/autonomous` still
stops per Step 3). Ruling: `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 row `10010`.

### Step 4 — sub-agent spawning: always set `model` explicitly

When using the Agent tool, **always** pass the `model` parameter. Never inherit:

```python
# Sonnet-doable sub-agent
Agent(model="sonnet", prompt="...")

# Opus-required sub-agent
Agent(model="opus", prompt="... OPUS-REQUIRED: cross-repo architecture ...")
```

Omitting `model` in an Agent call is a bug — it inherits the parent model, silently costing Opus rates for
Sonnet-suitable work if the parent happens to be Opus.

---

## Anti-patterns (cost waste, review-blocking)

- Using Opus for single-repo mechanical sweeps
- Using Opus for sub-agent fan-out workers (each worker is bounded by definition)
- Pre-escalating to Opus "just in case" without a provable context-size argument
- Omitting `model_tier` from work-split slot rows
- Using Opus for plan checkbox flips or codex doc edits
- Declaring `model: opus` in a role file (`agents/*.md`) as a standing default — as of 2026-08-07 that's true for EVERY
  role, main orchestrator included; Opus is a runtime dashboard escalation, not a role declaration
- Enabling max effort for mechanical sweeps (wastes budget with zero quality gain)
- Enabling max effort without declaring `effort: max` in the spawn prompt (silent budget bleed)

---

## Effort ladder (SUPERSEDES the old 3-tier "thinking" framing below the 2026-07-22 line)

**Ground truth (agent-orchestrator/server/model_tier.py, 2026-07)**: `--effort` is a FIVE-level ladder —
`low < medium < high < xhigh < max` — and it is an axis INDEPENDENT of model tier. Effort is the PRIMARY reasoning
control on every adaptive-reasoning model (Sonnet / Opus / Fable alike); only Haiku has no effort control at all.
**Nothing gates `xhigh` or `max` to Opus.** The "extended thinking isn't available on Sonnet" / "max requires Opus, no
exceptions" claims that used to live in this doc were WRONG relative to the current code and are removed.

**Default (operator ruling 2026-07-22)**: a plan/task declaring no tier at all (no `effort:`, no `thinking_tier:`, no
`assigned_role`) no longer falls through to the ladder's bare `medium` — it gets a todo-count-derived default instead:

```
IF plan declares NO tier (effort: / thinking_tier: / assigned_role all absent):
  IF plan's open-todo count > model_tier.LARGE_PLAN_TODO_THRESHOLD (10)  → effort = "max"
  ELSE                                                                    → effort = "xhigh"
IF plan declares a tier explicitly (effort: / thinking_tier: / assigned_role) → that declaration wins, unchanged
```

Wired in `agent-orchestrator/server/regen_backlog_from_plan.py` (the fallback added right after the explicit-`effort:`
override) and mirrored in `context_lifecycle.py`'s worker carve-out (same threshold — a large-plan worker gets pulled
into proactive compact/checkpoint management, not just a higher effort default). Model tier is UNTOUCHED by this — as of
2026-08-07 it defaults to Sonnet with ZERO standing qualitative escalation categories (main orchestrator role /
cross-repo architecture judgment / trading judgment were all retired in sequence — see "Opus — a manual lever now, not a
role" above; context size was never one of them, 2026-07-23 ruling).

Still declare `effort:` (or `thinking_tier:`) explicitly on a work-split slot row when you know better than the default
— the auto-default exists to raise the floor for plans that forgot to declare, not to discourage declaring.

| Level    | When it's the right choice (declare explicitly to confirm)                                                                                                 | Typical cost vs medium |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| `low`    | Trivial, high-volume mechanical work where even medium is overkill                                                                                         | ~0.5×                  |
| `medium` | Mechanical, impl-from-spec, script runs — the ladder's own floor                                                                                           | 1×                     |
| `high`   | Design, architecture within a single repo, plan writing                                                                                                    | ~2-3×                  |
| `xhigh`  | **New default** for any plan declaring no tier — works on Sonnet, no Opus needed                                                                           | ~4-6×                  |
| `max`    | **New default for large (>10-todo) undeclared plans**; also novel cross-repo design, complex debugging, trading judgment — works on Sonnet, no Opus needed | ~8-15×                 |

### What goes in each tier

**`medium`** — standard reasoning, no extended thinking budget needed:

- Ruff cleanup, callsite migration, import rename
- Implementing from a clear spec (plan body + file = full context)
- Script execution + output verification
- Test writing for a known pattern
- Plan checkbox flips, codex doc edits (single doc)
- Sub-agent fan-out workers (each worker is bounded)
- QG runs and lint fixes

**`high`** — needs careful reasoning but not extended thinking:

- Single-repo feature design where trade-offs exist
- Codex doc authoring for a new pattern (must cover edge cases)
- Per-service adapter implementation (protocol logic, error handling)
- Plan phase design (phased DAG, success criteria, downstream impact)
- Cross-service wiring where the interaction is non-trivial but bounded
- Debugging a single service's failing test with non-obvious root cause

**`xhigh`** — new default for any plan/task declaring no tier at all (2026-07-22); also the right explicit choice for
work that's clearly more-than-mechanical but doesn't need the full `max` treatment below. Works on Sonnet.

**`max`** — new default for large (>10-todo) undeclared plans; also the right explicit choice for:

- Novel trading archetype topology (carry_staked_basis, leveraged_funding_arb family decisions)
- Cross-repo migration pre-audit (all consumers must be in context, breakage is non-obvious)
- Complex multi-service debugging where the bug crosses 3+ system boundaries
- Schema design decisions with long-tail correctness implications (manifest columns, shard atoms)
- Trading judgment calls (position sizing, risk-limit calibration, archetype risk trade-offs)
- Work-split drafting by main orchestrator (reads all 50+ active plans to allocate)
- Anything where the agent must hold contradictory constraints and find a non-obvious resolution

### Pairing rules

Effort and model tier are INDEPENDENT (model_tier.py ground truth) — **no effort level requires or implies a particular
model tier.** `max` on Sonnet is normal, not an error; it does not imply `model_tier: opus-required`, and model tier
keeps defaulting to Sonnet for everything — see "Opus — a manual lever now, not a role" above (zero standing categories
left as of 2026-08-07).

`high` (and `xhigh`) work identically well on either model tier. Sonnet at high/xhigh is generally preferred over Opus
at a lower effort — effort is the cheap lever; model tier is the expensive one, reach for it only on its own criteria.

### Work-split slot declaration

```markdown
| Slot | Theme                     | Plan                   | model_tier    | effort | Cal AI-days |
| ---- | ------------------------- | ---------------------- | ------------- | ------ | ----------- |
| 1    | Main orchestrator         | LEDGER                 | sonnet-doable | max    | continuous  |
| 2    | defi_catalogue impl       | defi_catalogue         | sonnet-doable | high   | ~16         |
| 3    | ruff cleanup              | ruff_workspace_cleanup | sonnet-doable | medium | ~0.4        |
| 5    | archetype topology design | defi_recursive_borrow  | sonnet-doable | max    | ~14         |
```

### Spawn prompt header (required fields)

```
MODEL TIER: Sonnet | Opus | Fable
EFFORT: low | medium | high | xhigh | max
[If opus-required]: OPUS-REQUIRED — REASON: <one-line reason>
```

---

## Self-check — effort (extend the Step 3 model check)

After checking model tier, check effort (the five-level ladder: `low < medium < high < xhigh < max`):

**How the agent knows its effort level**: The spawn prompt declares it (`EFFORT: <level>`). Since 2026-07-22 a plan
declaring no tier at all is NOT "undeclared" in practice — regen already computed `xhigh` or `max` for it from todo
count and put that in the spawn prompt, so the agent should almost always find an explicit value there. Only fall back
to inferring from the task description (using the tier definitions above) if the spawn prompt is genuinely silent on it,
then flag if the inferred tier can't be confirmed against the description.

| Declared effort vs. what the task actually needs                                | Action                                        |
| ------------------------------------------------------------------------------- | --------------------------------------------- |
| Same ladder position                                                            | ✅ Proceed                                    |
| **Under-provisioned** (declared is a lower ladder position than the task needs) | 🔴 **HARD STOP — wait for operator override** |
| **Over-provisioned** (declared is a higher ladder position than the task needs) | 🔴 **HARD STOP — wait for operator override** |

No level "requires" or "implies" a model tier (see Pairing rules above) — a mismatch here is purely about whether the
_effort_ fits the _task_, independent of which model is running it.

**Both directions are hard stops.** The operator gets to see the mismatch and decide — either confirm the deviation is
intentional ("proceed anyway") or fix the spawn tier. This avoids silent quality degradation (under) and silent money
burn (over).

**Under-provisioned stop block:**

```
🔴 HARD STOP — EFFORT UNDER-PROVISIONED
Declared: effort: <declared>
Task requires: effort: <required>
Reason: <one-line — e.g. "cross-repo migration pre-audit requires holding all consumer files simultaneously">

I cannot start this task at the declared effort level without risking silent quality degradation.

To proceed:
  Option A — fix the tier: re-spawn with EFFORT: <required> (model tier is a separate decision — see Pairing rules)
  Option B — override: reply "proceed anyway" and I will start at the declared level with a quality caveat
```

**Over-provisioned stop block:**

```
🔴 HARD STOP — EFFORT OVER-PROVISIONED (COST WASTE)
Declared: effort: <declared>
Task needs: effort: <required>
Reason: <one-line — e.g. "ruff cleanup is mechanical; max effort adds no quality, only cost">

Estimated unnecessary spend: ~<N>× vs correct level.

To proceed:
  Option A — fix the tier: re-spawn with EFFORT: <required> (saves ~<N>× cost)
  Option B — override: reply "proceed anyway" and I will start at the declared level
```

**Override handling**: if the operator replies "proceed anyway" (or equivalent), the agent starts immediately with a
one-line caveat in its first output ("proceeding at <tier> per operator override"). No further stops.

---

## Multi-provider gateway boundary (2026-07-30)

`agent-orchestrator/server/accounts.py`'s `AccountProvider` Literal (the DeepSeek-routing mechanism, see
`/plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md`) is the one sanctioned way a worker-fleet spawn
picks a non-Anthropic backend — each value gets its own explicit eligibility/quota-adaptive/health-gate wiring in
`select_account_for_spawn()`, and `opus-required`/`fable-required` stay a hard, unconditional pin to Claude regardless
of provider count. An opaque multi-provider gateway (OmniRoute or equivalent — see
`/plans/archive/2026_08/omniroute_llm_gateway_pilot_design_2026_07_30.md`) that silently substitutes a cheaper/free
model underneath a task's tier assignment is **out of scope for any `AccountProvider`-routed worker traffic** — it would
let a task correctly tiered "sonnet is enough" land on some unrelated free-tier model with nothing in the dispatch path
aware of the difference, invisibly. The one sanctioned pilot surface for that class of gateway is `deployment-api`'s
pipeline-UAT commentary caller (a direct SDK call from a non-worker service, no model-tier semantics at all — tracked in
the OmniRoute plan above), not the worker fleet.

---

_Companion plan_: `plans/active/ruff_workspace_cleanup_*.md` (example of correctly classified Sonnet-suitable work).
_Enforced by_: work-split review — any slot missing `model_tier` or `thinking` defaults to Sonnet 5 / medium.
