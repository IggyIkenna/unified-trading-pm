---
scope: [engineer, admin]
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

- `model_tier: opus-required` → the regen-derived backlog task gets `model: opus`; else `sonnet`.
- `thinking_tier: max | high | medium` → task `effort`/`thinking`: `max`→`effort=max`+extended-thinking on (pairs with
  opus); `high`→`effort=high`; `medium`/absent → spawn default.
- `AutoSpawnLoop` spawns an idle slot's worker at the **top queued task's** model+effort+thinking (the worker's model is
  fixed at spawn, before dispatch picks its task — so it's chosen from the highest-priority pending task).

Code: `agent-orchestrator/server/regen_backlog_from_plan.py` (`_parse_frontmatter_model_tier` +
`_parse_frontmatter_thinking_tier`) → `server/backlog.py::BacklogTask` (`model`/`effort`/`thinking`) →
`server/autospawn.py::_top_queued_task_params`. Coverage audit: `unified-trading-pm/scripts/plans/audit_model_tier.py`.
Until a plan declares `model_tier`, it silently defaults to Sonnet. Backfilled opus set (2026-06-01):
`master_to_live_defi`, `mdps_long_running_multi_shard_architecture_audit`, `mdps_pure_polars_migration`,
`global_ledger_pnl_attribution_migration`, `regime_clustering_structure_allocator`, `solana_basis_trading_mvp`,
`pipeline_mode_audit`.

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
- Enabling max thinking for mechanical sweeps (wastes budget with zero quality gain)
- Enabling max thinking without declaring `thinking: max` in the spawn prompt (silent budget bleed)

---

## Thinking effort tiers

Three levels. Declared alongside `model_tier` in every work-split slot row and spawn prompt.

| Level              | Declaration                          | When                                                         | Typical cost vs medium |
| ------------------ | ------------------------------------ | ------------------------------------------------------------ | ---------------------- |
| `thinking: medium` | Default — omit or state explicitly   | Mechanical, impl-from-spec, script runs                      | 1×                     |
| `thinking: high`   | State explicitly                     | Design, architecture within a single repo, plan writing      | ~2-3×                  |
| `thinking: max`    | State explicitly + requires Opus 4.8 | Novel cross-repo design, complex debugging, trading judgment | ~8-15×                 |

### What goes in each tier

**`thinking: medium`** — standard reasoning, no extended thinking budget needed:

- Ruff cleanup, callsite migration, import rename
- Implementing from a clear spec (plan body + file = full context)
- Script execution + output verification
- Test writing for a known pattern
- Plan checkbox flips, codex doc edits (single doc)
- Sub-agent fan-out workers (each worker is bounded)
- QG runs and lint fixes

**`thinking: high`** — needs careful reasoning but not extended thinking:

- Single-repo feature design where trade-offs exist
- Codex doc authoring for a new pattern (must cover edge cases)
- Per-service adapter implementation (protocol logic, error handling)
- Plan phase design (phased DAG, success criteria, downstream impact)
- Cross-service wiring where the interaction is non-trivial but bounded
- Debugging a single service's failing test with non-obvious root cause

**`thinking: max`** — requires extended thinking; always paired with Opus 4.8:

- Novel trading archetype topology (carry_staked_basis, leveraged_funding_arb family decisions)
- Cross-repo migration pre-audit (all consumers must be in context, breakage is non-obvious)
- Complex multi-service debugging where the bug crosses 3+ system boundaries
- Schema design decisions with long-tail correctness implications (manifest columns, shard atoms)
- Trading judgment calls (position sizing, risk-limit calibration, archetype risk trade-offs)
- Work-split drafting by main orchestrator (reads all 50+ active plans to allocate)
- Anything where the agent must hold contradictory constraints and find a non-obvious resolution

### Pairing rules

`thinking: max` requires `model_tier: opus-required` — no exceptions. Extended thinking on Sonnet is not available in
this workspace's Claude Code configuration.

`thinking: high` works on either model tier. Sonnet 4.6 at high thinking is preferred over Opus at medium.

`thinking: medium` on Opus is always wrong (use Sonnet instead).

### Work-split slot declaration

```markdown
| Slot | Theme                     | Plan                   | model_tier    | thinking | Cal AI-days |
| ---- | ------------------------- | ---------------------- | ------------- | -------- | ----------- |
| 1    | Main orchestrator         | LEDGER                 | opus-required | max      | continuous  |
| 2    | defi_catalogue impl       | defi_catalogue         | sonnet-doable | high     | ~16         |
| 3    | ruff cleanup              | ruff_workspace_cleanup | sonnet-doable | medium   | ~0.4        |
| 5    | archetype topology design | defi_recursive_borrow  | opus-required | max      | ~14         |
```

### Spawn prompt header (required fields)

```
MODEL TIER: Sonnet 4.6 | Opus 4.8
THINKING: medium | high | max
[If max]: OPUS-REQUIRED — REASON: <one-line reason>
```

---

## Self-check — thinking effort (extend the Step 3 model check)

After checking model tier, check thinking effort:

**How the agent knows its thinking level**: The spawn prompt declares it. If not declared, the agent infers from the
task description using the tier definitions above, then flags if it cannot confirm the setting matches.

| Declared thinking                                         | Task actually needs | Action                                        |
| --------------------------------------------------------- | ------------------- | --------------------------------------------- |
| medium                                                    | medium              | ✅ Proceed                                    |
| high                                                      | high                | ✅ Proceed                                    |
| max (+ Opus)                                              | max                 | ✅ Proceed                                    |
| **under-provisioned** (medium→high, medium→max, high→max) | higher              | 🔴 **HARD STOP — wait for operator override** |
| **over-provisioned** (max→high, max→medium, high→medium)  | lower               | 🔴 **HARD STOP — wait for operator override** |

**Both directions are hard stops.** The operator gets to see the mismatch and decide — either confirm the deviation is
intentional ("proceed anyway") or fix the spawn tier. This avoids silent quality degradation (under) and silent money
burn (over).

**Under-provisioned stop block:**

```
🔴 HARD STOP — THINKING UNDER-PROVISIONED
Declared: thinking: <declared>
Task requires: thinking: <required>
Reason: <one-line — e.g. "cross-repo migration pre-audit requires holding all consumer files simultaneously">

I cannot start this task at the declared thinking tier without risking silent quality degradation.

To proceed:
  Option A — fix the tier: re-spawn with THINKING: <required> (and MODEL: Opus 4.8 if max)
  Option B — override: reply "proceed anyway" and I will start at the declared tier with a quality caveat
```

**Over-provisioned stop block:**

```
🔴 HARD STOP — THINKING OVER-PROVISIONED (COST WASTE)
Declared: thinking: <declared>
Task needs: thinking: <required>
Reason: <one-line — e.g. "ruff cleanup is mechanical; max thinking adds no quality, only cost">

Estimated unnecessary spend: ~<N>× vs correct tier.

To proceed:
  Option A — fix the tier: re-spawn with THINKING: <required> (saves ~<N>× cost)
  Option B — override: reply "proceed anyway" and I will start at the declared tier
```

**Override handling**: if the operator replies "proceed anyway" (or equivalent), the agent starts immediately with a
one-line caveat in its first output ("proceeding at <tier> per operator override"). No further stops.

---

_Companion plan_: `plans/active/ruff_workspace_cleanup_*.md` (example of correctly classified Sonnet-suitable work).
_Enforced by_: work-split review — any slot missing `model_tier` or `thinking` defaults to Sonnet 4.6 / medium.
