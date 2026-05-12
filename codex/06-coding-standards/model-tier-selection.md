# Model Tier Selection — Sonnet 4.6 vs Opus 4.7

**Rule**: Default to Sonnet 4.6. Opus 4.7 is a deliberate exception requiring justification. Every work-split MUST
classify each plan/slot as Sonnet-doable or Opus-required before spawning agents.

---

## The two tiers

| Tier | Model | Context | Cost | Use when |
|------|-------|---------|------|----------|
| **Default** | `claude-sonnet-4-6` | 200k | Low | Everything that fits in 200k context without multi-repo synthesis |
| **Escalation** | `claude-opus-4-7` | 1M | High (~5-10×) | Main orchestrator, cross-repo architecture decisions, tasks whose context provably exceeds 200k |

---

## Decision rule (apply at work-split time, per slot)

```
IF slot is main orchestrator (slot 1)     → Opus 4.7
IF task requires simultaneous reading of  → Opus 4.7
   >3 full service codebases OR
   a plan >50KB + multiple full files OR
   1M-context reasoning across the entire
   workspace state
OTHERWISE                                 → Sonnet 4.6
```

**When in doubt, use Sonnet 4.6 and escalate only if the agent hits a genuine context wall.**
Do NOT pre-escalate "just in case" — that is money waste with no quality upside for bounded tasks.

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

## Opus 4.7 — only for these

- **Slot 1 main orchestrator**: boot checklist, ledger sweep, cross-slot Q&A dispatch, plan curation, ping triage,
  master plan refresh. Orchestrator context = entire workspace state → requires 1M window.
- **Cross-repo architecture decisions**: design tasks that require simultaneously reading UAC schema + UTL helpers +
  3+ service implementations + codex SSOT to make a coherent decision (e.g., new shard-atom design, new manifest
  column rationale, signal-broadcast topology).
- **Large migration design**: tasks where the full impact surface (all consumers across all repos) must be in context
  simultaneously to avoid silent breakage (pre-audit manifests for public API changes).
- **Trading judgment calls**: position sizing, risk-limit calibration, archetype topology decisions — requires holding
  the entire live-pipeline architecture in context.
- **>200k context provably required**: if the agent's plan-of-record + all referenced files + the task output
  provably exceed 200k tokens, escalate. Document the reason in the spawn prompt: `OPUS-REQUIRED: <reason>`.

---

## Work-split classification protocol

Every slot in `work_split_<YYYY_MM_DD>_<side>.md` MUST include a `model_tier` field:

```markdown
| Slot | Theme | Plan-of-record | model_tier | Cal AI-days |
|------|-------|----------------|------------|-------------|
| 1    | Main orchestrator | LEDGER.md | **Opus 4.7** | continuous |
| 2    | defi_catalogue impl | defi_catalogue_chain_primitives | **Sonnet 4.6** | ~16 |
| 3    | code_freeze audit | code_freeze_migrate_backfill | **Sonnet 4.6** | ~14 |
```

Classification is the **first thing** the operator or main-orch agent fills in when drafting the split.
If model_tier is absent from a slot row, the agent MUST use Sonnet 4.6 and flag the omission.

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

Add `model_tier: sonnet-doable | opus-required` to each plan's frontmatter on the next substantive touch
(same logical unit as the substantive change — do NOT mass-sweep, per Findings Triage).

---

## Continuation prompt template (model tier enforcement)

When spawning a Sonnet 4.6 agent, start the prompt with:

```
MODEL TIER: Sonnet 4.6 (200k context). This task is bounded and does not require Opus.
If you hit a genuine context wall (cannot fit all needed files), stop and report — do NOT
silently skip files or hallucinate from partial context.
```

When spawning Opus 4.7, state the reason:

```
MODEL TIER: Opus 4.7 — REASON: [main orchestrator / cross-repo architecture / >200k context provably required].
```

---

## Self-check at task start (MANDATORY)

Every agent MUST perform this check as the **first action** of every task, before reading files or writing code.

### Step 1 — read your own model

The running model is stated in the system prompt: `"You are powered by the model named <X>"`. Read it. You always
know which model you are.

### Step 2 — read the required tier

From (in priority order):
1. The spawn prompt: look for `MODEL TIER: Sonnet 4.6` or `MODEL TIER: Opus 4.7 — REASON: ...`
2. The work-split slot row: `model_tier: sonnet-doable | opus-required`
3. The plan frontmatter: `model_tier:` field
4. If none of the above: apply the decision rule (main orchestrator → Opus; everything else → Sonnet)

### Step 3 — check for mismatch and act

| Running model | Required tier | Action |
|---|---|---|
| Sonnet 4.6 | sonnet-doable | ✅ Proceed |
| Opus 4.7 | opus-required | ✅ Proceed |
| **Sonnet 4.6** | **opus-required** | 🔴 **STOP — flag to operator, do not proceed** |
| **Opus 4.7** | **sonnet-doable** | 🟡 **FLAG to operator, then proceed (don't block on money waste)** |

**When Sonnet 4.6 detects opus-required task** — output this block and stop:

```
⚠️ WRONG MODEL — CANNOT PROCEED
Task requires: Opus 4.7 (1M context)
Running as: Sonnet 4.6 (200k context)
Reason this task needs Opus: <state the reason from spawn prompt or decision rule>

ACTION REQUIRED: Please reopen this tab/slot on Opus 4.7.
In Claude Code: use /model claude-opus-4-7 or restart with --model claude-opus-4-7
I will not start the task until the model is correct.
```

**When Opus 4.7 detects sonnet-doable task** — output this block then proceed:

```
💸 WRONG MODEL — PROCEEDING BUT FLAGGING COST WASTE
Task is: sonnet-doable
Running as: Opus 4.7 (unnecessary — ~5-10× more expensive)
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

---

*Companion plan*: `plans/active/ruff_workspace_cleanup_*.md` (example of correctly classified Sonnet-suitable work).
*Enforced by*: work-split review — any slot missing `model_tier` defaults to Sonnet 4.6.
