---
doc_type: codex-ssot
title: Model Tier Selection — Sonnet 4.6 vs Opus 4.8
summary: >-
  Model-tier + effort selection SSOT — model tier (sonnet/opus/fable) and effort (low<medium<high<xhigh<max) are
  INDEPENDENT axes (ground truth: agent-orchestrator/server/model_tier.py, 2026-07) — effort is the primary reasoning
  control on every adaptive-reasoning model (sonnet/opus/fable alike, Haiku excluded), NOT opus-gated. Model tier:
  default Sonnet, Opus only for the main orchestrator / cross-repo architecture / provably >200k context. Effort: a plan
  declaring no tier gets a todo-count-derived default (xhigh baseline, max past model_tier.LARGE_PLAN_TODO_THRESHOLD
  open todos — operator ruling 2026-07-22), not a silent "medium". Covers the mandatory task-start self-check (model +
  effort mismatch → STOP/FLAG), always-set sub-agent model=, and the orchestrator's frontmatter-driven autospawn tier
  enforcement.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [model-tier, orchestrator, role-registry, escalation, model-tier-selection]
related: [../12-agent-workflow/local-slot-host-symmetric-worker-model.md]
created: 2026-05-12
authoritative_for: [model-tier selection (Sonnet vs Opus), thinking-effort tier selection]
referenced_by: [codex/12-agent-workflow/work-philosophy.md, plans/active/issues/human_led_audit_pool_2026_05_21.md]
owner:
last_reviewed:
code_refs:
---

# Model Tier Selection — Sonnet 4.6 vs Opus 4.8

**Rule**: Default to Sonnet 4.6. Opus 4.8 is a deliberate exception requiring justification. Every work-split MUST
classify each plan/slot as Sonnet-doable or Opus-required before spawning agents.

---

## The two tiers

| Tier           | Model               | Context | Cost          | Use when                                                                                        |
| -------------- | ------------------- | ------- | ------------- | ----------------------------------------------------------------------------------------------- |
| **Default**    | `claude-sonnet-4-6` | 200k    | Low           | Everything that fits in 200k context without multi-repo synthesis                               |
| **Escalation** | `claude-opus-4-8`   | 1M      | High (~5-10×) | Main orchestrator, cross-repo architecture decisions, tasks whose context provably exceeds 200k |

---

## Decision rule (apply at work-split time, per slot)

```
IF slot is main orchestrator (slot 1)     → Opus 4.8
IF task requires simultaneous reading of  → Opus 4.8
   >3 full service codebases OR
   a plan >50KB + multiple full files OR
   1M-context reasoning across the entire
   workspace state
OTHERWISE                                 → Sonnet 4.6
```

**When in doubt, use Sonnet 4.6 and escalate only if the agent hits a genuine context wall.** Do NOT pre-escalate "just
in case" — that is money waste with no quality upside for bounded tasks.

---

## Sonnet 4.6 — default for all of these

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

## Opus 4.8 — only for these

- **Slot 1 main orchestrator**: boot checklist, ledger sweep, cross-slot Q&A dispatch, plan curation, ping triage,
  master plan refresh. Orchestrator context = entire workspace state → requires 1M window.
- **Cross-repo architecture decisions**: design tasks that require simultaneously reading UAC schema + UTL helpers + 3+
  service implementations + codex SSOT to make a coherent decision (e.g., new shard-atom design, new manifest column
  rationale, signal-broadcast topology).
- **Large migration design**: tasks where the full impact surface (all consumers across all repos) must be in context
  simultaneously to avoid silent breakage (pre-audit manifests for public API changes).
- **Trading judgment calls**: position sizing, risk-limit calibration, archetype topology decisions — requires holding
  the entire live-pipeline architecture in context.
- **>200k context provably required**: if the agent's plan-of-record + all referenced files + the task output provably
  exceed 200k tokens, escalate. Document the reason in the spawn prompt: `OPUS-REQUIRED: <reason>`.

---

## Work-split classification protocol

Every slot in `work_split_<YYYY_MM_DD>_<side>.md` MUST include a `model_tier` field:

```markdown
| Slot | Theme               | Plan-of-record                  | model_tier     | Cal AI-days |
| ---- | ------------------- | ------------------------------- | -------------- | ----------- |
| 1    | Main orchestrator   | LEDGER.md                       | **Opus 4.8**   | continuous  |
| 2    | defi_catalogue impl | defi_catalogue_chain_primitives | **Sonnet 4.6** | ~16         |
| 3    | code_freeze audit   | code_freeze_migrate_backfill    | **Sonnet 4.6** | ~14         |
```

Classification is the **first thing** the operator or main-orch agent fills in when drafting the split. If model_tier is
absent from a slot row, the agent MUST use Sonnet 4.6 and flag the omission.

---

## Classifying existing plans

When auditing `plans/active/` before drafting a work-split, classify each plan as one of:

**`sonnet-doable`** — bounded scope, single-repo or clear cross-repo spec, fits in 200k:

- Mechanical refactors (ruff, pipeline_mode sweep, import rename)
- Per-service impl (adapter, writer, test, codex doc)
- Script execution + verification
- Single-plan phase implementation

**`opus-required`** — needs 1M context OR is main-orchestrator work:

- Master plan refresh + inventory regeneration (reads all 50+ active plans + codex)
- Cross-repo architecture design (UAC schema + UTL + 3+ services simultaneously)
- Full workspace impact pre-audit for a public API change
- Work-split drafting itself (reads all plans to allocate scope)

Add `model_tier: sonnet-doable | opus-required` to each plan's frontmatter on the next substantive touch (same logical
unit as the substantive change — do NOT mass-sweep, per Findings Triage).

### Autonomous enforcement (wired 2026-06-01)

The orchestrator now **reads both tier fields from plan frontmatter and spawns the worker accordingly** — declaring a
tier is no longer advisory-only:

- `model_tier: opus-required` → the regen-derived backlog task gets `model: opus`; else `sonnet`. Effort is a SEPARATE
  decision (below) — it does not follow from model tier in either direction.
- `thinking_tier: max | high | medium` → task `effort`: `max`→`effort=max`; `high`→`effort=high`; `medium`/absent (and
  no `effort:` frontmatter, no `assigned_role`) → **todo-count-derived default** (operator ruling 2026-07-22): `max` if
  the plan has more than `model_tier.LARGE_PLAN_TODO_THRESHOLD` (10) open todos, else `xhigh` — replacing what used to
  be a silent, bare "medium" spawn default. None of this implies or requires `model: opus`.
- `AutoSpawnLoop` spawns an idle slot's worker at the **top queued task's** model+effort (the worker's model is fixed at
  spawn, before dispatch picks its task — so it's chosen from the highest-priority pending task).

Code: `agent-orchestrator/server/regen_backlog_from_plan.py` (`_parse_frontmatter_model_tier` +
`_parse_frontmatter_thinking_tier` + the todo-count-derived default added right after the explicit-`effort:` override) →
`server/backlog.py::BacklogTask` (`model`/`effort`/`thinking`) → `server/autospawn.py::_top_queued_task_params`. Shared
threshold constant: `server/model_tier.py::LARGE_PLAN_TODO_THRESHOLD` (also used by `context_lifecycle.py`'s
large-plan-worker carve-out from the worker exclusion, so the two never drift apart). Coverage audit:
`unified-trading-pm/scripts/plans/audit_model_tier.py`. Until a plan declares `model_tier`, it silently defaults to
Sonnet (model tier's silent default is UNCHANGED by the 2026-07-22 ruling — only effort's silent default changed).
Backfilled opus set (2026-06-01): `master_to_live_defi`, `mdps_long_running_multi_shard_architecture_audit`,
`mdps_pure_polars_migration`, `global_ledger_pnl_attribution_migration`, `regime_clustering_structure_allocator`,
`solana_basis_trading_mvp`, `pipeline_mode_audit`.

---

## Continuation prompt template (model tier enforcement)

When spawning a Sonnet 4.6 agent, start the prompt with:

```
MODEL TIER: Sonnet 4.6 (200k context). This task is bounded and does not require Opus.
If you hit a genuine context wall (cannot fit all needed files), stop and report — do NOT
silently skip files or hallucinate from partial context.
```

When spawning Opus 4.8, state the reason:

```
MODEL TIER: Opus 4.8 — REASON: [main orchestrator / cross-repo architecture / >200k context provably required].
```

---

## Self-check at task start (MANDATORY)

Every agent MUST perform this check as the **first action** of every task, before reading files or writing code.

### Step 1 — read your own model

The running model is stated in the system prompt: `"You are powered by the model named <X>"`. Read it. You always know
which model you are.

### Step 2 — read the required tier

From (in priority order):

1. The spawn prompt: look for `MODEL TIER: Sonnet 4.6` or `MODEL TIER: Opus 4.8 — REASON: ...`
2. The work-split slot row: `model_tier: sonnet-doable | opus-required`
3. The plan frontmatter: `model_tier:` field
4. If none of the above: apply the decision rule (main orchestrator → Opus; everything else → Sonnet)

### Step 3 — check for mismatch and act

| Running model  | Required tier     | Action                                                             |
| -------------- | ----------------- | ------------------------------------------------------------------ |
| Sonnet 4.6     | sonnet-doable     | ✅ Proceed                                                         |
| Opus 4.8       | opus-required     | ✅ Proceed                                                         |
| **Sonnet 4.6** | **opus-required** | 🔴 **STOP — flag to operator, do not proceed**                     |
| **Opus 4.8**   | **sonnet-doable** | 🟡 **FLAG to operator, then proceed (don't block on money waste)** |

**When Sonnet 4.6 detects opus-required task** — output this block and stop:

```
⚠️ WRONG MODEL — CANNOT PROCEED
Task requires: Opus 4.8 (1M context)
Running as: Sonnet 4.6 (200k context)
Reason this task needs Opus: <state the reason from spawn prompt or decision rule>

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

ACTION FOR NEXT RUN: Use Sonnet 4.6 for this task.
In Claude Code: /model claude-sonnet-4-6
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
into proactive compact/checkpoint management, not just a higher effort default). Model tier is UNTOUCHED by this — still
governed only by the existing three criteria below (main orchestrator / cross-repo arch / >200k context).

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
keeps being decided purely by the three criteria in "Opus 4.8 — only for these" above.

`high` (and `xhigh`) work identically well on either model tier. Sonnet at high/xhigh is generally preferred over Opus
at a lower effort — effort is the cheap lever; model tier is the expensive one, reach for it only on its own criteria.

### Work-split slot declaration

```markdown
| Slot | Theme                     | Plan                   | model_tier    | effort | Cal AI-days |
| ---- | ------------------------- | ---------------------- | ------------- | ------ | ----------- |
| 1    | Main orchestrator         | LEDGER                 | opus-required | max    | continuous  |
| 2    | defi_catalogue impl       | defi_catalogue         | sonnet-doable | high   | ~16         |
| 3    | ruff cleanup              | ruff_workspace_cleanup | sonnet-doable | medium | ~0.4        |
| 5    | archetype topology design | defi_recursive_borrow  | opus-required | max    | ~14         |
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

_Companion plan_: `plans/active/ruff_workspace_cleanup_*.md` (example of correctly classified Sonnet-suitable work).
_Enforced by_: work-split review — any slot missing `model_tier` or `thinking` defaults to Sonnet 4.6 / medium.
